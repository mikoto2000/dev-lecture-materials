# 4. アラートと通知を確かめる

## この章のゴール

Grafana が繰り返し評価するルールを読み、発火と復旧の通知を確認します。

## 登録済みのルールを読む

サイドメニューの **Alerting → Alert rules** を開き、Access Log Lab の3件を確認します。ファイルから自動登録したルールは GUI では編集できません。まず詳細画面でクエリーと判定条件を読みます。

| ルール名 | 調べる条件 |
|---|---|
| Access errors | 直近1分が10件以上で、5xx 率が20%以上 |
| Access slow | 直近1分が10件以上で、1000 ms 以上が3件以上 |
| Access logs missing | 直近1分の有効なログが0件 |

評価間隔は **10秒**、Pending の期間は **20秒** です。条件を満たすと Pending になり、その状態が続くと Firing になります。画面では正常を Normal と表示します。評価 API では inactive、通知では resolved という名前も使います。

最初の2ルールのクエリーは、`>= bool` で条件に合うと1、合わないと0を返します。`and (全件数 >= 10)` で母数を確認し、Grafana は値が0より大きいと異常にします。件数不足では判定値を返しません。

これは演習用の閾値です。通常のアクセス数と許容する失敗・遅延に合わせて決めます。低頻度でも失敗を見逃せない操作には、別の条件や外形監視が必要です。

## 通知先を確認する

**Alerting → Contact points** の **local-webhook** が通知先です。Compose 内部の `http://notification-sink:8081` へ送信します。外部のメールや Slack は使いません。

別の PowerShell を開き、同じラボのフォルダーで受信ログを表示します。

```powershell
docker compose logs --follow --tail 20 notification-sink
```

画面で Contact point の **Test** が使える場合は、先にテストします。テスト通知と実際のアラートは `alertname` で区別してください。テスト成功だけで実際の異常を検知できたとは扱いません。

通知ポリシーは、ルール名ごとにまとめ、初回は5秒待ちます。グループ更新の間隔は10秒、同じ異常の再通知は1時間です。Firing の表示と通知の到着は同時とは限りません。

## エラーの発火と復旧を見る

始める前に `normal` の状態で、Access errors が Normal になるまで待ちます。受信ログの現在の時刻を控えます。

```powershell
docker compose exec -T demo python /lab/demo.py mode error
```

1. ダッシュボードで5xx 率の上昇を確認する
2. Alert rules で Access errors の Pending → Firing を確認する
3. 受信ログで `alertname` が `Access errors`、`status` が `firing` の通知を探す

1〜2分が目安です。発火を確認したら解除します。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

直近1分の値が閾値を下回ると Normal に戻ります。同じルールの `resolved` が届くことを確認します。復旧の待機期間は追加していないため、20秒間の正常継続を要求する設定ではありません。

## 遅さの発火と復旧を見る

```powershell
docker compose exec -T demo python /lab/demo.py mode slow
```

今度は Access slow の Firing と通知を確認します。HTTP 200のままでも異常になることを確かめ、解除後の `resolved` まで確認します。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

## ログの途絶を正常と区別する

最初の2件が Normal に戻ってから、自動アクセスを止めます。実験中はブラウザーでアプリを開かないでください。

```powershell
docker compose stop traffic
```

最後のアクセスから1分以上経つと、Access logs missing が Pending → Firing になります。`firing` の通知を確認します。元のログファイルが残っていても、直近1分に新しいログがなければ異常です。

エラー率のグラフに値がないことは、0%と同じではありません。最初の2ルールはデータ不足のとき **Keep Last State** とし、以前の状態を維持します。データが消えただけで復旧したことにせず、途絶は別のルールで通知します。

```powershell
docker compose start traffic
```

ログ途絶の `resolved` と、新しいログを確認します。元のルールに十分な母数が戻るまでにも少し時間が必要です。

Loki 自体が止まった場合はクエリーの実行エラーです。これは0件とは違います。設定は **Error** 扱いで、Grafana の DatasourceError として調べます。Grafana 自体が停止するとこの通知もできないため、監視基盤への外形監視は別に必要です。

[前の章: 件数と割合を比べる](./03-measure.md) / [次の章: 調査と後片付け](./05-review.md)
