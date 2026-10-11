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
  - [x] **5-0**: shared/ 6ファイル作成 (game-shell.css / audio-engine.js / audio-player.js / speech.js / game-state.js / ui-common.js)、決定メモ追加 (docs/decisions/001-shared-design.md)
  - [x] **5-1**: compare-game を shared/ に移行（試験台）
  - [x] **5-2**: counting-game を shared/ に移行
  - [x] **5-3**: hiragana-hunt を shared/ に移行
  - [x] **5-4**: games/_template/ 作成

- [x] **ステップ6**: ものしりクイズ を games/ に追加、公開
  - JSON問題データ読み込み・出題エンジン実装
  - 出題・回答・選び直し・スキップ UI
  - localStorage 記録と保護者設定
  - games.json の status を `"live"` に変更

- [x] **ステップ7**: 実機(iPhone)フィードバック対応
  - ホーム画面アイコン追加 (icons/icon-180.png, icon-512.png)
  - 読み上げ形式: 「問題文。1、〇〇。2、〇〇。3、〇〇。えらんでね」、カードに番号バッジ
  - 正解後の解説表示・読み上げを廃止
  - 選択画面修正: iOS Safari スクロール(-webkit-overflow-scrolling: touch)、cat.name→cat.labelバグ修正、ジャンル絵文字追加
  - 難易度(やさしい/ちょっと考える) → 年齢(2さい/3さい/4さい)、デフォルト3さい、monoshiri_age_map.json 追加

## 近日公開（予定）

しりとり / めいろ / たりないかず / つぎはなにいろ?

- [x] **バグ修正**: ものしりクイズ 問題画面でカードが表示されないバグを修正 (e34aec8)
  - 原因: f43cddb で explanation 要素を削除したが JS 側の参照が残り null 例外でカード描画が止まっていた

- [x] **改善**: 正解後「つぎへ」ボタンを廃止し、1.5秒後に自動で次問題へ進むように変更 (514ffda)
  - 待機中タップ重複・🏠押下時のタイマーキャンセルを Playwright 自動テストで確認

## 次の一手

iPhone 実機でジャンル・年齢選択 → ゲーム → 正解自動進行 → クリア を通す。

- [x] **アイコン差し替え**: ポータルホーム画面アイコンを案A(2×2タイル)に更新 (icons/icon-180.png, icon-512.png)
