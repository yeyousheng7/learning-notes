"""Publication boundaries, encryption and synchronization of private sparks."""

from contextlib import redirect_stdout
from datetime import date
import io
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
import uuid

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import sparks
from hooks import private_sparks
from mkdocs.exceptions import PluginError
from types import SimpleNamespace


class PrivateSparksTests(unittest.TestCase):
    def setUp(self):
        self.root = (sparks.ROOT / ".uv-cache" / ("spark-test-" + uuid.uuid4().hex)).resolve()
        self.root.relative_to((sparks.ROOT / ".uv-cache").resolve())
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        with redirect_stdout(io.StringIO()):
            sparks.init(self.root)
        self.set_password("用于测试的密码-one")
        (self.root / "mkdocs.yml").write_text("markdown_extensions:\n  - fenced_code\n", encoding="utf-8")
        self.identifier = uuid.uuid4().hex
        self.meta = {"id": self.identifier, "date": date(2026, 11, 15), "encrypted": True, "public_title": "公开标题"}
        self.source = self.root / "local/sparks/不能公开的文件名.md"
        self.target = self.root / sparks.POSTS / f"private-{self.identifier}.md"
        self.write_source("非常私密的测试正文，含 **强调** 和 < & 符号。")

    def set_password(self, password):
        path = self.root / "local/sparks.toml"
        settings = sparks.tomllib.loads(sparks.read_text(path))
        self.salt = settings["salt"]
        path.write_text(f"password = '{password}'\nsalt = '{self.salt}'\n", encoding="utf-8")
        self.password = password

    def write_source(self, body):
        self.source.write_text(sparks.document(self.meta, body), encoding="utf-8")

    def prepare(self, **kwargs):
        with redirect_stdout(io.StringIO()):
            sparks.prepare(self.root, **kwargs)

    def decrypt(self):
        payload = sparks.validate_published(self.target)["private_spark"]
        key = sparks.derive_key(self.password, self.salt)
        return AESGCM(key).decrypt(sparks.decode(payload["nonce"]), sparks.decode(payload["ciphertext"]), sparks.aad(self.identifier))

    def test_publication_has_no_original_or_password_and_roundtrips(self):
        self.prepare()
        published = sparks.read_text(self.target)
        for secret in ["非常私密", "不能公开的文件名", self.password, "public_title"]:
            self.assertNotIn(secret, published)
        self.assertIn("公开标题", published)
        self.assertIn("<strong>强调</strong>", self.decrypt().decode("utf-8"))
        self.assertEqual(sparks.validate_published(self.target)["search"], {"exclude": True})

    def test_rename_and_unchanged_content_keep_ciphertext(self):
        self.prepare()
        first = self.target.read_bytes()
        self.source = self.source.rename(self.source.with_name("重命名.md"))
        self.prepare()
        self.assertEqual(first, self.target.read_bytes())
        self.meta["public_title"] = "新的公开标题"
        payload = sparks.validate_published(self.target)["private_spark"]
        self.write_source("非常私密的测试正文，含 **强调** 和 < & 符号。")
        self.prepare()
        self.assertEqual(payload, sparks.validate_published(self.target)["private_spark"])

    def test_edit_password_rotation_and_authenticated_id(self):
        self.prepare()
        old_key = sparks.derive_key(self.password, self.salt)
        self.set_password("另一个测试密码-two")
        self.write_source("更新后的私密正文")
        self.prepare()
        payload = sparks.validate_published(self.target)["private_spark"]
        self.assertIn("更新后的私密正文", self.decrypt().decode("utf-8"))
        with self.assertRaises(InvalidTag):
            AESGCM(old_key).decrypt(sparks.decode(payload["nonce"]), sparks.decode(payload["ciphertext"]), sparks.aad(self.identifier))
        with self.assertRaises(InvalidTag):
            AESGCM(sparks.derive_key(self.password, self.salt)).decrypt(
                sparks.decode(payload["nonce"]), sparks.decode(payload["ciphertext"]), sparks.aad(uuid.uuid4().hex))

    def test_missing_password_bad_encoding_and_images_stop_publication(self):
        self.set_password("")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.target.exists())
        self.set_password("测试密码")
        self.source.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            self.prepare()
        self.write_source("![私密图片](secret.png)")
        with self.assertRaisesRegex(ValueError, "仅支持文字"):
            self.prepare()
        self.assertFalse(self.target.exists())

    def test_plaintext_in_published_stub_is_rejected(self):
        self.prepare()
        self.target.write_text(sparks.read_text(self.target) + "泄露的明文", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "不能直接发布明文"):
            sparks.validate_published(self.target)

    def test_stale_publications_require_explicit_prune(self):
        self.prepare()
        public = self.target.with_name("ordinary.md")
        public.write_text("普通文章", encoding="utf-8")
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, "--prune"):
            self.prepare()
        self.assertTrue(self.target.exists())
        self.prepare(prune=True)
        self.assertFalse(self.target.exists())
        self.assertTrue(public.exists())

    def test_invalid_source_does_not_partially_update_other_articles(self):
        self.prepare()
        first = self.target.read_bytes()
        self.write_source("修改后的正文")
        bad = self.root / "local/sparks/第二篇.md"
        meta = dict(self.meta, id=uuid.uuid4().hex)
        bad.write_text(sparks.document(meta, "![图片](secret.png)"), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(self.target.read_bytes(), first)

    def test_preview_cannot_be_used_for_production_or_remote_binding(self):
        config = SimpleNamespace(dev_addr=SimpleNamespace(host="127.0.0.1"))
        with patch.dict(sparks.os.environ, {sparks.PREVIEW_ENV: "1"}):
            with patch.object(private_sparks, "_command", "build"):
                with self.assertRaises(PluginError):
                    private_sparks.on_config(config)
            config.dev_addr.host = "0.0.0.0"
            with patch.object(private_sparks, "_command", "serve"):
                with self.assertRaises(PluginError):
                    private_sparks.on_config(config)


if __name__ == "__main__":
    unittest.main()
