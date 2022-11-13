from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from environs import Env
import logging
import json
import settings
from redis import Redis

redis = Redis(host='localhost', port=6379, db=0)

logger = logging.getLogger('log.log')

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [settings.NEW_QUESTION_BUTTON, settings.GIVE_UP_BUTTON],
        [settings.SCORES_BUTTON]
    ],
    resize_keyboard=True
    )


def start(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        update.effective_chat.id,
        text='Здавствуйте',
        reply_markup=MAIN_KEYBOARD
    )


def message_handler(update: Update, context: CallbackContext) -> None:
    if update.message.text == settings.NEW_QUESTION_BUTTON:
        with open('test.json', 'r') as file:
            questions = json.load(file)
        
    context.bot.send_message(
        update.effective_chat.id,
        text=update.message.text
    )


def errors_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg='[TELEGRAM BOT ERROR]\n', exc_info=context.error)


def startbot(tg_bot_token: str):
    updater = Updater(token=tg_bot_token, use_context=True)

    updater.dispatcher.add_handler(
        CommandHandler(command='start', callback=start)
    )

    updater.dispatcher.add_handler(
        MessageHandler(filters=Filters.all, callback=message_handler)
    )

    updater.dispatcher.add_error_handler(errors_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    startbot(env.str('TELEGRAM_BOT_TOKEN'))