from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, ConversationHandler, CallbackQueryHandler
from environs import Env
import logging
import json
import settings
from redis import Redis
from random import choice
from difflib import SequenceMatcher

redis = Redis(host='localhost', port=6379, db=0)

logger = logging.getLogger('log.log')

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [settings.NEW_QUESTION_BUTTON, settings.GIVE_UP_BUTTON],
        [settings.SCORES_BUTTON]
    ],
    resize_keyboard=True
    )

CANCEL_INLINE_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text='Не хочу отвечать', callback_data='cancel')]]
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


def message_handler(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        update.effective_chat.id,
        text=update.message.text
    )

def send_answer(update: Update, context: CallbackContext) -> None:
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
        with open('new_test.json', 'r') as file:
            file_data = json.load(file)
        question = choice(file_data)["question"]
        redis.set(f'{update.effective_chat.id}_current_question', question)

    context.bot.send_message(
        update.effective_chat.id,
        text=question,
        reply_markup=CANCEL_INLINE_KEYBOARD
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


def check_answer(update: Update, context: CallbackContext) -> None:
    current_question = redis.get(
        f'{update.effective_chat.id}_current_question'
    )
    correct_answer = redis.get(current_question).decode('utf-8')
    clarified_answer = answer_clarify(correct_answer)
    print(clarified_answer)
    answer_ratio = SequenceMatcher(
        None,
        clarified_answer.lower(),
        update.message.text.lower()
    ).ratio()
    print(answer_ratio)
    if answer_ratio >= env.float('ANSWER_RATIO_BORDER'):
        context.bot.send_message(
            update.effective_chat.id,
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )
        redis.delete(f'{update.effective_chat.id}_current_question')
        return ConversationHandler.END
    else:
        context.bot.send_message(
            update.effective_chat.id,
            text='Неправильно… Попробуешь ещё раз?',
            reply_markup=CANCEL_INLINE_KEYBOARD
        )
        return 'GET_ANSWER'


def conversation_cancel(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        update.effective_chat.id,
        text='Ок',
    )
    return ConversationHandler.END


def errors_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg='[TELEGRAM BOT ERROR]\n', exc_info=context.error)


def startbot(tg_bot_token: str):
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
                    MessageHandler(Filters.text, check_answer)]
            },

            fallbacks=[
                CallbackQueryHandler(
                    callback=conversation_cancel,
                    pattern='cancel',
                )
            ]
        )
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