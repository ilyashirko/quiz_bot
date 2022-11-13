import json
import logging
from difflib import SequenceMatcher
from random import choice
from typing import Union

import settings
from environs import Env
from redis import Redis
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

redis = Redis(host='localhost', port=6379, db=0)

logger = logging.getLogger('log.log')

with open('new_test.json', 'r') as file:
    questions = json.load(file)

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


def answer_clarify(answer: str,
                   clarify_params: list = (' - ', '. ', ' ('),
                   clean_params: list = ('...', '"')) -> str:
    for param in clean_params:
        answer = ''.join(answer.split(param))
    for param in clarify_params:
        answer = answer.split(param)[0]
    return answer.strip()


def send_answer(update: Update, context: CallbackContext) -> str:
    current_question = redis.get(
        f'{update.effective_chat.id}_current_question'
    )
    if current_question:
        context.bot.send_message(
            update.effective_chat.id,
            text='Вы еще не ответили на предыдущий вопрос.'
        )
        question = current_question.decode('utf-8')
    else:
        
        question = choice(questions)["question"]
        redis.set(f'{update.effective_chat.id}_current_question', question)

    context.bot.send_message(
        update.effective_chat.id,
        text=question
    )
    return 'GET_ANSWER'


def change_question(update: Update, context: CallbackContext) -> None:
    current_question = redis.get(
        f'{update.effective_chat.id}_current_question'
    )
    correct_answer = redis.get(current_question).decode('utf-8')
    context.bot.send_message(
        update.effective_chat.id,
        text=f'Жаль, что не угадали.\n\nПравильный ответ:\n{correct_answer}',
    )
    redis.delete(f'{update.effective_chat.id}_current_question')
    send_answer(update, context)


def show_score(update: Update, context: CallbackContext) -> None:
    user_score = redis.get(f'{update.effective_chat.id}_score')
    if not user_score:
        context.bot.send_message(
            update.effective_chat.id,
            text=f'У вас пока ноль очков',
        )
    else:
        context.bot.send_message(
            update.effective_chat.id,
            text=f'Ваши очки: {user_score.decode("utf-8")}',
        )


def check_answer(update: Update, context: CallbackContext) -> Union[int, str]:
    current_question = redis.get(
        f'{update.effective_chat.id}_current_question'
    )
    
    correct_answer = redis.get(current_question).decode('utf-8')
    clarified_answer = answer_clarify(correct_answer)
    
    answer_ratio = SequenceMatcher(
        None,
        clarified_answer.lower(),
        update.message.text.lower()
    ).ratio()
    if answer_ratio >= env.float('ANSWER_RATIO_BORDER'):
        context.bot.send_message(
            update.effective_chat.id,
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )
        redis.delete(f'{update.effective_chat.id}_current_question')

        user_score = redis.get(f'{update.effective_chat.id}_score')
        if not user_score:
            redis.set(f'{update.effective_chat.id}_score', 1)
        else:
            redis.set(
                f'{update.effective_chat.id}_score',
                int(user_score.decode('utf-8')) + 1
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