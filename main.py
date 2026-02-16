"""Entry: run agent via CLI or Telegram trigger."""
import sys

from src.config import LOG_LEVEL, validate_for_agent, validate_for_telegram
from src.logging_utils import configure_logging


def main() -> None:
    configure_logging(LOG_LEVEL)
    if len(sys.argv) < 2:
        print("Usage: python main.py chat \"message\"  |  python main.py telegram", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1].lower()
    if cmd == "chat":
        validate_for_agent()
        from src.triggers.cli import run_cli
        run_cli()
    elif cmd == "telegram":
        validate_for_telegram()
        from src.triggers.telegram import run_telegram
        run_telegram()
    else:
        print("Unknown command. Use: chat | telegram", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
