# STATUS.md — kids-games-portal

## 進捗

- [x] **ステップ1**: ポータル + games.json + ドキュメント作成、GitHub Pages 公開準備
- [x] **ステップ2**: compare-game を games/ に統合
  - `audio/count_1.wav`〜`count_10.wav`（10ファイル）はコピーしない（未使用確認済み）
  - 統合後 games.json の status を `"live"` に変更
- [x] **ステップ3**: counting-game・hiragana-hunt を games/ に統合
  - Speech.speak / speakCount: `if (!AudioEngine.isEnabled()) return;` を先頭に追加（TTS漏れ修正）
  - btn-home-game: postMessage go-home in iframe, else showScreen start
  - hiragana-hunt の btn-home-level はゲーム内遷移（コース選択→スタート）のため変更せず
  - games.json の status を `"live"` に変更
- [ ] **ステップ4**: 旧3リポジトリの README に「ポータルへの誘導リンク」を追記
- [ ] **ステップ5**: shared/ への共通化
  - **追加予定の5本を作る前に実施する**
  - 対象: AudioEngine / AudioPlayer 骨格 / Speech 骨格 / 共通CSS（変数・ボタン・modal・confetti 等）
  - 実施前に3本すべてで動作確認してからコミット

## 近日公開（予定）

しりとり / ものしりクイズ / めいろ / たりないかず / つぎはなにいろ?

## 次の一手

ステップ4: 旧3リポジトリの README にポータルへの誘導リンクを追記する。
