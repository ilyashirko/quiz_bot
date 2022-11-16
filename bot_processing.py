import json
import logging
from difflib import SequenceMatcher
from random import choice

from redis.client import Redis

import settings

redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    password=settings.REDIS_PASSWORD
)

logger = logging.getLogger('log.log')

with open('questions.json', 'r') as file:
    questions = json.load(file)


def get_answer_and_status(redis: Redis,
                          user_tg_id: str,
                          questions: list,
                          platform: int) -> tuple[str, bool]:
    current_question = redis.get(
        f'{platform}_{user_tg_id}_current_question'
    )
    if current_question:
        return current_question.decode('utf-8'), True
    else:
        question = choice(questions)["question"]
        redis.set(f'{platform}_{user_tg_id}_current_question', question)
        return question, False


def answer_clarify(answer: str,
                   clarify_params: list = (' - ', '. ', ' ('),
                   clean_params: list = ('...', '"')) -> str:
    for param in clean_params:
        answer = ''.join(answer.split(param))
    for param in clarify_params:
        answer = answer.split(param)[0]
    return answer.strip()


def increase_user_score(redis: Redis,
                        user_id: str,
                        platform: int) -> None:
    user_score = redis.get(f'{platform}_{user_id}_score')
    if not user_score:
        redis.set(f'{platform}_{user_id}_score', 1)
    else:
        redis.set(
            f'{platform}_{user_id}_score',
            int(user_score.decode('utf-8')) + 1
        )


def is_correct_answer(correct_answer: str,
                      user_answer: str,
                      answer_ratio_border: float = settings.ANSWER_RATIO_BORDER) -> bool:
    clarified_answer = answer_clarify(correct_answer)
    answer_ratio = SequenceMatcher(
        None,
        clarified_answer.lower(),
        user_answer.lower()
    ).ratio()
    return answer_ratio >= answer_ratio_border
