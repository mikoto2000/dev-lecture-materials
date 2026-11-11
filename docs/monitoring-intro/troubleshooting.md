# 困ったとき

## Docker の Server に接続できない

Docker Desktop が起動しているか、Linux コンテナーになっているか確認します。PowerShell の `docker version` で Client だけでなく Server も表示される必要があります。インストール・WSL 2 バックエンドの準備は[公式手順](https://docs.docker.com/desktop/setup/install/windows-install/)を確認します。

Docker Engine を直接導入した場合は、Ubuntu の Bash で `docker version` と `systemctl is-active docker` を実行します。デーモンの起動やグループ設定は [Vol.0 開発環境構築](../コンテナで構築する開発環境/Vol0.md)を参照します。

## compose.yaml が見つからない

`Get-Location` と `Get-ChildItem` で、配布 ZIP の展開先を確認します。すべてのコマンドを同じ `compose.yaml` のある場所で実行します。フォルダー名だけでなく、プロジェクト名も同じものを使います。

## ポートが既に使われている

同じラボのコンテナーが起動済みか `docker compose ps` で確認します。別のサービスがポートを使っている場合は、`compose.yaml` の `ports` でホスト側の番号だけを空いている番号に変えます。たとえば `127.0.0.1:18080:18080` を `127.0.0.1:28080:18080` に変更します。この場合は Windows のブラウザーでも 28080 番を開きます。Kuma の監視先 `http://demo:18080/health` は引き続きコンテナー側の 18080 番を使います。

## Kuma の画面は開くが監視は Down

監視 URL を確認します。`demo-health` は `http://demo:18080/health`、`demo-item` は `http://demo:18080/items/1` です。Kuma 内の `localhost` は Kuma 自身を指すため、監視 URL には Compose のサービス名 `demo` を使います。

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

## stats コマンドが使えない

`docker compose version` と `docker compose stats --help` を確認します。古い Compose では利用できないことがあります。その場合は `docker compose ps` で `demo` と `kuma` が起動中であることを確認します。`NAME` 列のコンテナー名を `docker stats --no-stream` の引数に指定してください。以下は既定のプロジェクト名を使った場合の例です。

```powershell
docker stats --no-stream monitoring-intro-lab-demo-1
docker stats --no-stream monitoring-intro-lab-kuma-1
```

## df の空き容量が Windows と違う

`/lab/.state` を含む Linux 側のファイルシステムを読んでいます。Windows のドライブ空き容量と同じ表示になるとは限りません。コンテナーのディスク容量やメモリー上限を、ホスト全体の余裕と読み替えないでください。

## Ping に失敗するが HTTP は成功する

ICMP と HTTP は別の確認です。ICMP が許可されない環境や、途中の制限によって Ping だけ失敗することがあります。教材のためにファイアウォールやネットワーク権限を変更せず、監視地点と対象、HTTP の実測を確認してください。

[教材トップ](./index.md)
