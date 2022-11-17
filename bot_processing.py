import logging
from difflib import SequenceMatcher

from redis.client import Redis

import settings

logger = logging.getLogger('log.log')

redis_user = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB_QUESTIONS
)

redis_questions = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB_QUESTIONS
)


def get_answer_and_status(user_id: str,
                          platform: int) -> tuple[str, bool]:
    current_question = redis_user.get(
        f'{platform}_{user_id}_current_question'
    )
    if current_question:
        return current_question.decode('utf-8'), False
    else:
        question = redis_questions.randomkey().decode('utf-8')
        redis_user.set(
            f'{platform}_{user_id}_current_question',
            question
        )
        return question, True


def clarify_answer(answer: str,
                   clarify_params: list = (' - ', '. ', ' ('),
                   clean_params: list = ('...', '"')) -> str:
    for param in clean_params:
        answer = ''.join(answer.split(param))
    for param in clarify_params:
        answer = answer.split(param)[0]
    return answer.strip()


def increase_user_score(user_id: str,
                        platform: int) -> None:
    user_score = redis_user.get(f'{platform}_{user_id}_score')
    if not user_score:
        redis_user.set(f'{platform}_{user_id}_score', 1)
    else:
        redis_user.set(
            f'{platform}_{user_id}_score',
            int(user_score.decode('utf-8')) + 1
        )


def is_correct_answer(correct_answer: str,
                      user_answer: str,
                      answer_ratio_border: float = settings.ANSWER_RATIO_BORDER) -> bool:
    clarified_answer = clarify_answer(correct_answer)
    answer_ratio = SequenceMatcher(
        None,
        clarified_answer.lower(),
        user_answer.lower()
    ).ratio()
    return answer_ratio >= answer_ratio_border
