# 4. 通知を試し、ノイズを減らす

## 困りごと

画面を見ていなければ Down に気づけません。一方、同じ障害で何度も通知すると、大事な知らせを見落としやすくなります。

## 小さな追加: ローカルだけの通知先

この章では Slack やメールの認証情報を使いません。Kuma の **Webhook** 通知を、同じ Compose 内の小さな通知受信器へ送ります。受信器はアプリと別のサービスなので、demo を止めても通知を受け取れます。

```powershell
docker compose --profile notifications up -d notification-sink
```

`demo-health` の Edit 画面から **Setup Notification** を開きます。

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

保存した通知先を `demo-health` に割り当て、監視も保存します。Test の成功は通知経路の確認です。監視に割り当てたことや、実際の Down / Up 通知まで成功することは、次の実験で確かめます。

受信器は教材用の記録先です。ここへ届いたことは、人がメッセージを読んだことの証明にはなりません。

## 安全な故障: 本当の Down と Up を通知させる

**復旧コマンドは `docker compose start demo` です。**

```powershell
docker compose stop demo
```

Down を確認してから受信器のログを見ます。続いて復旧させます。

```powershell
docker compose start demo
docker compose --profile notifications logs --tail 20 notification-sink
```

次の成功確認の後に Up の通知も受信することを確かめます。

## 小さな追加: 連続する失敗だけを知らせる

`demo-health` の Edit で次を設定します。

- Retries: **2**
- Heartbeat Retry Interval: **20 秒**
- Resend Notification if Down X times consecutively: **0**（再通知なし）

Retries が 2 の場合、最初の2回の失敗は **Pending** として扱われ、3回目の連続失敗で Down になります。「2回失敗で通知」ではありません。Pending 中は再試行間隔、Down 確定後は通常の確認間隔が使われます。

もう一度 demo を止め、Pending → Down を観察します。失敗が続いても、再通知を 0 にした同じ監視から Down 通知が増え続けないことを確認します。別の監視や Test ボタンからの通知とは分けて数えます。

## 復旧

```powershell
docker compose start demo
```

次の成功確認で Up へ戻り、復旧通知が届くことを確認します。まだ Pending の間に成功へ戻った一時的な失敗は、Down 確定後の復旧と区別します。

この教材では Kuma の標準動作を使います。自作スクリプト版にあった「連続2回の成功で復旧」という条件を、Kuma の HTTP 監視へ同じように設定できるとは説明しません。

## 確かめた範囲

通知を遅らせて一時的な失敗を見送る分、異常を伝えるまでの時間は長くなります。再通知を 0 にすると、長く未対応でも追加の知らせは来ません。実運用では、担当者・通知先・再通知・対応手順を一緒に決めます。

## チェックポイント

- Test と、実際の Down / Up 通知を別々に確認する
- Retries 2 のとき、3回目の連続失敗まで待つ理由を説明する
- すぐ知らせる必要がある障害で、同じ設定を使ってよいか考える

[3. 必要な操作を確かめる](./03-operation.md) / [5. 遅さを確かめる](./04-latency.md)
