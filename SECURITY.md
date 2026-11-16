# Security Policy

DefenderBye changes security-relevant Windows settings by design (that's the
whole point of the app), so please read this before reporting.

## Reporting a vulnerability

If you find a bug that lets DefenderBye change *more* than it documents
(e.g. touching the firewall, bypassing Tamper Protection, or writing outside
the registry/service keys listed in `src/defenderbye/core/catalog.py`),
please open a private report via GitHub's "Report a vulnerability" button on
the Security tab, or open an issue if you're not comfortable with that.

Include:
- Windows version/build.
- Steps to reproduce.
- The relevant lines from `%ProgramData%\DefenderBye\logs\defenderbye.log`.

## Not a vulnerability

- Antivirus engines flagging `DefenderBye.exe` — expected, see the README FAQ.
- Windows Update or Tamper Protection reverting a change — expected and
  documented; the app detects and reports this, it does not fight it.

## Scope

In scope: the `defenderbye` Python package and its release artifacts built
by this repository's CI. Out of scope: Microsoft Defender itself, Windows,
or third-party forks.
