# FingerSwipe

FingerSwipe is a Linux user service that controls the default PipeWire sink
volume with three-finger vertical touchpad swipes.

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

## Hardware Eligibility Check

Before installing, you can verify if your system hardware and software environments are eligible:

```sh
# Run check using the local environment (before installation)
.venv/bin/python -m fingerswipe check
```

Or, if already installed:
```sh
fingerswipe check
```

## Install

### Method 1: Debian Package (Recommended)

You can build and install FingerSwipe as an installable Debian package:

1. Build the `.deb` package:
   ```sh
   ./build_deb.sh
   ```
2. Install the package:
   ```sh
   sudo apt install ./fingerswipe_1.0.0_amd64.deb
   ```
3. Enable and start the systemd user service:
   ```sh
   systemctl --user enable --now fingerswipe.service
   ```

---

### Method 2: Manual Build & Install

The native library is installed under `/usr/local`. Python is installed in an
isolated virtual environment at the exact executable path used by systemd:

```sh
sudo cmake --install build
sudo ldconfig
sudo uv venv --python /usr/bin/python3.13 /opt/fingerswipe
sudo uv pip install --python /opt/fingerswipe/bin/python \
  dist/fingerswipe-1.0.0-py3-none-any.whl
sudo /opt/fingerswipe/bin/python install/install.py --prefix /usr
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=input
systemctl --user daemon-reload
systemctl --user enable --now fingerswipe.service
```

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

### Configuration Reference

The default settings are tuned to match `FingerSwipe1` behavior (unbounded linear scaling for high responsiveness).

```yaml
engine:
  dead_zone: 0.0      # Minimum delta below which movement is ignored (default: 0.0)
  smoothing: 1.0      # Smoothing factor (alpha in (0, 1]) where 1.0 is no smoothing (default: 1.0)
  sensitivity: 1.0    # Input coordinate scaling factor (default: 1.0)
  curve: linear       # Scaling curve ('linear', 'power', or 'exponential') (default: linear)

volume:
  minimum: 0.0        # Minimum volume clamp (default: 0.0)
  maximum: 1.0        # Maximum volume clamp (default: 1.0)
  step: 0.01          # Volume step size per threshold (0.01 = 1%) (default: 0.01)
  threshold: 4.0      # Accumulated vertical delta required to trigger a step (default: 4.0)
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
