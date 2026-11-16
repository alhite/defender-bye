"""End-to-end: disable -> state reflects it; restore -> back to Protected."""

from __future__ import annotations

from pathlib import Path

from defenderbye.core import toggle
from defenderbye.core.backend import FakeBackend
from defenderbye.core.detect import ProtectionState, current_state


def test_disable_then_restore_roundtrip(tmp_path: Path) -> None:
    b = FakeBackend.windows_default()
    assert current_state(b) == ProtectionState.PROTECTED

    result = toggle.disable(b, snapshot_dir=tmp_path)
    assert result.changed_steps
    assert current_state(b) == ProtectionState.DISABLED

    result2 = toggle.restore(b, snapshot_dir=tmp_path)
    assert result2.changed_steps
    assert current_state(b) == ProtectionState.PROTECTED


def test_restore_without_snapshot_falls_back_to_defaults(tmp_path: Path) -> None:
    b = FakeBackend.windows_default()
    toggle.disable(b, snapshot_dir=None)
    assert current_state(b) == ProtectionState.DISABLED

    toggle.restore(b, snapshot_dir=tmp_path / "missing")
    assert current_state(b) == ProtectionState.PROTECTED


def test_dry_run_changes_nothing() -> None:
    b = FakeBackend.windows_default()
    result = toggle.disable(b, dry_run=True)
    assert result.changed_steps == []
    assert current_state(b) == ProtectionState.PROTECTED
    assert any("dry-run" in line for line in result.log_lines)


def test_disable_twice_is_idempotent(tmp_path: Path) -> None:
    b = FakeBackend.windows_default()
    toggle.disable(b, snapshot_dir=tmp_path)
    result = toggle.disable(b, snapshot_dir=tmp_path)
    assert result.changed_steps == []
