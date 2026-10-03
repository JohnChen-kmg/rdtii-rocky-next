"""When the interface stops once it has a window, one instance per repository, and what the server sends
for it: the presence stream, the page's shell, media types, a port that is not shared."""
import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from . import INTERFACE  # noqa: F401
from rdtii_ui import jobs, lifecycle, review, settings as settings_mod, shell
from rdtii_ui.server import App, make_server
from rdtii_ui.settings import REPO

G, S, O = lifecycle.GRACE_TICKS, lifecycle.STARTUP_TICKS, lifecycle.ORPHAN_TICKS


def decide(**kw):
    base = {"window_alive": True, "present": 0, "ever_present": True, "busy": False, "quiet_ticks": 0, "age_ticks": 100}
    return lifecycle.decide(**{**base, **kw})


class Decide(unittest.TestCase):
    def test_a_page_that_is_open_keeps_it_running(self):
        self.assertEqual(decide(present=1), "run")
        self.assertEqual(decide(present=2, window_alive=False, quiet_ticks=10 ** 6), "run")   # the browser handed the window on

    def test_closing_the_window_stops_it_after_a_short_grace(self):
        self.assertEqual(decide(window_alive=False, quiet_ticks=G - 1), "run")    # a reload reconnects inside the grace
        self.assertEqual(decide(window_alive=False, quiet_ticks=G), "stop")
        self.assertEqual(decide(window_alive=False, quiet_ticks=G, busy=True), "stop")   # closing stops a run, after the page's warning

    def test_a_window_that_never_came_up(self):
        self.assertEqual(decide(window_alive=True, ever_present=False, age_ticks=10 ** 6), "run")   # still loading, or showing an error
        self.assertEqual(decide(window_alive=False, ever_present=False, age_ticks=S - 1), "run")
        self.assertEqual(decide(window_alive=False, ever_present=False, age_ticks=S), "stop")

    def test_a_run_is_never_cut_short_while_its_window_exists(self):
        self.assertEqual(decide(busy=True, quiet_ticks=10 ** 6), "run")
        self.assertEqual(decide(busy=False, quiet_ticks=O - 1), "run")           # a laptop waking up reconnects long before this
        self.assertEqual(decide(busy=False, quiet_ticks=O), "stop")              # a browser process left behind with no page

    def test_the_watch_counts_ticks_not_seconds(self):
        class Proc:
            def __init__(self): self.code = None
            def poll(self): return self.code

        app = App(settings_mod.load({}))
        app.presence = lifecycle.Presence()
        app.jobs = None
        proc = Proc()
        ticks = []

        def sleep(_t):
            ticks.append(1)
            if len(ticks) == 3:
                app.presence.enter()             # the page connects
            if len(ticks) == 6:
                app.presence.leave()             # the window is closed
                proc.code = 0
        self.assertEqual(lifecycle.watch(app, proc, sleep=sleep), "the window was closed")
        self.assertEqual(len(ticks), 5 + G)      # no page from tick 6 on; the grace is G consecutive ticks of that

        app2 = App(settings_mod.load({}))
        app2.presence = lifecycle.Presence()
        app2.stop.set()
        self.assertEqual(lifecycle.watch(app2, proc, sleep=lambda t: None), "asked to stop")


class Instance(unittest.TestCase):
    def test_the_note_names_the_process_and_never_the_token(self):
        with tempfile.TemporaryDirectory() as d:
            note = lifecycle.InstanceNote(Path(d))
            self.assertIsNone(note.read())
            note.write("127.0.0.1", 8765)
            got = note.read()
            self.assertEqual((got["pid"], got["host"], got["port"]), (os.getpid(), "127.0.0.1", 8765))
            self.assertEqual(set(got), {"pid", "host", "port", "repo", "started"})
            note.release()
            self.assertFalse(note.path.exists())

    def test_running_means_alive_and_answering_for_this_repository(self):
        with tempfile.TemporaryDirectory() as d:
            note = lifecycle.InstanceNote(Path(d))
            note.write("127.0.0.1", 8765)
            mine = lambda host, port: {"app": shell.APP_NAME, "repo": str(REPO.resolve())}  # noqa: E731
            self.assertEqual(note.running(probe=mine, alive=lambda pid: True)["port"], 8765)
            self.assertIsNone(note.running(probe=mine, alive=lambda pid: False))                      # a note left by a crash
            self.assertIsNone(note.running(probe=lambda h, p: None, alive=lambda pid: True))            # the pid was reused by something else
            other = lambda host, port: {"app": shell.APP_NAME, "repo": "/another/clone"}  # noqa: E731
            self.assertIsNone(note.running(probe=other, alive=lambda pid: True))

    def test_each_repository_has_its_own_note(self):
        with tempfile.TemporaryDirectory() as d:
            a = lifecycle.InstanceNote(Path(d), Path(d) / "clone-a")
            b = lifecycle.InstanceNote(Path(d), Path(d) / "clone-b")
            self.assertNotEqual(a.path, b.path)
            a.write("127.0.0.1", 1)
            self.assertIsNone(b.read())

    def test_another_process_note_is_not_removed(self):
        with tempfile.TemporaryDirectory() as d:
            note = lifecycle.InstanceNote(Path(d))
            note.path.write_text(json.dumps({"pid": os.getpid() + 1, "host": "127.0.0.1", "port": 9}), encoding="utf-8")
            note.release()
            self.assertTrue(note.path.exists())


class Served(unittest.TestCase):
    """A real server on a free port."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = App(settings_mod.load({"RDTII_RUNS_ROOT": str(Path(cls.tmp.name) / "outputs")}))
        cls.app.jobs = jobs.JobManager()
        lifecycle.register(cls.app)
        review.register(cls.app)
        cls.server = make_server(cls.app, 0)
        cls.port = cls.app.port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.app.stop.set()
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def get(self, path, method="GET", body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        data = r.read()
        c.close()
        return r.status, r.getheader("Content-Type"), data

    def post(self, path, obj):
        return self.get(path, "POST", json.dumps(obj).encode("utf-8"),
                        {"Content-Type": "application/json", "X-RDTII-Token": self.app.token})

    def test_the_port_asked_of_the_system_is_the_one_reported(self):
        self.assertGreater(self.port, 0)
        self.assertEqual(self.port, self.server.server_address[1])
        self.assertEqual(lifecycle.ping("127.0.0.1", self.port)["repo"], str(REPO.resolve()))
        self.assertIsNone(lifecycle.ping("127.0.0.1", 9, timeout=0.3))          # nothing there

    def test_a_port_is_served_by_one_process_only(self):
        with self.assertRaises(OSError):
            make_server(self.app, self.port)
        self.assertEqual(self.app.port, self.port)       # a refused bind leaves the note of the real port alone

    def test_the_page_is_told_which_shell_it_runs_in(self):
        status, ctype, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b'<meta name="rdtii-shell" content="tab">', body)
        self.assertNotIn(b"__SHELL__", body)
        self.assertNotIn(b"__TOKEN__", body)
        self.app.shell = "window"
        try:
            self.assertIn(b'<meta name="rdtii-shell" content="window">', self.get("/")[2])
        finally:
            self.app.shell = "tab"

    def test_static_files_have_fixed_media_types(self):
        want = {"/static/app.js": "text/javascript; charset=utf-8", "/static/app.css": "text/css; charset=utf-8",
                "/static/icon.svg": "image/svg+xml", "/static/icon-192.png": "image/png",
                "/static/manifest.webmanifest": "application/manifest+json; charset=utf-8", "/favicon.ico": "image/x-icon"}
        for path, ctype in want.items():
            status, got, body = self.get(path)
            self.assertEqual((status, got), (200, ctype), path)
            self.assertTrue(body, path)
        self.assertEqual(self.get("/favicon.ico")[2][:4], b"\x00\x00\x01\x00")
        manifest = json.loads(self.get("/static/manifest.webmanifest")[2])
        for icon in manifest["icons"]:
            self.assertEqual(self.get(icon["src"])[0], 200, icon["src"])
        self.assertEqual(self.get("/static/../app.py")[0], 404)

    def test_each_open_page_is_counted_and_missed_when_it_goes(self):
        self.assertEqual(self.get("/api/presence?t=wrong")[0], 403)
        before = self.app.presence.count
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("GET", f"/api/presence?t={self.app.token}")
        r = c.getresponse()
        self.assertEqual(r.status, 200)
        self.assertTrue(r.getheader("Content-Type").startswith("text/event-stream"))
        first = r.fp.readline() + r.fp.readline() + r.fp.readline()
        self.assertIn(b"retry: 1000", first)
        self.assertEqual(json.loads(first.split(b"data: ")[1])["busy"], False)
        self.assertEqual(self.app.presence.count, before + 1)
        self.assertTrue(self.app.presence.ever)
        r.close()                                # the response holds the socket too: both go, as when a page closes
        c.close()
        deadline = time.monotonic() + 8
        while self.app.presence.count > before and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertEqual(self.app.presence.count, before)

    def test_only_web_addresses_are_opened_and_only_with_the_token(self):
        with mock.patch.object(shell.webbrowser, "open", return_value=True) as opened:
            self.assertEqual(self.post("/api/open-url", {"url": "file:///C:/x"})[0], 400)
            opened.assert_not_called()
            self.assertEqual(self.post("/api/open-url", {"url": "https://www.pdpc.gov.sg/"})[0], 200)
            opened.assert_called_once_with("https://www.pdpc.gov.sg/")
            status = self.get("/api/open-url", "POST", b'{"url": "https://example.org/"}', {"Content-Type": "application/json"})[0]
            self.assertEqual(status, 403)

    def test_export_can_say_where_the_file_is_instead_of_sending_it(self):
        # the window has no download bar: the file stays where the server wrote it
        status, ctype, body = self.get("/api/map/export?run=interface/fixtures&fmt=csv&save=1")
        got = json.loads(body)
        self.assertEqual((status, ctype), (200, "application/json; charset=utf-8"))
        self.assertTrue(got["filename"].endswith(".csv"))
        self.assertTrue((Path(got["folder"]) / got["filename"]).is_file())
        self.assertGreater(got["rows"], 0)
        status, ctype, body = self.get("/api/map/export?run=interface/fixtures&fmt=csv")      # a tab still downloads it
        self.assertEqual(status, 200)
        self.assertTrue(ctype.startswith("text/csv"))
        self.assertEqual(len(body.decode("utf-8-sig").splitlines()) - 1, got["rows"])

    def test_asking_to_stop_needs_the_token(self):
        self.assertEqual(self.get("/api/shutdown", "POST", b"{}", {"Content-Type": "application/json"})[0], 403)
        self.assertFalse(self.app.stop.is_set())


class Stopping(unittest.TestCase):
    def test_a_stop_ends_the_streams_and_the_watch(self):
        app = App(settings_mod.load({}))
        lifecycle.register(app)
        server = make_server(app, 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            c = http.client.HTTPConnection("127.0.0.1", app.port, timeout=10)
            c.request("GET", f"/api/presence?t={app.token}")
            r = c.getresponse()
            r.fp.readline()
            c2 = http.client.HTTPConnection("127.0.0.1", app.port, timeout=10)
            c2.request("POST", "/api/shutdown", body=b"{}", headers={"Content-Type": "application/json", "X-RDTII-Token": app.token})
            self.assertEqual(c2.getresponse().status, 200)
            c2.close()
            self.assertTrue(app.stop.is_set())
            self.assertEqual(lifecycle.watch(app, None, sleep=lambda t: None), "asked to stop")
            rest = r.read()                      # the stream ends by itself once a stop is asked
            self.assertIn(b"data: ", rest)
            c.close()
        finally:
            app.stop.set()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
