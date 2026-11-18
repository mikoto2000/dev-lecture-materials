# 1. 認証失敗の集中を見つける

## この章のゴール

同じ送信元とアカウントへの認証失敗を集計し、通知を確認します。

## シナリオと解除方法

最初に、解除コマンドを確認します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

次に認証失敗のシナリオへ切り替えます。固定の学習用アカウントに対し、固定の誤った値を送ります。外部の宛先やパスワードリストは使いません。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode login
```

Explore で認証失敗を探します。

```text
{job="security-log-lab"} | json | event="auth" | outcome="failure" | __error__=""
```

`account`、`client_ip`、時刻を確認します。401だけを検索する方法と違い、何の処理が失敗したかをアプリのイベントで確かめています。

## 送信元とアカウントで集計する

```text
sum by (client_ip, account) (
  count_over_time({job="security-log-lab"} | json | event="auth" | outcome="failure" | __error__="" [1m])
)
```

直近1分の失敗を、送信元とアカウントの組ごとに数えます。1つの IP を決め打ちして検索するより、新しい送信元にも気づきやすくなります。取り込み時のラベルにはせず、検索時に JSON から取り出しています。

この条件では、複数 IP から1つのアカウントへ分散する試行や、1つの IP から多くのアカウントへ少数ずつ試す動きを見逃します。実運用では、アカウント単位、送信元単位などの別集計も必要です。

## アラートと復旧を確認する

**Alerting → Alert rules** の **Repeated login failures** は、各組で **直近1分の失敗が10件以上** のとき異常とします。評価間隔は10秒、Pending は20秒です。

通知を別の PowerShell で表示します。

```powershell
docker compose logs --follow --tail 20 notification-sink
```

Firing と、同じ `alertname` の `firing` 通知を確認します。通知の `client_ip` と `account` も控えてください。1〜2分が目安です。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

正常な認証を再開すると、直近1分の失敗が減り、Normal と `resolved` 通知を確認できます。配布クエリーは同じ組の認証イベントがある間、失敗がない場合に0を補います。データ自体が来ない場合は Keep Last State とし、**Security logs missing** で別に検知します。

`resolved` はこの条件を下回ったという意味です。第三者が侵入していない、被害がない、と確認できた意味ではありません。

[前の章: 準備](./00-prepare.md) / [次の章: 探索的なアクセス](./02-paths.md)
