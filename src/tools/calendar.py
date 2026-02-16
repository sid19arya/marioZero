"""Google Calendar tool: create_calendar_event."""
from pathlib import Path

from src.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_TOKEN_PATH,
    USER_TIMEZONE,
    validate_for_calendar_tool,
)
from src.tools.base import make_tool
from src.tools.registry import register

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
# OpenAI tool schema for create_calendar_event
# Agent passes time/date as user stated; timezone is applied in the API call.
CREATE_EVENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Short title of the calendar event (e.g. 'Team standup', 'Meeting with John')"},
        "start_iso": {
            "type": "string",
            "description": "Start date and time as the user stated. Format: YYYY-MM-DDTHH:MM:SS (24h). Example: 2025-02-07T10:00:00 for 10am. Pass through the user's stated time; default duration 1 hour if only start given.",
        },
        "end_iso": {
            "type": "string",
            "description": "End date and time as the user stated: YYYY-MM-DDTHH:MM:SS. Must be after start_iso. Example: 2025-02-07T11:00:00. Infer from user (e.g. '1 hour meeting' -> end = start + 1h).",
        },
        "description": {
            "type": "string",
            "description": "Optional longer description or notes for the event. Use empty string if not provided.",
        },
    },
    "required": ["title", "start_iso", "end_iso"],
}


def _get_credentials():
    """Load existing credentials or run OAuth flow and save token."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    validate_for_calendar_tool()
    creds = None
    token_path = Path(GOOGLE_TOKEN_PATH)
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
            creds = flow.run_local_server(port=8080)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return creds


def create_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str,
    description: str | None = None,
) -> str:
    """Create a Google Calendar event. Returns a short summary or error string."""
    from googleapiclient.discovery import build

    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)
    body = {
        "summary": title,
        "description": description or "",
        "start": {"dateTime": start_iso, "timeZone": USER_TIMEZONE},
        "end": {"dateTime": end_iso, "timeZone": USER_TIMEZONE},
    }
    event = service.events().insert(calendarId="primary", body=body).execute()
    event_id = event.get("id", "")
    html_link = event.get("htmlLink", "")
    return f"Created event: {title} ({start_iso} – {end_iso}). Link: {html_link}" if html_link else f"Created event: {title} (id: {event_id})."


def _register_calendar_tool() -> None:
    definition, fn = make_tool(
        name="create_calendar_event",
        description=(
            "Create a new event on the user's primary Google Calendar. Call this when the user asks to add, schedule, or create a calendar event. "
            "Provide title, start_iso and end_iso in format YYYY-MM-DDTHH:MM:SS. Pass the time and date as the user stated them (e.g. '10am' -> 10:00); timezone is applied by the tool. "
            "Resolve the date from the user's words (today, tomorrow, next Monday) using the current date from the system message. "
            "If the user only gives a start time, assume 1 hour duration for end_iso. Always output both start_iso and end_iso."
        ),
        parameters=CREATE_EVENT_PARAMETERS,
        callable_fn=create_calendar_event,
    )
    register(definition, fn)


# Register on import so the agent sees the tool
_register_calendar_tool()
