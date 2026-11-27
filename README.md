# Performance Air

A Windows desktop performance monitor with a clean red, black and white interface.

## Features

- Live CPU usage, frequency and logical core count
- NVIDIA GPU utilization, VRAM usage and temperature when NVML is available
- RAM and storage usage
- Network upload/download rates
- Local IPv4 address and optional public IP lookup
- System uptime and running process count
- Optional FPS and ping cards
- Configurable refresh interval and saved preferences
- FPS capture through PresentMon for many DirectX, OpenGL and Vulkan games, including Roblox when its frames are visible to PresentMon

## Run the standalone app

Run `build.bat` once to create:

```
dist/Performance Air.exe
```

The EXE is a single-file, windowed application. It does not need a Command Prompt to remain open. You can launch it directly or use `run.vbs` to launch it without showing a console window.

## Build

1. Install Python 3.10 or newer.
2. Run `build.bat`.
3. Open `dist/Performance Air.exe`.

The build script downloads the official x64 PresentMon console executable from the GameTechDev/PresentMon GitHub release and bundles it with Python and the app dependencies inside the EXE. If the download is unavailable, you can select a local PresentMon executable in Settings.

## Game FPS setup

FPS capture uses the official PresentMon console executable. The build script downloads and bundles it automatically. You can also select a different copy in **Settings → Game FPS capture**.

PresentMon supports a broad range of Windows graphics APIs, but no capture tool can guarantee a reading for every game. FPS can be unavailable when a game blocks frame-event capture, uses an unsupported presentation path, or Windows permissions prevent ETW capture. Some systems may need the Windows **Performance Log Users** permission or an elevated launch for complete process visibility. The app does not attempt to change Windows permissions automatically.

Roblox experiences run under the Roblox player process; the capture follows the focused foreground application rather than relying on individual experience names.

## Options

- Show/hide FPS and ping cards
- Show/hide network traffic rates
- Show local IP address
- Optionally look up public IP through `api.ipify.org` (requires internet access)
- Show/hide CPU frequency, GPU temperature, storage card and process count
- Set refresh interval

The public IP option contacts an external IP lookup service only when enabled. The local IP is read from the active network route.

## Hardware support

CPU, RAM, storage and network metrics use psutil and Windows networking APIs. GPU utilization/VRAM/temperature currently use NVIDIA NVML; other GPU vendors may show N/A until additional providers are added.

PresentMon is an open-source component from Intel's GameTechDev project; see [the official project and license](https://github.com/GameTechDev/PresentMon).

## Scope

Performance Air is a monitoring app. It does not change CPU/GPU clocks, fan curves, game processes or system settings.
