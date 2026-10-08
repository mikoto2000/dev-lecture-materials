# 3. 200 でも、必要な操作ができるとは限らない

## 困りごと

`demo-health` は Up ですが、DB から必要なデータを読めるでしょうか。利用者が必要な操作へ、監視対象を1つだけ広げます。

## 小さな追加: キーワードを含む応答を確かめる

**Add New Monitor** から、別の監視を追加します。

| 項目 | 設定 |
|---|---|
| Monitor Type | HTTP(s) - Keyword |
| Friendly Name | demo-item |
| URL | `http://demo:18080/items/1` |
| Keyword | `monitoring-demo` |
| Heartbeat Interval | 20 秒 |
| Retries | 0 |
| Request Timeout | 1 秒 |

Keyword の反転条件は使いません。通知先はまだ設定しません。保存後、Up の表示を確認します。

`/items/1` は学習用 SQLite の ID 1 の行を読み、JSON を返します。キーワード監視では本文に `monitoring-demo` が含まれるかを確認します。JSON の構造や ID 自体まで厳密に検証する条件ではありません。

## 安全な故障 A: DB ファイルを使えなくする

**戻すコマンドは `docker compose exec demo python labctl.py db-unavailable off` です。**

```powershell
docker compose exec demo python labctl.py db-unavailable on
```

次の確認を待ち、2つの監視を比較します。

- `demo-health`: DB を使わないため Up のまま
- `demo-item`: DB を開けず 503 になり、Down

これは学習用 SQLite ファイルを退避する実験です。独立した DB サーバープロセスを停止したわけではありません。

## 復旧 A

```powershell
docker compose exec demo python labctl.py db-unavailable off
```

`demo-item` が Up に戻ったことを確かめます。

## 安全な故障 B: 200 で、違うデータが返る

**戻すコマンドは `docker compose exec demo python labctl.py wrong-data off` です。**

```powershell
docker compose exec demo python labctl.py wrong-data on
```

ブラウザーで [実際の応答](http://127.0.0.1:18080/items/1)を見ると、名前が `wrong-demo` になっています。HTTP は 200 でも、`demo-item` はキーワードが見つからず Down になります。

## 復旧 B

```powershell
docker compose exec demo python labctl.py wrong-data off
```

次の確認で Up に戻ることを確かめます。

## もう少し厳密にする: JSON Query

JSON の構造と値まで確かめたい場合は、追加の監視タイプ **HTTP(s) - Json Query** を使えます。URL は同じ `/items/1` です。

- Json Query Expression: `id = 1 and name = "monitoring-demo"`
- 条件: `==`
- Expected Value: `true`（引用符なし）

これは **JSONata** の式です。JSONPath とは書き方が違います。Kuma は式の結果と期待値を比較します。条件を追加したら、正常時だけでなく wrong-data の故障と復旧も同じように試します。

## 確かめた範囲

既知の1件について、HTTP → アプリ → DB 読み取りの経路を確認できました。全データの正しさ、書き込み、ログイン、支払い、外部 API は確認していません。実サービスでは、安全な読み取り専用の操作から始めましょう。

## チェックポイント

- `/health` が Up でも見逃す故障を説明する
- HTTP の状態、キーワード、JSON の値が答える問いの違いを整理する
- 成功しても分からない操作を1つ書く

[2. 停止と復旧を見る](./02-periodic.md) / [4. 遅さを確かめる](./04-latency.md)
