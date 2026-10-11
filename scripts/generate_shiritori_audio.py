#!/usr/bin/env python3
"""
Generate VOICEVOX audio files for しりとりゲーム.
話者: ずんだもん (あまあまスタイル)

Usage (run from project root):
    python3 scripts/generate_shiritori_audio.py --test
        -> games/shiritori/audio/test/ にテスト音声を生成

    python3 scripts/generate_shiritori_audio.py
        -> words/ と questions/ に全ファイルを生成 (生成済みはスキップ)

    python3 scripts/generate_shiritori_audio.py --force
        -> words/ と questions/ を強制上書き生成

VOICEVOX must be running on Windows (port 50022).
WSL: Windows host IP is resolved dynamically via `ip route show`.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# VOICEVOX 接続
# ---------------------------------------------------------------------------

def _windows_host_ip():
    # type: () -> str
    try:
        out = subprocess.check_output(['ip', 'route', 'show'], text=True)
        for line in out.splitlines():
            if line.startswith('default'):
                return line.split()[2]
    except Exception:
        pass
    return ''


_host_ip = _windows_host_ip()
HOSTS = (
    [f'http://{_host_ip}:50022', 'http://localhost:50022'] if _host_ip
    else ['http://localhost:50022']
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
GAME_DIR = os.path.join(PROJECT_ROOT, 'games', 'shiritori')
DATA_DIR = os.path.join(GAME_DIR, 'data')
AUDIO_DIR = os.path.join(GAME_DIR, 'audio')
WORDS_DIR = os.path.join(AUDIO_DIR, 'words')
QUESTIONS_DIR = os.path.join(AUDIO_DIR, 'questions')
TEST_DIR = os.path.join(AUDIO_DIR, 'test')


# ---------------------------------------------------------------------------
# 品質設定
# ---------------------------------------------------------------------------

SPEED = 0.95
PITCH = 0.04
INTON = 1.2

# ポーズ長 (秒)
PAUSE_LEAD  = 0.70   # 冒頭ポーズ
PAUSE_KUTEN = 0.45   # 句点後(文の途中)
PAUSE_TOTEN = 0.60   # 読点後
PAUSE_END   = 0.50   # 文末


# ---------------------------------------------------------------------------
# VOICEVOX API
# ---------------------------------------------------------------------------

def find_host():
    # type: () -> Optional[str]
    for host in HOSTS:
        try:
            with urllib.request.urlopen(host + '/version', timeout=5) as r:
                ver = r.read().decode().strip().strip('"')
            print(f'VOICEVOX {ver} @ {host}')
            return host
        except Exception:
            continue
    return None


def api_get(base, path):
    with urllib.request.urlopen(base + path, timeout=10) as r:
        return json.loads(r.read())


def find_speaker_id(base):
    speakers = api_get(base, '/speakers')
    for spk in speakers:
        if 'ずんだもん' in spk['name']:
            for style in spk['styles']:
                if 'あまあま' in style['name']:
                    return style['id']
            return spk['styles'][0]['id']
    raise RuntimeError('「ずんだもん」が見つかりません。VOICEVOXのバージョンを確認してください。')


def _set_sentence_pauses(query, text):
    # type: (dict, str) -> None
    """
    文の途中の句点(0.45)・読点(0.60)・文末(0.50)を accent_phrases に適用する。
    先頭の pause_mora は冒頭ポーズとして別途処理済み。
    """
    # テキストから句読点を収集 (最後の句点は文末)
    punct_list = [ch for ch in text if ch in ('。', '、')]

    # 最後が '。' → 文末としてpostPhonemeLength に反映し、リストから除外
    if punct_list and punct_list[-1] == '。':
        punct_list = punct_list[:-1]
        query['postPhonemeLength'] = PAUSE_END

    durations = [PAUSE_KUTEN if ch == '。' else PAUSE_TOTEN for ch in punct_list]

    # 先頭以外で pause_mora を持つ accent_phrase に順番に適用
    non_lead = [ap for i, ap in enumerate(query['accent_phrases'])
                if i > 0 and ap.get('pause_mora')]

    for i, ap in enumerate(non_lead):
        if i < len(durations):
            ap['pause_mora']['vowel_length'] = durations[i]


def synthesize(base, text, speaker_id, out_path, is_word=False):
    # type: (str, str, int, str, bool) -> dict
    """テキストを合成して wav に保存し、使用した query を返す (検証用)。"""
    qs = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = urllib.request.Request(
        f'{base}/audio_query?{qs}',
        data=b'',
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        query = json.loads(r.read())

    query['speedScale']       = SPEED
    query['pitchScale']       = PITCH
    query['intonationScale']  = INTON
    query['prePhonemeLength'] = 0.3

    for ap in query['accent_phrases']:
        ap['is_interrogative'] = False

    # 冒頭ポーズ 0.70 秒
    first = query['accent_phrases'][0]
    if first.get('pause_mora'):
        first['pause_mora']['vowel_length'] = PAUSE_LEAD

    if not is_word:
        _set_sentence_pauses(query, text)

    qs2 = urllib.parse.urlencode({'speaker': speaker_id})
    body = json.dumps(query, ensure_ascii=False).encode('utf-8')
    req2 = urllib.request.Request(
        f'{base}/synthesis?{qs2}',
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req2, timeout=30) as r:
        wav = r.read()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(wav)

    return query


# ---------------------------------------------------------------------------
# データ読み込み
# ---------------------------------------------------------------------------

def load_words():
    # type: () -> list
    with open(os.path.join(DATA_DIR, 'words.json'), encoding='utf-8') as f:
        data = json.load(f)
    return data['words']


def build_question_text(word, last_sound):
    # type: (str, str) -> str
    return f'{word}。さいごのおとは {last_sound}。{last_sound}、からはじまるのはどれかな。'


def get_question_words(words):
    # type: (list) -> list
    """lastSound が別の単語の firstSound と一致する単語 (= お題になれる単語) を返す。"""
    first_sounds = set(w['firstSound'] for w in words)
    return [w for w in words if w['lastSound'] in first_sounds]


# ---------------------------------------------------------------------------
# バッチ生成
# ---------------------------------------------------------------------------

def run_words(base, speaker_id, words, out_dir, skip_existing):
    # type: (str, int, list, str, bool) -> Tuple[int, List[str]]
    os.makedirs(out_dir, exist_ok=True)
    errors = []
    skipped = 0
    total = len(words)
    for i, w in enumerate(words, 1):
        fname = w['id'] + '.wav'
        out_path = os.path.join(out_dir, fname)
        if skip_existing and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f'[{i:2d}/{total}] words/{fname}  SKIP')
            skipped += 1
            continue
        print(f'[{i:2d}/{total}] words/{fname}  "{w["word"]}"', end=' ', flush=True)
        try:
            synthesize(base, w['word'], speaker_id, out_path, is_word=True)
            print('OK')
        except Exception as e:
            print(f'FAILED: {e}')
            errors.append(fname)
        time.sleep(0.05)
    if skipped:
        print(f'  (スキップ: {skipped}本 既存)')
    return total - len(errors) - skipped, errors


def run_questions(base, speaker_id, q_words, out_dir, skip_existing, sample_ids=None):
    # type: (str, int, list, str, bool, Optional[list]) -> Tuple[int, List[str], list]
    """
    question sentences を生成する。
    sample_ids: 検証用に query を返す単語 ID のリスト (None=全件スキップ)
    戻り値: (生成数, エラー一覧, [(id, query), ...])
    """
    os.makedirs(out_dir, exist_ok=True)
    errors = []
    skipped = 0
    total = len(q_words)
    sample_queries = []

    for i, w in enumerate(q_words, 1):
        fname = w['id'] + '.wav'
        out_path = os.path.join(out_dir, fname)
        text = build_question_text(w['word'], w['lastSound'])
        if skip_existing and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f'[{i:2d}/{total}] questions/{fname}  SKIP')
            skipped += 1
            continue
        print(f'[{i:2d}/{total}] questions/{fname}  "{text}"', end=' ', flush=True)
        try:
            q = synthesize(base, text, speaker_id, out_path, is_word=False)
            print('OK')
            if sample_ids and w['id'] in sample_ids:
                sample_queries.append((w['id'], text, q))
        except Exception as e:
            print(f'FAILED: {e}')
            errors.append(fname)
        time.sleep(0.05)
    if skipped:
        print(f'  (スキップ: {skipped}本 既存)')
    return total - len(errors) - skipped, errors, sample_queries


# ---------------------------------------------------------------------------
# ポーズ検証レポート
# ---------------------------------------------------------------------------

def print_pause_report(sample_queries):
    # type: (list) -> None
    """合成クエリから実際のポーズ値を出力する。"""
    print('\n--- ポーズ値サンプル (検証用) ---')
    for wid, text, query in sample_queries:
        print(f'\n  [{wid}] "{text}"')
        pauses_with_mora = [(i, ap) for i, ap in enumerate(query['accent_phrases'])
                            if ap.get('pause_mora')]
        for idx, (i, ap) in enumerate(pauses_with_mora):
            role = '冒頭' if idx == 0 else f'pause {idx}'
            val = ap['pause_mora']['vowel_length']
            print(f'    phrase[{i}] {role}: pause_mora.vowel_length = {val:.3f}s')
        print(f'    postPhonemeLength = {query.get("postPhonemeLength", 0):.3f}s')


# ---------------------------------------------------------------------------
# メインロジック
# ---------------------------------------------------------------------------

def _run_test(base, speaker_id, words):
    # type: (str, int, list) -> None
    print('=== テスト生成 ===')
    print(f'出力先: {TEST_DIR}\n')

    q_words = get_question_words(words)
    # 単語サンプル 3 本
    word_samples = words[:3]
    print('--- 単語サンプル ---')
    for w in word_samples:
        fname = f'test_word_{w["id"]}.wav'
        out_path = os.path.join(TEST_DIR, fname)
        print(f'  {fname}  "{w["word"]}"', end=' ', flush=True)
        synthesize(base, w['word'], speaker_id, out_path, is_word=True)
        print('OK')

    # 問題文サンプル 3 本 (先頭3語)
    q_samples = q_words[:3]
    print('\n--- 問題文サンプル ---')
    sample_queries = []
    for w in q_samples:
        fname = f'test_q_{w["id"]}.wav'
        out_path = os.path.join(TEST_DIR, fname)
        text = build_question_text(w['word'], w['lastSound'])
        print(f'  {fname}  "{text}"', end=' ', flush=True)
        q = synthesize(base, text, speaker_id, out_path, is_word=False)
        sample_queries.append((w['id'], text, q))
        print('OK')

    print_pause_report(sample_queries)
    print(f'\n完了 → {TEST_DIR}/')


def _run_full(base, speaker_id, words, force):
    # type: (str, int, list, bool) -> None
    skip_existing = not force
    print('=== 本生成 ===')

    q_words = get_question_words(words)
    print(f'単語: {len(words)}語 / お題対象: {len(q_words)}語\n')

    # 単語音声
    print('--- 単語 (words/) ---')
    ok_w, err_w = run_words(base, speaker_id, words, WORDS_DIR, skip_existing)

    # 問題文音声 (先頭3語のポーズを検証用に取得)
    sample_ids = [w['id'] for w in q_words[:3]]
    print('\n--- 問題文 (questions/) ---')
    ok_q, err_q, sample_queries = run_questions(
        base, speaker_id, q_words, QUESTIONS_DIR, skip_existing, sample_ids
    )

    total_ok = ok_w + ok_q
    total_err = len(err_w) + len(err_q)
    print(f'\n合計: {total_ok} 本 OK / {total_err} 本 FAILED')
    print(f'  words/:     {ok_w} 本')
    print(f'  questions/: {ok_q} 本')

    # サイズ集計
    def dir_size(d):
        return sum(
            os.path.getsize(os.path.join(d, f))
            for f in os.listdir(d)
            if f.endswith('.wav')
        ) if os.path.isdir(d) else 0

    words_size  = dir_size(WORDS_DIR)
    q_size      = dir_size(QUESTIONS_DIR)
    print(f'\n  words/ サイズ:     {words_size / 1024:.0f} KB')
    print(f'  questions/ サイズ: {q_size / 1024:.0f} KB')
    print(f'  合計サイズ:         {(words_size + q_size) / 1024:.0f} KB')

    # ポーズ検証サンプル (新規生成分のみ表示)
    if sample_queries:
        print_pause_report(sample_queries)

    if err_w or err_q:
        print('\n失敗ファイル:', file=sys.stderr)
        for f in err_w + err_q:
            print(f'  {f}', file=sys.stderr)
        sys.exit(1)


def main():
    # type: () -> None
    parser = argparse.ArgumentParser(description='しりとりゲーム VOICEVOX 音声生成')
    parser.add_argument('--test', action='store_true',
                        help='テスト生成: 少数サンプルを audio/test/ に出力')
    parser.add_argument('--force', action='store_true',
                        help='生成済みファイルも上書きする')
    args = parser.parse_args()

    # VOICEVOX 疎通確認
    base = find_host()
    if not base:
        print('ERROR: VOICEVOX に接続できません。', file=sys.stderr)
        print('・VOICEVOXアプリが起動しているか確認してください。', file=sys.stderr)
        print(f'・Windowsファイアウォールでポート50022を許可してください。', file=sys.stderr)
        sys.exit(1)

    speaker_id = find_speaker_id(base)
    print(f'話者ID (ずんだもん あまあま): {speaker_id}\n')

    words = load_words()
    print(f'words.json 読み込み: {len(words)}語\n')

    if args.test:
        _run_test(base, speaker_id, words)
    else:
        _run_full(base, speaker_id, words, args.force)


if __name__ == '__main__':
    main()
