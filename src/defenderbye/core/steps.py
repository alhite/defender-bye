"""The Step abstraction: the only place where system state is changed.

Each Step is idempotent: `apply()` / `revert()` return False when there is
nothing to do, and can be called any number of times safely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from defenderbye.core import catalog
from defenderbye.core.backend import Backend, RegValue

Captured = dict[str, Any]


class RefusedStepError(ValueError):
    """Raised when a step would touch something on the firewall refuse-list."""


def check_registry_allowed(key: str) -> None:
    low = key.lower()
    if any(frag in low for frag in catalog.FIREWALL_REG_FRAGMENTS):
        raise RefusedStepError(f"Refusing firewall-related registry key: {key}")


def check_service_allowed(name: str) -> None:
    if name.lower() in catalog.FIREWALL_SERVICES:
        raise RefusedStepError(f"Refusing firewall-related service: {name}")


@dataclass(frozen=True)
class Step:
    """Base step. Subclasses implement capture/apply/revert/dry_run."""

    id: str
    title: str
    group: str = "core"  # core | spynet | scan

    def capture(self, b: Backend) -> Captured:
        raise NotImplementedError

    def apply(self, b: Backend) -> bool:
        """Apply the change. Returns True if something actually changed."""
        raise NotImplementedError

    def revert(self, b: Backend, captured: Captured | None) -> bool:
        """Undo. With `captured`, restore the exact previous value; else fall
        back to the stock-Windows default."""
        raise NotImplementedError

    def dry_run(self, b: Backend) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class RegistryValueStep(Step):
    key: str = ""
    name: str = ""
    value: RegValue = field(default_factory=lambda: RegValue("REG_DWORD", 0))
    # Stock Windows value; None means the value does not exist by default
    # (i.e. reverting should delete it, not set it to something else).
    default: RegValue | None = None

    def __post_init__(self) -> None:
        check_registry_allowed(self.key)

    def capture(self, b: Backend) -> Captured:
        cur = b.reg_get(self.key, self.name)
        return {
            "exists": cur is not None,
            "kind": cur.kind if cur else None,
            "data": cur.data if cur else None,
        }

    def apply(self, b: Backend) -> bool:
        if b.reg_get(self.key, self.name) == self.value:
            return False
        b.reg_set(self.key, self.name, self.value)
        return True

    def revert(self, b: Backend, captured: Captured | None) -> bool:
        if captured is not None:
            target = RegValue(captured["kind"], captured["data"]) if captured["exists"] else None
        else:
            target = self.default
        if b.reg_get(self.key, self.name) == target:
            return False
        if target is None:
            b.reg_delete(self.key, self.name)
        else:
            b.reg_set(self.key, self.name, target)
        return True

    def dry_run(self, b: Backend) -> str:
        cur = b.reg_get(self.key, self.name)
        now = cur.data if cur else "<unset>"
        return f"{self.key}\\{self.name}: {now} -> {self.value.data}"


@dataclass(frozen=True)
class ServiceStartStep(Step):
    service: str = ""
    target: int = 4
    default: int = 3

    def __post_init__(self) -> None:
        check_service_allowed(self.service)

    def capture(self, b: Backend) -> Captured:
        return {"start": b.service_get_start(self.service)}

    def apply(self, b: Backend) -> bool:
        cur = b.service_get_start(self.service)
        if cur is None or cur == self.target:
            return False
        b.service_set_start(self.service, self.target)
        return True

    def revert(self, b: Backend, captured: Captured | None) -> bool:
        target = captured["start"] if captured is not None else self.default
        cur = b.service_get_start(self.service)
        if target is None or cur is None or cur == target:
            return False
        b.service_set_start(self.service, target)
        return True

    def dry_run(self, b: Backend) -> str:
        return f"service {self.service}: start {b.service_get_start(self.service)} -> {self.target}"


def _dword(v: int) -> RegValue:
    return RegValue("REG_DWORD", v)


def build_steps(*, spynet: bool = True, scheduled_scan: bool = True) -> list[Step]:
    """Return the ordered, reversible step list for disabling real-time
    protection (the only thing "Disable Defender" means in this app).

    `spynet` also turns off cloud-delivered protection / sample submission so
    the service does not immediately re-report "protection off" telemetry.
    `scheduled_scan` additionally turns off the periodic scheduled scan, which
    is the main source of delayed false-positive popups after a manual
    on/off toggle.
    """
    steps: list[Step] = [
        RegistryValueStep(
            "policy.disable_av",
            "Policy: DisableAntiSpyware = 1",
            "core",
            key=catalog.DEFENDER_POLICY,
            name="DisableAntiSpyware",
            value=_dword(1),
        ),
        RegistryValueStep(
            "policy.rtp.disable",
            "Policy: DisableRealtimeMonitoring = 1",
            "core",
            key=catalog.RTP_POLICY,
            name="DisableRealtimeMonitoring",
            value=_dword(1),
        ),
        RegistryValueStep(
            "policy.rtp.behavior",
            "Policy: DisableBehaviorMonitoring = 1",
            "core",
            key=catalog.RTP_POLICY,
            name="DisableBehaviorMonitoring",
            value=_dword(1),
        ),
        RegistryValueStep(
            "policy.rtp.onaccess",
            "Policy: DisableOnAccessProtection = 1",
            "core",
            key=catalog.RTP_POLICY,
            name="DisableOnAccessProtection",
            value=_dword(1),
        ),
        RegistryValueStep(
            "policy.rtp.ioav",
            "Policy: DisableIOAVProtection = 1",
            "core",
            key=catalog.RTP_POLICY,
            name="DisableIOAVProtection",
            value=_dword(1),
        ),
        ServiceStartStep(
            "svc.windefend",
            "Service WinDefend: start type -> Disabled",
            "core",
            service="WinDefend",
            target=4,
            default=catalog.DEFAULT_SERVICE_START["WinDefend"],
        ),
    ]
    if spynet:
        steps.append(
            RegistryValueStep(
                "policy.spynet.reporting",
                "Policy: cloud-delivered protection off",
                "spynet",
                key=catalog.SPYNET_POLICY,
                name="SpynetReporting",
                value=_dword(0),
            )
        )
        steps.append(
            RegistryValueStep(
                "policy.spynet.samples",
                "Policy: never send sample submissions",
                "spynet",
                key=catalog.SPYNET_POLICY,
                name="SubmitSamplesConsent",
                value=_dword(2),
            )
        )
    if scheduled_scan:
        steps.append(
            RegistryValueStep(
                "policy.scan.disable_scheduled",
                "Policy: disable scheduled scanning",
                "scan",
                key=catalog.SCAN_POLICY,
                name="DisableScheduledScan",
                value=_dword(1),
            )
        )
    return steps
