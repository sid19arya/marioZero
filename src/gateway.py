"""Gateway: all messages go through here; resolve skill and call agent."""
from src.agent import run
from src.logging_utils import get_logger, log_skill_invoked
from src.skills import resolve_skill

logger = get_logger(__name__)


def handle_message(message: str, *, trigger: str = "unknown") -> tuple[str, str | None]:
    """Handle an incoming message: resolve skill, then run agent with skill content and tool names.
    Returns (reply_text, skill_name or None). Reply text includes a '[Used skill: name]' line when a skill was invoked.
    """
    skill = resolve_skill(message)
    skill_content = skill.body.strip() if skill else None
    skill_tool_names = skill.tools if skill else None
    skill_name = skill.name if skill else None

    if skill:
        log_skill_invoked(logger, skill.name, skill.tools)

    reply = run(
        message,
        trigger=trigger,
        skill_content=skill_content,
        skill_tool_names=skill_tool_names,
        skill_name=skill_name,
    )

    if skill:
        reply = "[Used skill: " + skill.name + "]\n\n" + reply

    return (reply, skill_name)
