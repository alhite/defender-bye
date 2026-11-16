"""Pick the fake or real backend. The only place that branches on the env var."""

from __future__ import annotations

import os

from defenderbye.core.backend import Backend, FakeBackend


def get_backend() -> Backend:
    if os.environ.get("DEFENDERBYE_FAKE") == "1":
        return FakeBackend.windows_default()
    from defenderbye.core.real_backend import RealBackend

    return RealBackend()
