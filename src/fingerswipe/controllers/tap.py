from __future__ import annotations

import ctypes
import logging
import re
import shlex
import shutil
import subprocess
import time

from fingerswipe.config import TapConfig
from fingerswipe.controllers.base import Controller
from fingerswipe.engine.motion import ProcessedMotion


class TapController(Controller):

    def __init__(self, config: TapConfig, library: ctypes.CDLL | None = None) -> None:
        self._config = config
        self._library = library
        self._logger = logging.getLogger(__name__)
        self._last_trigger_time = 0.0

    def update_config(self, config: TapConfig) -> None:
        self._config = config

    def trigger(self) -> None:
        if not self._config.enabled:
            return

        now = time.monotonic()
        if now - self._last_trigger_time < 0.3:
            self._logger.debug("Tap trigger ignored due to 300ms debounce guard")
            return
        self._last_trigger_time = now

        if self._config.action == "super_key":
            self._trigger_super_key()
        elif self._config.action == "custom_command" and self._config.custom_command:
            self._trigger_custom_command(self._config.custom_command)

    def _trigger_super_key(self) -> None:
        if self._library and hasattr(self._library, "fs_uinput_trigger_super_key"):
            if hasattr(self._library, "fs_uinput_init"):
                self._library.fs_uinput_init()
            res = self._library.fs_uinput_trigger_super_key()
            if res == 0:
                self._logger.info("4-finger tap: Super key emitted via uinput")
                return

        if self._trigger_dbus_shortcut():
            return

        self._trigger_dbus_fallback()

    def _trigger_dbus_shortcut(self) -> bool:
        for cmd in [
            "gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell --method org.kde.PlasmaShell.activateLauncherMenu",
            "gdbus call --session --dest org.kde.kglobalaccel --object-path /component/plasmashell --method org.kde.kglobalaccel.Component.invokeShortcut 'activate application launcher'",
            "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval string:Main.overview.toggle();",
        ]:
            try:
                executable = shlex.split(cmd)[0]
                if shutil.which(executable):
                    subprocess.Popen(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._logger.info("4-finger tap: Start Menu triggered via D-Bus session shortcut")
                    return True
            except Exception:
                continue
        return False

    def _trigger_dbus_fallback(self) -> None:
        for cmd in [
            "wtype -k Super_L",
            "ydotool key 125:1 125:0",
            "xdotool key Super_L",
        ]:
            try:
                executable = shlex.split(cmd)[0]
                if shutil.which(executable):
                    subprocess.Popen(shlex.split(cmd))
                    self._logger.info("4-finger tap: Start Menu triggered via %s", executable)
                    return
            except Exception:
                continue

        self._logger.warning("4-finger tap: Failed to emit Super key (uinput and fallbacks unavailable)")

    def _trigger_custom_command(self, command: str) -> None:
        try:
            clean_cmd = re.sub(r"\s*--file-forwarding", "", command)
            clean_cmd = re.sub(r"\s*@@[fFuU]?\s*@@?", "", clean_cmd)
            clean_cmd = re.sub(r"\s*%[fFuUkKiIc]", "", clean_cmd).strip()

            if not clean_cmd:
                return

            unit_name = f"fingerswipe-app-{int(time.time() * 1000)}"

            # Check if command is gtk-launch or a desktop app ID
            if clean_cmd.startswith("gtk-launch "):
                app_id = clean_cmd.split(maxsplit=1)[1]
                try:
                    subprocess.Popen(["systemd-run", "--user", "--scope", "--slice=app.slice", f"--unit={unit_name}", "gtk-launch", app_id])
                    self._logger.info("4-finger tap: Spawned desktop session scope '%s' via gtk-launch '%s'", unit_name, app_id)
                    return
                except Exception as sys_err:
                    self._logger.debug("systemd-run failed: %s; falling back to direct gtk-launch", sys_err)
                    subprocess.Popen(["gtk-launch", app_id])
                    return

            parts = shlex.split(clean_cmd)
            bin_name = parts[0]
            resolved_bin = shutil.which(bin_name)

            if not resolved_bin:
                # Fallback to xdg-open or system default MIME launcher if specific binary is not found
                if shutil.which("xdg-open"):
                    resolved_bin = "xdg-open"
                    exec_args = ["xdg-open", "http://"] if bin_name in ("browser", "web") else ["xdg-open", clean_cmd]
                else:
                    resolved_bin = bin_name
                    exec_args = [resolved_bin] + parts[1:]
            else:
                exec_args = [resolved_bin] + parts[1:]

            # Dispatch launch to user session manager via systemd-run --user --scope under app.slice
            try:
                subprocess.Popen(["systemd-run", "--user", "--scope", "--slice=app.slice", f"--unit={unit_name}"] + exec_args)
                self._logger.info("4-finger tap: Spawned desktop session scope '%s' for '%s'", unit_name, " ".join(exec_args))
            except Exception:
                subprocess.Popen(exec_args)
                self._logger.info("4-finger tap: Executed direct process '%s'", " ".join(exec_args))
        except Exception as error:
            self._logger.error("4-finger tap: Failed to execute process '%s': %s", command, error)

    def handle(self, motion: ProcessedMotion) -> None:
        pass
