# Contributing to DefenderBye

Issues and PRs are welcome.

## Reporting a bug

Please include:
- Windows version/build (`winver`).
- What you clicked and what you expected vs. what happened.
- Relevant lines from `%ProgramData%\DefenderBye\logs\defenderbye.log`
  (do not paste the whole file if it's long — the last run is enough).

## Development setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m mypy
.\.venv\Scripts\python -m pytest -q
```

Develop the GUI against the in-memory fake backend, which never touches your
real system:

```powershell
$env:DEFENDERBYE_FAKE = "1"
.\.venv\Scripts\python -m defenderbye
```

## Rules for changes to `core/`

- Anything that changes system state goes through the `Step` abstraction in
  `src/defenderbye/core/steps.py` — no ad-hoc `winreg`/`subprocess` calls
  elsewhere.
- Every new `Step` needs a unit test covering apply → revert → apply-twice
  (idempotency), using `FakeBackend`.
- The Windows Firewall refuse-list (`tests/test_refuse_list.py`) must keep
  passing. If your change needs to touch anything firewall-related, it does
  not belong in this project.
- No new dependency without discussing it in an issue first — this ships as
  a one-file executable, so every dependency adds to that size.

## Code style

- Type hints everywhere in `core/`; `mypy --strict` must pass.
- `ruff check .` must pass.
- Keep functions small; prefer clarity over cleverness.
