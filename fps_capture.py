from __future__ import annotations

import csv
import ctypes
import platform
import shutil
import subprocess
import sys
import time
from collections import deque
from pathlib import Path
from threading import Thread


def find_presentmon(settings_path: str = "") -> str | None:
    candidates = [
        settings_path,
        str(Path(sys.executable).parent / "PresentMon.exe"),
        str(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "tools" / "PresentMon.exe"),
        str(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "PresentMon.exe"),
        str(Path(__file__).parent / "tools" / "PresentMon.exe"),
        shutil.which("PresentMon.exe") or "",
        shutil.which("PresentMon") or "",
    ]
    for item in candidates:
        if item and Path(item).is_file():
            return str(Path(item))
    return None


def foreground_pid() -> int | None:
    if platform.system() != "Windows":
        return None
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value) or None
    except Exception:
        return None


class FPSCapture:
    """Read PresentMon CSV output and estimate FPS for the focused application."""

    def __init__(self):
        self.value = None
        self.status = "FPS capture is not running"
        self.running = False
        self.process = None
        self.thread = None
        self._stop = False

    def start(self, executable: str):
        if self.running:
            return
        self._stop = False
        self.running = True
        self.status = "Starting PresentMon"
        self.thread = Thread(target=self._run, args=(executable,), daemon=True)
        self.thread.start()

    def stop(self):
        self._stop = True
        self.running = False
        proc = self.process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        self.value = None
        self.status = "FPS capture paused"

    def _run(self, executable: str):
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.process = subprocess.Popen(
                [executable, "--output_stdout", "--no_console_stats",
                 "--no_track_gpu", "--no_track_input",
                 "--session_name", "PerformanceAir"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8-sig",
                errors="replace",
                bufsize=1,
                creationflags=flags,
            )
            header = None
            pid_col = None
            frame_col = None
            samples = deque(maxlen=90)
            active_pid = None
            last_error = None
            self.status = "PresentMon running · waiting for game frames"
            while not self._stop and self.process.poll() is None:
                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue
                cleaned = line.strip()
                lowered = cleaned.lower()
                if any(term in lowered for term in (
                    "failed to start", "access denied", "error:", "unable to",
                    "could not", "not permitted"
                )):
                    last_error = cleaned[:180]
                    self.status = "PresentMon: " + last_error
                    continue
                try:
                    row = next(csv.reader([line]))
                except Exception:
                    continue
                if header is None:
                    names = [value.strip().lower() for value in row]
                    if "processid" not in names:
                        continue
                    header = names
                    pid_col = names.index("processid")
                    frame_col = next(
                        (names.index(key) for key in
                         ("msbetweenpresents", "msbetweendisplaychange", "msbetweenpresent")
                         if key in names), None
                    )
                    continue
                if frame_col is None or len(row) <= max(pid_col, frame_col):
                    continue
                target_pid = foreground_pid()
                try:
                    row_pid = int(float(row[pid_col]))
                    frame_ms = float(row[frame_col])
                except (ValueError, TypeError):
                    continue
                if target_pid and row_pid == target_pid and 0.1 <= frame_ms <= 1000:
                    if active_pid != target_pid:
                        samples.clear()
                        active_pid = target_pid
                    samples.append(frame_ms)
                    if len(samples) >= 8:
                        self.value = round(1000.0 / (sum(samples) / len(samples)))
                        self.status = "Live · focused game"
                elif target_pid != active_pid:
                    samples.clear()
                    active_pid = target_pid
                    self.value = None
                    self.status = "Waiting for game frames"
            if not self._stop:
                exit_code = self.process.poll()
                if last_error:
                    self.status = "PresentMon error: " + last_error
                elif header is None:
                    self.status = (
                        f"PresentMon exited (code {exit_code}) without CSV data. "
                        "Try running Performance Air as administrator."
                    )
                else:
                    self.status = (
                        f"PresentMon exited (code {exit_code}). "
                        "Try running Performance Air as administrator."
                    )
        except FileNotFoundError:
            self.status = "PresentMon executable not found"
        except Exception as exc:
            self.status = "FPS capture unavailable: " + str(exc)
        finally:
            self.running = False
            proc = self.process
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
            self.process = None
