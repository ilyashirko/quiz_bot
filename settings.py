from environs import Env

env = Env().read_env()

TELEGRAM_BOT_TOKEN = env.str('TELEGRAM_BOT_TOKEN')

ADMIN_TELEGRAM_ID = env.int('ADMIN_TELEGRAM_ID')

VK_BOT_TOKEN = env.str('VK_BOT_TOKEN')

REDIS_HOST = env.str('REDIS_HOST', 'localhost')

REDIS_PORT = env.int('REDIS_PORT', 6379)

REDIS_PASSWORD = env.str('REDIS_PASSWORD', None)

REDIS_DB_QUESTIONS = 0

REDIS_DB_USERS = 1

ANSWER_RATIO_BORDER = env.float('ANSWER_RATIO_BORDER', 0.9)

NEW_QUESTION_BUTTON = 'Новый вопрос'

GIVE_UP_BUTTON = 'Сдаться'

SCORES_BUTTON = 'Мой счет'
