# Performance Air

A lightweight Windows desktop performance monitor with a clean red, black and white interface.

## Features
- Live CPU utilization, frequency, core count and temperature when supported
- GPU utilization, memory, temperature and name when NVIDIA telemetry is available
- RAM and per-drive storage usage
- Network upload/download rates, uptime and running process count
- Optional overview metrics for FPS and network ping
- Configurable refresh interval and persistent preferences

## Requirements
- Windows 10 or Windows 11
- Python 3.10+
- NVIDIA drivers for NVIDIA GPU telemetry (optional)

## Run from source
```powershell
py -m pip install -r requirements.txt
py main.py
```

GPU telemetry uses NVML through `nvidia-ml-py` when available. Other system metrics use psutil. FPS is shown as unavailable until a supported game-specific source is connected; this app does not pretend to measure a universal system-wide FPS value.

## Notes
Performance Air is a monitoring application. It does not modify CPU/GPU clocks, fan curves, game processes, or system settings.
