import logging
from typing import Union

from environs import Env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

import settings
from bot_processing import (get_answer_and_status, increase_user_score,
                            is_correct_answer, logger, questions, redis)
from log_handlers import TelegramLogsHandler

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


def send_answer(update: Update, context: CallbackContext) -> str:
    question, wasnt_answered = get_answer_and_status(
        redis,
        update.effective_chat.id,
        questions,
        PLATFORM
    )
    if wasnt_answered:
        context.bot.send_message(
            update.effective_chat.id,
            text='Вы еще не ответили на предыдущий вопрос.'
        )
    context.bot.send_message(
        update.effective_chat.id,
        text=question
    )
    return 'GET_ANSWER'


def change_question(update: Update, context: CallbackContext) -> None:
    current_question = redis.get(
        f'{PLATFORM}_{update.effective_chat.id}_current_question'
    )
    correct_answer = redis.get(current_question).decode('utf-8')
    context.bot.send_message(
        update.effective_chat.id,
        text=f'Жаль, что не угадали.\n\nПравильный ответ:\n{correct_answer}',
    )
    redis.delete(f'{PLATFORM}_{update.effective_chat.id}_current_question')
    return ConversationHandler.END


def show_score(update: Update, context: CallbackContext) -> None:
    user_score = redis.get(f'{PLATFORM}_{update.effective_chat.id}_score')
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


def check_answer(update: Update, context: CallbackContext) -> Union[int, str]:
    current_question = redis.get(
        f'{PLATFORM}_{update.effective_chat.id}_current_question'
    )
    if is_correct_answer(redis.get(current_question).decode('utf-8'),
                         update.message.text,
                         env.float('ANSWER_RATIO_BORDER')):
        redis.delete(f'{PLATFORM}_{update.effective_chat.id}_current_question')
        increase_user_score(redis, update.effective_chat.id, PLATFORM)
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
    logger.error(msg='[TELEGRAM BOT ERROR]\n', exc_info=context.error)


def startbot(tg_bot_token: str) -> None:
    updater = Updater(token=tg_bot_token, use_context=True)

    logger.setLevel(logging.INFO)
    logger.addHandler(
        TelegramLogsHandler(updater.bot, env.int('ADMIN_TELEGRAM_ID'))
    )
    logger.info('[TELEGRAM] Support bot started')

    updater.dispatcher.add_handler(
        CommandHandler(command='start', callback=start)
    )

    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters=Filters.text([settings.NEW_QUESTION_BUTTON]), 
                    callback=send_answer
                )
            ],

            states={
                'GET_ANSWER': [
                    MessageHandler(
                        Filters.text([settings.GIVE_UP_BUTTON]),
                        change_question
                    ),
                    MessageHandler(
                        Filters.text([settings.SCORES_BUTTON]),
                        show_score
                    ),
                    MessageHandler(Filters.text, check_answer)]
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