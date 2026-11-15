"""Validate encrypted publications and opt into loopback-only writing previews."""

import os
from pathlib import Path
import sys
import tempfile
import yaml

from mkdocs.exceptions import PluginError
from mkdocs.plugins import event_priority
from mkdocs.structure.files import File

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sparks import (  # noqa: E402
    PREVIEW_ENV, document, parse_document, public_meta, sources, validate_published,
)

_command = None
_temporary = None


def on_startup(*, command, dirty):
    global _command
    _command = command


def on_config(config):
    if os.environ.get(PREVIEW_ENV) != "1":
        return
    if _command != "serve" or config.dev_addr.host != "127.0.0.1":
        raise PluginError("私密原文只能通过本机写作预览查看，不能用于正式构建或远程监听。")
    root = Path(config.config_file_path).parent
    config.watch.append(str(root / "local/sparks"))


@event_priority(100)
def on_files(files, *, config):
    global _temporary
    try:
        # Fail before rendering/search if an encrypted source was put in docs.
        for file in files.documentation_pages():
            if not file.src_uri.startswith("sparks/posts/"):
                continue
            path = Path(file.abs_src_path)
            meta, _ = parse_document(path)
            if meta.get("encrypted") or path.name.startswith("private-"):
                validate_published(path)

        if os.environ.get(PREVIEW_ENV) != "1":
            return files
        root = Path(config.config_file_path).parent
        if _temporary is None:
            _temporary = tempfile.TemporaryDirectory(prefix="sparks-preview-", dir=root / "local")
        for _, meta, body in sources(root):
            filename = f"private-{meta['id']}.md"
            published = f"sparks/posts/{filename}"
            old = files.get_file_from_path(published)
            if old is not None:
                files.remove(old)
            preview_meta = public_meta(meta)
            preview_meta["private_preview"] = True
            target = Path(_temporary.name) / filename
            target.write_text(document(preview_meta, body), encoding="utf-8")
            files.append(File.generated(config, published, abs_src_path=str(target)))
    except yaml.YAMLError:
        raise PluginError("文章 YAML 元信息格式有误，请检查原文；已停止构建。") from None
    except ValueError as error:
        raise PluginError(str(error)) from None
    return files


def on_shutdown():
    global _temporary
    if _temporary is not None:
        _temporary.cleanup()
        _temporary = None
