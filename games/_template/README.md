# 新ゲーム追加手順

1. `games/_template/` を `games/<new-id>/` にコピーする
2. `index.html` の `TODO:` をすべて埋め、ダミーボタン (`btn-dummy-correct`) と `DUMMY_` ブロックを削除する
3. `games.json` に 1 エントリ追加し、まず `"status": "coming-soon"` でコミット
4. スタート → ゲーム → クリア → 🏠 が通ったら `"status": "live"` に変えてコミット
5. **shared/ を変更した場合**: 3 本すべての `index.html` で `?v=N` を同じ番号にインクリメントする
6. iPhone 実機で音声が出ることを確認してから push する
