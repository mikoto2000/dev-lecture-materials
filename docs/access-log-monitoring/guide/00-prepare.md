# 準備: Loki・Grafana・Alloy を起動する

## この章のゴール

実験環境を起動し、Grafana のダッシュボードでアクセスの記録を確認します。

## ファイルと Docker を準備する

[教材トップ](../index.md)の ZIP をダウンロードして展開します。展開先の `access-log-lab` フォルダーには `compose.yaml`、`config.alloy`、`loki.yaml`、`demo.py`、`grafana` フォルダーがあります。

Docker Desktop を Linux コンテナーモードで起動します。PowerShell で、展開した `compose.yaml` のあるフォルダーへ移動します。保存先は自分の環境に合わせて変更してください。

```powershell
cd "$HOME\Downloads\access-log-lab"
docker version
docker compose version
docker compose up -d
docker compose ps --all
```

`demo`、`traffic`、`alloy`、`loki`、`grafana`、`notification-sink` の6サービスが起動します。`Exited` や `Restarting` があれば[困ったとき](../troubleshooting.md)を確認します。初回はイメージの取得と初期化を待ってください。

WSL 2 の Docker Engine を使う場合は、ZIP を Linux のホーム配下に展開し、Bash で同じ `docker compose` コマンドを実行します。以降の Compose コマンドもそのまま使えます。

## Grafana を開く

ブラウザーで [Grafana](http://127.0.0.1:13000/) を開きます。

| 項目 | 値 |
|---|---|
| ユーザー名 | `learner` |
| パスワード | `access-log-local-only` |

ローカル演習専用のアカウントです。画面名は英語で説明します。ホームに **Access Log Lab** が表示されなければ、サイドメニューの **Dashboards** から同名のダッシュボードを開きます。

右上の時間範囲を **Last 15 minutes**、自動更新を **5s** にします。起動後1〜2分待つと、Requests のグラフが増え、下の Access logs に JSON の行が現れます。

## 記録を発生させる

[実験用アプリ](http://127.0.0.1:18780/items)をブラウザーで開くと、`status` と `request_id` が返ります。このアクセスも記録されます。

自動アクセス役の `traffic` も、各リクエストの完了後に1秒待ってアクセスします。10回に1回は `/missing` へアクセスして404を発生させます。エラー実験をしていない状態でも404が少しあるのは仕様です。

Loki はホストへ公開していません。Grafana からは Compose 内部の `http://loki:3100` を使います。Grafana のデータソース URL を `localhost:3100` へ変えないでください。`localhost` は Grafana コンテナー自身を指します。

## 保存と安全な範囲

ブラウザーへ公開するのは、ループバックの13000番と18780番だけです。実験に使うログは、このアプリへのアクセスから作る練習用データです。本番のログや認証情報は追加しません。

ログ、Alloy の読み取り位置、Loki のデータ、Grafana の設定、故障モードは専用ボリュームへ保存します。Loki の保持期間は24時間ですが、アクセスログの元ファイルは自動で削除しません。短い演習として使い、終了後に後片付けを行ってください。

`access-log-lab` という固定プロジェクト名を使うため、複数コピーの同時起動は避けます。

[次の章: 1行を読む](./01-read.md)
