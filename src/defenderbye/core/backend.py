"""System access interface, plus an in-memory fake used for dev and tests.

The real Windows backend (Phase 3) implements the same `Backend` protocol
using `winreg` for registry access and `sc`/PowerShell for services, so the
rest of the app never talks to the OS directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RegValue:
    """A registry value. `kind` is e.g. "REG_DWORD" or "REG_SZ"."""

    kind: str
    data: int | str


class Backend(Protocol):
    """Everything a Step needs from the OS."""

    def reg_get(self, key: str, name: str) -> RegValue | None: ...
    def reg_set(self, key: str, name: str, value: RegValue) -> None: ...
    def reg_delete(self, key: str, name: str) -> None: ...
    def service_get_start(self, name: str) -> int | None: ...
    def service_set_start(self, name: str, start: int) -> None: ...


class FakeBackend:
    """In-memory system used for tests and GUI development (DEFENDERBYE_FAKE=1).

    Every mutation is recorded in `calls` so tests can assert exactly what
    would have happened on a real machine.
    """

    def __init__(self) -> None:
        self.registry: dict[tuple[str, str], RegValue] = {}
        self.services: dict[str, int] = {}
        self.calls: list[tuple[str, ...]] = []

    @classmethod
    def windows_default(cls) -> FakeBackend:
        """A fake machine with Defender fully enabled (stock Windows)."""
        from defenderbye.core.catalog import DEFAULT_SERVICE_START

        fake = cls()
        fake.services.update(DEFAULT_SERVICE_START)
        # Firewall services exist too, so tests can prove they are never touched.
        fake.services.update({"mpssvc": 2, "bfe": 2})
        return fake

    def reg_get(self, key: str, name: str) -> RegValue | None:
        return self.registry.get((key.lower(), name.lower()))

    def reg_set(self, key: str, name: str, value: RegValue) -> None:
        self.calls.append(("reg_set", key, name))
        self.registry[(key.lower(), name.lower())] = value

    def reg_delete(self, key: str, name: str) -> None:
        self.calls.append(("reg_delete", key, name))
        self.registry.pop((key.lower(), name.lower()), None)

    def service_get_start(self, name: str) -> int | None:
        return self.services.get(name)

    def service_set_start(self, name: str, start: int) -> None:
        self.calls.append(("service_set_start", name))
        if name not in self.services:
            raise KeyError(name)
        self.services[name] = start
