from typing import Any, List, Tuple

# A minimal JSON Schema for our inputs
BOOKING_SCHEMA = {
    "type": "object",
    "properties": {
        "remote": {"type": "string"},
        "start": {"type": "string", "pattern": "^\\d{2}:\\d{2}$"},
        "end": {"type": "string", "pattern": "^\\d{2}:\\d{2}$"},
    },
    "required": ["remote"],
    "additionalProperties": True
}

EXECUTION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "summary": {"type": "string"},
        "tests": {"type": "array"},
        "test_ids": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["id"],
    "additionalProperties": True
}


def _validate_item(schema, item):
    try:
        from jsonschema import validate, ValidationError
    except Exception:
        return 'jsonschema package is not installed'
    try:
        validate(instance=item, schema=schema)
        return None
    except ValidationError as e:
        return str(e)


def validate_bookings(raw: Any) -> Tuple[List[dict], List[str]]:
    errors = []
    valid = []
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], ['Bookings must be a JSON array']
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f'Bookings[{i}] must be an object')
            continue
        err = _validate_item(BOOKING_SCHEMA, item)
        if err:
            errors.append(f'Bookings[{i}]: {err}')
            continue
        # Ensure remote is provided by schema required, but add a friendly message if missing
        if not item.get('remote'):
            errors.append(f'Bookings[{i}]: "remote" is required')
            continue
        valid.append(item)
    return valid, errors


def validate_executions(raw: Any) -> Tuple[List[dict], List[str]]:
    errors = []
    valid = []
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], ['Executions must be a JSON array']
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f'Executions[{i}] must be an object')
            continue
        err = _validate_item(EXECUTION_SCHEMA, item)
        if err:
            errors.append(f'Executions[{i}]: {err}')
            continue
        valid.append(item)
    return valid, errors


def validate_blockers(raw: Any) -> Tuple[List[str], List[str]]:
    # same as other validators
    if raw is None:
        return [], []
    if isinstance(raw, str):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
    elif isinstance(raw, list):
        lines = raw
    else:
        return [], ['Blockers must be a newline-separated string or an array of strings']
    errors = []
    valid = []
    for i, b in enumerate(lines):
        if not isinstance(b, str):
            errors.append(f'Blocker[{i}] must be a string')
            continue
        if len(b) > 1000:
            errors.append(f'Blocker[{i}] is too long')
            continue
        valid.append(b)
    return valid, errors


def validate_extra_tasks(raw: Any) -> Tuple[List[str], List[str]]:
    if raw is None:
        return [], []
    if isinstance(raw, str):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
    elif isinstance(raw, list):
        lines = raw
    else:
        return [], ['Extra tasks must be a newline-separated string or an array of strings']
    errors = []
    valid = []
    for i, t in enumerate(lines):
        if not isinstance(t, str):
            errors.append(f'Extra Task[{i}] must be a string')
            continue
        if len(t) > 1000:
            errors.append(f'Extra Task[{i}] is too long')
            continue
        valid.append(t)
    return valid, errors
