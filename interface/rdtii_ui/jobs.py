"""The run layer: one subprocess at a time, its printed lines turned into plain words, and a Stop button.

A Job is a list of Steps. Each Step is a command line, a working directory, an environment, and a parser
that turns one printed line into a sentence for the page (or nothing). Lines the parser does not know go
to the raw tail only. A poll hook can read a file the stage writes when it prints nothing for a while.
"""
from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

HEARTBEAT_AFTER_S = 90
TICK_S = 5
RAW_KEEP = 2000

# type of a parser: line -> None | sentence | (sentence, progress-updates)
Parser = Callable[[str, "Job"], "None | str | tuple"]


@dataclass
class Step:
    label: str
    argv: list[str]
    cwd: Path
    env: dict
    parse: Parser | None = None
    poll: Callable[["Job"], "str | None"] | None = None
    ok_codes: tuple[int, ...] = (0,)
    on_done: Callable[["Job", int], None] | None = None


@dataclass
class Job:
    stage: str
    title: str
    steps: list[Step]
    out_dir: Path | None = None
    env_public: dict = field(default_factory=dict)
    redact: Callable[[str], str] = lambda s: s
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    status: str = "queued"  # queued | running | done | failed | cancelled
    created: float = field(default_factory=time.time)
    started: float | None = None
    ended: float | None = None
    step_index: int = -1
    rc: int | None = None
    error: str | None = None
    raw: deque = field(default_factory=lambda: deque(maxlen=RAW_KEEP))
    sentences: list = field(default_factory=list)
    progress: dict = field(default_factory=lambda: {"done": 0, "total": None, "unit": "", "cost_usd": None,
                                                    "failed": 0, "skipped": 0})
    cancel_requested: bool = False
    _proc: subprocess.Popen | None = field(default=None, repr=False)
    _last_line_at: float = field(default_factory=time.time, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def say(self, text: str) -> None:
        with self._lock:
            self.sentences.append({"t": time.time(), "text": text})

    def bump(self, **kw) -> None:
        with self._lock:
            for k, v in kw.items():
                if k.startswith("+"):
                    self.progress[k[1:]] = (self.progress.get(k[1:]) or 0) + v
                else:
                    self.progress[k] = v

    @property
    def step_label(self) -> str:
        return self.steps[self.step_index].label if 0 <= self.step_index < len(self.steps) else ""

    def public(self, since: int = 0, raw_tail: int = 40) -> dict:
        with self._lock:
            sentences = list(self.sentences[since:])
            n = len(self.sentences)
            raw = list(self.raw)[-raw_tail:]
            progress = dict(self.progress)
        return {
            "id": self.id, "stage": self.stage, "title": self.title, "status": self.status,
            "created": self.created, "started": self.started, "ended": self.ended,
            "step_index": self.step_index, "n_steps": len(self.steps), "step_label": self.step_label,
            "steps": [s.label for s in self.steps],
            "progress": progress, "sentences": sentences, "n_sentences": n, "raw_tail": raw,
            "rc": self.rc, "error": self.error, "out_dir": str(self.out_dir) if self.out_dir else None,
            "env_public": self.env_public,
        }

    def summary(self) -> dict:
        with self._lock:
            last = self.sentences[-1]["text"] if self.sentences else ""
            progress = dict(self.progress)
        return {"id": self.id, "stage": self.stage, "title": self.title, "status": self.status,
                "step_label": self.step_label, "step_index": self.step_index, "n_steps": len(self.steps),
                "progress": progress, "last": last, "started": self.started, "ended": self.ended}


class JobManager:
    """A serial queue: one stage process at a time, for portal politeness, Ollama contention and legible cost."""

    def __init__(self) -> None:
        self._q: queue.Queue[Job] = queue.Queue()
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self.active: Job | None = None
        self._worker = threading.Thread(target=self._loop, name="rdtii-jobs", daemon=True)
        self._worker.start()

    # -- public ---------------------------------------------------------------------------------------
    def submit(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
            self._order.append(job.id)
        self._q.put(job)
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def all(self) -> list[Job]:
        return [self._jobs[i] for i in reversed(self._order)]

    def busy_dirs(self) -> list[Path]:
        return [j.out_dir for j in self._jobs.values() if j.status in ("queued", "running") and j.out_dir]

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.status not in ("queued", "running"):
            return False
        job.cancel_requested = True
        if job.status == "queued":
            job.status = "cancelled"
            job.ended = time.time()
            job.say("Cancelled before it started.")
            return True
        proc = job._proc
        if proc and proc.poll() is None:
            _kill_tree(proc)
        return True

    def public_summary(self) -> dict:
        active = self.active.summary() if self.active and self.active.status == "running" else None
        queued = [j.summary() for j in self._jobs.values() if j.status == "queued"]
        recent = [j.summary() for j in self.all() if j.status in ("done", "failed", "cancelled")][:5]
        return {"active": active, "queued": queued, "recent": recent}

    # -- the worker ---------------------------------------------------------------------------------------
    def _loop(self) -> None:
        while True:
            job = self._q.get()
            if job.status == "cancelled":
                continue
            self.active = job
            try:
                self._run(job)
            finally:
                self.active = None

    def _run(self, job: Job) -> None:
        job.status = "running"
        job.started = time.time()
        for i, step in enumerate(job.steps):
            if job.cancel_requested:
                break
            job.step_index = i
            job.say(f"Step {i + 1} of {len(job.steps)}: {step.label}.")
            rc = self._run_step(job, step)
            job.rc = rc
            if step.on_done:
                try:
                    step.on_done(job, rc)
                except Exception as exc:  # noqa: BLE001
                    job.say(f"(after-step hook failed: {exc})")
            if job.cancel_requested:
                break
            forced = job.progress.pop("_fail", None)
            if forced:
                job.error = str(forced)
                job.say(job.error)
                job.status = "failed"
                job.ended = time.time()
                return
            if rc not in step.ok_codes:
                tail = [ln for ln in list(job.raw)[-6:] if ln.strip()]
                job.error = f"'{step.label}' stopped with exit code {rc}."
                job.say(job.error + (" Last lines: " + " | ".join(tail) if tail else ""))
                job.status = "failed"
                job.ended = time.time()
                return
        job.ended = time.time()
        if job.cancel_requested:
            job.status = "cancelled"
            job.say("Stopped by request.")
        else:
            job.status = "done"
            job.say("Finished.")

    def _run_step(self, job: Job, step: Step) -> int:
        job.raw.append(f"$ ({step.cwd}) " + " ".join(_q(a) for a in step.argv))
        creation = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        try:
            proc = subprocess.Popen(
                step.argv, cwd=str(step.cwd), env=step.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=creation)
        except OSError as exc:
            job.raw.append(f"could not start: {exc}")
            job.say(f"Could not start '{step.label}': {exc}")
            return 127
        job._proc = proc
        job._last_line_at = time.time()

        def reader() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                line = job.redact(line.rstrip("\r\n"))
                job.raw.append(line)
                job._last_line_at = time.time()
                if step.parse:
                    try:
                        out = step.parse(line, job)
                    except Exception as exc:  # noqa: BLE001 - a parser bug must not kill the run
                        out = None
                        job.raw.append(f"(parser error: {exc})")
                    if isinstance(out, tuple):
                        text, updates = out
                        if updates:
                            job.bump(**updates)
                        if text:
                            job.say(text)
                    elif out:
                        job.say(out)

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        heartbeat_at = None
        while proc.poll() is None:
            t.join(timeout=TICK_S)
            if proc.poll() is not None:
                break
            quiet = time.time() - job._last_line_at
            if step.poll:
                try:
                    msg = step.poll(job)
                    if msg:
                        job.say(msg)
                        job._last_line_at = time.time()
                        continue
                except Exception as exc:  # noqa: BLE001
                    job.raw.append(f"(poll error: {exc})")
            if quiet >= HEARTBEAT_AFTER_S and (heartbeat_at is None or time.time() - heartbeat_at >= HEARTBEAT_AFTER_S):
                heartbeat_at = time.time()
                job.say(f"Still working, {int(quiet // 60)} min since the last message.")
        t.join(timeout=5)
        try:
            if proc.stdout:
                proc.stdout.close()
        except OSError:
            pass
        job._proc = None
        return proc.returncode if proc.returncode is not None else -1


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _q(a: str) -> str:
    return f'"{a}"' if " " in a else a


# ---- a self-test job: proves the queue, the parser, the heartbeat and Stop without any stage ----------

SELFTEST_RX = re.compile(r"^tick (\d+)/(\d+)$")


def selftest_job(python: str, redact) -> Job:
    code = "import time\nfor i in range(1, 6):\n    print(f'tick {i}/5', flush=True)\n    time.sleep(1)\nprint('bye', flush=True)\n"

    def parse(line: str, job: Job):
        m = SELFTEST_RX.match(line)
        if m:
            return f"Tick {m.group(1)} of {m.group(2)}.", {"done": int(m.group(1)), "total": int(m.group(2)), "unit": "ticks"}
        if line == "bye":
            return "The test process said goodbye."
        return None

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    step = Step(label="count to five, one tick a second", argv=[python, "-c", code], cwd=Path.cwd(), env=env, parse=parse)
    return Job(stage="selftest", title="Run-layer self-test", steps=[step], redact=redact)


# ---- routes ---------------------------------------------------------------------------------------------

def register(app) -> None:
    from .server import ApiError

    app.jobs = JobManager()

    @app.route("GET", r"/api/jobs")
    def list_jobs(app, m, q, b):
        return 200, {"jobs": [j.summary() for j in app.jobs.all()][:30], **app.jobs.public_summary()}

    @app.route("GET", r"/api/jobs/([0-9a-f]{10})")
    def get_job(app, m, q, b):
        job = app.jobs.get(m.group(1))
        if not job:
            raise ApiError(404, "no such job")
        try:
            since = int(q.get("since", "0") or 0)
        except ValueError:
            since = 0
        return 200, job.public(since=since)

    @app.route("POST", r"/api/jobs/([0-9a-f]{10})/cancel")
    def cancel_job(app, m, q, b):
        if not app.jobs.cancel(m.group(1)):
            raise ApiError(409, "that job is not running")
        return 200, {"cancelled": m.group(1)}

    @app.route("POST", r"/api/jobs/selftest")
    def selftest(app, m, q, b):
        job = app.jobs.submit(selftest_job(sys.executable, app.key.redact))
        return 200, {"job": job.public()}
