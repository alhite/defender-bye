"""Administrator check and UAC relaunch. No logic lives here beyond that."""

from __future__ import annotations

import sys


def is_admin() -> bool:
    if sys.platform != "win32":
        return False
    import ctypes

    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except Exception:
        return False


def relaunch_as_admin() -> None:
    """Re-run the current executable elevated via UAC, then exit this process."""
    import ctypes

    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
        None, "runas", sys.executable, params, None, 1
    )
    raise SystemExit(0)
