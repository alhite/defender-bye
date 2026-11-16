"""DefenderBye: a simple, reversible toggle for Windows Defender real-time protection.

Scope:
- Disable / re-enable real-time protection, cloud-delivered protection and
  scheduled scanning through officially supported mechanisms (Group-Policy-style
  registry keys under HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender, the
  same keys enterprise GPO/Intune use, plus Set-MpPreference).
- No uninstall / deep-remove, no touching the Security Center app, no DISM,
  no VBS/HVCI changes, no Appx removal.
- The Windows Firewall is never touched, enforced by an explicit refuse-list
  plus a unit test.
- No Tamper Protection bypass: if Tamper Protection is on, the app only
  explains how to turn it off manually.
"""

__version__ = "0.1.0.dev0"
