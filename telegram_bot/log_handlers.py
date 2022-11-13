import logging
import os

from telegram import Bot


class TelegramLogsHandler(logging.Handler):
    def __init__(self,
                 tg_bot: Bot,
                 chat_id: int = os.getenv('ADMIN_TELEGRAM_ID')) -> None:
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)