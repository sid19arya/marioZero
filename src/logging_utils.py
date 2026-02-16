"""Structured logging with trace_id and agent trace events."""
import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

# Context variable for trace_id so it is attached to every log in the current run
trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str | None:
    return trace_id_ctx.get()


def set_trace_id(trace_id: str) -> None:
    trace_id_ctx.set(trace_id)


def clear_trace_id() -> None:
    try:
        trace_id_ctx.set("")
    except LookupError:
        pass


def add_trace_id(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor: add trace_id to every event."""
    tid = get_trace_id()
    if tid:
        event_dict["trace_id"] = tid
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog and stdlib logging. Call once at startup."""
    level = getattr(logging, log_level, logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_trace_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True)
            if log_level == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


# Convenience: log agent trace events with consistent event names
def log_agent_run_start(
    logger: structlog.stdlib.BoundLogger,
    trigger: str,
    user_message: str,
    trace_id: str,
) -> None:
    msg = user_message[:200] + "..." if len(user_message) > 200 else user_message
    logger.info(
        "agent_run_start",
        trigger=trigger,
        user_message=msg,
        trace_id=trace_id,
    )


def log_llm_request(
    logger: structlog.stdlib.BoundLogger,
    step: int,
    message_count: int,
) -> None:
    logger.info("llm_request", step=step, message_count=message_count)


def log_llm_response(
    logger: structlog.stdlib.BoundLogger,
    step: int,
    has_tool_calls: bool,
    tool_call_names: list[str] | None = None,
    content_length: int = 0,
) -> None:
    logger.info(
        "llm_response",
        step=step,
        has_tool_calls=has_tool_calls,
        tool_call_names=tool_call_names or [],
        content_length=content_length,
    )


def log_tool_call_start(
    logger: structlog.stdlib.BoundLogger,
    step: int,
    tool_name: str,
    arguments: dict[str, Any],
) -> None:
    logger.info("tool_call_start", step=step, tool_name=tool_name, arguments=arguments)


def log_tool_call_end(
    logger: structlog.stdlib.BoundLogger,
    step: int,
    tool_name: str,
    success: bool,
    result_summary: str | None = None,
    error: str | None = None,
) -> None:
    logger.info(
        "tool_call_end",
        step=step,
        tool_name=tool_name,
        success=success,
        result_summary=result_summary,
        error=error,
    )


def log_agent_run_end(
    logger: structlog.stdlib.BoundLogger,
    steps: int,
    final_response_length: int,
) -> None:
    logger.info(
        "agent_run_end",
        steps=steps,
        final_response_length=final_response_length,
    )
