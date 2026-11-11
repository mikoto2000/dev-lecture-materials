# 6. 異常の時刻から、ログで原因を絞る

## 困りごと

Kuma が Down を示しました。でも DB、アプリ、通信のどれが原因かは、赤い表示だけでは決まりません。失敗した時刻と対象から証拠を探します。

## 小さな追加: アプリログを読む

```powershell
docker compose logs --tail 30 demo
```

ログの `timestamp` は UTC です。Kuma の画面がローカル時刻を表示している場合は、同じ時刻基準へ合わせて比べます。たとえばログの `10:00:00.000+00:00` は日本標準時の 19:00:00 です。ログの `path`、`status`、`duration_ms` から、どのリクエストに何を返し、何ミリ秒かかったかが分かります。

1. Kuma は、いつ、どの監視で、何に失敗したか
2. 同じころのアプリログに、そのリクエストはあるか
3. アプリへ届いているなら、どこで何が起きたか
4. その仮説を確かめるために、次に何を1つ調べるか

## 安全な故障: 一つだけ壊して調べる

**戻すコマンドは `docker compose exec demo python labctl.py db-unavailable off` です。**

```powershell
docker compose exec demo python labctl.py db-unavailable on
```

`demo-item` の Down を待ってから確認します。

```powershell
docker compose logs --tail 30 demo
docker compose exec demo python labctl.py inspect
```

Kuma の HTTP 503 と同じ時刻の `/items/1` のログを探します。今回の故障では `status` が `503`、`db_error` が `SQLITE_CANTOPEN` になります。`inspect` で `database_parked` が `true` になっていれば、学習用ファイルは退避中です。

## 復旧

```powershell
docker compose exec demo python labctl.py db-unavailable off
```

Kuma が Up に戻り、アプリログも正常な応答へ戻ることを確認します。

## 確かめた範囲

ログと対象データの状態を合わせて、今回の故障の原因を絞れました。ただし「503 なら必ず DB の問題」とは限りません。

アプリを止めた場合には、停止中のリクエストはアプリログに届きません。ログがない理由は、通信の問題だけとは限りません。別のログを見ている、記録が遅れている、記録処理が壊れている可能性もあります。

次に調べる項目は、その仮説に合わせて選びます。たとえば DB の応答が遅いなら、該当クエリーやロックを調べます。保存に失敗するなら対象の保存先、全体が遅いなら対象プロセスの状態が候補です。最初から全部のグラフを並べる必要はありません。

## チェックポイント

「観測した事実」「考えている原因」「次に確かめること」を分けて3行のメモを書きます。`demo-item` の復旧時刻も記録します。

[5. 遅さを確かめる](./04-latency.md) / [7. 保存先の容量を読む](./09-disk.md)
