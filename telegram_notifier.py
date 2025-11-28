# telegram_notifier.py

import logging
from typing import Optional
from urllib import request, parse

import telegram_config

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Thin wrapper around Telegram Bot API sendMessage.
    - No external dependencies (uses stdlib urllib).
    - Completely no-op if token/chat_id are missing.
    """

    def __init__(self) -> None:
        self._token: Optional[str] = telegram_config.TELEGRAM_BOT_TOKEN
        self._chat_id: Optional[str] = telegram_config.TELEGRAM_CHAT_ID
        self.enabled: bool = bool(self._token and self._chat_id)

        if not self.enabled:
            logger.warning(
                "TelegramNotifier disabled: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID "
                "not set in environment."
            )

        self._base_url: Optional[str] = (
            f"https://api.telegram.org/bot{self._token}/sendMessage"
            if self.enabled
            else None
        )

    def send_message(self, text: str) -> None:
        """
        Fire-and-forget send. Never raises up the stack.
        """
        if not self.enabled or not text:
            return

        try:
            data = parse.urlencode(
                {
                    "chat_id": self._chat_id,
                    "text": text,
                    # Plain text, no parse_mode to avoid escaping headaches
                    "disable_web_page_preview": "true",
                }
            ).encode("utf-8")

            req = request.Request(self._base_url, data=data, method="POST")
            with request.urlopen(req, timeout=5) as resp:
                status = getattr(resp, "status", None)
                if status is not None and status != 200:
                    body = resp.read().decode("utf-8", errors="replace")
                    logger.error(
                        "Telegram sendMessage failed: status=%s body=%s",
                        status,
                        body,
                    )
        except Exception as e:
            logger.error("Error sending Telegram message: %s", e, exc_info=True)


_notifier = TelegramNotifier()


def send_telegram_message(text: str) -> None:
    """
    Public helper used by other modules.
    """
    _notifier.send_message(text)
