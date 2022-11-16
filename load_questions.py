import os
from pathlib import Path

from redis.client import Redis
from tqdm import tqdm

import settings


def parse_questions_files(files_dir: str = 'quiz-questions') -> list:
    questions_filenames = os.listdir(files_dir)

    questions = list()

    for filename in tqdm(questions_filenames, desc='parse questions files'):

        with open(Path(files_dir, filename), 'r', encoding='koi8-r') as file:
            dirty_questions = file.read()

        paragraphs = dirty_questions.split('\n\n')

        for next_paragraph_index, paragraph in enumerate(paragraphs, 1):
            if paragraph.strip().find('Вопрос') != 0:
                continue

            question = paragraph[paragraph.find(':\n') + 2:]

            next_paragraph = paragraphs[next_paragraph_index]

            answer = next_paragraph[next_paragraph.find(':\n') + 2:-1]

            questions.append({
                'question': question,
                'answer': answer
            })

    return questions


if __name__ == '__main__':
    redis_questions = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB_QUESTIONS
    )
    questions = parse_questions_files()
    listed_questions = list()

    for num, item in tqdm(questions, desc='add questions to redis'):
        redis_questions.set(item['question'], item['answer'])
