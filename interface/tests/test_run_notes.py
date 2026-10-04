"""The run note: a line written at Start, kept in the run folder, shown wherever that folder is listed."""
import json
import tempfile
import unittest
from pathlib import Path

from . import INTERFACE  # noqa: F401
from rdtii_ui import jobs, notes
from rdtii_ui.pages import extract, mapping


class Note(unittest.TestCase):
    def test_a_note_is_one_trimmed_line(self):
        self.assertEqual(notes.clean("  second pass\n after the\tsplitter fix  "), "second pass after the splitter fix")
        self.assertEqual(notes.clean(None), "")
        self.assertEqual(len(notes.clean("x" * 1000)), notes.MAX_CHARS)

    def test_it_is_kept_in_the_folder_and_the_latest_is_read(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            self.assertEqual(notes.read(folder), {"note": "", "noted": ""})
            self.assertFalse(notes.write(folder, "   "))
            self.assertTrue(notes.write(folder, "first crawl"))
            self.assertTrue(notes.write(folder, "second pass"))
            got = notes.read(folder)
            self.assertEqual(got["note"], "second pass")
            self.assertRegex(got["noted"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
            self.assertEqual(len((folder / notes.NOTE_FILE).read_text(encoding="utf-8").splitlines()), 2)
            self.assertFalse(notes.write(folder / "not-there", "x"))

    def test_the_run_writes_it_once_the_folder_exists_and_keeps_the_steps_own_hook(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "run"
            seen = []
            steps = [jobs.Step(label="a", argv=["x"], env={}, cwd=Path(d)), jobs.Step(label="b", argv=["x"], env={}, cwd=Path(d)),
                     jobs.Step(label="c", argv=["x"], env={}, cwd=Path(d), on_done=lambda job, rc: seen.append(rc))]
            notes.carry(steps, folder, "  demo, with the new splitter ")
            job = jobs.Job(stage="p2", title="t", steps=steps)
            steps[0].on_done(job, 0)                       # the stage has not made its folder yet
            self.assertEqual(notes.read(folder)["note"], "")
            folder.mkdir()
            steps[1].on_done(job, 0)
            steps[2].on_done(job, 0)                       # written once, and the step's own hook still ran
            self.assertEqual(notes.read(folder)["note"], "demo, with the new splitter")
            self.assertEqual(len((folder / notes.NOTE_FILE).read_text(encoding="utf-8").splitlines()), 1)
            self.assertEqual(seen, [0])

    def test_no_note_leaves_the_steps_alone(self):
        steps = [jobs.Step(label="a", argv=["x"], env={}, cwd=Path("."))]
        notes.carry(steps, Path("."), "")
        self.assertIsNone(steps[0].on_done)


class WhereItIsSeenAgain(unittest.TestCase):
    def test_extraction_output_and_mapping_input_show_the_note_of_the_folder(self):
        from rdtii_ui import settings as settings_mod
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "TL_run"
            out.mkdir()
            (out / "doc_status.jsonl").write_text(json.dumps({"doc_id": "tl-a-001", "status": "ok", "n_provisions": 3}) + "\n", encoding="utf-8")
            (out / "laws.jsonl").write_text(json.dumps({"doc_id": "tl-a-001", "economy": "TL"}) + "\n", encoding="utf-8")
            self.assertEqual(extract.describe_output(out, "test")["note"], "")
            notes.write(out, "after the heading fix")
            self.assertEqual(extract.describe_output(out, "test")["note"], "after the heading fix")
            handoff = mapping.describe_handoff(settings_mod.load({}), out, "test")     # what Mapping's Input lists
            self.assertEqual(handoff["note"], "after the heading fix")

    def test_a_mapping_run_shows_its_own_note(self):
        with tempfile.TemporaryDirectory() as d:
            arm = Path(d) / "out"
            arm.mkdir()
            notes.write(arm, "DeepSeek on the reading, first try")
            self.assertEqual(mapping._describe_run("r", "r", [arm], "interface run")["note"], "DeepSeek on the reading, first try")
            self.assertEqual(mapping._describe_run("r", "r", [], "interface run")["note"], "")


if __name__ == "__main__":
    unittest.main()
