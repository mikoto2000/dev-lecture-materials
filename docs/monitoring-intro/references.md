# 参考資料

各章の実験を終え、必要になった項目から参照してください。

## 実験の準備

- [Microsoft: WSL をインストールする](https://learn.microsoft.com/windows/wsl/install)
- [Microsoft: WSL の基本コマンド](https://learn.microsoft.com/windows/wsl/basic-commands)
- [Ubuntu: Python をインストールして使う](https://ubuntu.com/developers/docs/howto/python-setup/)

## 小さな HTTP 確認と、時間の扱い

- [Python 3.12: http.client](https://docs.python.org/3.12/library/http.client.html): HTTP 接続と、ブロッキング操作に対するタイムアウト
- [Python 3.12: http.server](https://docs.python.org/3.12/library/http.server.html): 学習用 HTTP サーバー。公式にも本番用途は推奨されていません
- [Python 3.12: time](https://docs.python.org/3.12/library/time.html): `monotonic()` による経過時間の測定
- [Python 3.12: subprocess](https://docs.python.org/3.12/library/subprocess.html): 子プロセスを時間で制限する仕組み

タイムアウト引数が、そのままリクエスト全体の絶対的な制限時間になるとは限りません。標準ライブラリーのソケット操作のタイムアウトと、スクリプト側が設ける処理全体の上限を区別します。

## データと観測記録

- [Python 3.12: sqlite3](https://docs.python.org/3.12/library/sqlite3.html): SQLite の接続、読み取り専用 URI、トランザクションと接続の終了
- [Python 3.12: os.replace](https://docs.python.org/3.12/library/os.html#os.replace): 同一ファイルシステム上で観測記録を置き換える処理

SQLite の接続コンテキストマネージャーは、トランザクションを扱います。接続を閉じる処理とは区別します。実験用アプリはリクエストごとに接続を終了します。

## 実験の後で読む監視設計

- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/): 利用者に見える症状、内部の原因、通知、レイテンシーなどを整理する

用語を一度に暗記するより、自分が検知できた故障・できなかった故障に結び付けて読みます。

[教材トップへ戻る](./index.md)
