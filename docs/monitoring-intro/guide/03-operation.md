# 3. 200 でも、必要な操作ができるとは限らない

## 困りごと

`/health` は 200 を返しています。でも利用者が商品を読み取れなければ、サービスを使えるとは言えません。今回は「ID が 1 の学習用データを読めるか」を1つだけ足します。

## 小さな追加: 既知データの内容も確かめる

```bash
python3 monitor.py --path /health
python3 monitor.py --path /items/1 --expect-name monitoring-demo
```

`/items/1` は SQLite から ID 1 の行を読み、JSON で返します。`--expect-name` を付けると、200 だけでなく、ID と名前が期待どおりかも判定します。実在の顧客データや個人情報は使いません。

## 安全な故障 A: DB ファイルを使えなくする

**戻すコマンドは `python3 labctl.py db-unavailable off` です。**

ターミナル B で、専用 DB ファイルを一時退避します。

```bash
python3 labctl.py db-unavailable on
python3 monitor.py --path /health
python3 monitor.py --path /items/1 --expect-name monitoring-demo
```

比較するのは次の2つです。

- `/health`: DB を使わないので 200 のまま
- `/items/1`: DB の読み取りが失敗し、503 になる

ここで止めたのは PostgreSQL のサービスではありません。SQLite には独立した DB サーバープロセスがなく、この故障は学習用ファイルを開けない状態です。Web アプリとデータへのアクセスが別々に失敗し得ることを、小さい環境で体験しています。

## 復旧 A

```bash
python3 labctl.py db-unavailable off
python3 monitor.py --path /items/1 --expect-name monitoring-demo
```

失敗した操作が成功に戻ることを確認します。

## 安全な故障 B: 200 で、違うデータが返る

**戻すコマンドは `python3 labctl.py wrong-data off` です。**

```bash
python3 labctl.py wrong-data on
python3 monitor.py --path /items/1
python3 monitor.py --path /items/1 --expect-name monitoring-demo
```

最初の確認は HTTP の状態だけを見るので成功します。次の確認は期待する名前も比べるので失敗します。同じ HTTP 200 でも、監視が答えている質問は違います。

## 復旧 B

```bash
python3 labctl.py wrong-data off
python3 monitor.py --path /items/1 --expect-name monitoring-demo
```

## 確かめた範囲

分かったのは、既知の一件について、HTTP → アプリ → DB 読み取りの経路と結果が正しいことです。全データの正しさ、書き込み、ログイン、支払い、外部 API は確認していません。

実サービスで操作監視を増やすときは、読み取り専用の安全な対象から始めます。注文や送金などの副作用を持つ操作を、本番に向けて気軽に繰り返してはいけません。

## チェックポイント

- 200 だけの確認で見逃した故障を2つ挙げる
- 自分のサービスで「1つだけ確認する操作」を選び、期待する結果を書く
- その操作が成功しても分からないことを1つ書く

[2. 繰り返して確かめる](./02-periodic.md) / [4. 遅さを確かめる](./04-latency.md)
