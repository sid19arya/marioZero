"""ReAct-style agent loop: LLM + tool-calling with structured logging."""
import json
import uuid
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from openai import OpenAI

from src.config import (
    AGENT_MAX_STEPS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    USER_TIMEZONE,
    validate_for_agent,
)
from src.logging_utils import (
    set_trace_id,
    get_logger,
    log_agent_run_end,
    log_agent_run_start,
    log_llm_request,
    log_llm_request_to_file,
    log_llm_response,
    log_llm_response_to_file,
    log_skill_invoked_to_file,
    log_tool_call_end,
    log_tool_call_start,
)
from src.tools import get_tool_registry

SYSTEM_PROMPT_TEMPLATE = """You are a personal assistant with access to tools. When the user asks you to do something that requires a tool, call the appropriate tool with the correct arguments.

The user is in timezone: {user_timezone} (for your awareness only; you do not convert times).
Current date and time in the user's timezone (use to resolve relative dates like "today", "tomorrow", "next Monday" when relevant): {current_datetime_local}.

When the user's message is not something you can do with your tools, reply politely and briefly. After calling a tool, summarize the result for the user in a short, friendly message."""

logger = get_logger(__name__)


def run(
    user_message: str,
    *,
    trigger: str = "unknown",
    skill_content: str | None = None,
    skill_tool_names: list[str] | None = None,
    skill_name: str | None = None,
) -> str:
    """Run the agent on a single user message. Returns the final text reply.
    trigger: 'cli' | 'telegram' | 'unknown' for logging.
    skill_content: optional skill body to prepend to system prompt.
    skill_tool_names: optional list of skill tool names to include for this run.
    skill_name: optional skill name for logging (skill_invoked in .log).
    """
    validate_for_agent()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)
    if skill_name and skill_tool_names is not None:
        log_skill_invoked_to_file(trace_id, skill_name, skill_tool_names)
    log_agent_run_start(logger, trigger=trigger, user_message=user_message, trace_id=trace_id)

    client = OpenAI(api_key=OPENAI_API_KEY)
    registry = get_tool_registry()
    tools = registry.get_openai_tools(include_skill_tool_names=skill_tool_names)
    if not tools:
        log_agent_run_end(logger, steps=0, final_response_length=0)
        return "No tools are available. Please configure at least one tool."

    try:
        tz = ZoneInfo(USER_TIMEZONE)
    except Exception:
        tz = timezone.utc  # fallback if tzdata missing or bad USER_TIMEZONE (e.g. on Windows: pip install tzdata)
    current_dt_local = datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S")
    base_system = SYSTEM_PROMPT_TEMPLATE.format(
        user_timezone=USER_TIMEZONE,
        current_datetime_local=current_dt_local,
    )
    if skill_content and skill_content.strip():
        system_content = skill_content.strip() + "\n\n" + base_system
    else:
        system_content = base_system
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message},
    ]
    step = 0
    final_content = ""

    while step < AGENT_MAX_STEPS:
        step += 1
        log_llm_request(logger, step=step, message_count=len(messages))
        log_llm_request_to_file(trace_id, step=step, model=OPENAI_MODEL, message_count=len(messages))

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        choice = response.choices[0]
        msg = choice.message
        has_tool_calls = bool(msg.tool_calls)
        tool_call_names = [tc.function.name for tc in (msg.tool_calls or [])]
        content = (msg.content or "").strip()
        log_llm_response(
            logger,
            step=step,
            has_tool_calls=has_tool_calls,
            tool_call_names=tool_call_names if tool_call_names else None,
            content_length=len(content),
        )
        usage = getattr(response, "usage", None)
        log_llm_response_to_file(
            trace_id,
            step=step,
            model=OPENAI_MODEL,
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
            content_length=len(content),
            tool_calls=tool_call_names if tool_call_names else None,
        )

        if not has_tool_calls:
            final_content = content or "I don't have a response for that."
            break

        # Append assistant message with tool_calls
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        }
        messages.append(assistant_msg)

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
            except json.JSONDecodeError:
                args = {}
            log_tool_call_start(logger, step=step, tool_name=name, arguments=args)
            try:
                result = registry.execute(name, args)
                log_tool_call_end(logger, step=step, tool_name=name, success=True, result_summary=result[:200] if result else None)
                result_str = result
            except Exception as e:
                result_str = f"Error: {e!s}"
                log_tool_call_end(logger, step=step, tool_name=name, success=False, error=result_str)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

    else:
        final_content = "I hit the step limit. Please try a simpler request."

    log_agent_run_end(logger, steps=step, final_response_length=len(final_content))
    return final_content
