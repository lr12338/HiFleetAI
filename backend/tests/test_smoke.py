from __future__ import annotations

from pathlib import Path

import backend.app as backend_app


def test_pytest_environment_is_isolated(test_environment_name: str) -> None:
    assert test_environment_name == "test"


def test_temp_workspace_fixture_creates_directory(temp_workspace: Path) -> None:
    assert temp_workspace.exists()
    assert temp_workspace.is_dir()


def test_backend_package_imports() -> None:
    assert backend_app.APP_PACKAGE_NAME == "hifleetai-backend"
