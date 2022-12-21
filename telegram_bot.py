import logging
from functools import partial
from typing import Union
import os

from environs import Env
from redis.client import Redis
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


from bot_processing import (get_answer_and_status, increase_user_score,
                            is_correct_answer, logger)
from log_handlers import TelegramLogsHandler
import settings

PLATFORM = 'TELEGRAM'

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


def send_answer(redis_users: Redis,
                redis_questions: Redis,
                update: Update,
                context: CallbackContext) -> str:
    question, is_new = get_answer_and_status(
        update.effective_chat.id,
        PLATFORM,
        redis_users,
        redis_questions
    )
    if not is_new:
        context.bot.send_message(
            update.effective_chat.id,
            text='Вы еще не ответили на предыдущий вопрос.'
        )
    context.bot.send_message(
        update.effective_chat.id,
        text=question
    )
    return 'GET_ANSWER'


def change_question(redis_users: Redis,
                    redis_questions: Redis,
                    update: Update,
                    context: CallbackContext) -> None:
    current_question = redis_users.get(
        f'{PLATFORM}_{update.effective_chat.id}_current_question'
    )
    correct_answer = redis_questions.get(current_question) \
        .decode('utf-8')
    context.bot.send_message(
        update.effective_chat.id,
        text=f'Жаль, что не угадали.\n\nПравильный ответ:\n{correct_answer}',
    )
    redis_users.delete(
        f'{PLATFORM}_{update.effective_chat.id}_current_question'
    )
    return ConversationHandler.END


def show_score(redis_users: Redis,
               update: Update,
               context: CallbackContext) -> None:
    user_score = redis_users.get(
        f'{PLATFORM}_{update.effective_chat.id}_score'
    )
    if not user_score:
        context.bot.send_message(
            update.effective_chat.id,
            text='У вас пока ноль очков',
        )
    else:
        context.bot.send_message(
            update.effective_chat.id,
            text=f'Ваши очки: {user_score.decode("utf-8")}',
        )


def check_answer(redis_users: Redis,
                 redis_questions: Redis,
                 update: Update,
                 context: CallbackContext) -> Union[int, str]:
    current_question = redis_users.get(
        f'{PLATFORM}_{update.effective_chat.id}_current_question'
    )
    if is_correct_answer(redis_questions.get(current_question).decode('utf-8'),
                         update.message.text):
        redis_users.delete(
            f'{PLATFORM}_{update.effective_chat.id}_current_question'
        )
        increase_user_score(update.effective_chat.id, PLATFORM, redis_users)
        context.bot.send_message(
            update.effective_chat.id,
            text=(
                'Правильно! Поздравляю! '
                'Для следующего вопроса нажми «Новый вопрос»'
            )
        )

        return ConversationHandler.END
    else:
        context.bot.send_message(
            update.effective_chat.id,
            text='Неправильно… Попробуешь ещё раз?'
        )
        return 'GET_ANSWER'


def conversation_cancel(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(
        update.effective_chat.id,
        text='Ок',
    )
    return ConversationHandler.END


def errors_handler(update: Update, context: CallbackContext) -> None:
    logger.exception('[TELEGRAM BOT ERROR]')


def startbot(tg_bot_token: str) -> None:
    updater = Updater(token=tg_bot_token, use_context=True)

    redis_users = Redis(
        host=os.getenv('REDIS_HOST', settings.DEFAULT_REDIS_HOST),
        port=int(os.getenv('REDIS_PORT', settings.DEFAULT_REDIS_PORT)),
        password=os.getenv('REDIS_PASSWORD', settings.DEFAULT_REDIS_PASSWORD),
        db=settings.REDIS_DB_USERS
    )

    redis_questions = Redis(
        host=os.getenv('REDIS_HOST', settings.DEFAULT_REDIS_HOST),
        port=int(os.getenv('REDIS_PORT', settings.DEFAULT_REDIS_PORT)),
        password=os.getenv('REDIS_PASSWORD', settings.DEFAULT_REDIS_PASSWORD),
        db=settings.REDIS_DB_QUESTIONS
    )

    logger.setLevel(logging.INFO)
    logger.addHandler(
        TelegramLogsHandler(updater.bot, int(os.getenv('ADMIN_TELEGRAM_ID')))
    )
    logger.info('[TELEGRAM] Support bot started')

    updater.dispatcher.add_handler(
        CommandHandler(command='start', callback=start)
    )

    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    Filters.text([settings.NEW_QUESTION_BUTTON]),
                    partial(send_answer, redis_users, redis_questions)
                )
            ],

            states={
                'GET_ANSWER': [
                    MessageHandler(
                        Filters.text([settings.GIVE_UP_BUTTON]),
                        partial(change_question, redis_users, redis_questions)
                    ),
                    MessageHandler(
                        Filters.text([settings.SCORES_BUTTON]),
                        partial(show_score, redis_users)
                    ),
                    MessageHandler(
                        Filters.text,
                        partial(check_answer, redis_users, redis_questions)
                    )
                ]
            },

            fallbacks=[
                CommandHandler(
                    command='cancel',
                    callback=conversation_cancel,
                )
            ]
        )
    )

    updater.dispatcher.add_handler(
        MessageHandler(
            filters=Filters.text(settings.SCORES_BUTTON),
            callback=show_score
        )
    )

    updater.dispatcher.add_error_handler(errors_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    startbot(env.str('TELEGRAM_BOT_TOKEN'))
