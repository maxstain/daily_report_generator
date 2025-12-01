import re
from typing import Any, List, Tuple

TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def _is_string(x: Any) -> bool:
    return isinstance(x, str)


def _error_str(e: Exception) -> str:
    try:
        return str(e)
    except Exception:
        return 'unknown validation error'


def validate_bookings(raw: Any) -> Tuple[List[dict], List[str]]:
    """Validate bookings JSON (expected list of objects).
    Each booking must be a dict with either 'remote' or 'location' (string).
    Optional 'start' and 'end' must be HH:MM if provided.
    Returns (valid_list_of_dicts, list_of_error_strings)
    """
    errors: List[str] = []
    valid: List[dict] = []
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], ['Bookings must be a JSON array']
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f'Bookings[{i}] must be an object')
            continue
        try:
            remote = item.get('remote')
            location = item.get('location')
            if not remote and not location:
                errors.append(f'Bookings[{i}]: either "remote" or "location" must be provided')
                continue
            start = item.get('start')
            end = item.get('end')
            if start and not (isinstance(start, str) and TIME_RE.match(start)):
                errors.append(f'Bookings[{i}]: "start" must be HH:MM')
                continue
            if end and not (isinstance(end, str) and TIME_RE.match(end)):
                errors.append(f'Bookings[{i}]: "end" must be HH:MM')
                continue
            # Normalize keys
            validated = {
                'remote': remote,
                'location': location,
                'start': start,
                'end': end,
            }
            valid.append(validated)
        except Exception as e:
            errors.append(f'Bookings[{i}]: {_error_str(e)}')
    return valid, errors


def validate_executions(raw: Any) -> Tuple[List[dict], List[str]]:
    """Validate executions JSON (expected list of objects).
    Each execution must be a dict with 'id' (string). 'summary' optional.
    'tests' may be a list containing strings or objects with 'id' and optional 'result'.
    'test_ids' may be a list of strings.
    Returns (validated_executions, errors)
    """
    errors: List[str] = []
    valid: List[dict] = []
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], ['Executions must be a JSON array']
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f'Executions[{i}] must be an object')
            continue
        try:
            ex_id = item.get('id')
            if not ex_id or not isinstance(ex_id, str):
                errors.append(f'Executions[{i}]: "id" is required and must be a string')
                continue
            summary = item.get('summary')
            tests = item.get('tests')
            test_ids = item.get('test_ids')

            normalized_tests = None
            if tests is not None:
                if not isinstance(tests, list):
                    errors.append(f'Executions[{i}]: "tests" must be a list if provided')
                    continue
                normalized_tests = []
                for j, t in enumerate(tests):
                    if isinstance(t, str):
                        normalized_tests.append(t)
                    elif isinstance(t, dict):
                        tid = t.get('id')
                        if not tid or not isinstance(tid, str):
                            errors.append(f'Executions[{i}].tests[{j}]: "id" is required and must be a string')
                            continue
                        result = t.get('result')
                        normalized_tests.append({
                            'id': tid,
                            'result': result
                        })
                    else:
                        errors.append(f'Executions[{i}].tests[{j}] must be a string or object')
                        continue
            if test_ids is not None:
                if not isinstance(test_ids, list):
                    errors.append(f'Executions[{i}]: "test_ids" must be a list if provided')
                    continue
                for j, tid in enumerate(test_ids):
                    if not isinstance(tid, str):
                        errors.append(f'Executions[{i}].test_ids[{j}] must be a string')
                        continue
            validated = {
                'id': ex_id,
                'summary': summary,
                'tests': normalized_tests,
                'test_ids': test_ids,
            }
            valid.append(validated)
        except Exception as e:
            errors.append(f'Executions[{i}]: {_error_str(e)}')
    return valid, errors


def validate_blockers(raw: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    valid: List[str] = []
    if raw is None:
        return [], []
    if isinstance(raw, str):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
    elif isinstance(raw, list):
        lines = raw
    else:
        return [], ['Blockers must be a newline-separated string or an array of strings']
    for i, b in enumerate(lines):
        if not isinstance(b, str):
            errors.append(f'Blocker[{i}] must be a string')
            continue
        if len(b) > 1000:
            errors.append(f'Blocker[{i}] is too long')
            continue
        valid.append(b)
    return valid, errors
