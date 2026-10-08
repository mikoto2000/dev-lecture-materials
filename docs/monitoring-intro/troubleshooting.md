# 困ったとき

## Docker の Server に接続できない

Docker Desktop が起動しているか、Linux コンテナーになっているか確認します。PowerShell の `docker version` で Client だけでなく Server も表示される必要があります。インストール・WSL 2 バックエンドの準備は[公式手順](https://docs.docker.com/desktop/setup/install/windows-install/)を確認します。

## compose.yaml が見つからない

`Get-Location` と `Get-ChildItem` で、配布 ZIP の展開先を確認します。すべてのコマンドを同じ `compose.yaml` のある場所で実行します。フォルダー名だけでなく、プロジェクト名も同じものを使います。

## ポートが既に使われている

既に起動した実験環境や、以前の Python アプリがないか確認します。自分で起動した対象だけを停止します。知らないプロセスをまとめて停止しないでください。別のサービスが 13001 / 18080 番を使っている場合は講師へ相談します。

## Kuma の画面は開くが監視は Down

監視 URL が `http://demo:18080/health` か確認します。Kuma 内の `localhost` は Kuma 自身です。ブラウザーから見る `127.0.0.1:18080` を、そのまま監視設定へコピーしないでください。

```powershell
docker compose ps
docker compose logs --tail 30 demo
docker compose logs --tail 30 kuma
```

## health は Up だが item は Down

前の故障が残っていないか確認します。

```powershell
docker compose exec demo python labctl.py inspect
docker compose exec demo python labctl.py db-unavailable off
docker compose exec demo python labctl.py wrong-data off
docker compose exec demo python labctl.py delay 0
```

起動し直すだけでは、保存された故障設定は消えません。[準備](./guide/00-prepare.md)の初期化手順は、必要な記録を保存してから実行します。

## Test は成功したのに Down 通知が来ない

通知先を監視へ割り当てて保存したか、まだ Pending 中ではないか確認します。Test は通知経路を試す操作です。監視状態の変化による通知は、別に試験します。

```powershell
docker compose --profile notifications ps
docker compose --profile notifications logs --tail 20 notification-sink
```

## 遅くなっても Up のまま

本文が正しく、タイムアウト以内に返れば Up になる場合があります。応答時間のグラフを見てください。500 ms を超えた成功応答への警告通知を、標準の HTTP 監視で設定したわけではありません。

## 通知が増え続ける

再通知の条件、複数の監視への通知割り当て、Test ボタンの操作を分けて確認します。通知の重複を避けたい実験では、Resend Notification を 0 にします。

## Kuma 再起動後の古い画面が気になる

ブラウザーを再読み込みし、最後の確認時刻や新しい履歴が増えることを確認します。過去の緑色だけで、現在も監視できているとは判断しません。

[教材トップ](./index.md)
