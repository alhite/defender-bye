"""Snapshot + apply/revert orchestration for the Disable/Restore buttons.

This is deliberately small: there is no "deep remove" mode. Disable means
"turn real-time protection off, persistently, via supported policy keys".
Restore means "put every touched value back exactly as it was".
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from defenderbye.core.backend import Backend
from defenderbye.core.steps import Captured, Step, build_steps


@dataclass
class RunResult:
    changed_steps: list[str]
    log_lines: list[str]


class Snapshot:
    """Captured before-state for a set of steps, serializable to JSON."""

    def __init__(self, captured: dict[str, Captured], created_at: float | None = None) -> None:
        self.captured = captured
        self.created_at = created_at if created_at is not None else time.time()

    def to_json(self) -> str:
        return json.dumps({"created_at": self.created_at, "captured": self.captured}, indent=2)

    @classmethod
    def from_json(cls, text: str) -> Snapshot:
        data: dict[str, Any] = json.loads(text)
        return cls(data["captured"], data.get("created_at"))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Snapshot:
        return cls.from_json(path.read_text(encoding="utf-8"))


def snapshot_path(data_dir: Path) -> Path:
    return data_dir / "snapshot.json"


def disable(
    b: Backend,
    *,
    spynet: bool = True,
    scheduled_scan: bool = True,
    dry_run: bool = False,
    snapshot_dir: Path | None = None,
) -> RunResult:
    """Turn real-time protection off. Captures a snapshot before changing
    anything, unless `dry_run` is set."""
    steps = build_steps(spynet=spynet, scheduled_scan=scheduled_scan)
    log: list[str] = []
    if dry_run:
        for step in steps:
            log.append(f"[dry-run] {step.title}: {step.dry_run(b)}")
        return RunResult([], log)

    captured = {step.id: step.capture(b) for step in steps}
    if snapshot_dir is not None:
        Snapshot(captured).save(snapshot_path(snapshot_dir))

    changed: list[str] = []
    for step in steps:
        if step.apply(b):
            changed.append(step.id)
            log.append(f"Applied: {step.title}")
        else:
            log.append(f"Already set: {step.title}")
    return RunResult(changed, log)


def restore(
    b: Backend,
    *,
    spynet: bool = True,
    scheduled_scan: bool = True,
    dry_run: bool = False,
    snapshot_dir: Path | None = None,
) -> RunResult:
    """Turn real-time protection back on. Prefers the exact values from the
    last snapshot; falls back to stock-Windows defaults if there is none."""
    steps = build_steps(spynet=spynet, scheduled_scan=scheduled_scan)
    log: list[str] = []

    snap: Snapshot | None = None
    if snapshot_dir is not None:
        path = snapshot_path(snapshot_dir)
        if path.exists():
            snap = Snapshot.load(path)

    if dry_run:
        for step in steps:
            log.append(f"[dry-run] revert: {step.title}")
        return RunResult([], log)

    changed: list[str] = []
    for step in steps:
        captured = snap.captured.get(step.id) if snap is not None else None
        if step.revert(b, captured):
            changed.append(step.id)
            log.append(f"Reverted: {step.title}")
        else:
            log.append(f"Already default: {step.title}")
    return RunResult(changed, log)


def steps_for_reference() -> list[Step]:
    """Exposed for the Advanced panel / dry-run preview in the GUI."""
    return build_steps()
