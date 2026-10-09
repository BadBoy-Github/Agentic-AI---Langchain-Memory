"""Local Date and Time tool for the ReAct Agent."""

import time
from datetime import datetime
from langchain_core.tools import tool


@tool
def local_date_time() -> str:
    """Returns the current local date, time, day of the week, and local timezone.

    Use this tool whenever the user asks for the current time, today's date,
    day of the week, or needs time-relative context (e.g., 'what time is it?',
    'what day is today?', 'current year', etc.).

    Returns:
        A formatted string with the local date, time, weekday, and timezone.
    """
    now = datetime.now()
    timezone_name = time.tzname[time.daylight] if time.daylight and time.tzname[1] else time.tzname[0]
    utc_offset = time.strftime("%z")

    return (
        f"Current Local Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Day of the Week: {now.strftime('%A')}\n"
        f"Timezone: {timezone_name} (UTC{utc_offset})"
    )
