"""Every Step: apply changes state, revert restores it, apply twice is a no-op."""

from __future__ import annotations

from defenderbye.core.backend import FakeBackend, RegValue
from defenderbye.core.steps import RegistryValueStep, ServiceStartStep, build_steps


def test_registry_step_apply_revert_roundtrip() -> None:
    b = FakeBackend.windows_default()
    step = RegistryValueStep(
        "t", "t", key=r"HKLM\SOFTWARE\Policies\Microsoft\Windows Defender",
        name="DisableAntiSpyware", value=RegValue("REG_DWORD", 1),
    )

    assert step.apply(b) is True
    assert b.reg_get(step.key, step.name) == RegValue("REG_DWORD", 1)

    # Idempotent: applying again changes nothing.
    assert step.apply(b) is False

    captured = {"exists": False, "kind": None, "data": None}
    assert step.revert(b, captured) is True
    assert b.reg_get(step.key, step.name) is None
    assert step.revert(b, captured) is False


def test_registry_step_revert_without_snapshot_uses_default() -> None:
    b = FakeBackend.windows_default()
    step = RegistryValueStep(
        "t", "t", key=r"HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet",
        name="SubmitSamplesConsent", value=RegValue("REG_DWORD", 2),
        default=RegValue("REG_DWORD", 1),
    )
    step.apply(b)
    assert step.revert(b, None) is True
    assert b.reg_get(step.key, step.name) == RegValue("REG_DWORD", 1)


def test_service_step_apply_revert_roundtrip() -> None:
    b = FakeBackend.windows_default()
    step = ServiceStartStep("t", "t", service="WinDefend", target=4, default=2)

    assert step.apply(b) is True
    assert b.service_get_start("WinDefend") == 4
    assert step.apply(b) is False

    captured = {"start": 2}
    assert step.revert(b, captured) is True
    assert b.service_get_start("WinDefend") == 2
    assert step.revert(b, captured) is False


def test_build_steps_is_ordered_and_non_empty() -> None:
    steps = build_steps()
    assert len(steps) >= 6
    assert len({s.id for s in steps}) == len(steps)  # unique ids
