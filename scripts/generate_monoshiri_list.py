#!/usr/bin/env python3
"""
ものしりクイズ 300問一覧を CSV に書き出す (UTF-8 BOM付き)
列: ID, ジャンル, 年齢, 問題文, 選択肢1, 選択肢2, 選択肢3, 正解番号

Usage (project root から実行):
    python3 scripts/generate_monoshiri_list.py
"""
import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
GAME_DIR = os.path.join(PROJECT_ROOT, 'games', 'monoshiri-quiz')
DATA_DIR = os.path.join(GAME_DIR, 'data')
OUT_PATH = os.path.join(PROJECT_ROOT, 'docs', 'monoshiri-question-list.csv')


def main():
    with open(os.path.join(DATA_DIR, 'quiz_questions_300.json'), encoding='utf-8') as f:
        quiz = json.load(f)

    with open(os.path.join(DATA_DIR, 'monoshiri_age_map.json'), encoding='utf-8') as f:
        age_data = json.load(f)

    age_map = age_data['ageByQuestionId']
    cat_label = {c['id']: c['label'] for c in quiz['categories']}

    rows = []
    for q in quiz['questions']:
        choices = q['choices']
        correct_idx = next(
            (i + 1 for i, c in enumerate(choices) if c['id'] == q['correctChoiceId']), ''
        )
        rows.append([
            q['id'],
            cat_label.get(q['categoryId'], q['categoryId']),
            age_map.get(q['id'], ''),
            q['prompt'],
            choices[0]['label'] if len(choices) > 0 else '',
            choices[1]['label'] if len(choices) > 1 else '',
            choices[2]['label'] if len(choices) > 2 else '',
            correct_idx,
        ])

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'ジャンル', '年齢', '問題文', '選択肢1', '選択肢2', '選択肢3', '正解番号'])
        writer.writerows(rows)

    print(f'{len(rows)}問を書き出しました → {OUT_PATH}')


if __name__ == '__main__':
    main()
