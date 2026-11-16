"""The firewall refuse-list must never be violated, now or in the future."""

from __future__ import annotations

import pytest

from defenderbye.core.backend import RegValue
from defenderbye.core.steps import (
    RefusedStepError,
    RegistryValueStep,
    ServiceStartStep,
    build_steps,
)


def test_build_steps_never_touches_firewall() -> None:
    for step in build_steps(spynet=True, scheduled_scan=True):
        if isinstance(step, RegistryValueStep):
            low = step.key.lower()
            assert "firewall" not in low
            assert "sharedaccess" not in low
            assert "mpssvc" not in low
            assert r"\bfe" not in low
        if isinstance(step, ServiceStartStep):
            assert step.service.lower() not in {"mpssvc", "bfe", "sharedaccess"}


@pytest.mark.parametrize("service", ["mpssvc", "MpsSvc", "bfe", "BFE", "SharedAccess"])
def test_cannot_construct_a_firewall_service_step(service: str) -> None:
    with pytest.raises(RefusedStepError):
        ServiceStartStep("x", "x", service=service, target=4)


@pytest.mark.parametrize(
    "key",
    [
        r"HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall",
        r"HKLM\SYSTEM\CurrentControlSet\Services\mpssvc\Parameters",
        r"HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess",
        r"HKLM\SYSTEM\CurrentControlSet\Services\BFE",
    ],
)
def test_cannot_construct_a_firewall_registry_step(key: str) -> None:
    with pytest.raises(RefusedStepError):
        RegistryValueStep("x", "x", key=key, name="Anything", value=RegValue("REG_DWORD", 1))
