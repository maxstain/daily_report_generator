import datetime
from flask import Flask, render_template, request
from Functions import generate_report
import importlib
import os
import json
import html

# choose validation backend via env var: 'auto' (default), 'pydantic', 'jsonschema', 'pure'
VALIDATOR_BACKEND = os.environ.get('VALIDATOR_BACKEND', 'auto').lower()

# default validators module (pure python)
from Functions import validation as pure_validation
validation = pure_validation

if VALIDATOR_BACKEND in ('auto', 'pydantic'):
    try:
        pmod = importlib.import_module('Functions.pydantic_validation')
        validation = pmod
        if VALIDATOR_BACKEND == 'pydantic':
            print('Using pydantic validation backend')
    except Exception:
        if VALIDATOR_BACKEND == 'pydantic':
            raise
        # else fall through to try jsonschema or pure

if VALIDATOR_BACKEND in ('auto', 'jsonschema') and validation is pure_validation:
    try:
        jsmod = importlib.import_module('Functions.jsonschema_validation')
        validation = jsmod
        if VALIDATOR_BACKEND == 'jsonschema':
            print('Using jsonschema validation backend')
    except Exception:
        if VALIDATOR_BACKEND == 'jsonschema':
            raise
        # fall back to pure

# expose functions
validate_bookings = validation.validate_bookings
validate_executions = validation.validate_executions
validate_blockers = validation.validate_blockers
validate_extra_tasks = validation.validate_extra_tasks

app = Flask(__name__)


@app.route('/')
def home():
    # Always show today's date in the form (user requested report date always be today)
    date_today = datetime.date.today().isoformat()
    return render_template('home.html', date=date_today)


@app.route('/generate_report', methods=['POST'])
def generate_report_route():
    # Force report date to today's date, ignore any provided date in the form
    date_today = datetime.date.today().isoformat()

    # parse optional JSON inputs for bookings and executions
    errors = []
    bookings_json = request.form.get('bookings_json', '').strip()
    executions_json = request.form.get('executions_json', '').strip()
    blockers_text = request.form.get('blockers_text', '').strip()
    extra_tasks_text = request.form.get('extra_tasks_text', '').strip()

    bookings_raw = None
    executions_raw = None
    blockers_raw = None
    extra_tasks_raw = None

    if bookings_json:
        try:
            bookings_raw = json.loads(bookings_json)
        except Exception as e:
            errors.append(f'Bookings JSON parse error: {e}')

    if executions_json:
        try:
            executions_raw = json.loads(executions_json)
        except Exception as e:
            errors.append(f'Executions JSON parse error: {e}')

    if blockers_text:
        blockers_raw = blockers_text

    if extra_tasks_text:
        extra_tasks_raw = extra_tasks_text

    if errors:
        # return to home with parse errors and preserve previously entered fields
        return render_template('home.html', errors=errors, bookings_json=bookings_json,
                               executions_json=executions_json, blockers_text=blockers_text,
                               extra_tasks_text=extra_tasks_text, date=date_today)

    # run schema validation using the chosen validation backend
    bookings, b_errors = validate_bookings(bookings_raw)
    executions, e_errors = validate_executions(executions_raw)
    blockers, bl_errors = validate_blockers(blockers_raw)
    extra_tasks, et_errors = validate_extra_tasks(extra_tasks_raw)

    validation_errors = b_errors + e_errors + bl_errors + et_errors
    if validation_errors:
        return render_template('home.html', errors=validation_errors, bookings_json=bookings_json,
                               executions_json=executions_json, blockers_text=blockers_text,
                               extra_tasks_text=extra_tasks_text, date=date_today)

    report = generate_report(bookings, executions, blockers, date=date_today, extra_tasks=extra_tasks)
    # escape the report to avoid HTML injection, then convert newlines to <br> for HTML display
    report_safe = html.escape(report)
    report_html = report_safe.replace('\n', '<br>')
    return render_template('report.html', report=report_html, date=date_today)


if __name__ == '__main__':
    app.run(debug=True)
