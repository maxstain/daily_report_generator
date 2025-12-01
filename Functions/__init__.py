import datetime
import logging
from typing import List, Dict, Any, Optional, Union


TEMPLATE = """
Hello,

This is my daily report for today {date}:

🕒 Bench Booking Time:
{bench_booking_block}

✅ Planned Test Executions (Before Bench Booking):
{planned_executions_block}

🧪 Executed Test Cases:
{executed_cases_block}

🚧 Blockers / Issues Encountered:
    - {blockers_block}
_____________________________
Best Regards.
"""


def _format_bookings(bookings: List[Dict[str, Any]]) -> str:
    """Format bench booking list into the template block.

    Expected bookings item: {"remote": "remote 1", "start": "08:30", "end": "12:30"}
    """
    if not bookings:
        return "    - No bench bookings recorded."

    lines = []
    for b in bookings:
        remote = b.get("remote") or b.get("location") or "Remote"
        start = b.get("start", "")
        end = b.get("end", "")
        lines.append(f"    - {remote}:")
        if start or end:
            lines.append(f"        * Start Time: {start}")
            lines.append(f"        * End Time: {end}")
    return "\n".join(lines)


def _format_planned_executions(executions: List[Dict[str, Any]]) -> str:
    """Format planned executions into numbered list lines.

    Expected execution item: {"id": "SECONPRO-30511", "summary": "..."}
    """
    if not executions:
        return "    - None"

    lines = []
    for idx, ex in enumerate(executions, start=1):
        ex_id = ex.get("id", "Unknown")
        summary = ex.get("summary")
        if summary:
            lines.append(f"    - (TE {idx}): {ex_id} - {summary}")
        else:
            lines.append(f"    - (TE {idx}): {ex_id}")
    return "\n".join(lines)


def _format_executed_cases(executions: List[Dict[str, Any]]) -> str:
    """Format executed test cases.

    Each execution may include a "tests" list of dicts: {"id": "SECONPRO-3930", "result": "Fail"}
    If no tests are provided, show a helpful message.
    """
    if not executions:
        return "    - No executed test cases recorded."

    lines = []
    for idx, ex in enumerate(executions, start=1):
        lines.append(f"    - TE {idx}:")
        tests = ex.get("tests")
        # If the execution carries a flat list of test ids under key "test_ids" also support it.
        if tests and isinstance(tests, list):
            for t in tests:
                # t can be a string or dict
                if isinstance(t, str):
                    lines.append(f"        * {t}")
                elif isinstance(t, dict):
                    tid = t.get("id", "Unknown")
                    result = t.get("result")
                    if result:
                        lines.append(f"        * {tid}: {result}")
                    else:
                        lines.append(f"        * {tid}")
        else:
            # try fallback: maybe this execution is itself a single test id under 'id' and 'result'
            # or there may be a top-level 'test_ids' list
            test_ids = ex.get("test_ids")
            if test_ids and isinstance(test_ids, list):
                for tid in test_ids:
                    lines.append(f"        * {tid}")
            else:
                # Nothing structured - mention the execution id as placeholder
                ex_id = ex.get("id")
                if ex_id:
                    lines.append(f"        * {ex_id} (no testcases provided)")
                else:
                    lines.append("        - No tests recorded for this TE")
    return "\n".join(lines)


def _format_blockers(blockers: List[str]) -> str:
    if not blockers:
        return "None"
    # join multiple blockers separated by "\n    - " so they render as separate list items
    return "\n    - ".join(blockers)


def _coerce_date(date_in: Optional[Union[str, datetime.date]]) -> str:
    """Return an ISO date string for the template. Accepts str or datetime.date or None."""
    if not date_in:
        return datetime.date.today().isoformat()
    if isinstance(date_in, datetime.date):
        return date_in.isoformat()
    # try parse from ISO-like string
    try:
        parsed = datetime.date.fromisoformat(str(date_in))
        return parsed.isoformat()
    except Exception:
        # fallback: return the raw string (safe fallback)
        return str(date_in)


def generate_report(bookings: List[Dict[str, Any]], executions: List[Dict[str, Any]], blockers: List[str], date: Optional[Union[str, datetime.date]] = None) -> str:
    """Generate the daily report string based on provided data.

    Inputs:
    - bookings: list of dicts with keys: remote/location, start, end
    - executions: list of dicts. Each dict may include id, summary, tests (list)
    - blockers: list of strings
    - date: optional date (str in ISO format or datetime.date). If omitted, uses today's date.

    Output: multi-line string ready for sending or printing.
    """
    # Allow callers to pass None for any of the inputs
    bookings = bookings or []
    executions = executions or []
    blockers = blockers or []

    date_str = _coerce_date(date)
    bench_block = _format_bookings(bookings)
    planned_block = _format_planned_executions(executions)
    executed_block = _format_executed_cases(executions)
    blockers_block = _format_blockers(blockers)

    report = TEMPLATE.format(
        date=date_str,
        bench_booking_block=bench_block,
        planned_executions_block=planned_block,
        executed_cases_block=executed_block,
        blockers_block=blockers_block,
    )
    logging.debug(report)
    return report
