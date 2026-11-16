# DefenderBye — Defender Remover & Restore GUI for Windows 10/11

> Say bye to Microsoft Defender — and bring it back anytime.

[![Release](https://img.shields.io/github/v/release/alhite/defender-bye)](https://github.com/alhite/defender-bye/releases/latest)
[![CI](https://github.com/alhite/defender-bye/actions/workflows/ci.yml/badge.svg)](https://github.com/alhite/defender-bye/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**DefenderBye** is a small, open-source Windows app with one job: turn Microsoft
Defender's real-time protection **off** and **back on** with a single click,
in a way that actually sticks (no fighting with it re-enabling itself a minute
later) and is always reversible.

Website: **https://alhite.github.io/defender-bye/** (English / Russian)

## Why this exists

Manually flipping the real-time-protection switch in Windows Security often
gets silently reverted, or leaves scheduled scans and cloud reporting still
running — which then throws delayed false-positive popups. DefenderBye
changes the same supported policy keys enterprise Group Policy / Intune use,
all of it, in the right order, and remembers exactly what it changed so it
can be undone precisely.

## What it does

- **Disable Defender** — turns off real-time monitoring, behavior/on-access/
  IOAV protection, cloud-delivered protection & sample submission, and
  scheduled scanning. Takes a snapshot of every value first.
- **Restore Defender** — replays that snapshot in reverse, or falls back to
  stock-Windows defaults if no snapshot exists.
- **Dry run** — preview exactly what would change, with no writes.
- Clear status card (Protected / Disabled / Partially disabled), a live log,
  and a reboot reminder when needed.

## What it does NOT do

- No uninstall / deep-remove of Microsoft Defender or the Security app.
- **Never touches the Windows Firewall** — enforced by an explicit
  refuse-list plus a unit test that fails the build if that is ever violated.
- No Tamper Protection bypass. If Tamper Protection is on, DefenderBye shows
  you how to turn it off yourself and stops there.
- No network calls, no telemetry, no auto-update that downloads executables,
  no persistence/startup entries, no obfuscation. It does exactly what it
  says and nothing else.

## Download

Grab the latest `DefenderBye.exe` from the
[Releases page](https://github.com/alhite/defender-bye/releases/latest), or
use the download button on the [website](https://alhite.github.io/defender-bye/).

Each release ships a `SHA256SUMS.txt` so you can verify the exe you downloaded
matches what CI built. **Antivirus false positives are expected** for a tool
that flips Defender's own switches — see the FAQ below.

## Quick start

1. Download `DefenderBye.exe`.
2. Run it — it will ask to relaunch as Administrator (required to change
   system settings).
3. Click **Disable Defender** or **Restore Defender**. Reboot if asked.

## How it works

1. Checks you're running as Administrator and reads the current state.
2. Warns if Tamper Protection is on (and stops — see above).
3. On Disable: saves a JSON snapshot of every value it's about to touch to
   `%ProgramData%\DefenderBye\snapshot.json`, then applies each change
   through a small, auditable `Step` abstraction (see
   `src/defenderbye/core/steps.py`).
4. On Restore: replays that snapshot in reverse (or Windows defaults if
   there's no snapshot).

## Safety

- Every change is captured before it's made and can be undone exactly.
- The Windows Firewall is on a hard refuse-list (code + test, see
  `tests/test_refuse_list.py`).
- Tamper Protection is only ever detected, never bypassed.
- Windows Update or Tamper Protection can re-enable Defender behind your
  back — DefenderBye detects this on next launch and shows it honestly in
  the status card, rather than pretending everything is still disabled.

## FAQ / Troubleshooting

**My antivirus flags DefenderBye.exe.** Expected — any tool that can switch
off Defender's own protections looks like something an antivirus should flag.
Verify the SHA-256 against `SHA256SUMS.txt` on the release, or build from
source yourself (below).

**I clicked Disable, but Defender turned itself back on.** Check Tamper
Protection (Windows Security → Virus & threat protection → Manage settings)
and recent Windows Updates — both can revert policy changes. DefenderBye will
show "Partially disabled" / "Protected" instead of pretending it's still off.

**Will this touch my firewall?** No, never — see Safety above.

## Build from source

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m PyInstaller build.spec --noconfirm
# -> dist\DefenderBye.exe
```

Run the GUI against an in-memory fake system (no real changes) during
development:

```powershell
$env:DEFENDERBYE_FAKE = "1"
.\.venv\Scripts\python -m defenderbye
```

## Contributing

Issues and PRs welcome — please include your Windows build and, for bugs, a
copy of the log (`%ProgramData%\DefenderBye\logs\`). See `CONTRIBUTING.md`.

## Disclaimer

Use at your own risk. Disabling your antivirus removes a layer of protection
against malware — you are responsible for your own security while it's off.
This project is not affiliated with or endorsed by Microsoft. Microsoft and
Windows are trademarks of Microsoft Corporation.

## License

MIT — see [LICENSE](LICENSE).
