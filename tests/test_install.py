from pathlib import Path

from fingerswipe.installer import install_system_integration


def test_system_integration_installs_at_service_paths(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1]
    install_system_integration(source, tmp_path)
    service = tmp_path / "lib/systemd/user/fingerswipe.service"
    assert service.is_file()
    assert "ExecStart=/opt/fingerswipe/bin/fingerswipe" in service.read_text(encoding="utf-8")
    assert (tmp_path / "lib/udev/rules.d/99-fingerswipe.rules").is_file()
    assert (tmp_path / "share/doc/fingerswipe/config.yaml").is_file()
