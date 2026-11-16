# PyInstaller spec for DefenderBye.
# Build with: .venv\Scripts\pyinstaller build.spec --noconfirm
#
# One-file, windowed (no console), requires Administrator via the embedded
# UAC manifest so the real backend's registry/service writes don't need a
# separate elevation prompt mid-run for most operations (the app also does
# its own is_admin() check + relaunch as a second line of defense).

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["src/defenderbye/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DefenderBye",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    manifest="manifest.xml",
    icon=None,
)
