import os
from pathlib import Path
from tqdm import tqdm
from redis import Redis
from environs import Env
import json


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
    env = Env()
    env.read_env()

    redis = Redis(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASSWORD', None),
        db=0
    )
    questions = parse_questions_files()
    listed_questions = list()
    for item in tqdm(questions, desc='add questions to redis'):
        redis.set(item['question'], item['answer'])
        listed_questions.append({
            'question': item['question'],
            'answer': item['answer']
        })
        try:
            assert redis.get(item['question']).decode('utf-8') == item['answer']
        except AssertionError:
            import sys
            sys.stdout.write(
                f"""
                ASSERTION ERROR
                
                Answer in file:
                {item['answer']}

                Answer in Redis:
                {redis.get(item['question']).decode('utf-8')}
                """
            )
    with open('questions.json', 'w') as file:
        json.dump(listed_questions, file, indent=4, ensure_ascii=False)