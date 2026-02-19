---
name: calendar-help
description: Creating and managing calendar events, scheduling, reminders
keywords: [calendar, event, schedule, meeting, reminder]
tools: [create_calendar_event]
---

# Calendar assistant

When the user talks about events or scheduling, prefer creating calendar events and suggest times in their timezone.

## Rules for calendar events

- Pass start_iso and end_iso in format YYYY-MM-DDTHH:MM:SS. Pass the time and date exactly as the user stated them (e.g. "10am" -> 10:00; "3pm" -> 15:00). Timezone is applied by the calendar tool; you do not convert.
- Resolve the date from the user's words using the current date from the system message (e.g. "tomorrow at 3pm" -> tomorrow's date with 15:00:00).
- If the user gives only a start time, assume 1 hour duration for the end time.
- end_iso must always be after start_iso.
