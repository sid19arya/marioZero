"""Load and validate configuration from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKENS_DIR = PROJECT_ROOT / "tokens"
TOKENS_DIR.mkdir(exist_ok=True)
GOOGLE_TOKEN_PATH = TOKENS_DIR / "google_token.json"
GOOGLE_CREDENTIALS_PATH = TOKENS_DIR / "google_credentials.json"

# OpenAI (required for agent)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Telegram (required only for telegram trigger)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")
# Optional: proxy for Telegram API (e.g. http://host:port or socks5://...). Also respects HTTPS_PROXY/HTTP_PROXY.
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
# Timeouts (seconds) for connecting to Telegram; increase if you see ConnectError on slow/proxy networks
TELEGRAM_CONNECT_TIMEOUT = float(os.getenv("TELEGRAM_CONNECT_TIMEOUT", "30"))
TELEGRAM_READ_TIMEOUT = float(os.getenv("TELEGRAM_READ_TIMEOUT", "30"))
if TELEGRAM_ALLOWED_USER_ID:
    try:
        TELEGRAM_ALLOWED_USER_ID = int(TELEGRAM_ALLOWED_USER_ID)
    except ValueError:
        TELEGRAM_ALLOWED_USER_ID = None

# Google Calendar (required only when using calendar tool)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# User timezone for calendar events (e.g. America/New_York for Eastern)
# Times from the user ("10am") are interpreted in this timezone.
USER_TIMEZONE = os.getenv("USER_TIMEZONE", "America/New_York")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Agent
AGENT_MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "10"))


def validate_for_agent() -> None:
    """Validate that required env vars for the agent core are set."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required. Set it in .env.")


def validate_for_telegram() -> None:
    """Validate that required env vars for the Telegram trigger are set."""
    validate_for_agent()
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is required for the Telegram trigger. Set it in .env.")


def validate_for_calendar_tool() -> None:
    """Validate that Google OAuth is configured (when calendar tool is used)."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required for the calendar tool. Set them in .env."
        )
