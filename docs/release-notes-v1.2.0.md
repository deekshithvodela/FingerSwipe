# FingerSwipe v1.2.0 — Custom 4-Finger Tap Launcher & Visual Settings GUI

FingerSwipe v1.2.0 brings custom 4-finger tap shortcuts, an intuitive GTK desktop GUI interface, instant live configuration hot-reloading, persistent touchpad tap gestures that stay reliable after reboots, and official signed APT repository support for Linux.

---

## What's New in v1.2.0

- **Custom 4-Finger Tap Launcher:** Tap your touchpad with 4 fingers to instantly open your favorite Web Browser, Terminal, File Manager, or Application Launcher — or open the system Start Menu.
- **Visual Settings GUI (`fingerswipe gui`):** Customize swipe axes, volume/brightness step sizes, motion curves, and 4-finger tap shortcuts from a desktop GUI interface with a visual configuration progress bar.
- **Instant Configuration Hot-Reloading:** Settings saved in the GUI take effect within 0.5 seconds without requiring service restarts or manual reloads.
- **Reliable Reboot Persistence:** Virtual key bindings ensure 4-finger touchpad tap gestures and Start Menu triggers stay reliable across system reboots.
- **Official Signed APT Repository & Package Upgrades:** Install and update FingerSwipe effortlessly on Ubuntu 24.04 LTS, Debian, and all major Linux distributions via our signed APT repository, `.deb` package, or universal archive.

---

## Installation & Usage

### Official APT Repository (Recommended):
```bash
sudo curl -fsSL https://deekshithvodela.github.io/FingerSwipe/apt/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/fingerswipe-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/fingerswipe-archive-keyring.gpg] https://deekshithvodela.github.io/FingerSwipe/apt stable main" | sudo tee /etc/apt/sources.list.d/fingerswipe.list
sudo apt update
sudo apt install fingerswipe
```

### Debian / Ubuntu (`.deb`):
```bash
sudo apt update
sudo apt install --reinstall ./fingerswipe_1.2.0_amd64.deb
```

### Universal Linux Package (`.tar.gz`):
```bash
tar -xzf fingerswipe-1.2.0-linux-x86_64.tar.gz
cd fingerswipe-1.2.0-linux-x86_64
sudo ./install.sh
```

### Launch Visual Settings GUI:
```bash
fingerswipe gui
```

**Full Changelog**: https://github.com/deekshithvodela/FingerSwipe/compare/v1.1.0...v1.2.0
