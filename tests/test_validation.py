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

