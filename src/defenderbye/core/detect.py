"""Read-only detection of the current protection state.

No write access here on purpose: this module only answers "what is the state
right now", used by the status card and by the "Defender re-enabled itself"
notice (Windows Update / Tamper Protection can silently revert policy keys).
"""

from __future__ import annotations

from enum import StrEnum

from defenderbye.core import catalog
from defenderbye.core.backend import Backend


class ProtectionState(StrEnum):
    PROTECTED = "protected"
    DISABLED = "disabled"
    PARTIAL = "partial"


def current_state(b: Backend) -> ProtectionState:
    """Best-effort state derived from the two keys that matter most."""
    rtp_off = b.reg_get(catalog.RTP_POLICY, "DisableRealtimeMonitoring")
    av_off = b.reg_get(catalog.DEFENDER_POLICY, "DisableAntiSpyware")
    svc_start = b.service_get_start("WinDefend")

    rtp_disabled = bool(rtp_off and rtp_off.data == 1)
    av_disabled = bool(av_off and av_off.data == 1)
    svc_disabled = svc_start == 4

    disabled_signals = sum([rtp_disabled, av_disabled, svc_disabled])
    if disabled_signals == 3:
        return ProtectionState.DISABLED
    if disabled_signals == 0:
        return ProtectionState.PROTECTED
    return ProtectionState.PARTIAL


def tamper_protection_on(b: Backend) -> bool | None:
    """Tamper Protection state, where detectable.

    The real backend reads it via PowerShell `Get-MpComputerStatus`
    (`IsTamperProtected`) as the authoritative source, since the underlying
    registry value is an OS-managed binary blob, not a plain flag. Returns
    None when it cannot be determined (e.g. the fake backend, or the cmdlet
    is unavailable).
    """
    probe = getattr(b, "tamper_protection", None)
    if not callable(probe):
        return None
    result = probe()
    return result if isinstance(result, bool) else None
