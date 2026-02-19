"""Telegram trigger: on message run agent and reply."""
import asyncio
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.gateway import handle_message
from src.config import (
    TELEGRAM_ALLOWED_USER_ID,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CONNECT_TIMEOUT,
    TELEGRAM_PROXY,
    TELEGRAM_READ_TIMEOUT,
)
from src.logging_utils import get_logger

logger = get_logger(__name__)


async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id if update.effective_user else None
    if TELEGRAM_ALLOWED_USER_ID is not None and user_id != TELEGRAM_ALLOWED_USER_ID:
        try:
            await update.message.reply_text("Unauthorized.")
        except NetworkError as e:
            logger.warning("telegram_network_error_reply", extra={"error": str(e)})
        return
    text = update.message.text.strip()
    try:
        loop = asyncio.get_running_loop()
        reply, _ = await loop.run_in_executor(None, lambda: handle_message(text, trigger="telegram"))
        await update.message.reply_text(reply)
    except NetworkError as e:
        logger.exception("telegram_network_error")
        try:
            await update.message.reply_text(
                "Could not reach Telegram. Check network/proxy (TELEGRAM_PROXY) and try again."
            )
        except Exception:
            pass
    except Exception as e:
        logger.exception("telegram_handler_error")
        try:
            await update.message.reply_text(f"Something went wrong: {e!s}")
        except NetworkError:
            logger.warning("telegram_network_error_reply", extra={"original_error": str(e)})


def run_telegram() -> None:
    """Start the Telegram bot with long-polling."""
    builder = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(TELEGRAM_CONNECT_TIMEOUT)
        .read_timeout(TELEGRAM_READ_TIMEOUT)
        .get_updates_connect_timeout(TELEGRAM_CONNECT_TIMEOUT)
        .get_updates_read_timeout(TELEGRAM_READ_TIMEOUT)
    )
    if TELEGRAM_PROXY:
        builder = builder.proxy(TELEGRAM_PROXY).get_updates_proxy(TELEGRAM_PROXY)

    # Fail fast if we cannot reach Telegram after a few retries (e.g. proxy/firewall/DNS)
    _max_startup_retries = 3
    _startup_retry_delay_s = 2.0

    async def post_init(application: Application) -> None:
        for attempt in range(1, _max_startup_retries + 1):
            try:
                await application.bot.get_me()
                return
            except NetworkError as e:
                if attempt < _max_startup_retries:
                    logger.warning(
                        "telegram_startup_retry",
                        extra={"attempt": attempt, "max": _max_startup_retries, "error": str(e)},
                    )
                    await asyncio.sleep(_startup_retry_delay_s)
                else:
                    logger.error(
                        "telegram_startup_connection_failed",
                        extra={"error": str(e)},
                    )
                    raise RuntimeError(
                        "Cannot reach Telegram API after %d attempts. "
                        "Check TELEGRAM_PROXY, firewall, and DNS. See README for proxy/timeout options."
                        % _max_startup_retries
                    ) from e

    app = builder.post_init(post_init).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES, bootstrap_retries=_max_startup_retries)
