# 準備: Uptime Kuma と実験アプリを用意する

## 実行場所をそろえる

本編は **Windows の PowerShell** で実行します。Docker Desktop が起動し、Linux コンテナーを使えることが前提です。WSL 2 バックエンドの準備や Docker Desktop の導入は、[公式の Windows 手順](https://docs.docker.com/desktop/setup/install/windows-install/)に沿って勉強会の前に済ませます。組織の利用条件も確認してください。

```powershell
docker version
docker compose version
```

Docker の Client と Server の両方が表示されること、Compose V2 が使えることを確認します。`docker` コマンドはあっても Server に接続できなければ、まだ実験を始められません。

本編では Ubuntu の Bash へ移りません。以前の自作 Python 監視を試したい方は、環境を分けた[補足](../appendix-custom-checker.md)を参照してください。

## 配布ファイルを置く

[教材トップ](../index.md)から ZIP をダウンロードし、エクスプローラーで展開します。`compose.yaml` と `Dockerfile` がある `monitoring-lab` フォルダーを PowerShell で開きます。例としてダウンロードフォルダーへ展開した場合は、次のようになります。実際の展開先に読み替えてください。

```powershell
Set-Location "$HOME\Downloads\monitoring-lab"
Get-ChildItem
```

Kuma は `louislam/uptime-kuma:2.5.5` に固定しています。`latest` や開発版へ置き換えず、まず同じ版で進めましょう。アプリは同梱の Dockerfile からビルドします。

## 壊す前に、戻し方を知る

停止させたアプリは、次のコマンドで戻せます。

```powershell
docker compose start demo
```

データと待ち時間の故障は、アプリが起動中なら個別に戻せます。

```powershell
docker compose exec demo python labctl.py db-unavailable off
docker compose exec demo python labctl.py wrong-data off
docker compose exec demo python labctl.py delay 0
```

実験アプリの状態を初期化するときは、アプリだけを止めてから専用データを作り直します。**アプリの学習用 DB とログが初期化されます。Kuma の監視設定は残ります。**

```powershell
docker compose stop demo
docker compose run --rm demo python labctl.py reset
docker compose up -d demo
```

初期化前に残したい記録を保存します。共有コンテナーを止めたり、`docker system prune` でまとめて削除したりする必要はありません。

## 起動する

```powershell
docker compose up -d --build
docker compose ps
```

初回はイメージの取得に時間がかかります。Kuma の起動・データベース準備を待ち、ブラウザーで次を開きます。

- Uptime Kuma: [http://127.0.0.1:13001](http://127.0.0.1:13001)
- 実験アプリ: [http://127.0.0.1:18080/health](http://127.0.0.1:18080/health)

Kuma の初期画面では、データベースとして **SQLite** を選びます。その後、実験用の管理者アカウントを自分で作成してください。パスワードを教材、チャット、スクリーンショットへ書き込まないでください。

本教材の画面項目は英語表記を基準に説明します。必要なら画面の言語を English にそろえます。日本語表示でも機能は同じです。

起動に失敗した場合は、`docker compose logs --tail 30 kuma` で状態を確認し、[困ったとき](../troubleshooting.md)へ進みます。

## 二つの localhost を区別する

ブラウザーは Windows からアクセスするので、`127.0.0.1:13001` を使います。一方、Kuma はコンテナー内で動いています。Kuma にとっての `localhost` は Kuma 自身です。

Kuma に登録する監視先は **`http://demo:18080/health`** です。Compose の同じネットワークにあるサービス名 `demo` を使います。画面を開く URL と、監視先の URL は役割が違います。

Kuma の設定・履歴とアプリのデータは、別々の専用名前付きボリュームに保存します。単なる stop/start や down では消えません。故障設定も再起動だけでは解除されないので、解除コマンドを使います。

[教材トップ](../index.md) / [1. URL を登録する](./01-url.md)
