"""Files dropped on the Scraping tab land in inbox/<economy>/<source>/<batch>/ once, under their own safe
name, with the address they came from noted beside them. Only an economy's designated sources are taken."""
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import settings as settings_mod, sources
from rdtii_ui.pages import inbox
from rdtii_ui.server import ApiError

BATCH = "2026-10-03_101522"


class Names(unittest.TestCase):
    def test_paths_are_stripped_and_formats_checked(self):
        self.assertEqual(inbox.safe_name("C:\\Users\\me\\Cyber Law (2017).pdf"), "Cyber Law (2017).pdf")
        self.assertEqual(inbox.safe_name("../../etc/passwd.html"), "passwd.html")
        self.assertEqual(inbox.safe_name("网络安全法.docx"), "网络安全法.docx")
        self.assertEqual(inbox.safe_name(".hidden.pdf"), "hidden.pdf")   # leading dots are dropped, not refused
        with self.assertRaises(ApiError):
            inbox.safe_name("notes.txt")
        with self.assertRaises(ApiError):
            inbox.safe_name("...")

    def test_a_long_name_keeps_its_suffix(self):
        name = inbox.safe_name("x" * 300 + ".pdf")
        self.assertEqual(len(name), 160)
        self.assertTrue(name.endswith(".pdf"))


class Save(unittest.TestCase):
    def _settings(self, root: Path):
        return settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs"), "RDTII_INBOX_DIR": str(root / "inbox")})

    def test_add_twice_keeps_one_copy_and_renames_a_different_file(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            r1 = inbox.save(s, "cn", "miit", "law.pdf", b"%PDF-1.4 one")
            self.assertEqual((r1["status"], r1["count"], r1["source"]), ("added", 1, "miit"))
            self.assertTrue((Path(d) / "inbox" / "CN" / "miit" / "law.pdf").is_file())
            r2 = inbox.save(s, "CN", "miit", "law.pdf", b"%PDF-1.4 one")
            self.assertEqual((r2["status"], r2["count"]), ("already there", 1))
            r3 = inbox.save(s, "CN", "miit", "law.pdf", b"%PDF-1.4 two")
            self.assertEqual(r3["saved"], "law (2).pdf")
            self.assertEqual(r3["count"], 2)
            self.assertFalse(list((Path(d) / "inbox" / "CN" / "miit").glob("*.part")))

    def test_a_drop_lands_in_its_source_and_batch_folder(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            r = inbox.save(s, "CN", "miit", "a.pdf", b"%PDF-1.4 a", BATCH)
            self.assertEqual(r["batch"], BATCH)
            self.assertTrue((Path(d) / "inbox" / "CN" / "miit" / BATCH / "a.pdf").is_file())
            inbox.save(s, "CN", "miit", "b.pdf", b"%PDF-1.4 b", BATCH)
            inbox.save(s, "CN", "customs", "c.pdf", b"%PDF-1.4 c")
            e = next(x for x in inbox.describe(s)["economies"] if x["code"] == "CN")
            self.assertEqual((e["files"], e["unsorted"]), (3, 0))
            by = {x["key"]: x for x in e["sources"]}
            self.assertEqual([x["key"] for x in e["sources"]], ["npc-database", "miit", "customs"])
            self.assertEqual((by["miit"]["files"], by["customs"]["files"], by["npc-database"]["files"]), (2, 1, 0))
            self.assertEqual([(b["name"], b["files"]) for b in by["miit"]["batches"]], [(BATCH, 2)])
            self.assertEqual(by["customs"]["loose"], 1)
            files = inbox.list_files(Path(d) / "inbox" / "CN" / "miit")
            self.assertEqual({f["name"]: f["batch"] for f in files}, {f"{BATCH}/a.pdf": BATCH, f"{BATCH}/b.pdf": BATCH})
            with self.assertRaises(ApiError):
                inbox.save(s, "CN", "miit", "d.pdf", b"%PDF-1.4 d", "../evil")

    def test_only_designated_sources_are_taken(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            for bad in ("", "random-site", "../miit", "MIIT/.."):
                with self.assertRaises(ApiError, msg=bad) as cm:
                    inbox.save(s, "CN", bad, "law.pdf", b"%PDF-1.4")
                self.assertIn("designated", str(cm.exception))
            self.assertFalse((Path(d) / "inbox" / "CN").exists())       # a refused drop writes nothing
            sg = sources.designated(s, "SG")[0]["key"]
            self.assertEqual(inbox.save(s, "SG", sg, "guide.pdf", b"%PDF-1.4")["source"], sg)

    def test_bad_economy_or_empty_file_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            with self.assertRaises(ApiError):
                inbox.save(s, "XX", "miit", "law.pdf", b"%PDF")
            with self.assertRaises(ApiError):
                inbox.save(s, "CN", "miit", "law.pdf", b"")

    def test_describe_lists_every_economy_with_counts(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            la = sources.designated(s, "LA")[0]["key"]
            inbox.save(s, "LA", la, "a.pdf", b"%PDF-1.4")
            desc = inbox.describe(s)
            by = {e["code"]: e for e in desc["economies"]}
            self.assertEqual(by["LA"]["files"], 1)
            self.assertEqual(by["SG"]["files"], 0)
            self.assertEqual([e["code"] for e in desc["economies"]][:6], ["SG", "AU", "MY", "TL", "LA", "CN"])
            self.assertTrue(all(e["sources"] for e in desc["economies"][:6]))      # every economy has its list
            files = inbox.list_files(Path(d) / "inbox" / "LA" / la)
            self.assertEqual([(f["name"], f["kind"], f["size"]) for f in files], [("a.pdf", "pdf", 8)])

    def test_files_of_the_older_layout_are_counted_as_unsorted(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            old = Path(d) / "inbox" / "CN" / "2026-09-30_101522"
            old.mkdir(parents=True)
            (old / "x.pdf").write_bytes(b"%PDF-1.4")
            (Path(d) / "inbox" / "CN" / "loose.pdf").write_bytes(b"%PDF-1.4")
            inbox.save(s, "CN", "miit", "a.pdf", b"%PDF-1.4 a")
            e = next(x for x in inbox.describe(s)["economies"] if x["code"] == "CN")
            self.assertEqual((e["files"], e["unsorted"]), (3, 2))


class Addresses(unittest.TestCase):
    def _settings(self, root: Path):
        return settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs"), "RDTII_INBOX_DIR": str(root / "inbox")})

    def test_a_saved_page_brings_its_own_address(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            page = b"<!DOCTYPE html>\n<!-- saved from url=(0040)https://www.miit.gov.cn/zwgk/art/x.html -->\n<html><body>x</body></html>"
            r = inbox.save(s, "CN", "miit", "rule.html", page, BATCH)
            self.assertEqual(r["url"], "https://www.miit.gov.cn/zwgk/art/x.html")
            self.assertIn("saved-from", r["url_basis"])
            row = inbox.read_provenance(Path(d) / "inbox" / "CN" / "miit" / BATCH)["rule.html"]
            self.assertEqual((row["url"], row["source"]), ("https://www.miit.gov.cn/zwgk/art/x.html", "miit"))
            self.assertRegex(row["fetched_on"], r"^\d{4}-\d{2}-\d{2}$")

    def test_an_address_can_be_typed_at_the_drop_or_afterwards(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            r = inbox.save(s, "CN", "customs", "notice.pdf", b"%PDF-1.4", BATCH, "https://www.customs.gov.cn/a/1.pdf")
            self.assertEqual((r["url"], r["url_basis"]), ("https://www.customs.gov.cn/a/1.pdf", "typed on the page"))
            inbox.save(s, "CN", "customs", "other.pdf", b"%PDF-1.4 b", BATCH)
            self.assertEqual(inbox.list_files(Path(d) / "inbox" / "CN" / "customs")[1]["url"], "")
            got = inbox.set_address(s, "CN", "customs", BATCH, "other.pdf", "https://www.customs.gov.cn/a/2.pdf")
            self.assertEqual(got["url"], "https://www.customs.gov.cn/a/2.pdf")
            urls = {f["name"].split("/")[-1]: f["url"] for f in inbox.list_files(Path(d) / "inbox" / "CN" / "customs")}
            self.assertEqual(urls, {"notice.pdf": "https://www.customs.gov.cn/a/1.pdf", "other.pdf": "https://www.customs.gov.cn/a/2.pdf"})
            for bad in ("javascript:alert(1)", "file:///C:/x", "www.customs.gov.cn/x", "https://a b"):
                with self.assertRaises(ApiError, msg=bad):
                    inbox.set_address(s, "CN", "customs", BATCH, "other.pdf", bad)
            with self.assertRaises(ApiError):
                inbox.set_address(s, "CN", "customs", BATCH, "missing.pdf", "https://www.customs.gov.cn/x")

    def test_the_china_collections_own_sheet_is_read(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            (folder / "provenance.tsv").write_text("n\ttitle\turl\tfile_saved_as\n1\tA rule\thttps://www.miit.gov.cn/a.html\ta.html\n", encoding="utf-8")
            self.assertEqual(inbox.read_provenance(folder)["a.html"]["url"], "https://www.miit.gov.cn/a.html")


class Archive(unittest.TestCase):
    def _settings(self, root: Path):
        return settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs"), "RDTII_INBOX_DIR": str(root / "inbox")})

    def _zip(self, members: dict) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for name, data in members.items():
                zf.writestr(name, data)
        return buf.getvalue()

    def test_a_bulk_download_is_unpacked_flat_and_safely(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            data = self._zip({"laws/a.docx": b"PK-a", "b.pdf": b"%PDF-1.4", "../../evil.pdf": b"%PDF-evil",
                              "readme.txt": b"no", "sub/": b""})
            r = inbox.save(s, "CN", "npc-database", "export.zip", data, BATCH)
            folder = Path(d) / "inbox" / "CN" / "npc-database" / BATCH
            self.assertEqual(sorted(p.name for p in folder.iterdir() if p.suffix != ".tsv"), ["a.docx", "b.pdf", "evil.pdf"])
            self.assertEqual((r["unpacked"]["added"], r["unpacked"]["skipped"]), (3, 1))
            self.assertIn("unpacked: 3 added", r["status"])
            self.assertFalse((Path(d) / "evil.pdf").exists())                   # nothing written outside the folder
            self.assertFalse((folder / "export.zip").exists())                  # the archive itself is not kept
            again = inbox.save(s, "CN", "npc-database", "export.zip", data, BATCH)
            self.assertEqual((again["unpacked"]["added"], again["unpacked"]["already_there"]), (0, 3))

    def test_names_written_on_a_chinese_system_are_read(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            # zipfile always flags its own non-ASCII names as UTF-8, so the GBK bytes are put in afterwards
            data = self._zip({"XXXXXXXXXX.docx": b"PK-a"}).replace(b"XXXXXXXXXX", "网络安全法".encode("gbk"))
            r = inbox.save(s, "CN", "npc-database", "export.zip", data, BATCH)
            self.assertEqual(r["unpacked"]["added"], 1)
            self.assertTrue((Path(d) / "inbox" / "CN" / "npc-database" / BATCH / "网络安全法.docx").is_file())

    def test_not_a_zip_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ApiError):
                inbox.save(self._settings(Path(d)), "CN", "npc-database", "export.zip", b"not a zip")


if __name__ == "__main__":
    unittest.main()
