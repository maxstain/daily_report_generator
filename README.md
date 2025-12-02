Daily Report Generator
======================

A small Flask web app to assemble a daily report from:
- Bench bookings (time on benches/locations)
- Planned and executed test executions
- Blockers/issues encountered

The app validates input (pluggable backends), generates a text report, and displays it as HTML with options to download or copy for email.

Project structure
-----------------

```
.
├─ app.py                      # Flask app and routes
├─ Functions/
│  ├─ __init__.py             # Report generator and helpers
│  ├─ validation.py           # Pure-Python validation (default/fallback)
│  ├─ pydantic_validation.py  # Optional Pydantic backend
│  └─ jsonschema_validation.py# Optional JSON Schema backend
├─ templates/
│  ├─ base.html
│  ├─ home.html               # Dynamic form page
│  └─ report.html             # Rendered report page
├─ static/
│  ├─ style.css
│  └─ js/form_helpers.js
├─ tests/
│  ├─ test_validation.py
│  └─ test_playwright_ui.py
└─ requirements.txt
```

Quick start
-----------

1) Setup environment (PowerShell on Windows):

```
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Choose validation backend (optional). Set `VALIDATOR_BACKEND` to one of:
- `auto` (default): try Pydantic, then jsonschema, else pure Python
- `pydantic`: require the Pydantic backend (must be installed)
- `jsonschema`: require the JSON Schema backend (must be installed)
- `pure`: force the pure-Python backend

Session-only (PowerShell):

```
$env:VALIDATOR_BACKEND = 'auto'   # or 'pure', 'pydantic', 'jsonschema'
```

3) Run the app:

```
python app.py
```

Open http://127.0.0.1:5000/ in your browser.

Note: The server sets the report date to today, regardless of the value in the form.

Using the app
-------------
- Bench bookings: Add rows with remote/location and optional start/end times (HH:MM).
- Planned executions: Add rows with an `id`, optional `summary`, and optional per-line test IDs.
- Blockers: Enter one issue per line.
- Click “Generate Report” to view the formatted result; download as `.txt` or `.html`, or copy email HTML.

Validation rules (summary)
--------------------------
- Bookings (list of objects): must include at least one of `remote` or `location`. `start`/`end` optional but, if present, must be `HH:MM`.
- Executions (list of objects): `id` required (string); `summary` optional. `tests` can be strings or `{id, result?}`; `test_ids` may be a list of strings.
- Blockers: newline-separated string or list of strings.

Running tests
-------------

Unit tests:

```
pytest tests/test_validation.py -q
```

Playwright UI test (optional):

```
pip install playwright pytest-playwright
playwright install

# start app in one terminal
python app.py

# run the test in another terminal
pytest tests/test_playwright_ui.py -q
```

Notes
-----
- If you don’t want optional backends, set `VALIDATOR_BACKEND=pure`.
- If you see import errors for Pydantic or jsonschema, either install them or switch the backend.
- The report text is HTML-escaped to prevent injection; line breaks render as `<br>` in the browser.
