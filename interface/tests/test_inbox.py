"""Files dropped on the Scraping tab land in inbox/<economy>/ once, under their own safe name."""
import tempfile
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import settings as settings_mod
from rdtii_ui.pages import inbox
from rdtii_ui.server import ApiError


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


class Save(unittest.TestCase):
    def _settings(self, root: Path):
        return settings_mod.load({"RDTII_RUNS_ROOT": str(root / "outputs"), "RDTII_INBOX_DIR": str(root / "inbox")})

    def test_add_twice_keeps_one_copy_and_renames_a_different_file(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            r1 = inbox.save(s, "cn", "law.html", b"<p>one</p>")
            self.assertEqual((r1["status"], r1["count"]), ("added", 1))
            self.assertTrue((Path(d) / "inbox" / "CN" / "law.html").is_file())
            r2 = inbox.save(s, "CN", "law.html", b"<p>one</p>")
            self.assertEqual((r2["status"], r2["count"]), ("already there", 1))
            r3 = inbox.save(s, "CN", "law.html", b"<p>two</p>")
            self.assertEqual(r3["saved"], "law (2).html")
            self.assertEqual(r3["count"], 2)
            self.assertFalse(list((Path(d) / "inbox" / "CN").glob("*.part")))

    def test_a_drop_lands_in_its_batch_folder(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            r = inbox.save(s, "CN", "a.html", b"<p>a</p>", "2026-09-30_101522")
            self.assertEqual(r["batch"], "2026-09-30_101522")
            self.assertTrue((Path(d) / "inbox" / "CN" / "2026-09-30_101522" / "a.html").is_file())
            inbox.save(s, "CN", "b.html", b"<p>b</p>", "2026-09-30_101522")
            inbox.save(s, "CN", "c.html", b"<p>c</p>")
            e = next(x for x in inbox.describe(s)["economies"] if x["code"] == "CN")
            self.assertEqual((e["files"], e["loose"]), (3, 1))
            self.assertEqual([(b["name"], b["files"]) for b in e["batches"]], [("2026-09-30_101522", 2)])
            files = inbox.list_files(Path(d) / "inbox" / "CN")
            self.assertEqual({f["name"]: f["batch"] for f in files},
                             {"2026-09-30_101522/a.html": "2026-09-30_101522", "2026-09-30_101522/b.html": "2026-09-30_101522", "c.html": ""})
            with self.assertRaises(ApiError):
                inbox.save(s, "CN", "d.html", b"<p>d</p>", "../evil")

    def test_bad_economy_or_empty_file_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            with self.assertRaises(ApiError):
                inbox.save(s, "XX", "law.pdf", b"%PDF")
            with self.assertRaises(ApiError):
                inbox.save(s, "CN", "law.pdf", b"")

    def test_describe_lists_every_economy_with_counts(self):
        with tempfile.TemporaryDirectory() as d:
            s = self._settings(Path(d))
            inbox.save(s, "LA", "a.pdf", b"%PDF-1.4")
            desc = inbox.describe(s)
            by = {e["code"]: e for e in desc["economies"]}
            self.assertEqual(by["LA"]["files"], 1)
            self.assertEqual(by["SG"]["files"], 0)
            self.assertEqual([e["code"] for e in desc["economies"]][:6], ["SG", "AU", "MY", "TL", "LA", "CN"])
            files = inbox.list_files(Path(d) / "inbox" / "LA")
            self.assertEqual([(f["name"], f["kind"], f["size"]) for f in files], [("a.pdf", "pdf", 8)])


if __name__ == "__main__":
    unittest.main()
