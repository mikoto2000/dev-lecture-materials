# 4. 通知を試し、ノイズを減らす

## 困りごと

画面を見ていなければ Down に気づけません。一方、同じ障害で何度も通知すると、大事な知らせを見落としやすくなります。

## 小さな追加: ローカルだけの通知先

この章では Slack やメールの認証情報を使いません。Kuma の **Webhook** 通知を、同じ Compose 内の小さな通知受信器へ送ります。受信器はアプリと別のサービスなので、demo を止めても通知を受け取れます。

```powershell
docker compose --profile notifications up -d notification-sink
```

`demo-health` の **Edit** 画面で、**Notifications** 欄の **Set Up Notification** を開きます。

| 項目 | 設定 |
|---|---|
| Notification Type | Webhook |
| Friendly Name | local-lab |
| Post URL | `http://notification-sink:18081/` |
| HTTP Method | POST |
| Request Body | Preset - application/json |

認証欄、追加ヘッダー、既定の通知先、既存の全監視への一括適用は設定しません。**Test** を押し、PowerShell で受信を確認します。

```powershell
docker compose --profile notifications logs --tail 20 notification-sink
```

通知のダイアログで **Save** を押し、**Notifications** 欄で `local-lab` にチェックが入っていることを確認します。続いて監視の編集画面でも **Save** を押し、左の一覧から `demo-health` の詳細に戻ります。Test の成功は通知経路の確認です。実際の Down / Up 通知は次の実験で確かめます。

受信器は教材用の記録先です。ここへ届いたことは、人がメッセージを読んだことの証明にはなりません。

## 安全な故障: 本当の Down と Up を通知させる

**復旧コマンドは `docker compose start demo` です。**

```powershell
docker compose stop demo
```

Down を確認してから、先ほどの `logs` コマンドで Down 通知が届いたことを確認します。続いて復旧させます。

```powershell
docker compose start demo
```

`demo-health` が Up に戻るまで待ち、受信器のログをもう一度表示して、復旧通知が届いたことを確かめます。

```powershell
docker compose --profile notifications logs --tail 20 notification-sink
```

受信ログでは、`monitor_name` が `demo-health` の行を見ます。`heartbeat_status` の `0` が Down、`1` が Up です。

## 小さな追加: 連続する失敗だけを知らせる

`demo-health` の Edit で次を設定します。

- Retries: **2**
- Heartbeat Retry Interval: **20 秒**
- Resend Notification if Down X times consecutively: **0**（再通知なし）

**Save** を押し、左の監視一覧から `demo-health` の詳細へ戻ります。停止前に Up を確認し、受信ログの `demo-health` の Down 通知件数を控えます。

もう一度 `docker compose stop demo` を実行します。詳細画面上部のハートビートでは、最初の2回の失敗で右端にオレンジの棒が1本ずつ増えます。状態は **Pending** のままです。この間に受信ログを表示し、`demo-health` の Down 通知がまだ増えていないことを確認します。Pending 中は **Heartbeat Retry Interval** の間隔で確認を繰り返します。

3回目の連続失敗で赤い棒が加わり、状態が **Down** に変わります。受信ログに `heartbeat_status` が `0` の行が1件増えたことを確認します。再通知を 0 にした場合は、次のチェックでも Down が続くまで待ち、新しい Down 通知が届かないことを確かめます。

画面の履歴にある Down の時刻と、ログの `received_at` を照合します。`received_at` は UTC です。日本標準時の画面と比べる場合は9時間を足します。

## 復旧

```powershell
docker compose start demo
```

次の成功確認で Up へ戻ったら、受信ログに `heartbeat_status` が `1` の行が増えたことを確認します。画面の Up の時刻と `received_at` を照合します。

## Down が続くときの再通知を試す

`demo-health` の **Edit** で **Retries** を **2** のままにし、**Resend Notification if Down X times consecutively** を **2** に変更します。**Save** を押して詳細画面へ戻ります。Up を確認し、受信ログの `demo-health` の Down 通知件数を控えます。

`docker compose stop demo` を実行し、詳細画面上部のハートビートを見ます。オレンジの Pending が2本並んだあと、最初の赤い棒で Down が確定し、Down 通知が1件届きます。赤い棒がさらに2本加わると、最初の再通知が届きます。通常の確認間隔が20秒なら、最初の Down 通知から約40秒後です。

再通知も受信ログでは `heartbeat_status` が `0` です。最初の Down を赤い棒の1本目として数え、3本目で受信ログが1件増えることを確かめます。画面下のイベント表には最初の Down の行が残るため、再通知の件数は受信ログで数えます。

`docker compose start demo` でアプリを再開します。状態が **Up** に戻り、`heartbeat_status` が `1` の通知を確認します。

## 確かめた範囲

通知を遅らせて一時的な失敗を見送る分、異常を伝えるまでの時間は長くなります。再通知を 0 にすると、長く未対応でも追加の知らせは来ません。実運用では、担当者・通知先・再通知・対応手順を一緒に決めます。

## チェックポイント

- Test と、実際の Down / Up 通知を別々に確認する
- Retries 2 のとき、3回目の連続失敗まで待つ理由を説明する
- すぐ知らせる必要がある障害で、同じ設定を使ってよいか考える

[3. 必要な操作を確かめる](./03-operation.md) / [5. 遅さを確かめる](./04-latency.md)
