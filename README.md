# Performance Air

A lightweight Windows desktop performance monitor with a clean red, black and white interface.

## Features
- Live CPU utilization, frequency and logical core count
- GPU utilization, VRAM usage and temperature when NVIDIA telemetry is available
- RAM and drive storage usage
- Network upload/download rates, system uptime and running process count
- Optional overview widgets for FPS and network ping
- Configurable refresh interval and persistent preferences

## Run from source
1. Install Python 3.10 or newer.
2. Run `py -m pip install -r requirements.txt`.
3. Double-click `run.bat` or run `py main.py`.

## Build a Windows executable
Run `build.bat`. The packaged application will be created in `dist/Performance Air/`. Distribute the complete folder, not only the EXE.

## Hardware support
GPU telemetry uses NVIDIA's NVML interface through `nvidia-ml-py`. It requires a supported NVIDIA driver and GPU. Other system metrics use psutil.

**FPS note:** the FPS option and overview card are present, but a reliable FPS value requires a game-specific capture source. The current version displays an unavailable state rather than inventing a number. A future PresentMon/game integration can provide real frame-rate data.

## Scope
Performance Air is a monitoring application. It does not modify CPU/GPU clocks, fan curves, game processes, or system settings.
