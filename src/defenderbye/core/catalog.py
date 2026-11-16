"""Catalog of every registry value / service DefenderBye is allowed to touch.

PROPOSED for review. Sources (to expand in docs/RESEARCH.md):
- Microsoft Learn: "Configure Microsoft Defender Antivirus with Group Policy" /
  "Prevent or allow users to locally modify Microsoft Defender Antivirus
  settings" (DisableAntiSpyware / DisableRealtimeMonitoring policy keys).
- `Set-MpPreference` docs (Defender PowerShell module) for the session-level
  equivalent used as a best-effort, non-persistent companion call.

Only officially documented, supported keys are listed here. Nothing related
to Tamper Protection bypass, driver/service deletion, or Appx removal is in
scope for the toggle-only build.
"""

from __future__ import annotations

DEFENDER_POLICY = r"HKLM\SOFTWARE\Policies\Microsoft\Windows Defender"
RTP_POLICY = DEFENDER_POLICY + r"\Real-Time Protection"
SPYNET_POLICY = DEFENDER_POLICY + r"\Spynet"
SCAN_POLICY = DEFENDER_POLICY + r"\Scan"

# Service/driver name -> stock Windows start type.
# 2 = automatic, 3 = manual/demand, 4 = disabled.
DEFAULT_SERVICE_START: dict[str, int] = {
    "WinDefend": 2,
    "WdNisSvc": 3,
}

# Hard refuse-list: nothing here may ever be referenced by a Step.
# Enforced both at Step construction time and by tests/test_refuse_list.py.
FIREWALL_SERVICES = frozenset({"mpssvc", "bfe", "sharedaccess"})
FIREWALL_REG_FRAGMENTS = (
    "windowsfirewall",
    "sharedaccess",
    r"\mpssvc",
    r"\bfe",
)
