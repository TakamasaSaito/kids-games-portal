# CLAUDE.md — kids-games-portal

## アプリ概要

子ども向けゲームポータル。`index.html` がゲーム一覧で、カードをタップすると
`games/<id>/index.html` を iframe で全画面表示する。

## ファイル構成

```
index.html              ポータル本体（単一HTML・Vanilla JS）
games.json              ゲームカタログ（id/title/subtitle/emoji/path/status の6項目）
games/<id>/             各ゲームフォルダ（独立した単一HTML）
games/_template/        新ゲーム用テンプレート（games.json には登録しない）
shared/                 全ゲーム共通部品（6ファイル）
icons/                  ポータル用アイコン画像（PNG）
icons/source/           アイコン正本SVG（portal_icon.svg）
scripts/                generate_icon.py 等のユーティリティ
docs/decisions/         設計・採用決定メモ
CLAUDE.md
STATUS.md
README.md
```

### shared/ ファイル構成と読み込み順

```
shared/
  game-shell.css      共通CSS全体
  audio-engine.js     AudioEngine IIFE — Web Audio API 効果音
  audio-player.js     AudioPlayer IIFE — VOICEVOX 音声ファイル再生
  speech.js           Speech IIFE — TTS フォールバック付き読み上げ
  game-state.js       createGameState() ファクトリ — localStorage 管理
  ui-common.js        UICommon IIFE — 画面遷移・アニメ・共通イベント
```

## 実装ルール

- フレームワーク・ビルドツールなし。単一 `index.html` + Vanilla JS
- iOS Safari 必須対応: `viewport-fit=cover` / `touch-action: manipulation`
- `alert` / `confirm` / `prompt` 禁止
- ファイル名・クラス名は英数字のみ
- `type="module"` は使わない（file:// 環境での CORS エラー回避のため）
- shared/ は classic script + 相対パスで読み込む（`?v=N` 付き）

### shared/ 読み込みの書き方

```html
<link rel="stylesheet" href="../../shared/game-shell.css?v=1">
<script src="../../shared/audio-engine.js?v=1"></script>
<script src="../../shared/audio-player.js?v=1"></script>
<script src="../../shared/speech.js?v=1"></script>
<script src="../../shared/game-state.js?v=1"></script>
<script src="../../shared/ui-common.js?v=1"></script>
```

## 音声アンロック (R1)

「はじめる」等のタップ処理の先頭で、**同期的に** `AudioPlayer.unlock()` と
`AudioEngine.resume()` を呼ぶ。Promise チェーンの後ろ・setTimeout・コールバック経由は不可。

## 予約グローバル名 (R4)

以下のオブジェクトはゲーム側で再定義しない:

`AudioEngine` / `AudioPlayer` / `Speech` / `UICommon` / `createGameState`

ゲーム固有の追加メソッド（`AudioEngine.playPop` 等）は既存オブジェクトへの後付けで行う。

## #parent-stats なし対応 (R5)

`UICommon.openParentMenu()` は `document.getElementById('parent-stats')` が
null でも例外を出さない（`if (statsEl && _cfg.renderStats)` でガード済み）。
各ゲームも `#parent-stats` が無い場合に例外が起きないように実装する。

## 見た目の統一値

| 項目 | 統一値 |
|------|--------|
| `.home-btn` サイズ | 44×44px / icon 20px |
| `.speak-btn` 最大サイズ | `clamp(44px, 10vmin, 64px)` |
| `.app-title` font-size | `clamp(36px, 11vmin, 72px)` |
| `.character-game` font-size | `clamp(28px, 7vmin, 52px)` |
| `.modal-box` | `width:min(340px,92vw); max-height:90vh; overflow-y:auto` |
| confetti タイムアウト | 4500ms |

## 🏠ボタンの動作

iframe 内で動作している場合は `window.parent.postMessage({ type: 'go-home' }, '*')` を送る。
単体（直接開いている）場合はスタート画面へ遷移する。

ポータル側はセキュリティのため以下の2条件を両方満たす場合のみ処理する:
- `event.origin === location.origin`
- `event.source === iframe要素.contentWindow`

## localStorage

- キーは `<game-id>-v1` の形（例: `monoshiri-quiz-v1`）
- 読み書きは try-catch で例外ガード必須
- データの形を変えるときは、既存の進捗を読めるようにする（`dataVersion` フィールドで管理）

## 音声 (VOICEVOX)

- 話者: ずんだもん（あまあまスタイル）
- テキストに `?` を使わない（`。` に置換する）
- `is_interrogative = false`（語尾上がり防止）
- `prePhonemeLength = 0.3`
- 冒頭ポーズ 0.70 秒（先頭音素の `pause_mora.vowel_length` を 0.70 に設定）
- 新しい文言は `audio/test/` にテスト音声を生成して聞き比べてから本生成する
  （スクリプトの `--test` オプションを使う）
- ポータルの親メニュー画面に以下のクレジットを必ず表示する:
  `音声: VOICEVOX / ずんだもん（あまあま）`

音声生成スクリプト・VOICEVOXの接続先ポートなど環境固有の設定は
`scripts/generate_monoshiri_audio.py` を参照する。

## キャッシュバスティング (?v= ルール)

shared/ のファイルを変更したら、全ゲームの `index.html` で
`?v=N` の番号を同じ値にインクリメントしてからコミットする。

- バージョンは `v=1` から始まり、shared/ の変更ごとに +1 する
- 変更していない shared ファイルも番号を揃える（揃えないとゲームによって版が混在する）
- shared/ を変更したら全ゲームでスタート→ゲーム→クリアを確認してからコミットする
- 現在 `?v=1`（5-0 以降、shared/ は未変更）

## アイコン

- ポータルのアイコン正本は `icons/source/portal_icon.svg`
- PNG の再生成コマンド（`-W`/`-H` は使わない）:
  ```
  cairosvg icons/source/portal_icon.svg -o icons/icon-512.png --output-width 512 --output-height 512
  cairosvg icons/source/portal_icon.svg -o icons/icon-180.png --output-width 180 --output-height 180
  ```
- `scripts/generate_icon.py` は古い仕様（グラデのベタ塗り）のため、アイコン再生成には使わない

## 運用

- Claude Code は **commit のみ実行、push しない**（push は本人がマイルストーン時）
- コミットメッセージ: `add:` / `feat:` / `fix:` / `docs:` プレフィックス
- コミットは意味のある単位で分ける
- 個人情報（子どもの名前など）をコードやコミットに入れない

## games.json のスキーマ

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | string | フォルダ名と一致させる |
| `title` | string | ひらがな表記のゲーム名 |
| `subtitle` | string | 一行説明 |
| `emoji` | string | カードに表示する絵文字 |
| `path` | string \| null | `"games/<id>/"` の形。近日公開は `null` |
| `status` | `"live"` \| `"coming-soon"` | `"live"` でカードが有効になる |

## ゲーム追加手順

1. `games/_template/` を `games/<new-id>/` にコピーする
2. `index.html` の `TODO:` をすべて埋め、ダミーボタンと `DUMMY_` ブロックを削除する
3. `games.json` にエントリを追加（`status: "coming-soon"` から始めてよい）
4. スタート → ゲーム → クリア → 🏠 が通ったら `status` を `"live"` に変更してコミット
5. shared/ を変更した場合は全ゲームの `?v=N` を同じ番号にインクリメントする

## プロジェクト管理方針

本リポジトリは TakamasaSaito/portfolio-dashboard の MANAGEMENT.md に従う。
作業開始前に次で取得して読むこと:
`gh api repos/TakamasaSaito/portfolio-dashboard/contents/MANAGEMENT.md --jq .content | base64 -d`
