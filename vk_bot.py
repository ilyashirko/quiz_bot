import logging
import random

import vk_api as vk
from environs import Env
from telegram import Bot
from vk_api.longpoll import Event, VkEventType, VkLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from log_handlers import TelegramLogsHandler
import settings

logger = logging.getLogger('log.log')


def get_main_keyboard() -> VkKeyboard:
    keyboard = VkKeyboard()
    keyboard.add_button(settings.NEW_QUESTION_BUTTON)
    keyboard.add_button(settings.GIVE_UP_BUTTON)
    keyboard.add_line()
    keyboard.add_button(settings.SCORES_BUTTON)
    return keyboard


def message_handler(event: Event, vk_api: vk.vk_api.VkApiMethod) -> None:
    if event.text == settings.NEW_QUESTION_BUTTON:
        pass
    elif event.text == settings.GIVE_UP_BUTTON:
        pass
    elif event.text == settings.SCORES_BUTTON:
        pass
    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text,
        random_id=random.randint(1,1000),
        keyboard=get_main_keyboard().get_keyboard()
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
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                message_handler(event, vk_api)
    except Exception as error:
        logger.error(msg='[VK BOT ERROR]\n', exc_info=error)


if __name__ == '__main__':
    env = Env()
    env.read_env()
    
    run_vk_bot(env.str('VK_BOT_TOKEN'))
