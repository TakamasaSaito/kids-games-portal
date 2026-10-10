# kids-games-portal

子ども向けゲームポータル。ゲーム一覧を表示し、各ゲームを iframe で全画面起動する。

**公開URL**: https://TakamasaSaito.github.io/kids-games-portal/

## ゲーム一覧

| ゲーム | 状態 |
|---|---|
| ひらがなたからさがし | 近日公開 |
| いちにのぽん! | 近日公開 |
| くらべっこ | 近日公開 |
| しりとり | 近日公開 |
| ものしりクイズ | 近日公開 |
| めいろ | 近日公開 |
| たりないかず | 近日公開 |
| つぎはなにいろ? | 近日公開 |

## ローカル確認

`games.json` を `fetch()` で読み込むため、HTTP サーバーが必要。

```bash
cd /path/to/kids-games-portal
python3 -m http.server 8080
# → http://localhost:8080 にアクセス
```

## 関連リポジトリ

- [TakamasaSaito/hiragana-hunt](https://github.com/TakamasaSaito/hiragana-hunt)
- [TakamasaSaito/counting-game](https://github.com/TakamasaSaito/counting-game)
- [TakamasaSaito/compare-game](https://github.com/TakamasaSaito/compare-game)
