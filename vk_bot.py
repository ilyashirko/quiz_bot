import logging
import random

import vk_api as vk
from environs import Env
from telegram import Bot
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import Event, VkChatEventType, VkEventType, VkLongPoll

import settings
from bot_processing import (get_answer_and_status, increase_user_score,
                            is_correct_answer, logger, questions, redis)
from log_handlers import TelegramLogsHandler

PLATFORM = 'VK'


def get_main_keyboard() -> VkKeyboard:
    keyboard = VkKeyboard()
    keyboard.add_button(settings.NEW_QUESTION_BUTTON)
    keyboard.add_button(settings.GIVE_UP_BUTTON)
    keyboard.add_line()
    keyboard.add_button(settings.SCORES_BUTTON)
    return keyboard.get_keyboard()


def message_handler(event: Event, vk_api: vk.vk_api.VkApiMethod) -> None:
    print(event.message_flags)
    print(event.type)
    input(dir(event))
    if event.text == settings.NEW_QUESTION_BUTTON:
        question, wasnt_answered = get_answer_and_status(
            redis,
            event.user_id,
            questions,
            PLATFORM
        )
        if wasnt_answered:
            vk_api.messages.send(
                user_id=event.user_id,
                message='Вы еще не ответили на предыдущий вопрос.',
                random_id=random.randint(1, 1000),
                keyboard=get_main_keyboard()
            )
        vk_api.messages.send(
            user_id=event.user_id,
            message=question,
            random_id=random.randint(1, 1000),
            keyboard=get_main_keyboard()
        )
    elif event.text == settings.GIVE_UP_BUTTON:
        current_question = redis.get(
            f'{PLATFORM}_{event.user_id}_current_question'
        )
        correct_answer = redis.get(current_question).decode('utf-8')
        vk_api.messages.send(
            user_id=event.user_id,
            message=f'Жаль, что не угадали.\n\nПравильный ответ:\n{correct_answer}',
            random_id=random.randint(1, 1000),
            keyboard=get_main_keyboard()
        )
        redis.delete(f'{PLATFORM}_{event.user_id}_current_question')
    elif event.text == settings.SCORES_BUTTON:
        user_score = redis.get(f'{PLATFORM}_{event.user_id}_score')
        if not user_score:
            vk_api.messages.send(
                user_id=event.user_id,
                message='У вас пока ноль очков',
                random_id=random.randint(1, 1000),
                keyboard=get_main_keyboard()
            )
        else:
            vk_api.messages.send(
                user_id=event.user_id,
                message=f'Ваши очки: {user_score.decode("utf-8")}',
                random_id=random.randint(1, 1000),
                keyboard=get_main_keyboard()
            )
    else:
        current_question = redis.get(f'{PLATFORM}_{event.user_id}_current_question')
        if not current_question:
            return
        if is_correct_answer(redis.get(current_question).decode('utf-8'),
                             event.message):
            redis.delete(f'{PLATFORM}_{event.user_id}_current_question')
            increase_user_score(redis, event.user_id, PLATFORM)
            vk_api.messages.send(
                user_id=event.user_id,
                message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
                random_id=random.randint(1, 1000),
                keyboard=get_main_keyboard()
            )
        else:
            vk_api.messages.send(
                user_id=event.user_id,
                message='Неправильно… Попробуешь ещё раз?',
                random_id=random.randint(1, 1000),
                keyboard=get_main_keyboard()
            )


def run_vk_bot(vk_bot_token: str) -> None:
    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    logger.setLevel(logging.INFO)
    logger.addHandler(
        TelegramLogsHandler(
            Bot(env.str('TELEGRAM_BOT_TOKEN')), env.int('ADMIN_TELEGRAM_ID')
        )
    )
    logger.info('[VK] Support bot started')

    try:
        for event in longpoll.listen():
            print(event.type)
            if event.type == VkChatEventType.USER_JOINED:
                input('yeah')
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                message_handler(event, vk_api)

    except Exception as error:
        logger.error(msg='[VK BOT ERROR]\n', exc_info=error)


if __name__ == '__main__':
    env = Env()
    env.read_env()

    run_vk_bot(env.str('VK_BOT_TOKEN'))
