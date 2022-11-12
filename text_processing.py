import os
import json
from pathlib import Path
from tqdm import tqdm


def parse_questions_files(files_dir: str = 'quiz-questions') -> list:
    questions_filenames = os.listdir(files_dir)

    questions = list()

    for filename in tqdm(questions_filenames):
        
        with open(Path(files_dir, filename), 'r', encoding='koi8-r') as file:
            dirty_questions = file.read()

        paragraphs = dirty_questions.split('\n\n')

        for next_paragraph_index, paragraph in enumerate(paragraphs, 1):
            if paragraph.strip().find('Вопрос') != 0:
                continue

            question = paragraph[paragraph.find(':\n') + 2 :]

            next_paragraph = paragraphs[next_paragraph_index]
            
            answer = next_paragraph[next_paragraph.find(':\n') + 2:]
            
            questions.append({
                'question': question,
                'answer': answer
            })

    return questions


def save_questions(questions: json) -> None:
    
    with open('test.json', 'w') as json_file:
        json.dump(questions, json_file, indent=4, ensure_ascii=False)
