# CLAUDE.md — kids-games-portal

## アプリ概要

子ども向けゲームポータル。`index.html` がゲーム一覧で、カードをタップすると
`games/<id>/index.html` を iframe で全画面表示する。

## ファイル構成

```
index.html          ポータル本体（単一HTML・Vanilla JS）
games.json          ゲームカタログ（id/title/subtitle/emoji/path/status の6項目）
games/<id>/         各ゲームフォルダ（独立した単一HTML。ステップ2〜3で追加）
icons/              アプリアイコン（仮。後で差し替える）
scripts/            generate_icon.py 等のユーティリティ
CLAUDE.md
STATUS.md
README.md
```

## 実装ルール

- フレームワーク・ビルドツールなし。単一 `index.html` + Vanilla JS
- iOS Safari 必須対応: `viewport-fit=cover` / `touch-action: manipulation`
- `alert` / `confirm` / `prompt` 禁止
- ファイル名・クラス名は英数字のみ
- `localStorage` は try-catch 例外ガード必須
- **commit のみ実行、push しない**（push は本人がマイルストーン時）
- コミットメッセージ: `add:` / `feat:` / `fix:` / `docs:` プレフィックス

## ゲーム追加手順

1. `games/<new-id>/` フォルダを作り `index.html` を配置
2. `games.json` にエントリを追加（`status: "coming-soon"` から始めてよい）
3. 動作確認後 `status` を `"live"` に変更してコミット

## games.json のスキーマ

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | string | フォルダ名と一致させる |
| `title` | string | ひらがな表記のゲーム名 |
| `subtitle` | string | 一行説明 |
| `emoji` | string | カードに表示する絵文字 |
| `path` | string \| null | `"games/<id>/"` の形。近日公開は `null` |
| `status` | `"live"` \| `"coming-soon"` | `"live"` でカードが有効になる |

## postMessage プロトコル

各ゲームの🏠ボタンから `window.parent.postMessage({ type: 'go-home' }, '*')` を
送ると、ポータルが iframe を閉じて一覧に戻る（ステップ3で各ゲームに追加）。

ポータル側はセキュリティのため以下の2条件を両方満たす場合のみ処理する:
- `event.origin === location.origin`
- `event.source === iframe要素.contentWindow`

## 共通部品（shared/）を変えるとき（ステップ5以降）

AudioEngine / Speech / 共通CSS など全ゲームが依存するコードを変更する場合は、
`games/` 以下の3本すべてで動作確認（スタート→ゲーム→クリア）してからコミットする。

## プロジェクト管理方針

本リポジトリは TakamasaSaito/portfolio-dashboard の MANAGEMENT.md に従う。
作業開始前に次で取得して読むこと:
`gh api repos/TakamasaSaito/portfolio-dashboard/contents/MANAGEMENT.md --jq .content | base64 -d`
