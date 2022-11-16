import os

NEW_QUESTION_BUTTON = 'Новый вопрос'

GIVE_UP_BUTTON = 'Сдаться'

SCORES_BUTTON = 'Мой счет'

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')

REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

ANSWER_RATIO_BORDER = float(os.getenv('ANSWER_RATIO_BORDER'), 0.9)