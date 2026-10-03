"""The app window: which browser is found on each system, how it is started, and what the page may open."""
import unittest
from pathlib import Path
from unittest import mock

from . import INTERFACE  # noqa: F401
from rdtii_ui import shell

WIN_ENV = {"ProgramFiles(x86)": r"C:\Program Files (x86)", "ProgramFiles": r"C:\Program Files",
           "LOCALAPPDATA": r"C:\Users\me\AppData\Local"}
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
NO_REGISTRY = lambda exe: []  # noqa: E731


class StateFolder(unittest.TestCase):
    def test_each_system_has_its_usual_place(self):
        home = Path("/home/me")
        self.assertEqual(shell.state_dir(WIN_ENV, "win32", home), Path(r"C:\Users\me\AppData\Local") / "rdtii-rocky")
        self.assertEqual(shell.state_dir({}, "darwin", home), home / "Library" / "Application Support" / "rdtii-rocky")
        self.assertEqual(shell.state_dir({}, "linux", home), home / ".local" / "state" / "rdtii-rocky")
        self.assertEqual(shell.state_dir({"XDG_STATE_HOME": "/x/state"}, "linux", home), Path("/x/state") / "rdtii-rocky")

    def test_a_setting_names_it(self):
        self.assertEqual(shell.state_dir({"RDTII_STATE_DIR": "/somewhere/else", "LOCALAPPDATA": "C:/x"}, "win32"),
                         Path("/somewhere/else"))


class Browsers(unittest.TestCase):
    def test_the_browser_every_machine_has_is_tried_first(self):
        win = shell.browser_candidates("win32", WIN_ENV, registry=NO_REGISTRY)
        self.assertEqual(win[0], ("Edge", EDGE))
        self.assertIn(("Chrome", CHROME), win)
        mac = shell.browser_candidates("darwin", {}, Path("/Users/me"))
        self.assertEqual(mac[0], ("Chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
        self.assertIn(("Chrome", "/Users/me/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"), mac)
        self.assertIn("Edge", [n for n, _ in mac])
        linux = shell.browser_candidates("linux", {})
        self.assertEqual(linux[0], ("Chrome", "google-chrome"))
        self.assertTrue(all("/" not in c for _, c in linux))           # commands, found on PATH

    def test_the_first_one_installed_is_taken(self):
        only_chrome = lambda p: p == CHROME  # noqa: E731
        got = shell.find_browser(platform="win32", env=WIN_ENV, exists=only_chrome, which=lambda c: None, registry=NO_REGISTRY)
        self.assertEqual(got, {"name": "Chrome", "path": CHROME})
        both = lambda p: p in (CHROME, EDGE)  # noqa: E731
        self.assertEqual(shell.find_browser(platform="win32", env=WIN_ENV, exists=both, which=lambda c: None,
                                            registry=NO_REGISTRY)["name"], "Edge")
        none = shell.find_browser(platform="win32", env=WIN_ENV, exists=lambda p: False, which=lambda c: None, registry=NO_REGISTRY)
        self.assertIsNone(none)

    def test_a_browser_installed_somewhere_unusual_is_found_through_the_registry(self):
        odd = r"D:\Apps\Edge\msedge.exe"
        got = shell.find_browser(platform="win32", env=WIN_ENV, exists=lambda p: p == odd, which=lambda c: None,
                                 registry=lambda exe: [odd] if exe == "msedge.exe" else [])
        self.assertEqual(got, {"name": "Edge", "path": odd})

    def test_on_linux_the_command_is_looked_up(self):
        which = lambda c: "/usr/bin/chromium" if c == "chromium" else None  # noqa: E731
        got = shell.find_browser(platform="linux", env={}, exists=lambda p: False, which=which)
        self.assertEqual(got, {"name": "Chromium", "path": "/usr/bin/chromium"})

    def test_a_named_browser_is_the_only_one_tried(self):
        everything = lambda p: True  # noqa: E731
        got = shell.find_browser("/opt/brave/brave", platform="linux", env={}, exists=everything, which=lambda c: None)
        self.assertEqual(got, {"name": "brave", "path": "/opt/brave/brave"})
        from_env = shell.find_browser(platform="win32", env={**WIN_ENV, "RDTII_BROWSER": "chromium"},
                                      exists=lambda p: False, which=lambda c: "/usr/bin/chromium")
        self.assertEqual(from_env["path"], "/usr/bin/chromium")
        # named and missing: nothing else is tried, so the wrong setting is seen
        self.assertIsNone(shell.find_browser("nosuch", platform="win32", env=WIN_ENV, exists=lambda p: p == EDGE,
                                             which=lambda c: None, registry=NO_REGISTRY))


class Starting(unittest.TestCase):
    def test_the_window_has_its_own_profile_and_ends_with_its_process(self):
        args = shell.app_args(EDGE, "http://127.0.0.1:8765/", Path("/state/browser-profile"))
        self.assertEqual(args[0], EDGE)
        self.assertIn("--app=http://127.0.0.1:8765/", args)
        self.assertIn(f"--user-data-dir={Path('/state/browser-profile')}", args)
        for flag in ("--no-first-run", "--no-default-browser-check", "--disable-background-mode", "--disable-sync"):
            self.assertIn(flag, args)
        # a new Edge profile must not sign itself in to the Windows account and start syncing
        features = next(a for a in args if a.startswith("--disable-features=")).split("=")[1].split(",")
        self.assertIn("msImplicitSignin", features)
        self.assertNotIn("--guest", args)            # both still sign in, and both rename the window
        self.assertNotIn("--inprivate", args)
        self.assertTrue(any(a.startswith("--window-size=") for a in args))

    def test_only_web_addresses_are_opened_outside(self):
        with mock.patch.object(shell.webbrowser, "open", return_value=True) as opened:
            for bad in ("file:///C:/Windows/system32/calc.exe", "javascript:alert(1)", "C:\\x.exe", "", "ms-settings:"):
                self.assertFalse(shell.open_external(bad), bad)
            opened.assert_not_called()
            self.assertTrue(shell.open_external("https://sso.agc.gov.sg/Act/PDPA2012"))
            opened.assert_called_once_with("https://sso.agc.gov.sg/Act/PDPA2012")


if __name__ == "__main__":
    unittest.main()
