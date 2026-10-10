# 001: shared/ 共通化の設計と決定事項

日付: 2026-10-10
状態: 採用

## 決定

3本のゲーム (compare-game / counting-game / hiragana-hunt) に重複していたコードを
`shared/` の6ファイルに集約する。新規ゲームはこれを読み込むことで外観・動作ルールが統一される。

## shared/ ファイル構成と読み込み順

```
shared/
  game-shell.css      共通CSS全体 (≈450行)
  audio-engine.js     AudioEngine IIFE — Web Audio API 効果音
  audio-player.js     AudioPlayer IIFE — VOICEVOX 音声ファイル再生
  speech.js           Speech IIFE — TTS フォールバック付き読み上げ
  game-state.js       createGameState() ファクトリ — localStorage管理
  ui-common.js        UICommon IIFE — 画面遷移・アニメ・共通イベント
```

各ゲームの `index.html` で読み込む順序:

```html
<link rel="stylesheet" href="../../shared/game-shell.css?v=1">
<script src="../../shared/audio-engine.js?v=1"></script>
<script src="../../shared/audio-player.js?v=1"></script>
<script src="../../shared/speech.js?v=1"></script>
<script src="../../shared/game-state.js?v=1"></script>
<script src="../../shared/ui-common.js?v=1"></script>
```

type="module" は使わない (file:// 環境での CORS エラー回避のため)。

## 各ゲームが UICommon に渡すコールバック

```js
UICommon.init({
  onStart:      () => { startGame(); },         // はじめるボタン後
  onSpeakGame:  () => { Speech.speak(...); },   // 🔊ボタン
  onNextClear:  () => { startGame(); },         // クリア後「もういちど」
  onReset:      () => { state = GameState.reset(); }, // リセット実行
  renderStats:  () => { /* #parent-stats に innerHTML */ }, // 省略可
  extraScreens: { level: document.getElementById('screen-level') }, // 省略可
});
```

## 各ゲームが preload を呼ぶ方法

```js
AudioPlayer.preload(['question.wav', 'praise_1.wav', 'praise_2.wav', ...]);
```

counting-game の `countPool` (count_1.wav〜count_10.wav) や `playCount()` は
ゲーム固有のため counting-game の index.html 内で管理する。

## 予約グローバル名 (R4)

以下はゲーム側で再定義しない:
`AudioEngine` / `AudioPlayer` / `Speech` / `UICommon` / `createGameState`

ゲーム固有の追加メソッド (`AudioEngine.playPop` 等) は既存オブジェクトへの後付けで行う。

## 決定事項: CSS 統一値 (R6)

| 項目 | 統一値 | 備考 |
|------|--------|------|
| `.app-title` font-size | `clamp(36px, 11vmin, 72px)` | compare-game の値 |
| `.home-btn` サイズ | 44×44px / icon 20px | タップ領域大きい方 |
| `.speak-btn` 最大サイズ | `clamp(44px, 10vmin, 64px)` | タップ領域大きい方 |
| `.character-game` font-size | `clamp(28px, 7vmin, 52px)` | compare-game の値 |
| `.modal-box` | `width:min(340px,92vw); max-height:90vh; overflow-y:auto` | compare-game の値 |
| confetti タイムアウト | 4500ms | compare-game の値 |

## 決定事項: iOS Safari 音声アンロック (R1)

`AudioEngine.resume()` と `AudioPlayer.unlock()` は必ずユーザーのタップハンドラの
先頭で**同期的**に呼ぶ。Promise チェーンの後ろ・setTimeout・コールバック経由は不可。
UICommon.init() の `btn-start` ハンドラがこの順序を守る。

## 決定事項: キャッシュバスティング (R3)

shared ファイルを読み込む `<link>` と `<script>` には `?v=N` を付ける。
shared/ のファイルを変更したら全ゲームの `v` を同じ番号に上げる。
バージョン番号は `v=1` から始め、shared/ の変更ごとにインクリメントする。

## 決定事項: R5 (#parent-stats なし対応)

UICommon.openParentMenu() は `document.getElementById('parent-stats')` が
null でも例外を出さない (`if (statsEl && _cfg.renderStats)` でガード)。

## 決定事項: _template/ の作成方針

- `games/_template/index.html` のみ作成 (ステップ5-4で)
- 近日公開5本のフォルダは作らない (games.json の coming-soon で管理する)
- `_template/` は games.json に登録しない

## 移行段階

| ステップ | 内容 | ロールバック |
|----------|------|-------------|
| 5-0 | shared/ 作成のみ。既存3本の index.html は変更しない | `git rm -r shared/` |
| 5-1 | compare-game を shared/ に移行 (試験台) | `git checkout HEAD -- games/compare-game/index.html` |
| 5-2 | counting-game を shared/ に移行 | `git checkout HEAD -- games/counting-game/index.html` |
| 5-3 | hiragana-hunt を shared/ に移行 | `git checkout HEAD -- games/hiragana-hunt/index.html` |
| 5-4 | _template/ 作成 | `git rm -r games/_template/` |

各ステップの完了条件:
スタート → ゲーム → クリア が動くこと / iOS Safari で音声が出ること / 🏠ボタンが機能すること

## 理由

3本のゲームはコピー由来でコードを丸ごと持っており、すでに細部に差が生じている。
新規5本を追加する前に共通化しておかないと同じ問題が10本分に拡大する。
ビルドツールなし・Vanilla JS の前提を維持したまま classic script + 相対パス読み込みで実現する。

## 影響

- 既存3本の動作は移行後も変わらない (ステップ5-1〜5-3で1本ずつ確認)
- shared/ を変更したら全ゲームで動作確認が必要になる (CLAUDE.md 参照)
- 新規ゲームは _template/ をコピーして共通部品を読み込むだけで外観が揃う
