import logging
import random
import os

import vk_api as vk
from environs import Env
from redis.client import Redis
from telegram import Bot
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import Event, VkEventType, VkLongPoll


from bot_processing import (get_answer_and_status, increase_user_score,
                            is_correct_answer, logger)
import settings
from log_handlers import TelegramLogsHandler

PLATFORM = 'VK'


def get_main_keyboard() -> VkKeyboard:
    keyboard = VkKeyboard()
    keyboard.add_button(settings.NEW_QUESTION_BUTTON)
    keyboard.add_button(settings.GIVE_UP_BUTTON)
    keyboard.add_line()
    keyboard.add_button(settings.SCORES_BUTTON)
    return keyboard.get_keyboard()


def send_answer(event: Event,
                vk_api: vk.vk_api.VkApiMethod,
                redis_users: Redis,
                redis_questions: Redis) -> None:
    question, is_new = get_answer_and_status(
        event.user_id,
        PLATFORM,
        redis_users,
        redis_questions
    )
    if not is_new:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Вы еще не ответили на предыдущий вопрос.',
            random_id=random.randint(1, 1000)
        )
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=random.randint(1, 1000)
    )


def give_up(event: Event,
            vk_api: vk.vk_api.VkApiMethod,
            redis_users: Redis,
            redis_questions: Redis) -> None:
    current_question = redis_users.get(
        f'{PLATFORM}_{event.user_id}_current_question'
    )
    correct_answer = redis_questions.get(current_question).decode('utf-8')
    vk_api.messages.send(
        user_id=event.user_id,
        message=f'Жаль, что не угадали.\n\nПравильный ответ:\n{correct_answer}',
        random_id=random.randint(1, 1000)
    )
    redis_users.delete(f'{PLATFORM}_{event.user_id}_current_question')


def send_user_scores(event: Event,
                     vk_api: vk.vk_api.VkApiMethod,
                     redis_users: Redis) -> None:
    user_score = redis_users.get(f'{PLATFORM}_{event.user_id}_score')
    if not user_score:
        vk_api.messages.send(
            user_id=event.user_id,
            message='У вас пока ноль очков',
            random_id=random.randint(1, 1000)
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            message=f'Ваши очки: {user_score.decode("utf-8")}',
            random_id=random.randint(1, 1000)
        )


def message_handler(event: Event,
                    vk_api: vk.vk_api.VkApiMethod,
                    redis_users: Redis,
                    redis_questions: Redis) -> None:
    current_question = redis_users.get(
        f'{PLATFORM}_{event.user_id}_current_question'
    )
    if not current_question:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Привет!',
            random_id=random.randint(1, 1000),
            keyboard=get_main_keyboard()
        )
        return
    if is_correct_answer(redis_questions.get(current_question).decode('utf-8'),
                         event.message):
        redis_users.delete(f'{PLATFORM}_{event.user_id}_current_question')
        increase_user_score(event.user_id, PLATFORM, redis_users)
        vk_api.messages.send(
            user_id=event.user_id,
            message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            random_id=random.randint(1, 1000)
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Неправильно… Попробуешь ещё раз?',
            random_id=random.randint(1, 1000)
        )


def run_vk_bot(vk_bot_token: str) -> None:
    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

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
        TelegramLogsHandler(
            Bot(os.getenv('TELEGRAM_BOT_TOKEN')),
            int(os.getenv('ADMIN_TELEGRAM_ID'))
        )
    )
    logger.info('[VK] Support bot started')

    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == settings.NEW_QUESTION_BUTTON:
                    send_answer(event, vk_api, redis_users, redis_questions)
                elif event.text == settings.GIVE_UP_BUTTON:
                    give_up(event, vk_api, redis_users, redis_questions)
                elif event.text == settings.SCORES_BUTTON:
                    send_user_scores(event, vk_api, redis_users)
                else:
                    message_handler(
                        event,
                        vk_api,
                        redis_users,
                        redis_questions
                    )

    except Exception:
        logger.exception('[VK BOT ERROR]')


if __name__ == '__main__':
    env = Env()
    env.read_env()
    
    run_vk_bot(os.getenv('VK_BOT_TOKEN'))
