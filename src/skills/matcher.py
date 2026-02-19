"""Match a user message to the best skill using frontmatter (description, keywords)."""
import re

from src.skills.loader import Skill


def _tokenize(text: str) -> set[str]:
    """Normalize and tokenize into words (lowercase, alphanumeric)."""
    text = (text or "").lower()
    words = re.findall(r"[a-z0-9]+", text)
    return set(w for w in words if len(w) > 1)


def match_skill(message: str, skills: list[Skill]) -> Skill | None:
    """Return the skill that best matches the message, or None if no score above threshold.
    Scores by term overlap between message and each skill's description + keywords.
    """
    if not skills:
        return None
    msg_tokens = _tokenize(message)
    if not msg_tokens:
        return None
    best_skill: Skill | None = None
    best_score = 0
    for skill in skills:
        skill_tokens = _tokenize(skill.description)
        for k in skill.keywords:
            skill_tokens |= _tokenize(k)
        if not skill_tokens:
            continue
        overlap = len(msg_tokens & skill_tokens)
        if overlap > best_score:
            best_score = overlap
            best_skill = skill
    # Require at least one shared meaningful term
    if best_skill is not None and best_score > 0:
        return best_skill
    return None
