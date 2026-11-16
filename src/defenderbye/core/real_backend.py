"""Real Windows backend: winreg for registry, `sc.exe` for service start type.

Implements the same `Backend` protocol as `FakeBackend` so `core/steps.py`
and `core/toggle.py` never need to know which one they're talking to.
Requires Administrator privileges for HKLM writes and for `sc config`.
"""

from __future__ import annotations

import subprocess
import sys

from defenderbye.core.backend import RegValue

_HIVES = {
    "HKLM": "HKEY_LOCAL_MACHINE",
    "HKCU": "HKEY_CURRENT_USER",
}

# Service start type name <-> `sc` keyword, used for both read and write.
_SC_START_TO_INT = {"boot": 0, "system": 1, "auto": 2, "demand": 3, "disabled": 4}
_INT_TO_SC_START = {v: k for k, v in _SC_START_TO_INT.items()}


def _split_key(key: str) -> tuple[int, str]:
    """`HKLM\\SOFTWARE\\...` -> (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\...")."""
    import winreg

    hive_name, _, rest = key.partition("\\")
    hive_name = _HIVES.get(hive_name.upper(), hive_name.upper())
    hive = getattr(winreg, hive_name)
    return hive, rest


class RealBackend:
    """Talks to the actual OS. No-op / raises clearly if not elevated."""

    def reg_get(self, key: str, name: str) -> RegValue | None:
        import winreg

        hive, subkey = _split_key(key)
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as hk:
                data, reg_type = winreg.QueryValueEx(hk, name)
        except FileNotFoundError:
            return None
        kind = {winreg.REG_DWORD: "REG_DWORD", winreg.REG_SZ: "REG_SZ"}.get(
            reg_type, str(reg_type)
        )
        return RegValue(kind, data)

    def reg_set(self, key: str, name: str, value: RegValue) -> None:
        import winreg

        hive, subkey = _split_key(key)
        reg_type = winreg.REG_DWORD if value.kind == "REG_DWORD" else winreg.REG_SZ
        with winreg.CreateKeyEx(hive, subkey, 0, winreg.KEY_WRITE) as hk:
            winreg.SetValueEx(hk, name, 0, reg_type, value.data)

    def reg_delete(self, key: str, name: str) -> None:
        import winreg

        hive, subkey = _split_key(key)
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_WRITE) as hk:
                winreg.DeleteValue(hk, name)
        except FileNotFoundError:
            pass

    def service_get_start(self, name: str) -> int | None:
        proc = self._run(["sc", "qc", name])
        if proc.returncode != 0:
            return None
        for line in proc.stdout.splitlines():
            if "START_TYPE" in line.upper():
                low = line.lower()
                for word, val in _SC_START_TO_INT.items():
                    if word.upper() in line.upper() or word in low:
                        return val
        return None

    def service_set_start(self, name: str, start: int) -> None:
        keyword = _INT_TO_SC_START.get(start)
        if keyword is None:
            raise ValueError(f"Unsupported start type: {start}")
        proc = self._run(["sc", "config", name, "start=", keyword])
        if proc.returncode != 0:
            raise RuntimeError(
                f"sc config {name} start= {keyword} failed (exit {proc.returncode}): "
                f"{proc.stdout}{proc.stderr}"
            )

    @staticmethod
    def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
        creationflags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=creationflags,
            check=False,
        )

    def tamper_protection(self) -> bool | None:
        """Best-effort read via PowerShell `Get-MpComputerStatus`.

        Returns None (unknown) rather than guessing when the cmdlet is
        unavailable (e.g. Defender itself already removed/disabled enough
        that the module fails to load).
        """
        proc = self._run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "(Get-MpComputerStatus).IsTamperProtected",
            ]
        )
        if proc.returncode != 0:
            return None
        out = proc.stdout.strip().lower()
        if out == "true":
            return True
        if out == "false":
            return False
        return None
