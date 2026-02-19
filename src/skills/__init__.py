"""Skills: load from YAML-frontmatter Markdown files and match to user messages."""
from src.skills.loader import Skill, load_skills
from src.skills.matcher import match_skill


def resolve_skill(message: str) -> Skill | None:
    """Return the best-matching skill for the message (body + tools), or None."""
    skills = load_skills()
    return match_skill(message, skills)


__all__ = ["Skill", "load_skills", "match_skill", "resolve_skill"]
