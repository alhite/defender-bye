"""Single-screen main window: status card, two big buttons, log pane."""

from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from defenderbye import __version__
from defenderbye.core import toggle
from defenderbye.core.backend import Backend
from defenderbye.core.detect import ProtectionState, current_state, tamper_protection_on
from defenderbye.core.log import data_dir
from defenderbye.core.toggle import RunResult
from defenderbye.gui.worker import ToggleWorker, run_in_thread

_STATE_TEXT = {
    ProtectionState.PROTECTED: ("Protected", "Microsoft Defender real-time protection is on."),
    ProtectionState.DISABLED: ("Disabled", "Real-time protection is off (DefenderBye)."),
    ProtectionState.PARTIAL: (
        "Partially disabled",
        "Some but not all protection settings are off.",
    ),
}


class MainWindow(QMainWindow):
    def __init__(self, backend: Backend) -> None:
        super().__init__()
        self._backend = backend
        self._thread: QThread | None = None
        self._worker: ToggleWorker | None = None

        self.setWindowTitle("DefenderBye")
        self.resize(720, 520)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.status_sub_label = QLabel()
        self.status_sub_label.setWordWrap(True)
        root.addWidget(self.status_label)
        root.addWidget(self.status_sub_label)

        self.tamper_label = QLabel()
        self.tamper_label.setWordWrap(True)
        self.tamper_label.setStyleSheet("color: #c77;")
        self.tamper_label.hide()
        root.addWidget(self.tamper_label)

        buttons = QHBoxLayout()
        self.disable_btn = QPushButton("Remove / Disable Defender")
        self.disable_btn.setStyleSheet(
            "QPushButton { background:#8b2c2c; color:white; padding:14px; "
            "font-size:15px; border-radius:8px; }"
        )
        self.restore_btn = QPushButton("Restore Defender")
        self.restore_btn.setStyleSheet(
            "QPushButton { background:#2c7a4b; color:white; padding:14px; "
            "font-size:15px; border-radius:8px; }"
        )
        self.disable_btn.clicked.connect(self._on_disable_clicked)
        self.restore_btn.clicked.connect(self._on_restore_clicked)
        buttons.addWidget(self.disable_btn)
        buttons.addWidget(self.restore_btn)
        root.addLayout(buttons)

        self.dry_run_checkbox = QCheckBox("Dry run (show what would change, apply nothing)")
        root.addWidget(self.dry_run_checkbox)

        root.addWidget(QLabel("Log:"))
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: Consolas, monospace;")
        root.addWidget(self.log, stretch=1)

        footer = QLabel(f"DefenderBye v{__version__} — not affiliated with Microsoft")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer.setStyleSheet("color: gray;")
        root.addWidget(footer)

        self.refresh_status()

    # -- status ---------------------------------------------------------
    def refresh_status(self) -> None:
        state = current_state(self._backend)
        title, sub = _STATE_TEXT[state]
        self.status_label.setText(f"Status: {title}")
        self.status_sub_label.setText(sub)
        self.disable_btn.setEnabled(state != ProtectionState.DISABLED)
        self.restore_btn.setEnabled(state != ProtectionState.PROTECTED)

        tamper = tamper_protection_on(self._backend)
        if tamper:
            self.tamper_label.setText(
                "Tamper Protection is ON. Turn it off manually first: "
                "Windows Security → Virus & threat protection → Manage settings "
                "→ Tamper Protection → Off. DefenderBye will not try to bypass it."
            )
            self.tamper_label.show()
        else:
            self.tamper_label.hide()

    # -- actions ----------------------------------------------------------
    def _on_disable_clicked(self) -> None:
        if not self.dry_run_checkbox.isChecked():
            confirmed = QMessageBox.question(
                self,
                "Disable Defender?",
                "This will turn off Microsoft Defender real-time protection.\n\n"
                "Your PC will have no built-in antivirus until you click "
                '"Restore Defender". A reboot may be required for all changes '
                "to take effect.\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirmed != QMessageBox.StandardButton.Yes:
                return
        self._run(toggle.disable)

    def _on_restore_clicked(self) -> None:
        self._run(toggle.restore)

    def _run(self, action: object) -> None:
        dry_run = self.dry_run_checkbox.isChecked()
        bound = partial(  # type: ignore[operator]
            action, spynet=True, scheduled_scan=True, dry_run=dry_run, snapshot_dir=data_dir()
        )
        self.disable_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self._thread, self._worker = run_in_thread(
            bound, self._backend, self._on_run_done, self._on_run_error
        )

    def _on_run_done(self, result: RunResult) -> None:
        self.log.appendPlainText("\n".join(result.log_lines))
        self.refresh_status()
        if result.changed_steps:
            QMessageBox.information(
                self,
                "Done",
                "Done. A reboot is recommended for every change to fully apply.",
            )

    def _on_run_error(self, message: str) -> None:
        self.log.appendPlainText(f"ERROR: {message}")
        self.refresh_status()
        QMessageBox.critical(self, "Something went wrong", message)
