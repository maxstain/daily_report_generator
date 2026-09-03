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

🧪 Executed Test Cases: {total_testcases_number} TCs
{executed_cases_block}

🚧 Blockers / Issues Encountered:
    - {blockers_block}
{extra_tasks_block}
{pv9_actions_block}
_____________________________
Best Regards.
"""


def _format_bookings(bookings: List[Dict[str, Any]]) -> str:
    """Format the bench booking list into the template block.

    Expected bookings item: {"remote": "remote 1", "start": "08:30", "end": "12:30"}
    """
    if not bookings:
        return "    - No bench bookings recorded."

    lines = []
    for b in bookings:
        remote = b.get("remote") or "Remote"
        start = b.get("start", "")
        end = b.get("end", "")
        lines.append(f"    - {remote}:")
        if start or end:
            lines.append(f"        * Start Time: {start}")
            lines.append(f"        * End Time: {end}")
    return "\n".join(lines)


def _format_planned_executions(executions: List[Dict[str, Any]]) -> str:
    """
    Format planned executions into numbered list lines.
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


def _count_testcases(executions: List[Dict[str, Any]]) -> int:
    """Count structured executed test cases across all executions."""
    total = 0

    for ex in executions:
        tests = ex.get("tests")
        if tests and isinstance(tests, list):
            total += len(tests)
            continue

        test_ids = ex.get("test_ids")
        if test_ids and isinstance(test_ids, list):
            total += len(test_ids)

    return total


def _format_executed_cases(executions: List[Dict[str, Any]]) -> str:
    """Format executed test cases into the template block.

    Expected execution item may include 'id' (TE id), 'tests' (list) or 'test_ids' (list).
    """
    if not executions:
        return "    - None"

    lines = []
    for ex in executions:
        ex_id = ex.get("id", "Unknown")

        # Check if there are any tests to report
        tests = ex.get("tests")
        test_ids = ex.get("test_ids")

        if not tests and not test_ids:
            continue

        lines.append(f"    - {ex_id}:")

        if tests and isinstance(tests, list):
            for t in tests:
                if isinstance(t, str):
                    lines.append(f"        * {t}")
                elif isinstance(t, dict):
                    tid = t.get("id", "Unknown")
                    result = t.get("result", "")
                    if result:
                        lines.append(f"        * {tid}: {result}")
                    else:
                        lines.append(f"        * {tid}")
        elif test_ids and isinstance(test_ids, list):
            for tid in test_ids:
                lines.append(f"        * {tid}")

    if not lines:
        return "    - None"

    return "\n".join(lines)


def _format_blockers(blockers: List[str]) -> str:
    if not blockers:
        return "None"
    # join multiple blockers separated by "\n    - " so they render as separate list items
    return "\n    - ".join(blockers)


def _format_extra_tasks(extra_tasks: List[str]) -> str:
    """Format the extra tasks list into the template block.
    If no extra tasks are provided, return an empty string.
    """
    if not extra_tasks:
        return ""

    lines = ["", "📝 Extra Tasks:"]
    for task in extra_tasks:
        lines.append(f"    - {task}")
    return "\n".join(lines)


def _format_pv9_actions(pv9_actions: List[str]) -> str:
    """Format the PV9 actions list into the template block.
    If no PV9 actions are provided, return an empty string.
    """
    if not pv9_actions:
        return ""

    lines = ["", "🚗 PV9 Actions:"]
    for action in pv9_actions:
        lines.append(f"    - {action}")
    return "\n".join(lines)


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


def generate_report(bookings: List[Dict[str, Any]], executions: List[Dict[str, Any]], blockers: List[str], date: Optional[Union[str, datetime.date]] = None, extra_tasks: Optional[List[str]] = None, pv9_actions: Optional[List[str]] = None) -> str:
    """Generate the daily report string based on provided data.

    Inputs:
    - bookings: list of dicts with keys: remote, start, end
    - executions: list of dicts. Each dict may include id, summary, tests (list)
    - blockers: list of strings
    - date: optional date (str in ISO format or datetime.date). If omitted, uses today's date.
    - extra_tasks: optional list of strings
    - pv9_actions: optional list of strings

    Output: multi-line string ready for sending or printing.
    """
    # Allow callers to pass None for any of the inputs
    bookings = bookings or []
    executions = executions or []
    blockers = blockers or []
    extra_tasks = extra_tasks or []
    pv9_actions = pv9_actions or []

    total_tcs = _count_testcases(executions)
    date_str = _coerce_date(date)
    bench_block = _format_bookings(bookings)
    planned_block = _format_planned_executions(executions)
    executed_block = _format_executed_cases(executions)
    blockers_block = _format_blockers(blockers)
    extra_tasks_block = _format_extra_tasks(extra_tasks)
    pv9_actions_block = _format_pv9_actions(pv9_actions)

    report = TEMPLATE.format(
        date=date_str,
        bench_booking_block=bench_block,
        planned_executions_block=planned_block,
        total_testcases_number=total_tcs,
        executed_cases_block=executed_block,
        blockers_block=blockers_block,
        extra_tasks_block=extra_tasks_block,
        pv9_actions_block=pv9_actions_block,
    )
    logging.debug(report)
    return report
