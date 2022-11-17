import os
from argparse import ArgumentParser
from pathlib import Path

from redis.client import Redis
from tqdm import tqdm

import settings


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Create redis with questions"
    )
    parser.add_argument(
        '--dir_with_txt',
        '-d',
        type=str,
        help='dir with questions txt files',
        required=True
    )
    return parser


def parse_questions_files(files_dir: str) -> list:
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
    args = create_parser().parse_args()

    redis_questions = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB_QUESTIONS
    )
    questions = parse_questions_files(args.dir_with_txt)
    
    for item in tqdm(questions, desc='add questions to redis'):
        redis_questions.set(item['question'], item['answer'])
