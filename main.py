from __future__ import annotations

import sys
import time
import platform
import subprocess
from threading import Thread

import psutil
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QProgressBar,
    QCheckBox, QComboBox
)

APP_NAME = "Performance Air"
RED = "#e53945"
BG = "#101114"
PANEL = "#191b20"
TEXT = "#f4f4f5"
MUTED = "#9297a1"
BORDER = "#2b2e35"


def nice_bytes(value: float) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} TB"


def gpu_stats() -> dict:
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode(errors="replace")
        try:
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        except Exception:
            temp = None
        return {"available": True, "name": name, "usage": util.gpu,
                "memory_used": mem.used, "memory_total": mem.total, "temperature": temp}
    except Exception:
        return {"available": False}


class MetricCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("metricCard")
        self.setMinimumHeight(145)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(8)
        top = QHBoxLayout()
        heading = QLabel(title.upper())
        heading.setObjectName("cardHeading")
        live = QLabel("LIVE")
        live.setObjectName("liveTag")
        top.addWidget(heading)
        top.addStretch()
        top.addWidget(live)
        layout.addLayout(top)
        self.value = QLabel("--")
        self.value.setObjectName("metricValue")
        layout.addWidget(self.value)
        self.detail = QLabel("Waiting for system data")
        self.detail.setObjectName("muted")
        layout.addWidget(self.detail)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        layout.addWidget(self.bar)

    def update_metric(self, value: str, detail: str, percent: int | None = None):
        self.value.setText(value)
        self.detail.setText(detail)
        self.bar.setVisible(percent is not None)
        if percent is not None:
            self.bar.setValue(max(0, min(100, int(percent))))


class PerformanceAir(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("PerformanceAir", "PerformanceAir")
        self.setWindowTitle(APP_NAME)
        self.resize(1160, 760)
        self.setMinimumSize(920, 620)
        self.last_net = psutil.net_io_counters()
        self.last_tick = time.time()
        self.ping_value = None
        self.ping_busy = False
        self.metrics = {}
        self._build_ui()
        self._load_options()
        psutil.cpu_percent(interval=None)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(self.settings.value("refresh_ms", 1000, int))
        self.refresh()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(224)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 26, 20, 20)
        side.setSpacing(10)
        brand = QHBoxLayout()
        mark = QLabel("P")
        mark.setObjectName("brandMark")
        mark.setFixedSize(38, 38)
        mark.setAlignment(Qt.AlignCenter)
        brand_name = QLabel("PERFORMANCE\nAIR")
        brand_name.setObjectName("brandName")
        brand.addWidget(mark)
        brand.addWidget(brand_name)
        brand.addStretch()
        side.addLayout(brand)
        side.addSpacing(34)
        self.nav_buttons = {}
        for key, label in (("overview", "Overview"), ("options", "Options"), ("settings", "Settings")):
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self.show_page(k))
            self.nav_buttons[key] = btn
            side.addWidget(btn)
        side.addStretch()
        foot = QLabel("DESKTOP MONITOR\nVERSION 1.0.0")
        foot.setObjectName("sidebarFoot")
        side.addWidget(foot)

        content = QFrame()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 26, 32, 22)
        content_layout.setSpacing(18)
        header = QHBoxLayout()
        self.page_title = QLabel("Overview")
        self.page_title.setObjectName("pageTitle")
        self.header_status = QLabel("● SYSTEM ONLINE")
        self.header_status.setObjectName("systemStatus")
        header.addWidget(self.page_title)
        header.addStretch()
        header.addWidget(self.header_status)
        content_layout.addLayout(header)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._overview_page())
        self.pages.addWidget(self._options_page())
        self.pages.addWidget(self._settings_page())
        content_layout.addWidget(self.pages)
        outer.addWidget(sidebar)
        outer.addWidget(content, 1)
        self.setCentralWidget(root)
        self.show_page("overview")
        self.setStyleSheet(self._stylesheet())

    def _overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(14)
        intro = QHBoxLayout()
        intro_text = QVBoxLayout()
        title = QLabel("Your system at a glance")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Live hardware and system performance")
        subtitle.setObjectName("muted")
        intro_text.addWidget(title)
        intro_text.addWidget(subtitle)
        intro.addLayout(intro_text)
        intro.addStretch()
        self.updated_label = QLabel("Updating…")
        self.updated_label.setObjectName("muted")
        intro.addWidget(self.updated_label, 0, Qt.AlignBottom)
        layout.addLayout(intro)
        grid = QGridLayout()
        grid.setSpacing(13)
        for i, (key, label) in enumerate([
            ("cpu", "Processor"), ("gpu", "Graphics"), ("ram", "Memory"),
            ("storage", "Storage"), ("network", "Network"), ("system", "System")
        ]):
            card = MetricCard(label)
            self.metrics[key] = card
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)
        optional = QHBoxLayout()
        optional.setSpacing(13)
        self.fps_card = MetricCard("Game FPS")
        self.ping_card = MetricCard("Network ping")
        self.metrics["fps"] = self.fps_card
        self.metrics["ping"] = self.ping_card
        optional.addWidget(self.fps_card)
        optional.addWidget(self.ping_card)
        layout.addLayout(optional)
        layout.addStretch()
        return page

    def _option_row(self, checkbox):
        row = QFrame()
        row.setObjectName("settingRow")
        box = QHBoxLayout(row)
        box.setContentsMargins(16, 12, 16, 12)
        box.addWidget(checkbox)
        box.addStretch()
        return row

    def _options_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        title = QLabel("Overview widgets")
        title.setObjectName("sectionTitle")
        desc = QLabel("Choose which optional metrics appear on your Overview.")
        desc.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(10)
        self.option_fps = QCheckBox("Show FPS in Overview")
        self.option_ping = QCheckBox("Show ping in Overview")
        self.option_processes = QCheckBox("Show running process count in System card")
        self.option_network = QCheckBox("Show network traffic rates")
        for checkbox in (self.option_fps, self.option_ping, self.option_processes, self.option_network):
            checkbox.setObjectName("optionCheck")
            checkbox.stateChanged.connect(self._save_options)
            layout.addWidget(self._option_row(checkbox))
        layout.addStretch()
        return page

    def _settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        title = QLabel("Application settings")
        title.setObjectName("sectionTitle")
        desc = QLabel("Adjust how Performance Air updates system information.")
        desc.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(10)
        row_frame = QFrame()
        row_frame.setObjectName("settingRow")
        row = QHBoxLayout(row_frame)
        row.setContentsMargins(16, 14, 16, 14)
        labels = QVBoxLayout()
        name = QLabel("Refresh interval")
        name.setObjectName("settingTitle")
        hint = QLabel("How often metrics are refreshed")
        hint.setObjectName("muted")
        labels.addWidget(name)
        labels.addWidget(hint)
        row.addLayout(labels)
        row.addStretch()
        self.refresh_select = QComboBox()
        for label, ms in (("0.5 seconds", 500), ("1 second", 1000), ("2 seconds", 2000), ("5 seconds", 5000)):
            self.refresh_select.addItem(label, ms)
        current = self.settings.value("refresh_ms", 1000, int)
        self.refresh_select.setCurrentIndex(max(0, self.refresh_select.findData(current)))
        self.refresh_select.currentIndexChanged.connect(self._change_refresh)
        row.addWidget(self.refresh_select)
        layout.addWidget(row_frame)
        about = QFrame()
        about.setObjectName("settingRow")
        about_layout = QVBoxLayout(about)
        about_layout.setContentsMargins(16, 14, 16, 14)
        about_title = QLabel("About Performance Air")
        about_title.setObjectName("settingTitle")
        about_text = QLabel("Version 1.0.0 · Windows desktop monitor\nGPU telemetry depends on driver and hardware support.")
        about_text.setObjectName("muted")
        about_layout.addWidget(about_title)
        about_layout.addWidget(about_text)
        layout.addWidget(about)
        layout.addStretch()
        return page

    def show_page(self, key):
        self.pages.setCurrentIndex({"overview": 0, "options": 1, "settings": 2}[key])
        self.page_title.setText(key.capitalize())
        for name, button in self.nav_buttons.items():
            button.setChecked(name == key)

    def _load_options(self):
        self.option_fps.setChecked(self.settings.value("show_fps", False, bool))
        self.option_ping.setChecked(self.settings.value("show_ping", False, bool))
        self.option_processes.setChecked(self.settings.value("show_processes", True, bool))
        self.option_network.setChecked(self.settings.value("show_network", True, bool))
        self._apply_option_visibility()

    def _save_options(self, *_):
        for key, widget in (("show_fps", self.option_fps), ("show_ping", self.option_ping),
                            ("show_processes", self.option_processes), ("show_network", self.option_network)):
            self.settings.setValue(key, widget.isChecked())
        self._apply_option_visibility()

    def _apply_option_visibility(self):
        if hasattr(self, "fps_card"):
            self.fps_card.setVisible(self.option_fps.isChecked())
            self.ping_card.setVisible(self.option_ping.isChecked())

    def _change_refresh(self):
        interval = int(self.refresh_select.currentData())
        self.settings.setValue("refresh_ms", interval)
        self.timer.setInterval(interval)

    def _ping(self):
        if self.ping_busy:
            return
        self.ping_busy = True
        def run():
            try:
                flag = "-n" if platform.system().lower() == "windows" else "-c"
                result = subprocess.run(["ping", flag, "1", "-w", "1200", "1.1.1.1"],
                                        capture_output=True, text=True, timeout=2)
                self.ping_value = round(result.elapsed * 1000) if hasattr(result, "elapsed") and result.returncode == 0 else None
                if result.returncode == 0:
                    import re
                    match = re.search(r"time[=<]([\d.]+)\s*ms", result.stdout, re.I)
                    if match:
                        self.ping_value = round(float(match.group(1)))
            except Exception:
                self.ping_value = None
            self.ping_busy = False
        Thread(target=run, daemon=True).start()

    def refresh(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            freq = psutil.cpu_freq()
            cores = psutil.cpu_count(logical=True) or 0
            detail = f"{cores} logical cores"
            if freq:
                detail += f" · {freq.current / 1000:.2f} GHz"
            self.metrics["cpu"].update_metric(f"{cpu:.0f}%", detail, cpu)

            gpu = gpu_stats()
            if gpu.get("available"):
                used, total = gpu["memory_used"], gpu["memory_total"]
                detail = f'{nice_bytes(used)} / {nice_bytes(total)} VRAM'
                if gpu.get("temperature") is not None:
                    detail += f' · {gpu["temperature"]}°C'
                self.metrics["gpu"].update_metric(f'{gpu["usage"]}%', gpu["name"] + " · " + detail, gpu["usage"])
            else:
                self.metrics["gpu"].update_metric("N/A", "GPU telemetry unavailable on this system", None)

            mem = psutil.virtual_memory()
            self.metrics["ram"].update_metric(f"{mem.percent:.0f}%", f"{nice_bytes(mem.used)} / {nice_bytes(mem.total)} used", mem.percent)

            drives = []
            for part in psutil.disk_partitions(all=False):
                if "cdrom" in part.opts.lower():
                    continue
                try:
                    drives.append((part.device.rstrip("\\\\"), psutil.disk_usage(part.mountpoint)))
                except (PermissionError, OSError):
                    pass
            if drives:
                drive, disk = max(drives, key=lambda item: item[1].percent)
                self.metrics["storage"].update_metric(f"{disk.percent:.0f}%", f"{drive} · {nice_bytes(disk.used)} / {nice_bytes(disk.total)}", disk.percent)
            else:
                self.metrics["storage"].update_metric("N/A", "No accessible drives found", None)

            now = time.time()
            net = psutil.net_io_counters()
            elapsed = max(0.1, now - self.last_tick)
            down = max(0, net.bytes_recv - self.last_net.bytes_recv) / elapsed
            up = max(0, net.bytes_sent - self.last_net.bytes_sent) / elapsed
            self.last_net, self.last_tick = net, now
            net_detail = f"↓ {nice_bytes(down)}/s  ↑ {nice_bytes(up)}/s" if self.option_network.isChecked() else "Traffic rates hidden in Options"
            self.metrics["network"].update_metric(f"↓ {nice_bytes(down)}/s", net_detail, None)

            uptime = int(time.time() - psutil.boot_time())
            days, rem = divmod(uptime, 86400)
            hours, _ = divmod(rem, 3600)
            processes = len(psutil.pids())
            sys_detail = f"Uptime {days}d {hours}h · {platform.system()} {platform.release()}"
            if self.option_processes.isChecked():
                sys_detail += f" · {processes} processes"
            self.metrics["system"].update_metric(str(processes), sys_detail, None)

            if self.option_fps.isChecked():
                self.fps_card.update_metric("N/A", "No game FPS source connected yet", None)
            if self.option_ping.isChecked():
                self._ping()
                self.ping_card.update_metric(f"{self.ping_value} ms" if self.ping_value is not None else "—",
                                             "Latency to 1.1.1.1" if self.ping_value is not None else "Checking connection…", None)
            self.updated_label.setText("Updated just now")
            self.header_status.setText("● SYSTEM ONLINE")
        except Exception as exc:
            self.header_status.setText("● MONITORING ISSUE")
            self.updated_label.setText(f"Update issue: {exc}")

    def _stylesheet(self):
        return f"""
        * {{ font-family: 'Segoe UI'; color: {TEXT}; }}
        QWidget#root {{ background: {BG}; }}
        QFrame#sidebar {{ background: #0b0c0f; border-right: 1px solid {BORDER}; }}
        QFrame#content {{ background: {BG}; }}
        QLabel#brandMark {{ background: {RED}; color: white; font-size: 22px; font-weight: 800; border-radius: 10px; }}
        QLabel#brandName {{ font-size: 12px; font-weight: 800; letter-spacing: 1px; }}
        QLabel#sidebarFoot {{ color: #686d77; font-size: 10px; }}
        QPushButton#navButton {{ text-align: left; padding: 13px 14px; border: 0; border-radius: 8px; color: {MUTED}; font-size: 14px; }}
        QPushButton#navButton:hover {{ background: #1b1d22; color: white; }}
        QPushButton#navButton:checked {{ background: #301a1d; color: #ff626b; border-left: 3px solid {RED}; font-weight: 700; }}
        QLabel#pageTitle {{ font-size: 25px; font-weight: 750; }}
        QLabel#systemStatus {{ color: #75d69a; font-size: 11px; font-weight: 700; }}
        QLabel#sectionTitle {{ font-size: 18px; font-weight: 700; }}
        QLabel#muted {{ color: {MUTED}; font-size: 12px; }}
        QFrame#metricCard, QFrame#settingRow {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}
        QLabel#cardHeading {{ color: #aeb2bb; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
        QLabel#liveTag {{ color: #ff6972; font-size: 9px; font-weight: 800; }}
        QLabel#metricValue {{ font-size: 28px; font-weight: 750; }}
        QProgressBar {{ background: #30333a; border: 0; border-radius: 3px; }}
        QProgressBar::chunk {{ background: {RED}; border-radius: 3px; }}
        QCheckBox#optionCheck {{ font-size: 14px; spacing: 10px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid #555b66; border-radius: 5px; background: #14161a; }}
        QCheckBox::indicator:checked {{ background: {RED}; border-color: {RED}; }}
        QLabel#settingTitle {{ font-size: 14px; font-weight: 650; }}
        QComboBox {{ background: #202329; border: 1px solid #383c45; border-radius: 7px; padding: 8px 12px; min-width: 130px; }}
        QComboBox QAbstractItemView {{ background: {PANEL}; selection-background-color: {RED}; }}
        """

    def closeEvent(self, event):
        self.settings.sync()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Segoe UI", 10))
    window = PerformanceAir()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
