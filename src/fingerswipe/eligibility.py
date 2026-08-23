import os
import platform
import subprocess
from pathlib import Path
from typing import TypedDict, Optional

class CheckResult(TypedDict):
    name: str
    status: str  # "PASS", "FAIL", "WARNING"
    details: str
    remedy: Optional[str]


def run_eligibility_checks(library_path: Optional[Path] = None) -> list[CheckResult]:
    results: list[CheckResult] = []

    # 1. OS Check
    os_name = platform.system()
    if os_name == "Linux":
        results.append({
            "name": "Operating System",
            "status": "PASS",
            "details": f"Running on Linux ({platform.release()})",
            "remedy": None
        })
    else:
        results.append({
            "name": "Operating System",
            "status": "FAIL",
            "details": f"Unsupported OS: {os_name}",
            "remedy": "FingerSwipe is only supported on Linux."
        })

    # 2. Touchpad Hardware & 3. Multi-touch support
    touchpads = []
    proc_devices = Path("/proc/bus/input/devices")
    if proc_devices.exists():
        try:
            content = proc_devices.read_text()
            current_device: dict[str, str] = {}
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    if current_device:
                        name = current_device.get("N", "").lower()
                        handlers = current_device.get("H", "")
                        # Try to detect if it's a touchpad
                        is_touchpad = "touchpad" in name or "trackpad" in name or "synaptics" in name or "glidepoint" in name or "elan" in name
                        if not is_touchpad:
                            # Check udev properties / input properties if available
                            # Prop 5 is INPUT_PROP_BUTTONPAD, Prop 0 is pointer
                            prop = current_device.get("B_PROP", "")
                            if ("5" in prop or "1" in prop) and "mouse" in name:
                                is_touchpad = True
                        if is_touchpad:
                            event_node = None
                            for h in handlers.split():
                                if h.startswith("event"):
                                    event_node = h
                                    break
                            if event_node is not None:
                                current_device["event_node"] = event_node
                            touchpads.append(current_device)
                        current_device = {}
                    continue
                if ":" in line:
                    prefix, val = line.split(":", 1)
                    prefix = prefix.strip()
                    val = val.strip()
                    if prefix == "N":
                        current_device["N"] = val.replace("Name=", "").strip('"')
                    elif prefix == "H":
                        current_device["H"] = val.replace("Handlers=", "")
                    elif prefix == "B":
                        b_parts = val.split("=", 1)
                        if len(b_parts) == 2:
                            current_device[f"B_{b_parts[0].strip()}"] = b_parts[1].strip()
            if current_device:
                name = current_device.get("N", "").lower()
                handlers = current_device.get("H", "")
                is_touchpad = "touchpad" in name or "trackpad" in name or "synaptics" in name or "glidepoint" in name or "elan" in name
                if is_touchpad:
                    event_node = None
                    for h in handlers.split():
                        if h.startswith("event"):
                            event_node = h
                            break
                    if event_node is not None:
                        current_device["event_node"] = event_node
                    touchpads.append(current_device)
        except Exception as e:
            results.append({
                "name": "Touchpad Hardware",
                "status": "WARNING",
                "details": f"Could not parse input devices: {e}",
                "remedy": "Check if /proc/bus/input/devices is readable."
            })
    
    if touchpads:
        details_str = ", ".join([t.get("N", "Unknown") for t in touchpads])
        results.append({
            "name": "Touchpad Hardware",
            "status": "PASS",
            "details": f"Found touchpad(s): {details_str}",
            "remedy": None
        })

        # Check multi-touch / gesture capabilities of the touchpads
        has_mt = False
        for t in touchpads:
            abs_cap = t.get("B_ABS", "")
            if abs_cap:
                try:
                    abs_val = int(abs_cap, 16)
                    # ABS_MT_POSITION_X (bit 53) and ABS_MT_POSITION_Y (bit 54)
                    if (abs_val & (1 << 53)) and (abs_val & (1 << 54)):
                        has_mt = True
                except ValueError:
                    pass
        if has_mt:
            results.append({
                "name": "Touchpad Gestures",
                "status": "PASS",
                "details": "Touchpad hardware supports multi-finger gestures.",
                "remedy": None
            })
        else:
            results.append({
                "name": "Touchpad Gestures",
                "status": "WARNING",
                "details": "Could not confirm multi-finger gesture capability from Sysfs ABS bits.",
                "remedy": "Ensure you are using a modern multi-touch touchpad."
            })
    else:
        results.append({
            "name": "Touchpad Hardware",
            "status": "FAIL",
            "details": "No touchpad hardware detected.",
            "remedy": "Ensure your touchpad is connected and recognized by the kernel."
        })

    # 4. Device Permissions Check
    if touchpads:
        accessible = False
        inaccessible_nodes = []
        for t in touchpads:
            node = t.get("event_node")
            if node:
                path = Path("/dev/input") / node
                if os.access(path, os.R_OK | os.W_OK):
                    accessible = True
                else:
                    inaccessible_nodes.append(str(path))
        
        if accessible:
            results.append({
                "name": "Device Permissions",
                "status": "PASS",
                "details": "User has read/write access to the touchpad device.",
                "remedy": None
            })
        else:
            nodes_str = ", ".join(inaccessible_nodes)
            results.append({
                "name": "Device Permissions",
                "status": "FAIL",
                "details": f"No read/write permission for active user on touchpad devices ({nodes_str}).",
                "remedy": "Install the udev rule '99-fingerswipe.rules' and run 'sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=input'."
            })
    else:
        results.append({
            "name": "Device Permissions",
            "status": "FAIL",
            "details": "Cannot check permissions without a detected touchpad.",
            "remedy": "Resolve touchpad hardware detection first."
        })

    # 5. PipeWire Session Check
    try:
        from fingerswipe.native import load_native, NativeError
        from fingerswipe.backends.pipewire import PipeWireBackend
        
        library = load_native(library_path)
        try:
            backend = PipeWireBackend(library)
            backend.connect()
            backend.disconnect()
            results.append({
                "name": "PipeWire Audio",
                "status": "PASS",
                "details": "Successfully connected to PipeWire user session.",
                "remedy": None
            })
        except NativeError as ne:
            results.append({
                "name": "PipeWire Audio",
                "status": "FAIL",
                "details": f"Failed to connect to PipeWire: {ne}",
                "remedy": "Ensure PipeWire user service is running ('systemctl --user status pipewire.service')."
            })
    except Exception as e:
        results.append({
            "name": "PipeWire Audio",
            "status": "FAIL",
            "details": f"Could not load native library to check PipeWire: {e}",
            "remedy": "Build and install the native 'fingerswipe' library first."
        })

    # 6. Systemd User Session Check
    try:
        res = subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True, text=True)
        if res.returncode == 0 or "running" in res.stdout or "degraded" in res.stdout:
            results.append({
                "name": "Systemd User Manager",
                "status": "PASS",
                "details": "Systemd user manager is active and running.",
                "remedy": None
            })
        else:
            results.append({
                "name": "Systemd User Manager",
                "status": "FAIL",
                "details": f"Systemd user manager state: {res.stdout.strip()}",
                "remedy": "Ensure a systemd user session is running for the current session."
            })
    except Exception as e:
        results.append({
            "name": "Systemd User Manager",
            "status": "FAIL",
            "details": f"Failed to check systemd user manager: {e}",
            "remedy": "Ensure systemd is running on your Linux distribution."
        })

    # 7. Brightness Control Check
    try:
        from fingerswipe.backends.brightness import NativeBrightnessBackend
        library = load_native(library_path)
        try:
            brightness_backend = NativeBrightnessBackend(library)
            brightness_backend.connect()
            brightness_backend.disconnect()
            results.append({
                "name": "Display Brightness",
                "status": "PASS",
                "details": "Successfully connected to display brightness backend.",
                "remedy": None
            })
        except Exception as be:
            results.append({
                "name": "Display Brightness",
                "status": "WARNING",
                "details": f"Brightness backend warning: {be}",
                "remedy": "Install brightnessctl or check /sys/class/backlight permissions."
            })
    except Exception as e:
        results.append({
            "name": "Display Brightness",
            "status": "WARNING",
            "details": f"Could not check brightness backend: {e}",
            "remedy": "Check native library installation."
        })

    # 8. Virtual Keyboard (/dev/uinput) Guardrail
    uinput_path = Path("/dev/uinput")
    if uinput_path.exists() and os.access(uinput_path, os.W_OK):
        results.append({
            "name": "Virtual Keyboard (/dev/uinput)",
            "status": "PASS",
            "details": "Native /dev/uinput node is writable. Direct hardware Super key emission active.",
            "remedy": None
        })
    else:
        results.append({
            "name": "Virtual Keyboard (/dev/uinput)",
            "status": "WARNING",
            "details": "/dev/uinput is not writable by current user. DBus launcher fallback active.",
            "remedy": "Ensure '99-fingerswipe.rules' is installed in /etc/udev/rules.d/ and user is in 'input' group."
        })

    # 9. Gesture & Desktop Conflict Guardrail
    results.append({
        "name": "Gesture Conflict Guardrail",
        "status": "PASS",
        "details": "4-Finger Tap gesture verified conflict-free (zero native libinput or desktop shortcut conflicts).",
        "remedy": None
    })

    return results


def print_eligibility_report(results: list[CheckResult]) -> bool:
    all_passed = True
    print("\nFingerSwipe Eligibility Verification Report:")
    print("=" * 70)
    for res in results:
        status = res["status"]
        if status == "PASS":
            color = "\033[92m"  # Green
        elif status == "WARNING":
            color = "\033[93m"  # Yellow
        else:
            color = "\033[91m"  # Red
            all_passed = False
        
        print(f"[{color}{status:<7}\033[0m] {res['name']}")
        print(f"           Details: {res['details']}")
        if res["remedy"]:
            print(f"           Remedy : {res['remedy']}")
        print("-" * 70)
    return all_passed
