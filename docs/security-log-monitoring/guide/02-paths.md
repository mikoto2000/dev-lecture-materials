# 2. 探索的なアクセスを調べる

## この章のゴール

404の集中を検知し、どのパスを探しているかを調べます。

## 固定したパスへのアクセスを発生させる

前のシナリオを `normal` に戻してから実行します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode scan
```

このシナリオは、存在しない `/unknown-a`、`/unknown-b`、`/unknown-c` の3つだけを繰り返します。脆弱性の悪用や外部サイトのスキャンは行いません。

Explore で404を探します。

```text
{job="security-log-lab"} | json | status = 404 | __error__=""
```

パスと送信元の分布を集計します。

```text
sum by (client_ip, path) (
  count_over_time({job="security-log-lab"} | json | status = 404 | __error__="" [1m])
)
```

同じ送信元から3つのパスへのアクセスが見つかれば成功です。具体的な IP と件数は実行時に変わります。

## 警報を確かめる

**Repeated missing paths** は、送信元ごとの404が **直近1分で20件以上** だと異常です。Pending を経た Firing と、受信ログの `firing` を確認します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

解除したら、Normal と `resolved` 通知まで待ちます。404が0でも、その送信元の有効なログがある間は0を補います。

## 404の多さだけでは断定しない

実際の探索では、短時間に多様なパスへアクセスする場合があります。ただし、このルールは件数だけを見ています。パスの種類や内容まで判定していません。

また、存在するページの探索では200や403が返る場合もあり、404だけでは検知できません。公開直後のリンク切れや、正規のクローラーも404増加の要因です。次の章では、同じ警報をリンクミスでも発生させます。

[前の章: 認証失敗](./01-auth.md) / [次の章: 誤検知を確かめる](./03-triage.md)
