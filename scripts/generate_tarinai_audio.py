#!/usr/bin/env python3
"""
Generate VOICEVOX audio files for たりないかず.
話者: ずんだもん (あまあまスタイル)

Usage (run from project root):
    python3 scripts/generate_tarinai_audio.py --test
        -> games/tarinai-kazu/audio/test/ にテスト音声を生成して確認
    python3 scripts/generate_tarinai_audio.py
        -> games/tarinai-kazu/audio/ に本生成
"""
import argparse
import json
import os
import urllib.parse
import urllib.request
import subprocess

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
AUDIO_DIR    = os.path.join(PROJECT_ROOT, 'games', 'tarinai-kazu', 'audio')
TEST_DIR     = os.path.join(AUDIO_DIR, 'test')

SPEED = 0.95
PITCH = 0.04
INTON = 1.2

# 全レベルで使う (total, have) の組み合わせ
# ファイル名: q_{total}_{have}.wav
# テキスト: "ぜんぶで {total} こ。いま {have} こ。あと いくつ。"
QUESTION_PAIRS = [
    # N=3: missing 1-2
    (3, 2), (3, 1),
    # N=4: missing 1-2
    (4, 3), (4, 2),
    # N=5: missing 1-3
    (5, 4), (5, 3), (5, 2),
    # N=6: missing 1-3
    (6, 5), (6, 4), (6, 3),
    # N=7: missing 1-4
    (7, 6), (7, 5), (7, 4), (7, 3),
    # N=8: missing 1-4
    (8, 7), (8, 6), (8, 5), (8, 4),
    # N=9: missing 1-4
    (9, 8), (9, 7), (9, 6), (9, 5),
    # N=10: missing 1-4
    (10, 9), (10, 8), (10, 7), (10, 6),
]

FILES = (
    [(f'q_{n}_{m}', f'ぜんぶで {n} こ。いま {m} こ。あと いくつ。')
     for n, m in QUESTION_PAIRS]
)


def _windows_host_ip():
    try:
        out = subprocess.check_output(['ip', 'route', 'show'], text=True)
        for line in out.splitlines():
            if line.startswith('default'):
                return line.split()[2]
    except Exception:
        pass
    return ''


def _voicevox_base():
    ip = _windows_host_ip()
    for host in ([f'http://{ip}:50022'] if ip else []) + ['http://localhost:50022']:
        try:
            urllib.request.urlopen(host + '/version', timeout=3)
            return host
        except Exception:
            continue
    raise RuntimeError('VOICEVOX に接続できません。VOICEVOXが起動しているか確認してください。')


def _speaker_id(base):
    with urllib.request.urlopen(base + '/speakers', timeout=10) as r:
        speakers = json.loads(r.read())
    for spk in speakers:
        if 'ずんだもん' in spk['name']:
            for style in spk['styles']:
                if 'あまあま' in style['name']:
                    return style['id']
            return spk['styles'][0]['id']
    raise RuntimeError('「ずんだもん」が見つかりません。')


def synthesize(base, text, speaker_id, out_path):
    qs = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = urllib.request.Request(
        f'{base}/audio_query?{qs}', data=b'',
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        query = json.loads(r.read())

    query['speedScale']       = SPEED
    query['pitchScale']       = PITCH
    query['intonationScale']  = INTON
    query['prePhonemeLength'] = 0.3
    for ap in query['accent_phrases']:
        ap['is_interrogative'] = False
    first = query['accent_phrases'][0]
    if first.get('pause_mora'):
        first['pause_mora']['vowel_length'] = 0.70

    qs2  = urllib.parse.urlencode({'speaker': speaker_id})
    body = json.dumps(query, ensure_ascii=False).encode('utf-8')
    req2 = urllib.request.Request(
        f'{base}/synthesis?{qs2}', data=body,
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req2, timeout=30) as r:
        wav = r.read()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(wav)
    print(f'  -> {os.path.relpath(out_path, PROJECT_ROOT)}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true',
                        help='テスト用に audio/test/ に出力')
    parser.add_argument('--only', default='',
                        help='カンマ区切りのファイル名(拡張子なし)だけ生成。例: q_3_2,q_5_3')
    args = parser.parse_args()

    only_set = set(args.only.split(',')) if args.only else set()

    base       = _voicevox_base()
    speaker_id = _speaker_id(base)
    print(f'VOICEVOX: {base}  speaker_id={speaker_id}')

    out_dir = TEST_DIR if args.test else AUDIO_DIR
    for fname, text in FILES:
        if only_set and fname not in only_set:
            continue
        out_path = os.path.join(out_dir, fname + '.wav')
        print(f'生成中: {fname}.wav  「{text}」')
        synthesize(base, text, speaker_id, out_path)

    print(f'完了。({len([f for f, _ in FILES if not only_set or f in only_set])} ファイル)')


if __name__ == '__main__':
    main()
