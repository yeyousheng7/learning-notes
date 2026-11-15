"""Keep private originals local and publish only encrypted spark articles."""

from __future__ import annotations

import argparse
import base64
from datetime import date
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import secrets
import sys
import tomllib
import uuid

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from markdown import Markdown
import yaml


ROOT = Path(__file__).resolve().parents[1]
POSTS = Path("docs/sparks/posts")
ITERATIONS = 600_000
PREVIEW_ENV = "SPARKS_LOCAL_PREVIEW"
_ID = re.compile(r"[0-9a-f]{32}")
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="strict")
    except UnicodeError:
        raise ValueError(f"{path}: 不是有效的 UTF-8 文件，请先确认编码。") from None


def parse_document(path: Path) -> tuple[dict, str]:
    text = read_text(path)
    match = _FRONTMATTER.match(text)
    if not match:
        raise ValueError(f"{path}: 缺少开头的 YAML 元信息。")
    meta = yaml.safe_load(match[1])
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: 元信息必须是键值配置。")
    return meta, text[match.end():]


def encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode(data: str) -> bytes:
    return base64.b64decode(data, validate=True)


def derive_key(password: str, salt: str) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), decode(salt), ITERATIONS, 32)


def aad(identifier: str) -> bytes:
    return f"private-spark:v1:{identifier}".encode("ascii")


def public_stub() -> str:
    return "内容已加密。\n\n<!-- more -->\n"


def document(meta: dict, body: str) -> str:
    return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + body


def sources(root: Path = ROOT) -> list[tuple[Path, dict, str]]:
    result = []
    seen = set()
    for path in sorted((root / "local/sparks").rglob("*.md")):
        meta, body = parse_document(path)
        identifier = str(meta.get("id", ""))
        if not _ID.fullmatch(identifier) or identifier in seen:
            raise ValueError(f"{path}: id 必须是唯一的 32 位随机编号，请用 new 命令创建文章。")
        seen.add(identifier)
        if meta.get("encrypted") is not True:
            raise ValueError(f"{path}: local/sparks 中的文章必须设置 encrypted: true。公开文章请放到 docs/sparks/posts。")
        if not isinstance(meta.get("date"), date):
            raise ValueError(f"{path}: 请设置 date: YYYY-MM-DD。")
        title = meta.get("public_title")
        if not isinstance(title, str) or not title.strip() or "\n" in title:
            raise ValueError(f"{path}: 请设置单行 public_title，作为对外展示的标题。")
        if "draft" in meta and not isinstance(meta["draft"], bool):
            raise ValueError(f"{path}: draft 必须为 true 或 false。")
        result.append((path, meta, body))
    return result


def public_meta(meta: dict, payload: dict | None = None) -> dict:
    result = {
        "title": meta["public_title"],
        "date": meta["date"],
        "slug": "private-" + meta["id"],
        "encrypted": True,
        "search": {"exclude": True},
    }
    if "draft" in meta:
        result["draft"] = meta["draft"]
    if payload is not None:
        result["private_spark"] = payload
    return result


def validate_published(path: Path) -> dict:
    meta, body = parse_document(path)
    payload = meta.get("private_spark", {})
    try:
        identifier = payload["id"]
        valid = (
            _ID.fullmatch(identifier)
            and path.name == f"private-{identifier}.md"
            and meta["slug"] == f"private-{identifier}"
            and meta["encrypted"] is True
            and meta["search"] == {"exclude": True}
            and payload["version"] == 1
            and payload["iterations"] == ITERATIONS
            and len(decode(payload["salt"])) == 16
            and len(decode(payload["nonce"])) == 12
            and len(decode(payload["ciphertext"])) >= 16
            and body.strip() == public_stub().strip()
            and set(meta) <= {"title", "date", "slug", "encrypted", "search", "draft", "private_spark"}
        )
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError(f"{path}: 加密发布文件无效。请将原文移至 local/sparks，再运行 prepare；不能直接发布明文。")
    return meta


class _TextOnly(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag in {"img", "svg", "script", "style", "iframe", "object", "embed", "audio", "video", "link"}:
            raise ValueError("私密文章目前仅支持文字和 Markdown 排版，请移除图片、嵌入内容或脚本。")


def render_body(body: str, config: dict) -> bytes:
    extensions, settings = [], {}
    for extension in config["markdown_extensions"]:
        if isinstance(extension, str):
            extensions.append(extension)
        else:
            for name, options in extension.items():
                extensions.append(name)
                settings[name] = options or {}
    html = Markdown(extensions=extensions, extension_configs=settings).convert(body)
    _TextOnly().feed(html)
    return html.encode("utf-8")


def init(root: Path = ROOT) -> None:
    (root / "local/sparks").mkdir(parents=True, exist_ok=True)
    path = root / "local/sparks.toml"
    if not path.exists():
        path.write_text(
            '# 仅在本机保存，不要提交。所有私密灵光共用此密码。\n'
            '# 将密码填在单引号内；密码不能含单引号或换行。\n'
            "password = ''\n"
            f'salt = "{encode(secrets.token_bytes(16))}"\n',
            encoding="utf-8",
        )
    print("本地目录已准备好。请在 local/sparks.toml 中设置 password。")


def new(title: str, root: Path = ROOT) -> None:
    init(root)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title).strip(" .") or "随想"
    path = root / "local/sparks" / (name + ".md")
    if path.exists():
        raise ValueError("同名原文已存在，请换一个标题。")
    meta = {"id": uuid.uuid4().hex, "date": date.today(), "encrypted": True, "public_title": title}
    path.write_text(document(meta, "正文从这里开始。\n"), encoding="utf-8")
    print(f"已创建 {path.relative_to(root)}。文件名可以修改，id 请保持不变。")


def prepare(root: Path = ROOT, *, prune: bool = False) -> None:
    path = root / "local/sparks.toml"
    if not path.exists():
        raise ValueError("请先运行 init，并在 local/sparks.toml 中设置密码。")
    settings = tomllib.loads(read_text(path))
    password, salt = settings.get("password"), settings.get("salt", "")
    if not isinstance(password, str) or not password.strip():
        raise ValueError("local/sparks.toml 尚未设置 password，已停止，不会生成明文文件。")
    if len(decode(salt)) != 16:
        raise ValueError("local/sparks.toml 中的 salt 无效，请保留 init 生成的值。")
    key = derive_key(password, salt)
    config = yaml.safe_load(read_text(root / "mkdocs.yml"))
    output = root / POSTS
    output.mkdir(parents=True, exist_ok=True)
    expected, pending = set(), []
    # Validate and encrypt everything before writing any publication files.
    for source, meta, body in sources(root):
        identifier = meta["id"]
        target = output / f"private-{identifier}.md"
        expected.add(target)
        plain = render_body(body, config)
        payload = None
        if target.exists():
            old = validate_published(target)["private_spark"]
            if old["salt"] == salt:
                try:
                    if AESGCM(key).decrypt(decode(old["nonce"]), decode(old["ciphertext"]), aad(identifier)) == plain:
                        payload = old
                except InvalidTag:
                    pass  # Password changed: re-encrypt using the new key.
        if payload is None:
            nonce = secrets.token_bytes(12)
            payload = {
                "version": 1, "id": identifier, "iterations": ITERATIONS, "salt": salt,
                "nonce": encode(nonce),
                "ciphertext": encode(AESGCM(key).encrypt(nonce, plain, aad(identifier))),
            }
        text = document(public_meta(meta, payload), public_stub())
        if not target.exists() or read_text(target) != text:
            pending.append((target, text))
    stale = []
    for target in sorted(output.glob("private-*.md")):
        validate_published(target)
        if target not in expected:
            stale.append(target)
    if stale and not prune:
        names = ", ".join(path.name for path in stale)
        raise ValueError(f"以下发布文件没有对应本地原文：{names}。请先确认原文是否齐全；确认删除后运行 prepare --prune。")
    for target, text in pending:
        temporary = target.with_suffix(".md.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(target)
    for target in stale:
        target.unlink()
    print(f"已同步 {len(expected)} 篇加密灵光，更新 {len(pending)} 篇，清理 {len(stale)} 篇。请检查 git diff 后提交。")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="准备本地目录和密码配置")
    create = commands.add_parser("new", help="创建一篇私密灵光原文")
    create.add_argument("title", help="初始公开标题，也用作本地文件名")
    publish = commands.add_parser("prepare", help="同步生成可提交的加密文章")
    publish.add_argument("--prune", action="store_true", help="确认删除没有本地原文的生成文件")
    preview = commands.add_parser("preview", help="仅在本机预览私密原文，不生成发布文件")
    preview.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        if args.command == "init":
            init()
        elif args.command == "new":
            new(args.title)
        elif args.command == "prepare":
            prepare(prune=args.prune)
        else:
            from mkdocs.commands.serve import serve

            (ROOT / "local/sparks").mkdir(parents=True, exist_ok=True)
            os.environ[PREVIEW_ENV] = "1"
            print(f"本地写作预览：http://127.0.0.1:{args.port}/\n私密原文直接显示，仅监听本机。Ctrl+C 停止。", flush=True)
            serve(config_file=str(ROOT / "mkdocs.yml"), dev_addr=f"127.0.0.1:{args.port}")
    except (ValueError, OSError, yaml.YAMLError) as error:
        # Never echo config contents or YAML/TOML parser input (may contain secrets).
        if isinstance(error, (yaml.YAMLError, tomllib.TOMLDecodeError)):
            print("配置或文章元信息格式有误，请检查 YAML / local/sparks.toml。", file=sys.stderr)
        else:
            print(str(error), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
