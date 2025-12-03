try:
    from pydantic import BaseModel, field_validator, model_validator
except Exception as e:
    raise ImportError('pydantic is not available')

from typing import List, Optional, Any, Tuple
import re

TIME_RE = re.compile(r"^\d{2}:\d{2}$")


class BookingModel(BaseModel):
    remote: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None

    @field_validator('start', 'end')
    def check_time(cls, v):
        if v is None or v == '':
            return v
        if not TIME_RE.match(v):
            raise ValueError('time must be in HH:MM format')
        return v

    @model_validator(mode='after')
    def check_remote_required(self):
        if not self.remote:
            raise ValueError('"remote" is required')
        return self


class TestCaseModel(BaseModel):
    id: str
    result: Optional[str] = None


class ExecutionModel(BaseModel):
    id: str
    summary: Optional[str] = None
    tests: Optional[List[Any]] = None
    test_ids: Optional[List[str]] = None


def validate_bookings(raw: Any) -> Tuple[List[dict], List[str]]:
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
            m = BookingModel(**item)
            valid.append(m.model_dump())
        except Exception as e:
            errors.append(f'Bookings[{i}]: {e}')
    return valid, errors


def validate_executions(raw: Any) -> Tuple[List[dict], List[str]]:
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
            m = ExecutionModel(**item)
            data = m.model_dump()
            if data.get('tests'):
                norm = []
                for t in data['tests']:
                    if isinstance(t, dict):
                        norm.append(t)
                    else:
                        norm.append(str(t))
                data['tests'] = norm
            valid.append(data)
        except Exception as e:
            errors.append(f'Executions[{i}]: {e}')
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
