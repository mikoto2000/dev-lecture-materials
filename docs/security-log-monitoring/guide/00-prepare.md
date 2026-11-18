# 準備と観測の範囲

## この章のゴール

専用の Grafana を開き、アクセスログに加えて記録する認証イベントを確認します。

## 独立したラボを起動する

[教材トップ](../index.md)の ZIP を展開し、`compose.yaml` のある `security-log-lab` フォルダーで実行します。前の教材のフォルダーとは分けてください。

```powershell
cd "$HOME\Downloads\security-log-lab"
docker compose up -d
docker compose ps --all
```

Linux コンテナーを使います。WSL 2 の Docker Engine では Linux のホーム配下に展開し、同じ Compose コマンドを実行します。

[Grafana](http://127.0.0.1:13010/)を開き、`learner` / `access-log-local-only` でログインします。**Security Log Lab** ダッシュボードを開き、**Last 15 minutes**、更新間隔 **5s** にします。起動後1〜2分待ちます。

アプリはループバックの18790番、Grafana は13010番だけに公開します。Loki や通知受信器はホストへ公開しません。前の教材と別のプロジェクトとボリュームを使います。

## Explore で確認する

**Explore → Loki → Code** で実行します。

```text
{job="security-log-lab"} | json
```

アプリの通常アクセスに加え、5回に1回程度、学習用認証の成功イベントが出ます。認証の成功・失敗はアプリが判定したものであり、HTTP ステータスから推測した値ではありません。

| 項目 | この教材での意味 |
|---|---|
| `event` | `access` または `auth` |
| `outcome` | 認証では `success` または `failure` |
| `account` | 固定の `demo-user` または `other`。通常アクセスは空欄 |
| `client_ip` | アプリが TCP 接続の相手として見た IP |
| `time` / `request_id` | 発生時刻とリクエストの照合用 ID |

学習用の認証処理はセッションやトークンを発行しません。パスワードや要求の本文をログへ保存しません。実サービスでは、アクセスログとは別の認証ログが必要になることもあります。

## 送信元を読み違えない

`client_ip` はこのラボの自動アクセスコンテナーの IP です。値は環境で変わるので、教材の固定値を期待しません。

実際のサービスでは、プロキシや NAT の背後の利用者が同じ IP に見える場合があります。送信元 IP は人の識別子ではありません。外部から届いた `X-Forwarded-For` を無条件で信用せず、信頼するプロキシが設定した値だけを採用する設計が必要です。

[次の章: 認証失敗の集中](./01-auth.md)
