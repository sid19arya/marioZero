"""CLI trigger: read message from arg or stdin, run gateway, print reply."""
import sys

from src.gateway import handle_message
from src.logging_utils import get_trace_id


def run_cli() -> None:
    """Entry for CLI: message from argv (after 'chat') or stdin, then agent.run and print result."""
    # When invoked as "python main.py chat <message>", argv is [main.py, chat, ...message]
    if len(sys.argv) > 2:
        message = " ".join(sys.argv[2:])
    else:
        print("Enter your message:")
        message = (sys.stdin.readline() or "").strip()
    if not message:
        print("Usage: python main.py chat \"your message\" or echo \"message\" | python main.py chat", file=sys.stderr)
        sys.exit(1)
    reply, skill_name = handle_message(message, trigger="cli")
    if skill_name:
        print(f"[Skill loaded: {skill_name}]", file=sys.stderr)
    print(reply)
    trace_id = get_trace_id()
    if trace_id:
        print(f"[trace_id={trace_id}]", file=sys.stderr)
