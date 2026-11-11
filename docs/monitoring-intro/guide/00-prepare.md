# 準備: Uptime Kuma と実験アプリを用意する

## 実行場所をそろえる

本編は **Windows の PowerShell** で実行します。Docker Desktop が起動し、Linux コンテナーを使えることが前提です。WSL 2 バックエンドの準備や Docker Desktop の導入は、[公式の Windows 手順](https://docs.docker.com/desktop/setup/install/windows-install/)に沿って勉強会の前に済ませます。組織の利用条件も確認してください。

```powershell
docker version
docker compose version
docker compose stats --help
```

Docker の Client と Server の両方が表示されることを確認します。教材は `docker compose` で実行する Compose v2 と v5 に対応します。8章で使う `docker compose stats` のヘルプも表示できることを確認してください。[Docker Compose のバージョン](https://docs.docker.com/compose/intro/history/)

`stats` が使えない場合も準備は続けられます。8章の計測では、[代替手順](../troubleshooting.md)を使ってください。

### WSL 2 に Docker Engine を直接導入済みの場合

Ubuntu の Bash で `docker version` と `docker compose version` が動く場合は、その Bash で本編を進められます。ZIP を Ubuntu のホーム配下に展開し、`cd` で `compose.yaml` のあるフォルダーへ移動します。以降は `docker compose` も Bash で実行し、`Get-Date -Format o` は `date --iso-8601=seconds` に読み替えます。Windows のブラウザーで開く URL は共通です。

自作の Python 監視を試す場合は、環境を分けた[補足](../appendix-custom-checker.md)を参照してください。

## 配布ファイルを置く

[教材トップ](../index.md)から ZIP をダウンロードします。PowerShell を使う場合は、エクスプローラーで展開し、`compose.yaml` と `Dockerfile` があるフォルダーを開きます。次はダウンロードフォルダーへ展開した例です。実際の展開先に読み替えてください。

```powershell
Set-Location "$HOME\Downloads\monitoring-lab"
Get-ChildItem
```

Kuma は `louislam/uptime-kuma:2.5.5` に固定しています。`latest` や開発版へ置き換えず、まず同じ版で進めましょう。アプリは同梱の Dockerfile からビルドします。

同じ Docker Engine で複数のラボを使う場合は、配布 README の「安全に片付けるための注意」に沿って Compose プロジェクト名とホスト側ポートを分けます。`compose.yaml` の `name` が固定されているため、ZIP を別のフォルダーへ展開するだけではプロジェクトを分けられません。

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

`reset` の出力にある `app and monitors` は、同じ `.state` を使うアプリと補足の自作監視を指します。本編の Kuma は別のボリュームを使うため、この手順では起動したままで進められます。停止中のアプリを Kuma が確認すると、Down が記録される場合があります。

## 起動する

```powershell
docker compose up -d --build
docker compose ps
```

初回はイメージの取得に時間がかかります。Kuma の起動・データベース準備を待ち、ブラウザーで次を開きます。

- Uptime Kuma: [http://127.0.0.1:13001](http://127.0.0.1:13001)
- 実験アプリ: [http://127.0.0.1:18080/health](http://127.0.0.1:18080/health)

`docker compose ps` で Kuma が起動中（`health: starting`）の場合や、ブラウザーに応答が返らない場合は、数秒待って再読み込みします。

### 初回だけ行う設定

1. データベースの選択画面で **SQLite** を選び、**Next** を押す
2. **Create your admin account** が表示されたら、**Username** に実験用のユーザー名を入力する。**Password** と **Repeat Password** に同じ実験用パスワードを入力し、**Create** を押す
3. ダッシュボードで **Add New Monitor** の表示を確認する

すでに初期設定を済ませた環境では、作成したアカウントでログインします。

他のサービスのパスワードは流用せず、実験用に新しく作ります。パスワードを教材、チャット、スクリーンショットへ書き込まないでください。

本教材の画面項目は英語表記を基準に説明します。初期設定画面では **Language** から **English** を選べます。ログイン後に切り替える場合は、右上のユーザーメニューから「設定」→「外観」を開き、「言語」で **English** を選びます。

起動に失敗した場合は、`docker compose logs --tail 30 kuma` で状態を確認し、[困ったとき](../troubleshooting.md)へ進みます。

## 二つの localhost を区別する

ブラウザーは Windows からアクセスするので、`127.0.0.1:13001` を使います。一方、Kuma はコンテナー内で動いています。Kuma にとっての `localhost` は Kuma 自身です。

Kuma に登録する監視先は **`http://demo:18080/health`** です。Compose の同じネットワークにあるサービス名 `demo` を使います。画面を開く URL と、監視先の URL は役割が違います。

Kuma の設定・履歴とアプリのデータは、別々の専用名前付きボリュームに保存します。単なる stop/start や down では消えません。故障設定も再起動だけでは解除されないので、解除コマンドを使います。

## チェックポイント

- `docker version` で Client と Server の両方が表示される
- `docker compose ps` で kuma と demo が動いている
- ブラウザーで開く `127.0.0.1` と、Kuma に登録する `demo` の役割の違いを説明する
- 故障を起こす前に、戻し方のコマンドを確認した

[教材トップ](../index.md) / [1. URL を登録する](./01-url.md)
