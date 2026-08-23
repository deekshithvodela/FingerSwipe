from __future__ import annotations

from unittest.mock import MagicMock, patch

from fingerswipe.config import TapConfig
from fingerswipe.controllers.tap import TapController


def test_tap_controller_triggers_super_key_via_native() -> None:
    mock_lib = MagicMock()
    mock_lib.fs_uinput_trigger_super_key.return_value = 0

    config = TapConfig(enabled=True, action="super_key")
    controller = TapController(config, mock_lib)

    controller.trigger()

    mock_lib.fs_uinput_trigger_super_key.assert_called_once()


def test_tap_controller_disabled_does_nothing() -> None:
    mock_lib = MagicMock()
    config = TapConfig(enabled=False, action="super_key")
    controller = TapController(config, mock_lib)

    controller.trigger()

    mock_lib.fs_uinput_trigger_super_key.assert_not_called()


@patch("subprocess.Popen")
def test_tap_controller_executes_custom_command(mock_popen: MagicMock) -> None:
    config = TapConfig(enabled=True, action="custom_command", custom_command="rofi -show drun")
    controller = TapController(config)

    controller.trigger()

    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert "rofi" in " ".join(args)


def test_tap_controller_debounces_rapid_triggers() -> None:
    mock_lib = MagicMock()
    mock_lib.fs_uinput_trigger_super_key.return_value = 0

    config = TapConfig(enabled=True, action="super_key")
    controller = TapController(config, mock_lib)

    controller.trigger()
    controller.trigger()

    mock_lib.fs_uinput_trigger_super_key.assert_called_once()
