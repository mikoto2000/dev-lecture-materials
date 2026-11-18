# 2. LogQL で時間と条件を絞る

## この章のゴール

エラーと遅い応答を実際に発生させ、Explore で対象のログを探します。

## 先に解除方法を確認する

異常を解除するコマンドは、いつでも次の1行です。`compose.yaml` のあるフォルダーで実行します。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

`python` はコンテナー内で実行するため、PC にインストールする必要はありません。故障モードは再起動後も残ります。異常の実験は1つずつ行い、終わったら `normal` へ戻します。

## 5xx を発生させる

```powershell
docker compose exec -T demo python /lab/demo.py mode error
```

`/items` が503を返すようになります。自動アクセスは継続しています。Explore の時間範囲を **Last 5 minutes** にし、次の式を実行します。

```text
{job="access-log-lab"} | json | status >= 500 | __error__=""
```

新しい503の行が見つかれば成功です。少し待ってから **Run query** で更新してください。

| 部分 | 意味 |
|---|---|
| `{job="access-log-lab"}` | このラボのログを選ぶ |
| `| json` | JSON の項目を取り出す |
| `| status >= 500` | ステータスを数値として比較する |
| `| __error__=""` | 解析・変換でエラーになった行を除く |

`__error__` のある行を除外すると、壊れたログは件数からも除かれます。本番では、それらが増えていないかを別に監視します。

503の行を1つ開き、時刻・パス・ID を控えます。次の式の ID を、控えた値に置き換えて検索します。

```text
{job="access-log-lab"} | json | request_id="ここを実際のIDに置き換える"
```

正常へ戻してから、次の実験へ進みます。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

## 200のまま遅い応答を探す

```powershell
docker compose exec -T demo python /lab/demo.py mode slow
```

`/items` の処理で約1.2秒待ちます。ステータスは200のままです。

```text
{job="access-log-lab"} | json | request_time_ms >= 1000 | __error__=""
```

1000 ms 以上の200が表示されます。5xx だけを探す式では見つかりません。終わったら `normal` に戻します。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

確認: 過去の503が表示されても、現在も故障中とは限りません。右上の時間範囲を絞り、各行の時刻を確認してください。

[前の章: 1行を読む](./01-read.md) / [次の章: 件数と割合を比べる](./03-measure.md)
