from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
from typing import Any

# Ensure system PyGObject dist-packages is accessible inside virtualenvs on Debian/Ubuntu
try:
    import gi  # type: ignore
except ImportError:
    for path in ["/usr/lib/python3/dist-packages", "/usr/lib/python3.13/dist-packages", "/usr/lib/python3.12/dist-packages"]:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)
    import gi  # type: ignore

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Pango  # type: ignore # noqa: E402
from ruamel.yaml import YAML  # noqa: E402

from fingerswipe.config import default_config_path, load_config  # noqa: E402


def resolve_preset_command(candidates: list[str]) -> str:
    for cmd in candidates:
        bin_name = cmd.split()[0]
        if shutil.which(bin_name):
            return cmd
    return candidates[0]


class FingerSwipeSettingsWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="FingerSwipe Settings")
        self.set_default_size(800, 560)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Pre-resolve system binaries
        self._preset_browser = resolve_preset_command(["brave", "firefox", "google-chrome", "chromium", "zen-browser"])
        self._preset_terminal = resolve_preset_command(["konsole", "gnome-terminal", "alacritty", "kitty", "xfce4-terminal"])
        self._preset_file_manager = resolve_preset_command(["dolphin", "nautilus", "thunar", "pcmanfm"])
        self._preset_launcher = resolve_preset_command(["rofi -show drun", "krunner", "dmenu"])

        # HeaderBar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("FingerSwipe Settings")
        header.set_subtitle("Touchpad Gestures & 4-Finger Tap Configuration")
        self.set_titlebar(header)

        # Action Buttons in HeaderBar
        self.btn_open_config = Gtk.Button(label="📂 Open Config")
        self.btn_open_config.connect("clicked", self.on_open_config_clicked)
        header.pack_start(self.btn_open_config)

        self.btn_reset = Gtk.Button(label="🔄 Reset Defaults")
        self.btn_reset.connect("clicked", self.on_reset_clicked)
        header.pack_start(self.btn_reset)

        self.btn_apply = Gtk.Button(label="💾 Apply Configuration")
        self.btn_apply.get_style_context().add_class("suggested-action")
        self.btn_apply.connect("clicked", self.on_apply_clicked)
        header.pack_end(self.btn_apply)

        # Main Layout: Fixed Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        self.add(main_box)

        # Column 1: Gestures & Axis Tuning
        col1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.pack_start(col1, True, True, 0)

        lbl_sec1 = Gtk.Label()
        lbl_sec1.set_markup("<b>🎛️ Gestures &amp; Axis Tuning</b>")
        lbl_sec1.set_xalign(0)
        col1.pack_start(lbl_sec1, False, False, 0)

        # Frame for Gestures
        frame1 = Gtk.Frame()
        col1.pack_start(frame1, False, False, 0)
        grid1 = Gtk.Grid()
        grid1.set_column_spacing(12)
        grid1.set_row_spacing(12)
        grid1.set_margin_top(12)
        grid1.set_margin_bottom(12)
        grid1.set_margin_start(12)
        grid1.set_margin_end(12)
        frame1.add(grid1)

        # Sensitivity Curve Radio Group
        grid1.attach(Gtk.Label(label="Sensitivity Curve:", xalign=0), 0, 0, 1, 1)
        box_curve = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.radio_curve_linear = Gtk.RadioButton.new_with_label(None, "Linear (1:1 direct tracking)")
        self.radio_curve_exp = Gtk.RadioButton.new_with_label_from_widget(self.radio_curve_linear, "Exponential (Fine low-speed precision)")
        self.radio_curve_power = Gtk.RadioButton.new_with_label_from_widget(self.radio_curve_linear, "Power (Smooth acceleration)")
        box_curve.pack_start(self.radio_curve_linear, False, False, 0)
        box_curve.pack_start(self.radio_curve_exp, False, False, 0)
        box_curve.pack_start(self.radio_curve_power, False, False, 0)
        grid1.attach(box_curve, 1, 0, 1, 1)

        # Volume Axis Radio Group
        grid1.attach(Gtk.Label(label="Volume Control Axis:", xalign=0), 0, 1, 1, 1)
        box_vol = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.radio_vol_vert = Gtk.RadioButton.new_with_label(None, "Vertical (Up/Down)")
        self.radio_vol_horiz = Gtk.RadioButton.new_with_label_from_widget(self.radio_vol_vert, "Horizontal (Left/Right)")
        box_vol.pack_start(self.radio_vol_vert, False, False, 0)
        box_vol.pack_start(self.radio_vol_horiz, False, False, 0)
        grid1.attach(box_vol, 1, 1, 1, 1)

        # Brightness Axis Radio Group
        grid1.attach(Gtk.Label(label="Brightness Control Axis:", xalign=0), 0, 2, 1, 1)
        box_bright = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.radio_bright_horiz = Gtk.RadioButton.new_with_label(None, "Horizontal (Left/Right)")
        self.radio_bright_vert = Gtk.RadioButton.new_with_label_from_widget(self.radio_bright_horiz, "Vertical (Up/Down)")
        box_bright.pack_start(self.radio_bright_horiz, False, False, 0)
        box_bright.pack_start(self.radio_bright_vert, False, False, 0)
        grid1.attach(box_bright, 1, 2, 1, 1)

        # Volume Step Size Scale
        grid1.attach(Gtk.Label(label="Volume Step Size (%):", xalign=0), 0, 3, 1, 1)
        self.scale_vol_step = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 10, 1)
        self.scale_vol_step.set_value(1)
        grid1.attach(self.scale_vol_step, 1, 3, 1, 1)

        # Brightness Step Size Scale
        grid1.attach(Gtk.Label(label="Brightness Step Size (%):", xalign=0), 0, 4, 1, 1)
        self.scale_bright_step = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 10, 1)
        self.scale_bright_step.set_value(1)
        grid1.attach(self.scale_bright_step, 1, 4, 1, 1)

        # Axis Lock Threshold Scale
        grid1.attach(Gtk.Label(label="Axis Lock Threshold:", xalign=0), 0, 5, 1, 1)
        self.scale_lock_thresh = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1.0, 5.0, 0.5)
        self.scale_lock_thresh.set_value(2.0)
        grid1.attach(self.scale_lock_thresh, 1, 5, 1, 1)

        # Column 2: 4-Finger Tap Application Target
        col2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.pack_start(col2, True, True, 0)

        lbl_sec2 = Gtk.Label()
        lbl_sec2.set_markup("<b>👆 4-Finger Tap Application Target</b>")
        lbl_sec2.set_xalign(0)
        col2.pack_start(lbl_sec2, False, False, 0)

        frame2 = Gtk.Frame()
        col2.pack_start(frame2, False, False, 0)
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box2.set_margin_top(14)
        box2.set_margin_bottom(14)
        box2.set_margin_start(14)
        box2.set_margin_end(14)
        frame2.add(box2)

        # Tap Category Radio Selection
        self.radio_tap_super = Gtk.RadioButton.new_with_label(None, "🚀 System Start Menu (Default)")
        self.radio_tap_browser = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_tap_super, f"🌐 Web Browser (Auto-detected: {self._preset_browser})"
        )
        self.radio_tap_terminal = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_tap_super, f"🖥️ Terminal Emulator (Auto-detected: {self._preset_terminal})"
        )
        self.radio_tap_file_manager = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_tap_super, f"📁 File Manager (Auto-detected: {self._preset_file_manager})"
        )
        self.radio_tap_launcher = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_tap_super, f"⚡ Application Launcher (Auto-detected: {self._preset_launcher})"
        )

        box2.pack_start(self.radio_tap_super, False, False, 0)
        box2.pack_start(self.radio_tap_browser, False, False, 0)
        box2.pack_start(self.radio_tap_terminal, False, False, 0)
        box2.pack_start(self.radio_tap_file_manager, False, False, 0)
        box2.pack_start(self.radio_tap_launcher, False, False, 0)

        # Clean Visual Progress Bar (Hidden by default, zero text/percentages shown)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(False)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_no_show_all(True)
        col2.pack_start(self.progress_bar, False, False, 0)

        # Clean Confirmation Status Label (Fixed Height, Zero Shift)
        self.lbl_status = Gtk.Label(label="", xalign=0)
        self.lbl_status.set_ellipsize(Pango.EllipsizeMode.END)
        self.lbl_status.set_size_request(-1, 30)
        col2.pack_start(self.lbl_status, False, False, 0)

        self.load_existing_config()

    def on_open_config_clicked(self, button: Gtk.Button) -> None:
        cfg_path = default_config_path()
        if not cfg_path.exists():
            self.on_apply_clicked(button)
        try:
            subprocess.Popen(["xdg-open", str(cfg_path)])
            self.lbl_status.set_markup("<span foreground='#0284c7'>📂 Opened config.yaml in desktop text editor</span>")
        except Exception as err:
            self.lbl_status.set_markup(f"<span foreground='red'>Failed to open config: {err}</span>")

    def load_existing_config(self) -> None:
        cfg_path = default_config_path()
        if not cfg_path.exists():
            return
        try:
            cfg = load_config(cfg_path)
            if cfg.engine.curve == "exponential":
                self.radio_curve_exp.set_active(True)
            elif cfg.engine.curve == "power":
                self.radio_curve_power.set_active(True)
            else:
                self.radio_curve_linear.set_active(True)

            if cfg.volume.axis == "horizontal":
                self.radio_vol_horiz.set_active(True)
            else:
                self.radio_vol_vert.set_active(True)

            if cfg.brightness.axis == "vertical":
                self.radio_bright_vert.set_active(True)
            else:
                self.radio_bright_horiz.set_active(True)

            self.scale_vol_step.set_value(int(round(cfg.volume.step * 100)))
            self.scale_bright_step.set_value(int(round(cfg.brightness.step * 100)))
            self.scale_lock_thresh.set_value(cfg.engine.axis_lock_threshold)

            # Match tap action
            action = cfg.tap.action
            custom_cmd = cfg.tap.custom_command.strip()
            if action == "super_key":
                self.radio_tap_super.set_active(True)
            elif action == "custom_command":
                if custom_cmd == self._preset_browser:
                    self.radio_tap_browser.set_active(True)
                elif custom_cmd == self._preset_terminal:
                    self.radio_tap_terminal.set_active(True)
                elif custom_cmd == self._preset_file_manager:
                    self.radio_tap_file_manager.set_active(True)
                elif custom_cmd == self._preset_launcher:
                    self.radio_tap_launcher.set_active(True)
                else:
                    self.radio_tap_super.set_active(True)
        except Exception as e:
            print(f"Notice: Could not parse existing config: {e}")

    def on_apply_clicked(self, button: Gtk.Button) -> None:
        self.btn_apply.set_sensitive(False)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.show()
        self.lbl_status.set_markup("<span foreground='#0284c7'>⏳ Applying configuration...</span>")

        def save_worker() -> None:
            cfg_path = default_config_path()
            cfg_path.parent.mkdir(parents=True, exist_ok=True)

            curve = "linear"
            if self.radio_curve_exp.get_active():
                curve = "exponential"
            elif self.radio_curve_power.get_active():
                curve = "power"

            vol_axis = "horizontal" if self.radio_vol_horiz.get_active() else "vertical"
            bright_axis = "vertical" if self.radio_bright_vert.get_active() else "horizontal"

            selected_action = "super_key"
            selected_cmd = ""

            if self.radio_tap_browser.get_active():
                selected_action = "custom_command"
                selected_cmd = self._preset_browser
            elif self.radio_tap_terminal.get_active():
                selected_action = "custom_command"
                selected_cmd = self._preset_terminal
            elif self.radio_tap_file_manager.get_active():
                selected_action = "custom_command"
                selected_cmd = self._preset_file_manager
            elif self.radio_tap_launcher.get_active():
                selected_action = "custom_command"
                selected_cmd = self._preset_launcher

            # Load existing config structure if present to preserve non-GUI custom fields
            yaml = YAML()
            yaml.default_flow_style = False
            existing_dict: dict[str, Any] = {}
            if cfg_path.exists():
                try:
                    with open(cfg_path, "r") as f:
                        existing_dict = yaml.load(f) or {}
                except Exception:
                    existing_dict = {}

            if not isinstance(existing_dict, dict):
                existing_dict = {}

            engine_sec = existing_dict.setdefault("engine", {})
            vol_sec = existing_dict.setdefault("volume", {})
            bright_sec = existing_dict.setdefault("brightness", {})
            tap_sec = existing_dict.setdefault("tap", {})
            logging_sec = existing_dict.setdefault("logging", {})

            engine_sec["curve"] = curve
            engine_sec["axis_lock_threshold"] = float(self.scale_lock_thresh.get_value())

            vol_sec["enabled"] = True
            vol_sec["axis"] = vol_axis
            vol_sec["step"] = float(self.scale_vol_step.get_value()) / 100.0

            bright_sec["enabled"] = True
            bright_sec["axis"] = bright_axis
            bright_sec["step"] = float(self.scale_bright_step.get_value()) / 100.0

            tap_sec["enabled"] = True
            tap_sec["action"] = selected_action
            tap_sec["custom_command"] = selected_cmd

            if "level" not in logging_sec:
                logging_sec["level"] = "INFO"
            if "json" not in logging_sec:
                logging_sec["json"] = False

            with open(cfg_path, "w") as f:
                yaml.dump(existing_dict, f)

            try:
                os.utime(cfg_path, None)
            except Exception:
                pass

            # Smooth 10-Second Visual Progress Bar Animation (50 steps @ 0.2s = 10.0s)
            for step in range(1, 51):
                time.sleep(0.2)
                fraction = step / 50.0
                GLib.idle_add(self.progress_bar.set_fraction, fraction)

            def on_complete() -> None:
                self.progress_bar.hide()
                self.lbl_status.set_markup("<span foreground='green'>✓ Configuration applied &amp; daemon reloaded successfully!</span>")
                self.btn_apply.set_sensitive(True)

            GLib.idle_add(on_complete)

            GLib.idle_add(on_complete)

        threading.Thread(target=save_worker, daemon=True).start()

    def on_reset_clicked(self, button: Gtk.Button) -> None:
        self.radio_curve_linear.set_active(True)
        self.radio_vol_vert.set_active(True)
        self.radio_bright_horiz.set_active(True)
        self.scale_vol_step.set_value(1)
        self.scale_bright_step.set_value(1)
        self.scale_lock_thresh.set_value(2.0)
        self.radio_tap_super.set_active(True)

        self.lbl_status.set_markup("<span foreground='#0284c7'>✓ Controls reset to defaults. Click 'Apply Configuration' to save.</span>")


def launch_native_gui() -> None:
    try:
        win = FingerSwipeSettingsWindow()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()
    except KeyboardInterrupt:
        print("\n👋 FingerSwipe GUI closed.")
        sys.exit(0)
