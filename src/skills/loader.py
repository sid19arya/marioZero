"""Load skill files from a directory: YAML frontmatter + Markdown body."""
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.config import SKILLS_DIR
from src.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class Skill:
    """A single skill: metadata from frontmatter and body text for the system prompt."""

    name: str
    description: str
    body: str
    keywords: list[str]
    tools: list[str]


def _parse_frontmatter_and_body(content: str) -> tuple[dict, str]:
    """Split content into frontmatter dict and body. Returns ({}, content) if no valid frontmatter."""
    content = content.strip()
    if not content.startswith("---"):
        return {}, content
    parts = content.split("\n", 1)
    if len(parts) < 2:
        return {}, content
    rest = parts[1]
    idx = rest.find("\n---")
    if idx == -1:
        return {}, content
    yaml_block = rest[:idx].strip()
    body = rest[idx + 4 :].strip()
    try:
        meta = yaml.safe_load(yaml_block)
        return (meta or {}), body
    except yaml.YAMLError as e:
        logger.warning("skill_frontmatter_parse_error", extra={"error": str(e)})
        return {}, content


def load_skills(skills_dir: Path | None = None) -> list[Skill]:
    """Discover *.md files in skills_dir, parse frontmatter + body, return list of Skill.
    If skills_dir does not exist or is empty, return [].
    Malformed files are skipped with a log warning.
    """
    directory = skills_dir or SKILLS_DIR
    if not directory.exists() or not directory.is_dir():
        return []
    skills: list[Skill] = []
    for path in sorted(directory.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            logger.warning("skill_file_read_error", extra={"path": str(path), "error": str(e)})
            continue
        meta, body = _parse_frontmatter_and_body(text)
        name = meta.get("name") or path.stem
        description = meta.get("description") or ""
        keywords = meta.get("keywords")
        if keywords is None:
            keywords = []
        if not isinstance(keywords, list):
            keywords = [str(k) for k in (keywords,)]
        tools = meta.get("tools")
        if tools is None:
            tools = []
        if not isinstance(tools, list):
            tools = [str(tools)]
        if not description.strip():
            logger.warning("skill_missing_description", extra={"path": str(path), "name": name})
        skills.append(
            Skill(
                name=str(name),
                description=str(description),
                body=body,
                keywords=[str(k) for k in keywords],
                tools=[str(t) for t in tools],
            )
        )
    return skills
