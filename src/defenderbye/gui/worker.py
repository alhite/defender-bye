"""Background worker so the UI thread never blocks on registry/sc calls."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, Signal

from defenderbye.core.backend import Backend
from defenderbye.core.toggle import RunResult


class ToggleWorker(QObject):
    finished = Signal(object)  # RunResult
    failed = Signal(str)

    def __init__(self, action: Callable[[Backend], RunResult], backend: Backend) -> None:
        super().__init__()
        self._action = action
        self._backend = backend

    def run(self) -> None:
        try:
            result = self._action(self._backend)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


def run_in_thread(
    action: Callable[[Backend], RunResult],
    backend: Backend,
    on_done: Callable[[RunResult], None],
    on_error: Callable[[str], None],
) -> tuple[QThread, ToggleWorker]:
    """Caller must keep both returned objects alive until `finished`/`failed` fires."""
    thread = QThread()
    worker = ToggleWorker(action, backend)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(on_done)
    worker.failed.connect(on_error)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.start()
    return thread, worker
