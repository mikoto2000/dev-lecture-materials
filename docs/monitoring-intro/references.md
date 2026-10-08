# 参考資料

本編は **Uptime Kuma 2.5.5** を対象にしています。2026-10-08 に公式の安定版と設定を確認しました。開発中の master ではなく、リリースの版を合わせて参照します。

## 導入とデータ保存

- [Uptime Kuma 2.5.5 リリース](https://github.com/louislam/uptime-kuma/releases/tag/2.5.5)
- [2.5.5 の README](https://github.com/louislam/uptime-kuma/blob/2.5.5/README.md)
- [初期データベース選択画面](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/pages/SetupDatabase.vue)
- [Kuma v2 の移行・バックアップに関する説明](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2)
- [Docker Desktop の Windows 導入手順](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Docker Compose のネットワーク](https://docs.docker.com/compose/how-tos/networking/)
- [Docker Compose down とボリューム削除](https://docs.docker.com/reference/cli/docker/compose/down/)

## 設定と通知の意味を確認する

- [2.5.5 の監視設定画面](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/pages/EditMonitor.vue): HTTP、Keyword、JSON Query、間隔、再試行、タイムアウト
- [2.5.5 の監視実行処理](https://github.com/louislam/uptime-kuma/blob/2.5.5/server/model/monitor.js): Pending / Down / Up と通知の判定
- [2.5.5 の Webhook 通知](https://github.com/louislam/uptime-kuma/blob/2.5.5/server/notification-providers/webhook.js)
- [2.5.5 の日本語訳](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/lang/ja.json): 英語の項目名との対応

## 実験アプリと次の学習

- [Python の http.server](https://docs.python.org/3.12/library/http.server.html): 学習用サーバー。本番利用は推奨されていません
- [Python の sqlite3](https://docs.python.org/3.12/library/sqlite3.html): ファイル型 DB と読み取り専用接続
- [Uptime Kuma の Prometheus 連携](https://github.com/louislam/uptime-kuma/wiki/Prometheus-Integration)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

分類や用語を一度に暗記するより、自分が検知できた故障と、見逃した故障に結び付けて読みます。

[教材トップ](./index.md)
