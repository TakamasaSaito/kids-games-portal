#!/usr/bin/env python3
"""
Generate VOICEVOX audio files for ものしりクイズ.
話者: ずんだもん (あまあまスタイル)

Usage (run from project root):
    python3 scripts/generate_monoshiri_audio.py --test
        → audio/test/ にテスト音声を生成

    python3 scripts/generate_monoshiri_audio.py
        → audio/ に全ファイルを生成 (声を決めてから実行)

VOICEVOX must be running on Windows (port 50022).
WSL: Windows host IP is resolved dynamically via `ip route show`.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
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
GAME_DIR = os.path.join(PROJECT_ROOT, 'games', 'monoshiri-quiz')
AUDIO_DIR = os.path.join(GAME_DIR, 'audio')
TEST_DIR = os.path.join(GAME_DIR, 'audio', 'test')
DATA_DIR = os.path.join(GAME_DIR, 'data')


# ---------------------------------------------------------------------------
# 品質設定 (参照: compare-game/scripts/generate_audio.py)
# ---------------------------------------------------------------------------

# 問題文: ゆっくりめ (子ども向け)
SPEED_QUESTION = 0.95
# 選択肢・番号・案内: やや遅め
SPEED_CHOICE   = 0.95
PITCH          = 0.04
INTON          = 1.2


# ---------------------------------------------------------------------------
# テスト用フレーズ定義
# ---------------------------------------------------------------------------

# a. 番号の読み方 2パターン
NUMBER_FILES = {
    'num_ichi':    ('いち',   SPEED_CHOICE, PITCH, INTON),
    'num_ni':      ('に',     SPEED_CHOICE, PITCH, INTON),
    'num_san':     ('さん',   SPEED_CHOICE, PITCH, INTON),
    'num_ichiban': ('いちばん', SPEED_CHOICE, PITCH, INTON),
    'num_niban':   ('にばん',  SPEED_CHOICE, PITCH, INTON),
    'num_sanban':  ('さんばん', SPEED_CHOICE, PITCH, INTON),
}  # type: Dict[str, Tuple]

# b. 最後の言葉 3パターン
END_FILES = {
    'end_erandene':      ('えらんでね',       SPEED_CHOICE, PITCH, INTON),
    'end_erandekudasai': ('えらんでください', SPEED_CHOICE, PITCH, INTON),
    'end_dorekana':      ('どれかな。',       SPEED_CHOICE, PITCH, INTON),
}  # type: Dict[str, Tuple]


# ---------------------------------------------------------------------------
# テキスト正規化
# ---------------------------------------------------------------------------

def normalize_text(text):
    # type: (str) -> str
    """「？」「?」を「。」に置換する (is_interrogative=false と合わせて語尾制御)"""
    text = text.replace('？', '。')
    text = text.replace('?', '。')
    return text


# ---------------------------------------------------------------------------
# ひらがな → ローマ字変換 (ファイル名用)
# ---------------------------------------------------------------------------

_HIRA_TABLE = {
    'あ': 'a',  'い': 'i',  'う': 'u',  'え': 'e',  'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'si', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'ti', 'つ': 'tu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'hu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya',             'ゆ': 'yu',             'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa',                                     'を': 'wo',
    'ん': 'n',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'zi', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
    'しゃ': 'sya', 'しゅ': 'syu', 'しょ': 'syo',
    'ちゃ': 'tya', 'ちゅ': 'tyu', 'ちょ': 'tyo',
    'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
    'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
    'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
    'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
    'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
    'じゃ': 'zya', 'じゅ': 'zyu', 'じょ': 'zyo',
    'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
    'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
    'ふぁ': 'fa',  'ふぃ': 'fi',  'ふぇ': 'fe',  'ふぉ': 'fo',
    'ー': '',  'っ': 'tt', '・': '',
}


def hiragana_to_romaji(text):
    # type: (str) -> str
    """ひらがな文字列をローマ字に変換 (ファイル名用・英数字のみ)"""
    result = []
    i = 0
    while i < len(text):
        # 2文字の組み合わせを先に試す
        two = text[i:i+2]
        if two in _HIRA_TABLE:
            result.append(_HIRA_TABLE[two])
            i += 2
            continue
        one = text[i]
        if one in _HIRA_TABLE:
            result.append(_HIRA_TABLE[one])
        elif one.isascii() and (one.isalnum() or one == '_'):
            result.append(one.lower())
        # その他 (漢字、記号など) は無視
        i += 1
    romaji = ''.join(result)
    # 連続するアンダースコア・不要文字を除去
    romaji = re.sub(r'[^a-z0-9]', '', romaji)
    return romaji


def build_choice_filename_map(questions):
    # type: (list) -> Dict[str, str]
    """
    spokenLabel → ファイル名 (拡張子なし) のマッピングを構築する。
    同一ローマ字になるラベルが複数ある場合は _2, _3 サフィックスを付ける。
    """
    label_to_romaji = {}  # type: Dict[str, str]
    romaji_count = {}     # type: Dict[str, int]

    for q in questions:
        for c in q['choices']:
            label = c['spokenLabel']
            if label in label_to_romaji:
                continue
            romaji = hiragana_to_romaji(label)
            if not romaji:
                romaji = 'choice'
            romaji_count[romaji] = romaji_count.get(romaji, 0) + 1

    # 衝突があるかを事前確認
    label_list = []
    for q in questions:
        for c in q['choices']:
            label = c['spokenLabel']
            if label not in [l for l, _ in label_list]:
                label_list.append((label, hiragana_to_romaji(c['spokenLabel']) or 'choice'))

    # 重複ローマ字の割り当て
    seen_romaji = {}  # type: Dict[str, int]
    result = {}       # type: Dict[str, str]
    for label, romaji in label_list:
        if romaji not in seen_romaji:
            seen_romaji[romaji] = 1
            result[label] = f'c_{romaji}'
        else:
            seen_romaji[romaji] += 1
            result[label] = f'c_{romaji}_{seen_romaji[romaji]}'

    return result


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


def synthesize(base, text, speaker_id, out_path, speed=1.00, pitch=0.04, inton=1.2):
    # type: (str, str, int, str, float, float, float) -> None
    qs = urllib.parse.urlencode({'text': text, 'speaker': speaker_id})
    req = urllib.request.Request(
        f'{base}/audio_query?{qs}',
        data=b'',
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        query = json.loads(r.read())

    query['speedScale']       = speed
    query['pitchScale']       = pitch
    query['intonationScale']  = inton
    query['prePhonemeLength'] = 0.3

    for ap in query['accent_phrases']:
        ap['is_interrogative'] = False  # 語尾上がり防止

    # 冒頭ポーズ 0.70 秒
    first = query['accent_phrases'][0]
    if first.get('pause_mora'):
        first['pause_mora']['vowel_length'] = 0.70

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

    with open(out_path, 'wb') as f:
        f.write(wav)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_questions():
    # type: () -> list
    with open(os.path.join(DATA_DIR, 'quiz_questions_300.json'), encoding='utf-8') as f:
        data = json.load(f)
    return data['questions']


def load_age_map():
    # type: () -> Dict[str, int]
    with open(os.path.join(DATA_DIR, 'monoshiri_age_map.json'), encoding='utf-8') as f:
        data = json.load(f)
    return data['ageByQuestionId']


def run_batch(base, speaker_id, items, out_dir, label, skip_existing=False):
    # type: (str, int, list, str, str, bool) -> List[str]
    """items: list of (filename_without_ext, text, speed, pitch, inton)"""
    os.makedirs(out_dir, exist_ok=True)
    errors = []
    total = len(items)
    skipped = 0
    for i, (fname, text, speed, pitch, inton) in enumerate(items, 1):
        norm_text = normalize_text(text)
        out_path = os.path.join(out_dir, f'{fname}.wav')
        if skip_existing and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f'[{i:3d}/{total}] {fname}.wav  SKIP')
            skipped += 1
            continue
        print(f'[{i:3d}/{total}] {fname}.wav  "{norm_text}"', end=' ', flush=True)
        try:
            synthesize(base, norm_text, speaker_id, out_path, speed, pitch, inton)
            print('OK')
        except Exception as e:
            print(f'FAILED: {e}')
            errors.append(fname)
        time.sleep(0.05)
    if skipped:
        print(f'  (スキップ: {skipped}本 既存)')
    return errors


def main():
    # type: () -> None
    parser = argparse.ArgumentParser(description='ものしりクイズ VOICEVOX 音声生成')
    parser.add_argument('--test', action='store_true',
                        help='テスト生成: 聞き比べ用サンプルを audio/test/ に出力')
    parser.add_argument('--only', type=str, default='',
                        help='カンマ区切りの問題ID (例: --only Q012,Q020) — 指定した問題のみ再生成')
    parser.add_argument('--force', action='store_true',
                        help='--only で指定した問題のファイルを強制上書き (既存ファイルを再生成する)')
    args = parser.parse_args()

    if args.force and not args.only:
        print('ERROR: --force は --only と一緒に使ってください。', file=sys.stderr)
        sys.exit(1)

    base = find_host()
    if not base:
        print('ERROR: VOICEVOX に接続できません。', file=sys.stderr)
        print('・VOICEVOXアプリが起動しているか確認してください。', file=sys.stderr)
        print(f'・Windowsファイアウォールでポート50022を許可してください。', file=sys.stderr)
        sys.exit(1)

    speaker_id = find_speaker_id(base)
    print(f'話者ID (ずんだもん あまあま): {speaker_id}\n')

    questions = load_questions()
    age_map = load_age_map()

    if args.test:
        _run_test(base, speaker_id, questions, age_map)
    elif args.only:
        only_ids = set(q.strip().upper() for q in args.only.split(',') if q.strip())
        _run_partial(base, speaker_id, questions, only_ids, args.force)
    else:
        _run_full(base, speaker_id, questions)


def _run_test(base, speaker_id, questions, age_map):
    # type: (str, int, list, dict) -> None
    print('=== テスト生成 ===')
    print(f'出力先: {TEST_DIR}\n')

    # --- a. 番号の読み方 ---
    print('--- a. 番号の読み方 ---')
    items_a = [(k, v[0], v[1], v[2], v[3]) for k, v in NUMBER_FILES.items()]
    errs = run_batch(base, speaker_id, items_a, TEST_DIR, '番号')

    # --- b. 最後の言葉 ---
    print('\n--- b. 最後の言葉 ---')
    items_b = [(k, v[0], v[1], v[2], v[3]) for k, v in END_FILES.items()]
    errs += run_batch(base, speaker_id, items_b, TEST_DIR, '最後の言葉')

    # --- c. 問題文サンプル (2歳・3歳・4歳 各1問) ---
    print('\n--- c. 問題文サンプル ---')
    q_by_id = {q['id']: q for q in questions}
    samples = []
    for age in [2, 3, 4]:
        for qid, a in age_map.items():
            if a == age and qid in q_by_id:
                q = q_by_id[qid]
                fname = f'q_age{age}_{qid.lower()}'
                samples.append((fname, q['spokenPrompt'], SPEED_QUESTION, PITCH, INTON))
                break
    errs += run_batch(base, speaker_id, samples, TEST_DIR, '問題文')

    # --- d. 上の3問の選択肢 (重複除去) ---
    print('\n--- d. 選択肢サンプル ---')
    seen_labels = set()
    choice_filename_map = build_choice_filename_map(questions)
    choice_items = []
    for (fname_q, text_q, *_) in samples:
        # fname_q から qid を逆引き
        qid_part = fname_q.split('_')[-1].upper()  # 'q001' → 'Q001'
        q = q_by_id.get(qid_part)
        if q:
            for c in q['choices']:
                lbl = c['spokenLabel']
                if lbl not in seen_labels:
                    seen_labels.add(lbl)
                    cfname = choice_filename_map[lbl]
                    choice_items.append((cfname, lbl, SPEED_CHOICE, PITCH, INTON))
    errs += run_batch(base, speaker_id, choice_items, TEST_DIR, '選択肢')

    total_files = len(items_a) + len(items_b) + len(samples) + len(choice_items)
    failed = len(errs)
    print(f'\n完了: {total_files - failed}/{total_files} ファイル → {TEST_DIR}/')
    if errs:
        print(f'失敗: {errs}', file=sys.stderr)
        sys.exit(1)

    print('\n--- 生成ファイル一覧 ---')
    for fname, (text, *_) in NUMBER_FILES.items():
        print(f'  {fname}.wav  "{text}"')
    for fname, (text, *_) in END_FILES.items():
        print(f'  {fname}.wav  "{text}"')
    for fname, text, *_ in samples:
        print(f'  {fname}.wav  "{normalize_text(text)}"')
    for fname, text, *_ in choice_items:
        print(f'  {fname}.wav  "{text}"')


def _run_partial(base, speaker_id, questions, only_ids, force):
    # type: (str, int, list, set, bool) -> None
    """--only で指定した問題IDの音声のみ再生成し、不要になった選択肢 wav を削除する。"""
    q_by_id = {q['id']: q for q in questions}
    missing = only_ids - set(q_by_id.keys())
    if missing:
        print(f'ERROR: 以下の問題IDが見つかりません: {sorted(missing)}', file=sys.stderr)
        sys.exit(1)

    target_qs = [q_by_id[qid] for qid in sorted(only_ids)]
    print(f'=== 部分再生成: {sorted(only_ids)} (force={force}) ===\n')

    # 問題文 wav を再生成
    print('--- 問題文 ---')
    q_items = [
        (f'q_{q["id"].lower()}', q['spokenPrompt'], SPEED_QUESTION, PITCH, INTON)
        for q in target_qs
    ]
    errs = run_batch(base, speaker_id, q_items, AUDIO_DIR, '問題文', skip_existing=not force)

    # 選択肢 wav を再生成 (対象問題のラベルのみ)
    new_map = build_choice_filename_map(questions)
    target_labels = set()
    for q in target_qs:
        for c in q['choices']:
            target_labels.add(c['spokenLabel'])

    print('\n--- 選択肢 ---')
    c_items = [
        (new_map[lbl], lbl, SPEED_CHOICE, PITCH, INTON)
        for lbl in sorted(target_labels)
        if lbl in new_map
    ]
    errs += run_batch(base, speaker_id, c_items, AUDIO_DIR, '選択肢', skip_existing=not force)

    # 使われなくなった選択肢 wav を削除
    existing_c = set(
        fn for fn in os.listdir(AUDIO_DIR)
        if fn.startswith('c_') and fn.endswith('.wav')
    )
    needed_c = set(fn + '.wav' for fn in new_map.values())
    to_delete = existing_c - needed_c
    if to_delete:
        print('\n--- 不要な選択肢 wav を削除 ---')
        for fname in sorted(to_delete):
            os.remove(os.path.join(AUDIO_DIR, fname))
            print(f'  削除: {fname}')
    else:
        print('\n不要な選択肢 wav はありませんでした')

    # choice_filename_map.json を更新
    map_path = os.path.join(AUDIO_DIR, 'choice_filename_map.json')
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(new_map, f, ensure_ascii=False, indent=2)
    print(f'\nマッピング更新: {map_path}')

    total = len(q_items) + len(c_items)
    failed = len(errs)
    print(f'\n完了: {total - failed}/{total} ファイル')
    if errs:
        print(f'失敗: {errs}', file=sys.stderr)
        sys.exit(1)


def _run_full(base, speaker_id, questions):
    # type: (str, int, list) -> None
    print('=== 本生成 ===')
    print(f'出力先: {AUDIO_DIR}\n')

    choice_filename_map = build_choice_filename_map(questions)

    # 番号 (いち/に/さん の3種のみ) + 案内フレーズ
    print('--- 番号・案内フレーズ ---')
    fixed_items = [
        ('num_ichi', 'いち',     SPEED_CHOICE, PITCH, INTON),
        ('num_ni',   'に',       SPEED_CHOICE, PITCH, INTON),
        ('num_san',  'さん',     SPEED_CHOICE, PITCH, INTON),
        ('end_erandene', 'えらんでね', SPEED_CHOICE, PITCH, INTON),
    ]
    errs = run_batch(base, speaker_id, fixed_items, AUDIO_DIR, '固定フレーズ', skip_existing=True)

    # 問題文 300 問
    print('\n--- 問題文 300 問 ---')
    q_items = []
    for q in questions:
        q_items.append((f'q_{q["id"].lower()}', q['spokenPrompt'], SPEED_QUESTION, PITCH, INTON))
    errs += run_batch(base, speaker_id, q_items, AUDIO_DIR, '問題文', skip_existing=True)

    # 選択肢ラベル
    print('\n--- 選択肢ラベル ---')
    seen = set()
    c_items = []
    for q in questions:
        for c in q['choices']:
            lbl = c['spokenLabel']
            if lbl not in seen:
                seen.add(lbl)
                c_items.append((choice_filename_map[lbl], lbl, SPEED_CHOICE, PITCH, INTON))
    errs += run_batch(base, speaker_id, c_items, AUDIO_DIR, '選択肢', skip_existing=True)

    total_files = len(fixed_items) + len(q_items) + len(c_items)
    failed = len(errs)
    print(f'\n完了: {total_files - failed}/{total_files} ファイル → {AUDIO_DIR}/')
    if errs:
        print(f'失敗: {errs}', file=sys.stderr)
        sys.exit(1)

    # ラベル→ファイル名マッピングを JSON で保存
    map_path = os.path.join(AUDIO_DIR, 'choice_filename_map.json')
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(choice_filename_map, f, ensure_ascii=False, indent=2)
    print(f'\nマッピング保存: {map_path}')


if __name__ == '__main__':
    main()
