import datetime
from flask import Flask, render_template, request, jsonify
from Functions import generate_report
import importlib
import os
import json
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_apscheduler import APScheduler

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

app = Flask(__name__)

# Scheduler configuration
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


def send_email_task(report_content, date_str):
    """Background task to send email via SMTP."""
    try:
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        sender_email = os.environ.get('SENDER_EMAIL')
        sender_password = os.environ.get('SENDER_PASSWORD')
        recipients = os.environ.get('EMAIL_RECIPIENTS', '').split(',')
        cc_recipients = os.environ.get('EMAIL_CC', '').split(',')

        if not all([smtp_server, sender_email, sender_password, recipients]):
            print("Email configuration is missing in .env")
            return

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        if cc_recipients:
            msg['Cc'] = ", ".join(cc_recipients)
        msg['Subject'] = f"Daily Report {date_str}"

        # Attach report as plain text
        msg.attach(MIMEText(report_content, 'plain', 'utf-8'))

        all_recipients = recipients + (cc_recipients if cc_recipients else [])
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg, from_addr=sender_email, to_addrs=all_recipients)
        server.quit()
        print(f"Scheduled email sent successfully for {date_str}")
    except Exception as e:
        print(f"Error in send_email_task: {e}")


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

    bookings_raw = None
    executions_raw = None
    blockers_raw = None

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

    if errors:
        # return to home with parse errors and preserve previously entered fields
        return render_template('home.html', errors=errors, bookings_json=bookings_json,
                               executions_json=executions_json, blockers_text=blockers_text, date=date_today)

    # run schema validation using the chosen validation backend
    bookings, b_errors = validate_bookings(bookings_raw)
    executions, e_errors = validate_executions(executions_raw)
    blockers, bl_errors = validate_blockers(blockers_raw)

    validation_errors = b_errors + e_errors + bl_errors
    if validation_errors:
        return render_template('home.html', errors=validation_errors, bookings_json=bookings_json,
                               executions_json=executions_json, blockers_text=blockers_text, date=date_today)

    report = generate_report(bookings, executions, blockers, date=date_today)
    # escape the report to avoid HTML injection, then convert newlines to <br> for HTML display
    report_safe = html.escape(report)
    report_html = report_safe.replace('\n', '<br>')
    return render_template('report.html', report=report_html, date=date_today, report_raw=report)


@app.route('/send_email', methods=['POST'])
def send_email_route():
    try:
        data = request.get_json()
        report_content = data.get('report_content', '')
        schedule_time = data.get('schedule_time')  # Optional ISO format string
        date_today = datetime.date.today().isoformat()

        if schedule_time:
            try:
                # Expecting format 'YYYY-MM-DDTHH:MM' or similar that datetime.fromisoformat can handle
                run_date = datetime.datetime.fromisoformat(schedule_time)
                
                # Check if the date is in the past
                if run_date < datetime.datetime.now():
                    return jsonify({'success': False, 'message': 'Scheduled time must be in the future.'}), 400
                
                # Schedule the task
                job_id = f"email_{datetime.datetime.now().timestamp()}"
                scheduler.add_job(
                    id=job_id,
                    func=send_email_task,
                    trigger='date',
                    run_date=run_date,
                    args=[report_content, date_today]
                )
                return jsonify({'success': True, 'message': f'Email scheduled for {run_date.strftime("%Y-%m-%d %H:%M")}'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Invalid schedule time format: {e}'}), 400

        # Immediate send logic (now using the same task function for consistency)
        send_email_task(report_content, date_today)
        return jsonify({'success': True, 'message': 'Email sent successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
