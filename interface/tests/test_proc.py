"""Child processes: no console window, the whole tree ended on Stop, a console Python for the stages."""
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from . import INTERFACE
from rdtii_ui import jobs, proc

GRANDCHILD = (
    "import subprocess, sys, time\n"
    "g = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
    "print(g.pid, flush=True)\n"
    "time.sleep(120)\n"
)


class Flags(unittest.TestCase):
    def test_no_console_window_on_windows_and_nothing_elsewhere(self):
        self.assertTrue(proc.quiet_flags(os_name="nt") & proc.CREATE_NO_WINDOW)
        self.assertTrue(proc.quiet_flags(proc.CREATE_NEW_PROCESS_GROUP, os_name="nt") & proc.CREATE_NEW_PROCESS_GROUP)
        self.assertEqual(proc.quiet_flags(os_name="posix"), 0)


class ConsolePython(unittest.TestCase):
    def test_pythonw_is_mapped_to_the_python_beside_it(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("pythonw.exe", "python.exe"):
                (Path(d) / name).write_bytes(b"")
            self.assertEqual(proc.console_python(str(Path(d) / "pythonw.exe")), str(Path(d) / "python.exe"))

    def test_pythonw_without_a_twin_and_plain_python_are_left_alone(self):
        with tempfile.TemporaryDirectory() as d:
            lone = Path(d) / "pythonw.exe"
            lone.write_bytes(b"")
            self.assertEqual(proc.console_python(str(lone)), str(lone))
        self.assertEqual(proc.console_python(sys.executable), sys.executable)


class Tree(unittest.TestCase):
    def test_pid_alive(self):
        import os
        self.assertTrue(proc.pid_alive(os.getpid()))
        self.assertFalse(proc.pid_alive(0))
        child = proc.popen_quiet([sys.executable, "-c", "pass"])
        child.wait(timeout=30)
        time.sleep(0.2)
        self.assertFalse(proc.pid_alive(child.pid))

    def test_kill_tree_ends_the_child_and_its_grandchild(self):
        child = proc.popen_quiet([sys.executable, "-c", GRANDCHILD], new_group=True, stdout=subprocess.PIPE, text=True)
        try:
            grandchild = int(child.stdout.readline().strip())
            self.assertTrue(proc.pid_alive(grandchild))
            proc.kill_tree(child)
            self.assertIsNotNone(child.poll())
            deadline = time.time() + 10
            while proc.pid_alive(grandchild) and time.time() < deadline:
                time.sleep(0.1)
            self.assertFalse(proc.pid_alive(grandchild), "the grandchild outlived Stop")
        finally:
            if child.poll() is None:
                child.kill()
            if child.stdout:
                child.stdout.close()

    def test_kill_tree_on_a_finished_process_does_nothing(self):
        child = proc.popen_quiet([sys.executable, "-c", "pass"])
        child.wait(timeout=30)
        proc.kill_tree(child)


class Shutdown(unittest.TestCase):
    def test_shutdown_cancels_the_running_job_and_refuses_new_ones(self):
        mgr = jobs.JobManager()
        job = mgr.submit(jobs.selftest_job(sys.executable, lambda s: s))
        queued = mgr.submit(jobs.selftest_job(sys.executable, lambda s: s))
        deadline = time.time() + 10
        while job.status != "running" and time.time() < deadline:
            time.sleep(0.1)
        mgr.shutdown()
        self.assertEqual(job.status, "cancelled")
        self.assertEqual(queued.status, "cancelled")
        self.assertIsNone(mgr.active)
        self.assertEqual(mgr.busy(), [])
        with self.assertRaises(RuntimeError):
            mgr.submit(jobs.selftest_job(sys.executable, lambda s: s))


class NoBareSubprocess(unittest.TestCase):
    """Every child process goes through proc.py; a bare call would flash a console window on Windows."""

    def test_only_proc_starts_processes(self):
        bare = re.compile(r"\b_?subprocess\.(run|Popen|call|check_call|check_output)\(|\bos\.(system|popen|spawn\w*)\(")
        offenders = []
        for path in sorted((INTERFACE / "rdtii_ui").rglob("*.py")):
            if path.name == "proc.py":
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if bare.search(line.split("#", 1)[0]):
                    offenders.append(f"{path.relative_to(INTERFACE)}:{n}: {line.strip()}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
