# Uptime Kuma と Compose のローカル監視ラボ

Windows の PowerShell と、起動済みの Docker Desktop（Linux コンテナ）を使います。
ホストへの Python のインストールは不要です。Python は学習用コンテナの中だけで動きます。
初回のイメージ取得にはインターネット接続が必要です。外部通知先や本番環境は使いません。

ZIP をすべて展開し、PowerShell で `compose.yaml` のあるフォルダーへ移動してください。
単一の Python ファイルだけをダウンロードしても、この手順は実行できません。

## 1. 起動する

```powershell
docker compose version
docker compose config
docker compose up -d --build
docker compose ps
```

ブラウザーで http://127.0.0.1:13001 を開きます。Uptime Kuma は `2.5.5` に固定しています。
初回はローカルの SQLite と管理者アカウントを設定します。この実験用に作ったパスワードを使い、
実在する外部サービスのパスワードを流用しないでください。画面が開かない場合は数十秒待ち、
`docker compose logs --tail 30 kuma` で起動状況を確認します。

- ブラウザーからの Kuma：`http://127.0.0.1:13001`
- ブラウザーからのアプリ：`http://127.0.0.1:18080/health`
- Kuma に入力する監視 URL：`http://demo:18080/health` または `http://demo:18080/items/1`

Kuma の画面に `localhost` や `127.0.0.1` を監視先として入力すると、Kuma 自身のコンテナを
指します。Compose のサービス名 `demo` を使ってください。ホストに公開する 2 つのポートは
ループバック限定です。外部公開、Docker ソケットの共有、特権コンテナは不要です。

## 2. 監視して故障を入れる

Kuma で HTTP(s) モニターを追加し、最初は `http://demo:18080/health` を設定します。
次に `/items/1` 用の HTTP(s) モニターを追加します。名前、間隔、再試行、タイムアウト、
本文の検証条件は、教材の各章の指定に合わせて変更します。

```powershell
docker compose stop demo
docker compose start demo
docker compose exec demo python labctl.py db-unavailable on
docker compose exec demo python labctl.py db-unavailable off
docker compose exec demo python labctl.py wrong-data on
docker compose exec demo python labctl.py wrong-data off
docker compose exec demo python labctl.py delay 0.8
docker compose exec demo python labctl.py delay 2
docker compose exec demo python labctl.py delay 0
docker compose exec demo python labctl.py inspect
docker compose logs --tail 20 demo
```

一行ずつ実行し、故障中と解除後を観察します。すべてを一括実行すると変化を見逃します。

- `stop demo`：アプリを停止します。Kuma は起動したままです。
- `db-unavailable on`：専用 SQLite ファイルを一時退避します。`/health` は 200 のまま、
  SQLite を毎回読み取り専用で開いて SELECT する `/items/1` は 503 になります。
  存在しない DB を勝手に新規作成することはありません。
- `wrong-data on`：SQLite の `name` が `wrong-demo` になります。HTTP 200 だけでは検出できません。
  正常値は `{"id": 1, "name": "monitoring-demo"}` です。
- `delay`：`/items/1` にだけ 0〜2 秒の待ち時間を入れます。グラフでの遅延観察と、
  タイムアウトによる DOWN 判定は分けて考えます。

SQLite はファイル型 DB です。この実験は、独立した DB サーバーの停止やネットワーク障害を
そのまま再現するものではありません。

## 3. ローカルで通知の到着を確かめる

通知の章に進んだら、独立した受信コンテナを追加します。

```powershell
docker compose --profile notifications up -d notification-sink
docker compose logs --tail 20 notification-sink
```

Kuma の通知設定で種類 `Webhook`、送信先 `http://notification-sink:18081/`、
本文形式 `application/json` を設定します。カスタム本文や認証情報は不要です。
通知名は `local-lab` などの学習用の名前にします。テスト送信を実行して保存し、
対象モニターにその通知を割り当てて保存します。

`docker compose logs --tail 20 notification-sink` に `notification_received` と受信時刻が
出たことを確認します。テスト送信の成功だけで、故障通知まで届いたとは判断しません。
次に `docker compose stop demo` で DOWN、`docker compose start demo` で UP を発生させ、
それぞれの通知を受信ログで確認します。受信コンテナはアプリ停止中も動き続けます。

受信先は Compose の内部ネットワークだけで使い、ホストにはポートを公開しません。
受信本文は最大 8 KiB、本文読み取りは最大 3 秒で、ログは限られたフィールドだけです。
名前・メッセージには学習用の文字列だけを使い、個人情報や秘密情報は送らないでください。
この受信プログラムに監視機能や外部への送信機能はありません。

## 4. 保存、再開、アプリだけの初期化

Kuma の設定・履歴は `kumadata`、アプリの DB・故障設定・ログは `labstate` という
名前付きボリュームに保存します。実際のリソース名にはプロジェクト名が付きます。
初回に空の `labstate` だけを初期化し、以後の再起動では DB や故障設定を保持します。
DB を退避した故障も、再起動だけで勝手に復旧しません。

```powershell
docker compose stop demo kuma
docker compose start demo kuma
```

通知の受信コンテナも停止・再開したい場合は、同様に `notification-sink` を指定します。

コンテナを削除してもデータを残す場合は、次を使います。

```powershell
docker compose --profile notifications down
docker compose up -d
```

通知実験を再開する場合は、受信コンテナも再度起動します。

```powershell
docker compose --profile notifications up -d notification-sink
```

アプリの状態だけを初期化するには、必ずアプリを停止してから実行します。
Kuma の設定と監視履歴は消えません。モニターを動かしていれば、この停止も記録されます。

```powershell
docker compose stop demo
docker compose run --rm demo python labctl.py reset
docker compose up -d demo
```

`reset` は専用 DB、既知の故障設定、アプリのログを作り直します。
稼働中に `docker compose exec demo python labctl.py reset` を実行しないでください。

### 明示的な全消去：やり直すと決めた場合だけ

次のコマンドは、この Compose プロジェクトの名前付きボリュームも削除します。
Kuma のアカウント、監視設定、履歴、アプリの状態がすべて失われ、元には戻せません。

```powershell
docker compose --profile notifications down --volumes
```

## 安全に片付けるための注意

- プロジェクト名は `monitoring-intro-lab` です。他の教材のコンテナやボリュームは操作しません。
- 同じ PC で複数人・複数コピーを同時に使う場合は、たとえば `docker compose -p monitoring-pair2`
  をすべての操作で一貫して使い、`compose.yaml` のホスト側ポート 13001 と 18080 も空いている
  別番号へ変更します。コンテナ側のポートと Kuma の監視 URL は変更しません。
- ポートが競合した場合は、何が使っているか確認します。知らないプロセスは停止しません。
- Docker 全体を対象にした削除コマンドや、一括クリーンアップは使いません。
- `requests.jsonl` はアプリの実験ログです。実験中に増えるため、不要になったら上の停止・reset
  手順で片付けます。Compose の標準出力ログは各サービス最大 1 MiB × 3 ファイルです。
- これは信頼できるローカル環境での学習用です。本番運用の堅牢化・バックアップ設計ではありません。

## 任意の付録と開発者向けテスト

自作の `monitor.py` と `watchdog.py` は [任意の付録](README-appendix.md) に残しています。
本編の監視は Uptime Kuma が担当し、付録の Python 実行は本編の前提条件ではありません。

教材の開発者は Python 3.10 以上で `python3 test_container.py` と `python3 test_lab.py` を実行できます。
後者はポート 18080 が空いている必要があります。前者は一時ディレクトリと動的ポートを使います。
利用者の実験データは初期化しません。コンテナ構成の静的検証と Docker 上の統合テストは
リポジトリの `scripts/check-monitoring-compose.py` と `scripts/test-compose-monitoring.py` です。
