# FingerSwipe

<p align="center">
  <a href="https://github.com/deekshithvodela/FingerSwipe/releases"><img src="https://img.shields.io/badge/version-v1.2.0-blue.svg?style=for-the-badge&logo=git" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License"></a>
  <a href="https://kernel.org"><img src="https://img.shields.io/badge/platform-Linux-orange.svg?style=for-the-badge&logo=linux&logoColor=white" alt="Platform"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.13+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://kde.org"><img src="https://img.shields.io/badge/KDE_Plasma-OSD_Support-1D99F3.svg?style=for-the-badge&logo=kde&logoColor=white" alt="KDE Plasma"></a>
  <a href="https://pipewire.org"><img src="https://img.shields.io/badge/audio-PipeWire-000000.svg?style=for-the-badge" alt="PipeWire"></a>
</p>

FingerSwipe is a lightweight, responsive Linux user service that controls default PipeWire sink volume and display brightness with three-finger touchpad swipes, and opens target applications or the Start Menu with a 4-finger tap.

**[Live Website & Documentation Portal](https://deekshithvodela.github.io/FingerSwipe/)**  •  **[GitHub Releases & Downloads](https://github.com/deekshithvodela/FingerSwipe/releases)**

## Requirements

- CMake 3.28+ and a C23 compiler
- Python 3.13 and `uv`
- Development packages for libinput, libudev, and PipeWire 0.3
- A systemd user session and a PipeWire user service

## Build

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --build build --parallel
UV_CACHE_DIR=/tmp/fingerswipe-uv-cache uv build
```

Run the verification gate before installation:

```sh
.venv/bin/pytest -q
.venv/bin/ruff check src tests install
.venv/bin/mypy src tests
```

## Quick Verification

Run pre-flight checks before or after installation:

```sh
fingerswipe check
```

## Install & Update

Pre-built binaries, universal packages, and checksums are available for download on [GitHub Releases](https://github.com/deekshithvodela/FingerSwipe/releases).

### Method 1A: APT Repository (Recommended for Debian / Ubuntu / Pop!_OS / Mint)

Add the FingerSwipe APT repository to get automatic system updates via `sudo apt upgrade`:

1. **Add FingerSwipe GPG Key & Repository:**
   ```sh
   curl -fsSL https://deekshithvodela.github.io/FingerSwipe/apt/KEY.gpg | sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/fingerswipe.gpg
   echo "deb [signed-by=/etc/apt/trusted.gpg.d/fingerswipe.gpg] https://deekshithvodela.github.io/FingerSwipe/apt stable main" | sudo tee /etc/apt/sources.list.d/fingerswipe.list
   ```
2. **Install FingerSwipe & Enable Service:**
   ```sh
   sudo apt update && sudo apt install fingerswipe
   systemctl --user enable --now fingerswipe.service
   ```

---

### Method 1B: Standalone Debian Package (.deb)

Download `fingerswipe_1.2.0_amd64.deb` from [Releases](https://github.com/deekshithvodela/FingerSwipe/releases/latest) or build locally:

1. **Install or Update:**
   ```sh
   # Install fresh or update an existing version:
   sudo apt install ./fingerswipe_1.2.0_amd64.deb
   ```
2. **Enable and start the systemd user service (first-time install only):**
   ```sh
   systemctl --user enable --now fingerswipe.service
   ```

*(When updating via `.deb`, the package automatically stops the running service, upgrades files, reloads systemd/udev, and restarts the service without modifying your custom configuration.)*

---

### Method 2: Universal Linux Installer (Arch, Fedora, openSUSE, etc.)

Download `fingerswipe-1.2.0-linux-x86_64.tar.gz` from [Releases](https://github.com/deekshithvodela/FingerSwipe/releases/latest) or build locally:

1. **Extract the universal package:**
   ```sh
   # Extract the release bundle
   tar -xzf fingerswipe-1.2.0-linux-x86_64.tar.gz
   cd fingerswipe-1.2.0-linux-x86_64
   ```
2. **Run the installer:**
   ```sh
   sudo ./install.sh
   ```
3. **Start the user service:**
   ```sh
   systemctl --user enable --now fingerswipe.service
   ```

*(To update in the future, simply re-run `sudo ./install.sh`. It automatically detects the existing install, cleanly stops the background daemon, updates binaries, and restarts the service.)*

---

### Method 3: Manual Build & Install from Source

```sh
sudo cmake --install build
sudo ldconfig
sudo uv venv --python 3.13 /opt/fingerswipe
sudo uv pip install --python /opt/fingerswipe/bin/python \
  dist/fingerswipe-1.1.0-py3-none-any.whl
sudo /opt/fingerswipe/bin/python install/install.py --prefix /usr
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=input
systemctl --user daemon-reload
systemctl --user enable --now fingerswipe.service
```

---

## Updating FingerSwipe

Updating is completely seamless and **preserves your custom configuration** (`~/.config/fingerswipe/config.yaml`):

- **Debian / Ubuntu (.deb):** `sudo apt install --reinstall ./fingerswipe_1.1.0_amd64.deb` (Automatically restarts the service).
- **Universal Package:** Re-run `sudo ./install.sh` from the new release directory.
- **Source Build:** Run `git pull`, rebuild, re-run `sudo ./install.sh` or `sudo cmake --install build`, and run `systemctl --user restart fingerswipe.service`.

---

## Verification & Configuration

Log out and back in, or disconnect and reconnect the touchpad, if its session
ACL was established before the udev rule was installed. Verify deployment with:

```sh
fingerswipe --help
ldconfig -p | grep libfingerswipe
systemctl --user status fingerswipe.service
journalctl --user -u fingerswipe.service -n 50
```

Copy `config.yaml` to `~/.config/fingerswipe/config.yaml` to customize gesture curves, sensitivity, and dead zones. Malformed configuration is rejected at startup. Run `fingerswipe --help` for explicit configuration and native-library paths.

### CLI Flags & Usage

```sh
# Run service with all default components (Volume on Vertical, Brightness on Horizontal)
fingerswipe run

# Disable volume control (Brightness only)
fingerswipe run --disable-volume

# Disable brightness control (Volume only)
fingerswipe run --disable-brightness

# Swap gesture axes (Brightness on Vertical, Volume on Horizontal)
fingerswipe run --volume-axis horizontal --brightness-axis vertical
```

### Configuration Reference

The default settings provide seamless, conflict-free 3-finger volume and brightness gestures.

```yaml
engine:
  dead_zone: 0.0          # Minimum delta below which movement is ignored (default: 0.0)
  smoothing: 1.0          # Smoothing factor (alpha in (0, 1]) where 1.0 is no smoothing (default: 1.0)
  sensitivity: 1.0        # Input coordinate scaling factor (default: 1.0)
  curve: linear           # Scaling curve ('linear', 'power', or 'exponential') (default: linear)
  axis_lock_threshold: 2.0 # Motion threshold to lock gesture axis (default: 2.0)

volume:
  enabled: true           # Enable volume control (default: true)
  axis: vertical          # Gesture axis ('vertical' or 'horizontal') (default: vertical)
  minimum: 0.0            # Minimum volume clamp (default: 0.0)
  maximum: 1.0            # Maximum volume clamp (default: 1.0)
  step: 0.01              # Volume step size per threshold (0.01 = 1%) (default: 0.01)
  threshold: 4.0          # Accumulated delta required to trigger a step (default: 4.0)

brightness:
  enabled: true           # Enable display brightness control (default: true)
  axis: horizontal        # Gesture axis ('horizontal' or 'vertical') (default: horizontal)
  minimum: 0.01           # Minimum brightness clamp (1%) (default: 0.01)
  maximum: 1.0            # Maximum brightness clamp (default: 1.0)
  step: 0.01              # Brightness step size per threshold (0.01 = 1%) (default: 0.01)
  threshold: 4.0          # Accumulated delta required to trigger a step (default: 4.0)
```

> [!NOTE]
> When `engine.curve` is set to `linear`, input coordinate clamping to `[-1.0, 1.0]` is bypassed to allow raw touchpad gestures to flow directly to the volume controller without range limitation. For non-linear curves (`power` and `exponential`), values are clamped to `[-1.0, 1.0]` for compatibility.

## Uninstall

### If installed via Debian Package:

```sh
sudo apt purge fingerswipe
```

### If installed manually:

```sh
systemctl --user disable --now fingerswipe.service
sudo rm -rf /opt/fingerswipe
sudo rm -f /usr/local/lib/libfingerswipe.so /usr/local/lib/libfingerswipe.so.1 \
  /usr/local/lib/libfingerswipe.so.1.0.0
sudo rm -rf /usr/local/include/fingerswipe
sudo rm -f /usr/lib/systemd/user/fingerswipe.service \
  /usr/lib/udev/rules.d/99-fingerswipe.rules
sudo ldconfig
systemctl --user daemon-reload
```
