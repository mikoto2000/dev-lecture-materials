# 2. 時間と条件で絞る

## この章のゴール

「エラーがある」から一歩進めて、いつ、どのパスで、何件起きたかを読み取ります。

## JSON として読み出す

```powershell
$logs = @(Get-Content .\access.jsonl -Encoding UTF8 | ForEach-Object {
    $_ | ConvertFrom-Json
})
$logs | Select-Object -First 3 | Format-Table
```

この小さなログは全件をメモリーに読み込みます。数 GB の本番ログへそのまま使う手順ではありません。

## 時間窓を決める

09:01台に失敗が増えたという報告を想定します。UTC の `00:01:00` 以上、`00:02:00` 未満を選びます。

```powershell
$start = [DateTimeOffset]'2026-11-18T00:01:00Z'
$end = [DateTimeOffset]'2026-11-18T00:02:00Z'
$window = @($logs | Where-Object {
    [DateTimeOffset]$_.time -ge $start -and [DateTimeOffset]$_.time -lt $end
})
$window.Count
```

結果は `10` 件です。**開始を含み、終了を含まない**区間を使います。これで隣り合う時間窓の境界を重複して数えるのを防げます。

## 失敗と遅さを別々に探す

```powershell
$window | Where-Object { $_.status -ge 500 } |
    Format-Table time, path, status, request_time_ms, request_id

$window | Where-Object { $_.request_time_ms -ge 1000 } |
    Format-Table time, path, status, request_time_ms, request_id

$window | Group-Object path | Select-Object Name, Count
```

5xx は3件、1000 ms 以上は4件です。`req-015` は HTTP 200 でも1500 ms かかっています。エラーだけを見る監視では、成功した遅いリクエストを見落とします。パス別では `/items` が9件、`/missing` が1件です。

## 文字列検索との使い分け

```powershell
Select-String -Path .\access.jsonl -Pattern 'req-013'
```

既知の ID を探すときは文字列検索も便利です。ただし、文字列の `500` を探すだけでは処理時間や ID の一部まで一致する場合があります。ステータスの判定には、JSON の `status` フィールドを使います。

確認: 遅い4件のうち、5xx は何件でしょうか。両方の条件を `-and` で指定すると **3件** になります。2つの件数を足すと同じリクエストを重複して数えるため、注意してください。

[前へ: 1行を読む](./01-read.md) / [次へ: 件数と割合を比べる](./03-measure.md)
