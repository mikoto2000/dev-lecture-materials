# 準備: ログと集計スクリプト

## この章のゴール

配布ファイルを保存し、30行の練習用ログを読み出します。

## ファイルを保存する

作業用に空の `access-log-lab` フォルダーを作ります。[教材トップ](../index.md)の配布資料から、次の2ファイルを保存してください。

```text
access-log-lab/
  access.jsonl
  Measure-AccessLog.ps1
```

拡張子が `.txt` になっていないことを確認します。このログはすべて架空です。実際の利用者の情報や本番のログを追加する必要はありません。

PowerShell を開き、保存先へ移動します。パスは自分の保存先に変更してください。

```powershell
cd "$HOME\Downloads\access-log-lab"
$PSVersionTable.PSVersion
(Get-Content .\access.jsonl -Encoding UTF8).Count
Get-Content .\access.jsonl -Encoding UTF8 -TotalCount 1
```

行数が `30`、先頭行の `time` が `2026-11-18T00:00:00Z` なら準備完了です。以後のコマンドは、このフォルダーで実行します。

## スクリプトを実行する

```powershell
.\Measure-AccessLog.ps1 -Path .\access.jsonl -End '2026-11-18T00:01:00Z'
```

`Requests` が `10`、`State` が `OK` と出れば成功です。表示の並び方は PowerShell の版により異なります。`-End` は集計の終了時刻です。実行した日の時計に依存せず、同じ結果を確認できます。

実行ポリシーで止まった場合は、先にスクリプトをエディターで読み、[困ったとき](../troubleshooting.md)を確認してください。

[次へ: 1行を読む](./01-read.md)
