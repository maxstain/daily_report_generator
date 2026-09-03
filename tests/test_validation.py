from Functions import validation


def test_validate_bookings_happy():
    raw = [
        {"remote": "remote 1", "start": "08:30", "end": "12:30"},
        {"remote": "remote 2", "start": "13:00", "end": "17:00"},
    ]
    valid, errors = validation.validate_bookings(raw)
    assert errors == []
    assert isinstance(valid, list)
    assert valid[0]["remote"] == "remote 1"


def test_validate_bookings_errors():
    raw = [
        {"start": "8:30"},  # invalid time and missing remote/location
        "not-an-object"
    ]
    valid, errors = validation.validate_bookings(raw)
    assert len(errors) >= 1


def test_validate_executions_happy():
    raw = [
        {"id": "SECONPRO-1", "summary": "sum", "tests": ["T1", {"id": "T2", "result": "Fail"}]}
    ]
    valid, errors = validation.validate_executions(raw)
    assert errors == []
    assert valid[0]["id"] == "SECONPRO-1"
    assert isinstance(valid[0]["tests"], list)


def test_validate_executions_errors():
    raw = [
        {"summary": "no id"},
        "string"
    ]
    valid, errors = validation.validate_executions(raw)
    assert len(errors) >= 1


def test_validate_blockers():
    raw = "issue one\nissue two"
    valid, errors = validation.validate_blockers(raw)
    assert errors == []
    assert valid == ["issue one", "issue two"]


def test_validate_extra_tasks():
    raw = "task one\ntask two"
    valid, errors = validation.validate_extra_tasks(raw)
    assert errors == []
    assert valid == ["task one", "task two"]


def test_validate_extra_tasks_none():
    valid, errors = validation.validate_extra_tasks(None)
    assert errors == []
    assert valid == []


def test_validate_pv9_actions():
    raw = "action one\naction two"
    valid, errors = validation.validate_pv9_actions(raw)
    assert errors == []
    assert valid == ["action one", "action two"]


def test_validate_pv9_actions_none():
    valid, errors = validation.validate_pv9_actions(None)
    assert errors == []
    assert valid == []


def test_validate_pv9_actions_errors():
    raw = 12345
    valid, errors = validation.validate_pv9_actions(raw)
    assert len(errors) == 1
    assert valid == []


def test_generate_report_with_pv9_actions():
    from Functions import generate_report

    bookings = [{"remote": "remote 1", "start": "08:30", "end": "12:30"}]
    executions = [{"id": "SECONPRO-100", "summary": "Sample execution", "tests": ["TC-1", "TC-2"]}]
    blockers = ["None blocker"]
    extra_tasks = ["Reviewed logs"]
    pv9_actions = ["Flashed ECU on PV9", "Captured trace on bench"]

    report = generate_report(
        bookings=bookings,
        executions=executions,
        blockers=blockers,
        date="2026-09-03",
        extra_tasks=extra_tasks,
        pv9_actions=pv9_actions,
    )

    assert "🚗 PV9 Actions:" in report
    assert "- Flashed ECU on PV9" in report
    assert "- Captured trace on bench" in report
    assert "📝 Extra Tasks:" in report
    assert "- Reviewed logs" in report


def test_pydantic_validation_pv9_actions():
    try:
        from Functions import pydantic_validation
    except ImportError:
        return
    valid, errors = pydantic_validation.validate_pv9_actions("act1\nact2")
    assert errors == []
    assert valid == ["act1", "act2"]

    valid_none, errors_none = pydantic_validation.validate_pv9_actions(None)
    assert errors_none == []
    assert valid_none == []


def test_jsonschema_validation_pv9_actions():
    try:
        from Functions import jsonschema_validation
    except ImportError:
        return
    valid, errors = jsonschema_validation.validate_pv9_actions("act1\nact2")
    assert errors == []
    assert valid == ["act1", "act2"]

    valid_none, errors_none = jsonschema_validation.validate_pv9_actions(None)
    assert errors_none == []
    assert valid_none == []


def test_flask_generate_report_route_with_pv9():
    from app import app
    client = app.test_client()
    response = client.post('/generate_report', data={
        'bookings_json': '[{"remote": "remote 1", "start": "08:30", "end": "12:30"}]',
        'executions_json': '[{"id": "SECONPRO-100", "summary": "Sample", "tests": ["TC-1"]}]',
        'blockers_text': 'None blocker',
        'extra_tasks_text': 'Extra task 1',
        'pv9_actions_text': 'PV9 Action item 1\nPV9 Action item 2'
    })
    assert response.status_code == 200
    html_content = response.get_data(as_text=True)
    assert "PV9 Actions" in html_content
    assert "PV9 Action item 1" in html_content
    assert "PV9 Action item 2" in html_content

