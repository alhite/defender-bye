"""Entry point: launches the GUI (default) or a fake-backend CLI smoke test."""

from __future__ import annotations

import os
import sys


def main() -> int:
    if os.environ.get("DEFENDERBYE_CLI") == "1":
        return _cli_smoke_test()
    from defenderbye.gui.app import main as gui_main

    return gui_main()


def _cli_smoke_test() -> int:
    from defenderbye.core import toggle
    from defenderbye.core.backend import FakeBackend
    from defenderbye.core.detect import current_state

    if os.environ.get("DEFENDERBYE_FAKE") != "1":
        print("Set DEFENDERBYE_FAKE=1 together with DEFENDERBYE_CLI=1.", file=sys.stderr)
        return 1

    backend = FakeBackend.windows_default()
    print("State before:", current_state(backend).value)
    result = toggle.disable(backend)
    for line in result.log_lines:
        print(line)
    print("State after disable:", current_state(backend).value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
