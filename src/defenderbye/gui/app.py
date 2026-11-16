"""GUI entry point: elevation check, backend selection, main window."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from defenderbye import elevate
from defenderbye.core.factory import get_backend
from defenderbye.core.log import data_dir, setup_logging
from defenderbye.gui.main_window import MainWindow


def main() -> int:
    fake = os.environ.get("DEFENDERBYE_FAKE") == "1"

    if not fake and sys.platform == "win32" and not elevate.is_admin():
        app = QApplication(sys.argv)
        choice = QMessageBox.question(
            None,
            "Administrator rights required",
            "DefenderBye needs to run as Administrator to change Defender "
            "settings. Relaunch with elevated permissions now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if choice == QMessageBox.StandardButton.Yes:
            elevate.relaunch_as_admin()
        return 1

    setup_logging(log_dir=data_dir() / "logs")

    app = QApplication(sys.argv)
    window = MainWindow(get_backend())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
