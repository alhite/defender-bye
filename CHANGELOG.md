# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-11-17

### Added
- Core `Step` abstraction (`core/steps.py`) with registry-value and
  service-start-type steps, idempotent apply/revert.
- `FakeBackend` (in-memory) and `RealBackend` (`winreg` + `sc.exe` +
  `Get-MpComputerStatus`) implementing the same `Backend` protocol.
- Disable/Restore flow with JSON snapshot (`core/toggle.py`) and dry-run.
- Read-only state detection (Protected / Disabled / Partially disabled) and
  Tamper Protection detection (`core/detect.py`).
- Hard refuse-list preventing any step from ever touching the Windows
  Firewall, enforced by `tests/test_refuse_list.py`.
- PySide6 GUI: status card, Disable/Restore buttons, dry-run checkbox, live
  log, confirmation dialog, admin-elevation flow.
- PyInstaller one-file build producing `DefenderBye.exe` with a
  `requireAdministrator` manifest.
- Bilingual (EN/RU) GitHub Pages site under `docs/`.
- CI (lint + type-check + test) and Pages deployment workflows.

### Known limitations
- Default values for some service start types in
  `src/defenderbye/core/catalog.py` are marked for verification on a clean
  Windows 10/11 VM.
- No deep-remove / uninstall mode, no VBS/HVCI toggle, no Security-app
  (SecHealthUI) removal — out of scope for this release by design.
