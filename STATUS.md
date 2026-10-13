# STATUS.md — kids-games-portal

最終更新: 2026-10-13

## 現状

5本すべて公開済み（hiragana-hunt / counting-game / compare-game / shiritori / ものしりクイズ）。
現在は shared/ 共通化の第1弾（SE wav 共有 / JS ユーティリティ整理）に着手中。

## 完了済み

- [x] **ステップ1**: ポータル + games.json + ドキュメント作成、GitHub Pages 公開準備
- [x] **ステップ2**: compare-game を games/ に統合
  - `audio/count_1.wav`〜`count_10.wav`（10ファイル）はコピーしない（未使用確認済み）
  - 統合後 games.json の status を `"live"` に変更
- [x] **ステップ3**: counting-game・hiragana-hunt を games/ に統合
  - Speech.speak / speakCount: `if (!AudioEngine.isEnabled()) return;` を先頭に追加（TTS漏れ修正）
  - btn-home-game: postMessage go-home in iframe, else showScreen start
  - hiragana-hunt の btn-home-level はゲーム内遷移のため変更せず
  - games.json の status を `"live"` に変更
- [ ] **ステップ4**: 旧3リポジトリの README に「ポータルへの誘導リンク」を追記
- [x] **ステップ5**: shared/ 基盤整備
  - shared/ 6ファイル作成・全ゲーム移行・_template 作成
- [x] **ステップ6**: ものしりクイズ 公開
  - JSON問題データ300問・出題エンジン・localStorage 記録・保護者設定
- [x] **ステップ7**: 実機(iPhone)フィードバック対応
  - ホーム画面アイコン・読み上げ形式改善・年齢別難易度
- [x] **ステップ8**: しりとり 公開
  - words.json 31語・questions 21本・3択カード UI
- [x] **バグ修正**: ものしりクイズ カード非表示バグ修正 (e34aec8)
- [x] **改善**: ものしりクイズ 正解後 1.5秒自動進行 (514ffda)
- [x] **デザイン刷新(案D)**: 星かざり・3D底面影・--game-accent 適用 (shared/game-shell.css v=2)
- [x] **共通化 P1〜P3**: STATUS.md 整理・_template --game-accent 追加・しりとり © 表記修正
- [x] **共通化 P4**: SE wav を shared/audio/se/ に集約（audio-player.js パス対応・?v=3 バンプ）

## 近日公開（予定）

めいろ / たりないかず / つぎはなにいろ?

## 残タスク

- [ ] 旧3リポジトリの README 誘導リンク追記（ステップ4）

## 次の一手

新ゲーム追加、または旧3リポジトリへの誘導リンク追記（ステップ4）。
