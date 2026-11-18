<a id="top"></a>

# インフラ監視実践入門

監視の分類をまとめて覚える前に、**URL を1つ登録して、正常を示す緑色を見る**ところから始めます。困りごとが見つかったら、観測や設定を少しだけ足しましょう。

本編では OSS の **Uptime Kuma 2.5.5** を使います。監視プログラムを自作する必要はありません。監視対象には、安全に止めたり、学習用データを変えたりできる小さな Python / SQLite アプリを用意しました。Python や Spring の実装知識は不要です。

## できるようになること

- GUI で HTTP 監視を登録し、停止と復旧を確認する
- 通知のテストと、本当の異常・復旧の通知を区別する
- HTTP 200 でも、必要なデータが返らない状態を検知する
- 応答時間のグラフとタイムアウトの役割を区別する
- 異常の時刻からログを調べ、必要な容量・CPU・メモリー・通信の観測を選ぶ
- コンテナーの値とホストの値、1回の観察と継続監視の範囲を区別する

## 使うものと前提

本編のコマンド例は Windows の PowerShell と Docker Desktop の Linux コンテナーを前提にしています。WSL 2 に Docker Engine を直接導入済みの場合は、[準備の読み替え手順](#guide-00-prepare)で進められます。Uptime Kuma、実験アプリ、ローカル通知受信器を Docker Compose で動かします。

- PC への Python / Node.js の直接インストールは不要
- 外部の Slack、メール、Webhook アカウントや認証情報は不要
- アプリと画面は自分の PC のループバックだけに公開
- 本番環境、顧客データ、共有 DB は不使用

SQLite はファイル型の DB です。DB 故障の実験は、専用ファイルを一時退避して読めなくするものです。PostgreSQL サーバーの停止や、本番のネットワーク障害を再現したとは言いません。

## この順番にする理由

CPU 使用率、メモリー使用量、ディスク容量、ネットワーク遅延、アプリログはいずれも基本的な観測対象です。ただし、この5項目だけですべての障害が分かるわけではありません。最初に数値を集めることを目標にせず、**利用者の必要な操作ができるか**を先に確かめます。

この教材では、まず使えることを確認し、失敗と復旧を知らせます。続いて遅さを読み、その時刻のログから調べます。その後で保存先の容量、CPU・メモリー、通信へ観測を広げます。利用者に見える症状と、原因を絞るための内部情報を分ける考え方は、[Google SRE の監視解説](https://sre.google/sre-book/monitoring-distributed-systems/)も参考になります。

後半の資源観測は、まず対象を限定した読み取り専用のコマンドで試します。1回の確認だけで継続監視を構築したとは扱いません。履歴や自動通知が必要になった段階で、Prometheus / Grafana などへ進みます。

## 学習の順番

| 章 | 困りごと | 足すもの |
|---|---|---|
| [準備](#guide-00-prepare) | 安全に試す環境がない | Compose と専用データ保存先 |
| [1. URL を登録する](#guide-01-url) | 動いているか分からない | HTTP 監視1件 |
| [2. 停止と復旧を見る](#guide-02-periodic) | 見ていない間の停止が心配 | 定期確認と履歴 |
| [3. 必要な操作を確かめる](#guide-03-operation) | 200 なのに使えない | キーワード・JSON の内容確認 |
| [4. 通知を整える](#guide-05-alerts) | 異常に気づけない・何度も鳴る | ローカル通知、再試行、再通知の条件 |
| [5. 遅さを確かめる](#guide-04-latency) | 成功しても待たされる | 応答時間グラフとタイムアウト |
| [6. 原因を絞る](#guide-06-diagnose) | 失敗の理由が不明 | 該当時刻のログ |
| [7. 保存先の容量を読む](#guide-09-disk) | 保存に失敗する前に余裕を知りたい | 対象ファイルシステムの容量と inode |
| [8. CPU・メモリーを比べる](#guide-10-cpu-memory) | 遅さと資源の関係を調べたい | 対象コンテナーの使用量と時間の比較 |
| [9. 通信を分けて確かめる](#guide-11-network) | どこまで届いているか知りたい | 名前解決・ICMP の往復時間・損失 |
| [10. 監視自身を確かめる](#guide-07-watchdog) | 監視が止まると静かになる | 監視地点と共通障害の確認 |
| [整理と後片付け](#guide-08-review) | 次に何を増やせばよいか | 限界の整理と次の OSS への道筋 |

準備を除いて 3〜4 時間が目安です。前半の HTTP・通知・遅さまでを最初の回とし、ログと資源観測を次の回に分けても構いません。故障の解除方法を先に読み、正常・故障・復旧の3段階を記録します。

## 配布資料

- <a href="./monitoring-lab.zip" download>Compose と実験アプリ一式（ZIP）</a>
- <a href="./lab/README.md" download>ラボの起動・復旧・後片付け</a>
- [困ったとき](#troubleshooting)
- [講師用ガイド](#facilitator)
- [参考資料](#references)
- [補足: 自作監視の仕組みを読む](#appendix-custom-checker)

[準備へ進む](#guide-00-prepare)

[教材一覧](../index.md)

<a id="guide-00-prepare"></a>

## 準備: Uptime Kuma と実験アプリを用意する

### 実行場所をそろえる

本編は **Windows の PowerShell** で実行します。Docker Desktop が起動し、Linux コンテナーを使えることが前提です。WSL 2 バックエンドの準備や Docker Desktop の導入は、[公式の Windows 手順](https://docs.docker.com/desktop/setup/install/windows-install/)に沿って勉強会の前に済ませます。組織の利用条件も確認してください。

```powershell
docker version
docker compose version
docker compose stats --help
```

Docker の Client と Server の両方が表示されることを確認します。教材は `docker compose` で実行する Compose v2 と v5 に対応します。8章で使う `docker compose stats` のヘルプも表示できることを確認してください。[Docker Compose のバージョン](https://docs.docker.com/compose/intro/history/)

`stats` が使えない場合も準備は続けられます。8章の計測では、[代替手順](#troubleshooting)を使ってください。

#### WSL 2 に Docker Engine を直接導入済みの場合

Ubuntu の Bash で `docker version` と `docker compose version` が動く場合は、その Bash で本編を進められます。ZIP を Ubuntu のホーム配下に展開し、`cd` で `compose.yaml` のあるフォルダーへ移動します。以降は `docker compose` も Bash で実行し、`Get-Date -Format o` は `date --iso-8601=seconds` に読み替えます。Windows のブラウザーで開く URL は共通です。

自作の Python 監視を試す場合は、環境を分けた[補足](#appendix-custom-checker)を参照してください。

### 配布ファイルを置く

[教材トップ](#top)から ZIP をダウンロードします。PowerShell を使う場合は、エクスプローラーで展開し、`compose.yaml` と `Dockerfile` があるフォルダーを開きます。次はダウンロードフォルダーへ展開した例です。実際の展開先に読み替えてください。

```powershell
Set-Location "$HOME\Downloads\monitoring-lab"
Get-ChildItem
```

Kuma は `louislam/uptime-kuma:2.5.5` に固定しています。`latest` や開発版へ置き換えず、まず同じ版で進めましょう。アプリは同梱の Dockerfile からビルドします。

同じ Docker Engine で複数のラボを使う場合は、配布 README の「安全に片付けるための注意」に沿って Compose プロジェクト名とホスト側ポートを分けます。`compose.yaml` の `name` が固定されているため、ZIP を別のフォルダーへ展開するだけではプロジェクトを分けられません。

### 壊す前に、戻し方を知る

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

### 起動する

```powershell
docker compose up -d --build
docker compose ps
```

初回はイメージの取得に時間がかかります。Kuma の起動・データベース準備を待ち、ブラウザーで次を開きます。

- Uptime Kuma: [http://127.0.0.1:13001](http://127.0.0.1:13001)
- 実験アプリ: [http://127.0.0.1:18080/health](http://127.0.0.1:18080/health)

`docker compose ps` で Kuma が起動中（`health: starting`）の場合や、ブラウザーに応答が返らない場合は、数秒待って再読み込みします。

#### 初回だけ行う設定

1. データベースの選択画面で **SQLite** を選び、**Next** を押す
2. **Create your admin account** が表示されたら、**Username** に実験用のユーザー名を入力する。**Password** と **Repeat Password** に同じ実験用パスワードを入力し、**Create** を押す
3. ダッシュボードで **Add New Monitor** の表示を確認する

すでに初期設定を済ませた環境では、作成したアカウントでログインします。

他のサービスのパスワードは流用せず、実験用に新しく作ります。パスワードを教材、チャット、スクリーンショットへ書き込まないでください。

本教材の画面項目は英語表記を基準に説明します。初期設定画面では **Language** から **English** を選べます。ログイン後に切り替える場合は、右上のユーザーメニューから「設定」→「外観」を開き、「言語」で **English** を選びます。

起動に失敗した場合は、`docker compose logs --tail 30 kuma` で状態を確認し、[困ったとき](#troubleshooting)へ進みます。

### 二つの localhost を区別する

ブラウザーは Windows からアクセスするので、`127.0.0.1:13001` を使います。一方、Kuma はコンテナー内で動いています。Kuma にとっての `localhost` は Kuma 自身です。

Kuma に登録する監視先は **`http://demo:18080/health`** です。Compose の同じネットワークにあるサービス名 `demo` を使います。画面を開く URL と、監視先の URL は役割が違います。

Kuma の設定・履歴とアプリのデータは、別々の専用名前付きボリュームに保存します。単なる stop/start や down では消えません。故障設定も再起動だけでは解除されないので、解除コマンドを使います。

### チェックポイント

- `docker version` で Client と Server の両方が表示される
- `docker compose ps` で kuma と demo が動いている
- ブラウザーで開く `127.0.0.1` と、Kuma に登録する `demo` の役割の違いを説明する
- 故障を起こす前に、戻し方のコマンドを確認した

<a id="guide-01-url"></a>

## 1. URL を登録して、緑色を見る

### 困りごと

アプリを起動しました。でも、プロセスが動いているだけでは HTTP の返事が返るか分かりません。最初は URL を1つだけ登録します。

### 小さな追加: HTTP 監視1件

Uptime Kuma の **Add New Monitor** から、次の内容を設定します。項目名は英語表示です。

| 項目 | 設定 |
|---|---|
| Monitor Type | HTTP(s) |
| Friendly Name | demo-health |
| URL | `http://demo:18080/health` |
| Heartbeat Interval | 20 秒 |
| Retries | 0 |
| Request Timeout | 1 秒 |
| Accepted Status Codes | 既定の 200–299 |

ほかは既定値のまま保存します。最初の確認まで待ち、状態が **Up**、色が緑になることを確認します。アプリは 200 を返しますが、この設定で受け入れる範囲は 200–299 です。

状態が Down の場合は、まず URL の `demo` とポート番号を確認します。Kuma の URL 欄へ `localhost:18080` を入れないでください。

### 安全な故障: 登録先を一時的に存在しないパスへ変える

**復旧時は URL を `http://demo:18080/health` へ戻し、保存します。**

登録した監視を **Edit** し、URL の末尾だけを `/missing` に変更して **Save** を押します。編集を保存しても編集画面に留まります。左の監視一覧で `demo-health` を選び、詳細画面へ戻ります。

次の確認で Down になり、詳細の履歴に HTTP 404 のエラーが表示されます。アプリや DB は変更しません。

### 復旧

**Edit** で URL を `/health` に戻し、**Save** を押します。左の監視一覧から詳細を開き、最新の結果が Up に戻ることを確認します。

### 確かめた範囲

この時点で分かったのは、Kuma のコンテナーから対象 URL の応答を受け取れたことです。DB を読めること、利用者の操作が成功すること、インターネットからアクセスできることは、まだ分かりません。

### チェックポイント

- Up と Down をそれぞれ画面で確認する
- Kuma の URL 欄と Windows のブラウザーで、ホスト名が違う理由を説明する
- この1件が成功しても分からないことを1つ書く

<a id="guide-02-periodic"></a>

## 2. アプリの停止と復旧を見つける

### 困りごと

手で URL を開く確認では、見ていない間の停止に気づけません。前章で登録した監視が、定期的に確認した履歴を見ます。

### 小さな追加: 履歴と時刻を読む

`demo-health` の詳細画面で、最近の確認結果、応答時間、イベントを確認します。確認間隔は 20 秒、Retries は 0、タイムアウトは 1 秒のままです。

タイムアウトはリクエストを待つ上限の設定です。実際の失敗確定までには OS・接続・処理の時間差があり、時計の秒と完全には一致しません。20 秒間隔だからといって、故障後ちょうど 20 秒で必ず通知されるという意味でもありません。

### 安全な故障: アプリだけを止める

**復旧コマンドは `docker compose start demo` です。Kuma は止めません。**

```powershell
docker compose stop demo
```

次の監視が行われるまで待ち、`demo-health` が Down になることを確認します。接続できない理由と時刻を記録します。

ブラウザーを再読み込みしても、確認間隔そのものは短くなりません。結果が変わるのを落ち着いて待ちます。

### 復旧

```powershell
docker compose start demo
```

次の確認で Up に戻ることを確認します。アプリを起動した事実だけで復旧とせず、**失敗した監視が再び成功する**ところまで見ます。

### 確かめた範囲

Kuma が動いている間は人がコマンドを繰り返さなくても確認できます。ただし確認と確認の間に発生して戻った短い障害は、見逃すことがあります。

今はダッシュボードを見ている人しか変化に気づけません。外部の人に通知を届ける設定はまだありません。

### チェックポイント

- 停止・Down・再起動・Up の時刻を並べる
- 確認間隔を延ばすと、確認回数と発見までの時間がどう変わるか考える
- 次章へ進む前に demo が Up へ戻っていることを確認する

<a id="guide-03-operation"></a>

## 3. 200 でも、必要な操作ができるとは限らない

### 困りごと

`demo-health` は Up ですが、DB から必要なデータを読めるでしょうか。利用者が必要な操作へ、監視対象を1つだけ広げます。

### 小さな追加: キーワードを含む応答を確かめる

**Add New Monitor** から、別の監視を追加します。

| 項目 | 設定 |
|---|---|
| Monitor Type | HTTP(s) - Keyword |
| Friendly Name | demo-item |
| URL | `http://demo:18080/items/1` |
| Keyword | `monitoring-demo` |
| Heartbeat Interval | 20 秒 |
| Retries | 0 |
| Request Timeout | 1 秒 |

Keyword の反転条件は使いません。通知先はまだ設定しません。保存後、Up の表示を確認します。

`/items/1` は学習用 SQLite の ID 1 の行を読み、JSON を返します。キーワード監視では本文に `monitoring-demo` が含まれるかを確認します。JSON の構造や ID 自体まで厳密に検証する条件ではありません。

### 安全な故障 A: DB ファイルを使えなくする

**戻すコマンドは `docker compose exec demo python labctl.py db-unavailable off` です。**

```powershell
docker compose exec demo python labctl.py db-unavailable on
```

次の確認を待ち、2つの監視を比較します。

- `demo-health`: DB を使わないため Up のまま
- `demo-item`: DB を開けず 503 になり、Down

これは学習用 SQLite ファイルを退避する実験です。独立した DB サーバープロセスを停止したわけではありません。

### 復旧 A

```powershell
docker compose exec demo python labctl.py db-unavailable off
```

`demo-item` が Up に戻ったことを確かめます。

### 安全な故障 B: 200 で、違うデータが返る

**戻すコマンドは `docker compose exec demo python labctl.py wrong-data off` です。**

```powershell
docker compose exec demo python labctl.py wrong-data on
```

ブラウザーで [実際の応答](http://127.0.0.1:18080/items/1)を見ると、名前が `wrong-demo` になっています。HTTP は 200 でも、`demo-item` はキーワードが見つからず Down になります。

### 復旧 B

```powershell
docker compose exec demo python labctl.py wrong-data off
```

次の確認で Up に戻ることを確かめます。

### もう少し厳密にする: JSON Query

JSON の構造と値まで確かめたい場合は、**Add New Monitor** から **HTTP(s) - Json Query** を選び、`demo-item-json` という名前で追加します。URL は `http://demo:18080/items/1`、間隔・再試行・タイムアウトは `demo-item` と同じです。

- Json Query Expression: `id = 1 and name = "monitoring-demo"`
- Condition: `==`
- Expected Value: `true`（引用符なし）

これは **JSONata** の式です。JSONPath とは書き方が違います。Kuma は式の評価結果を文字列にして Expected Value と比較します。`true` を引用符で囲むと別の文字列になり、一致しません。条件を追加したら、正常時だけでなく wrong-data の故障と復旧も同じように試します。

次章以降は `demo-health` と `demo-item` を使います。比較が済んだら、`demo-item-json` の詳細画面で **Pause** を押し、確認画面の **Yes** を選ぶと一時停止できます。

### 確かめた範囲

既知の1件について、HTTP → アプリ → DB 読み取りの経路を確認できました。全データの正しさ、書き込み、ログイン、支払い、外部 API は確認していません。実サービスでは、安全な読み取り専用の操作から始めましょう。

### チェックポイント

- `/health` が Up でも見逃す故障を説明する
- HTTP の状態、キーワード、JSON の値が答える問いの違いを整理する
- 成功しても分からない操作を1つ書く

<a id="guide-05-alerts"></a>

## 4. 通知を試し、ノイズを減らす

### 困りごと

画面を見ていなければ Down に気づけません。一方、同じ障害で何度も通知すると、大事な知らせを見落としやすくなります。

### 小さな追加: ローカルだけの通知先

この章では Slack やメールの認証情報を使いません。Kuma の **Webhook** 通知を、同じ Compose 内の小さな通知受信器へ送ります。受信器はアプリと別のサービスなので、demo を止めても通知を受け取れます。

```powershell
docker compose --profile notifications up -d notification-sink
```

`demo-health` の **Edit** 画面で、**Notifications** 欄の **Set Up Notification** を開きます。

| 項目 | 設定 |
|---|---|
| Notification Type | Webhook |
| Friendly Name | local-lab |
| Post URL | `http://notification-sink:18081/` |
| HTTP Method | POST |
| Request Body | Preset - application/json |

認証欄、追加ヘッダー、既定の通知先、既存の全監視への一括適用は設定しません。**Test** を押し、PowerShell で受信を確認します。

```powershell
docker compose --profile notifications logs --tail 20 notification-sink
```

通知のダイアログで **Save** を押し、**Notifications** 欄で `local-lab` にチェックが入っていることを確認します。続いて監視の編集画面でも **Save** を押し、左の一覧から `demo-health` の詳細に戻ります。Test の成功は通知経路の確認です。実際の Down / Up 通知は次の実験で確かめます。

受信器は教材用の記録先です。通知は1件ずつ処理するため、同時に届いた通知は前の処理が終わるまで待ちます。ここへ届いたことは、人がメッセージを読んだことの証明にはなりません。

### 安全な故障: 本当の Down と Up を通知させる

**復旧コマンドは `docker compose start demo` です。**

```powershell
docker compose stop demo
```

Down を確認してから、先ほどの `logs` コマンドで Down 通知が届いたことを確認します。続いて復旧させます。

```powershell
docker compose start demo
```

`demo-health` が Up に戻るまで待ち、受信器のログをもう一度表示して、復旧通知が届いたことを確かめます。

```powershell
docker compose --profile notifications logs --tail 20 notification-sink
```

受信ログでは、`monitor_name` が `demo-health` の行を見ます。`heartbeat_status` の `0` が Down、`1` が Up です。

### 小さな追加: 連続する失敗だけを知らせる

`demo-health` の Edit で次を設定します。

- Retries: **2**
- Heartbeat Retry Interval: **20 秒**
- Resend Notification if Down X times consecutively: **0**（再通知なし）

**Save** を押し、左の監視一覧から `demo-health` の詳細へ戻ります。停止前に Up を確認し、受信ログの `demo-health` の Down 通知件数を控えます。

もう一度 `docker compose stop demo` を実行します。詳細画面上部のハートビートでは、最初の2回の失敗で右端にオレンジの棒が1本ずつ増えます。状態は **Pending** のままです。この間に受信ログを表示し、`demo-health` の Down 通知がまだ増えていないことを確認します。Pending 中は **Heartbeat Retry Interval** の間隔で確認を繰り返します。

3回目の連続失敗で赤い棒が加わり、状態が **Down** に変わります。受信ログに `heartbeat_status` が `0` の行が1件増えたことを確認します。再通知を 0 にした場合は、次のチェックでも Down が続くまで待ち、新しい Down 通知が届かないことを確かめます。

画面の履歴にある Down の時刻と、ログの `received_at` を照合します。`received_at` は UTC です。日本標準時の画面と比べる場合は9時間を足します。

### 復旧

```powershell
docker compose start demo
```

次の成功確認で Up へ戻ったら、受信ログに `heartbeat_status` が `1` の行が増えたことを確認します。画面の Up の時刻と `received_at` を照合します。

### Down が続くときの再通知を試す

`demo-health` の **Edit** で **Retries** を **2** のままにし、**Resend Notification if Down X times consecutively** を **2** に変更します。**Save** を押して詳細画面へ戻ります。Up を確認し、受信ログの `demo-health` の Down 通知件数を控えます。

`docker compose stop demo` を実行し、詳細画面上部のハートビートを見ます。オレンジの Pending が2本並んだあと、最初の赤い棒で Down が確定し、Down 通知が1件届きます。赤い棒がさらに2本加わると、最初の再通知が届きます。通常の確認間隔が20秒なら、最初の Down 通知から約40秒後です。

再通知も受信ログでは `heartbeat_status` が `0` です。最初の Down を赤い棒の1本目として数え、3本目で受信ログが1件増えることを確かめます。画面下のイベント表には最初の Down の行が残るため、再通知の件数は受信ログで数えます。

`docker compose start demo` でアプリを再開します。状態が **Up** に戻り、`heartbeat_status` が `1` の通知を確認します。

### 確かめた範囲

通知を遅らせて一時的な失敗を見送る分、異常を伝えるまでの時間は長くなります。再通知を 0 にすると、長く未対応でも追加の知らせは来ません。実運用では、担当者・通知先・再通知・対応手順を一緒に決めます。

### チェックポイント

- Test と、実際の Down / Up 通知を別々に確認する
- Retries 2 のとき、3回目の連続失敗まで待つ理由を説明する
- すぐ知らせる必要がある障害で、同じ設定を使ってよいか考える

<a id="guide-04-latency"></a>

## 5. 応答時間のグラフとタイムアウトを区別する

### 困りごと

名前は正しく返ります。でも毎回待たされるなら、利用者は困ります。次は Kuma にある応答時間のグラフを見ます。

### 小さな追加: 正常時と比べる

`demo-item` の詳細画面で、直近の **Response (Current)** と **Avg. Response (24 hours)** を確認します。その下のグラフは **Recent** で表示し、最初に正常時の値を数回観察します。

**この版の HTTP 監視に「成功していても 500 ms を超えたら警告通知」という独立したしきい値設定はありません。** グラフで遅さを読むことと、タイムアウトで失敗扱いにすることを分けます。500 ms は説明用の目安であり、全サービス共通の基準ではありません。

### 安全な故障: この操作だけ待たせる

**戻すコマンドは `docker compose exec demo python labctl.py delay 0` です。** CPU に負荷を掛けたり、ディスクを埋めたりしません。`/items/1` の処理にだけ、最大2秒の待ち時間を入れます。

まず `demo-item` の **Edit** を開き、**Request Timeout** を **3 秒**にして **Save** を押します。**Retries** は **0** のままです。前章で Retries を **2** にしたのは `demo-health` です。保存後は、左の監視一覧で `demo-item` を選んで詳細画面へ戻ります。

```powershell
docker compose exec demo python labctl.py delay 0.8
```

数回の確認を待ちます。状態は Up のままでも、応答時間は通常時より増えます。グラフの過去の点と新しい点を比べます。縦軸の目盛りは測定値に応じて変わるので、単位と目盛りも確認してください。

次に、待ち時間を延ばします。

```powershell
docker compose exec demo python labctl.py delay 2
```

まず Up のまま、グラフに約 2,000 ms の点が加わることを確認します。続いて **Request Timeout** を **1 秒**へ変更して保存し、詳細画面へ戻ります。次の確認で Down になると、**Response (Current)** は `N/A` になります。履歴の `timeout of 1000ms exceeded` で失敗理由を確認できます。

### 復旧

```powershell
docker compose exec demo python labctl.py delay 0
```

タイムアウト1秒のままでも Up に戻り、応答時間が正常時に近づくことを確認します。待機上限だけを延ばしても、遅さそのものが直ったとは言いません。

### 確かめた範囲

Kuma から行った数回の確認で、そのつど応答時間が分かりました。多数の利用者が同時に使うときの性能や、全利用者の応答時間分布を測ったわけではありません。

「成功した応答でも一定時間を超えたら通知したい」という要件が出たら、対応する監視方式や、後で紹介する数値の収集・警告ルールを検討します。Kuma の Request Timeout を、それと同じ機能だと読み替えないでください。

### チェックポイント

- 遅延0秒、0.8秒、2秒のグラフを比べる
- Up のまま遅くなる場合と、タイムアウトで Down になる場合を説明する
- しきい値を決める前に、通常時と利用者の許容時間を知る理由を考える

<a id="guide-06-diagnose"></a>

## 6. 異常の時刻から、ログで原因を絞る

### 困りごと

Kuma が Down を示しました。でも DB、アプリ、通信のどれが原因かは、赤い表示だけでは決まりません。失敗した時刻と対象から証拠を探します。

### 小さな追加: アプリログを読む

```powershell
docker compose logs --tail 30 demo
```

ログの `timestamp` は UTC です。Kuma の画面がローカル時刻を表示している場合は、同じ時刻基準へ合わせて比べます。たとえばログの `10:00:00.000+00:00` は日本標準時の 19:00:00 です。ログの `path`、`status`、`duration_ms` から、どのリクエストに何を返し、何ミリ秒かかったかが分かります。

1. Kuma は、いつ、どの監視で、何に失敗したか
2. 同じころのアプリログに、そのリクエストはあるか
3. アプリへ届いているなら、どこで何が起きたか
4. その仮説を確かめるために、次に何を1つ調べるか

### 安全な故障: 一つだけ壊して調べる

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

### 復旧

```powershell
docker compose exec demo python labctl.py db-unavailable off
```

Kuma が Up に戻り、アプリログも正常な応答へ戻ることを確認します。

### 確かめた範囲

ログと対象データの状態を合わせて、今回の故障の原因を絞れました。ただし「503 なら必ず DB の問題」とは限りません。

アプリを止めた場合には、停止中のリクエストはアプリログに届きません。ログがない理由は、通信の問題だけとは限りません。別のログを見ている、記録が遅れている、記録処理が壊れている可能性もあります。

次に調べる項目は、その仮説に合わせて選びます。たとえば DB の応答が遅いなら、該当クエリーやロックを調べます。保存に失敗するなら対象の保存先、全体が遅いなら対象プロセスの状態が候補です。最初から全部のグラフを並べる必要はありません。

### チェックポイント

「観測した事実」「考えている原因」「次に確かめること」を分けて3行のメモを書きます。`demo-item` の復旧時刻も記録します。

<a id="guide-09-disk"></a>

## 7. 保存先の空き容量を確かめる

### 困りごと

アプリは動いています。でも DB やログの保存先に余裕がなくなると、保存に失敗するかもしれません。まず実際の保存先を確認し、空き容量を読みます。

### 小さな追加: 保存先を指定して読む

前章の故障を戻し、`demo-health` と `demo-item` が Up であることを確認します。以降も、教材の `compose.yaml` があるフォルダーで操作します。WSL 2 上の Docker Engine を使う場合は、[準備の読み替え手順](#guide-00-prepare)に沿って Bash で実行します。

実験アプリの DB とログは、`demo` 内の `/lab/.state` にあります。この場所を指定して読みます。

```powershell
Get-Date -Format o
docker compose exec demo df -h /lab/.state
```

- `Size`: ファイルシステムの容量
- `Used`: 使用済みの容量
- `Avail`: 利用可能な空き容量
- `Use%`: 使用率
- `Mounted on`: そのファイルシステムを接続している場所

`df` は指定した場所を含むファイルシステムの容量を表示します。`-h` は容量を読みやすい単位にする指定です。[Debian の df マニュアル](https://manpages.debian.org/bookworm/coreutils/df.1.en.html)

**ここで表示するのは、名前付きボリュームの保存先である Linux ファイルシステムの容量です。** `/lab/.state` だけの使用量や専用の容量上限ではありません。他のコンテナーなどが同じ保存先を使っていれば、その使用分も含まれます。Windows の C ドライブの空き容量を測った結果でもありません。

Docker Desktop の Linux 環境と Windows 側の保存先には、それぞれ容量の制約があります。今回の結果だけで PC 全体の空き容量に問題がないとは判断できません。[Docker Desktop の WSL 2 バックエンド](https://docs.docker.com/desktop/features/wsl/)

### 安全な観察: バイト数とファイルの数を分ける

**この章では状態を変更しません。ディスクを埋める実験や、ファイルの削除は不要です。**

容量とは別に、ファイルなどの管理情報に使う **inode** の空きも確認します。

```powershell
docker compose exec demo df -i /lab/.state
```

`Inodes` は inode の総数、`IUsed` は使用数、`IFree` は空き数、`IUse%` は使用率です。小さなファイルを大量に作ると、空き容量を残したまま inode 不足となることがあります。ファイルシステムによっては、この値を提供しない場合もあります。[df の inode 表示](https://manpages.debian.org/bookworm/coreutils/df.1.en.html)

通常の監視を数分続けた後、時刻と2つのコマンドの結果をもう一度記録します。

1. 同じ保存先の `Avail` と `IFree` を比べる
2. 減っていたら、どのくらいの時間で、どれだけ減ったかを記録する
3. 変わらなくても、そのまま記録する。表示の丸めや短い観察時間で差が見えない場合もある

教材はリクエストログを最大 1 MiB のファイル2本に保存します。`df` の変化には、同じファイルシステムを使う別の処理も影響します。

### 復旧

読み取りだけなので、戻す操作はありません。Kuma の2つの HTTP 監視で、新しい Up の結果が増えていることを確認します。

空きが少ないと分かっても、原因を調べずにログや Docker ボリュームを削除しません。消してよい対象と保存期間、バックアップの有無を確認する必要があります。

### 確かめた範囲

今回分かったのは、その時点の空き容量と inode の空きです。保存の失敗が起きた時刻より後の測定だけでは、失敗時にも空きがあったとは言えません。空きがあることだけでは、書き込み権限やディスクの速度も分かりません。

「使用率80%なら必ず異常」のような共通の境界は置きません。空きが少なくても増え方が落ち着いている場合と、余裕があっても急に増えている場合では、対応の急ぎ方が違います。

継続して減るなら、空き容量を普段の増加量で割ると、埋まるまでの時間の目安になります。ただし増加が同じ速さで続くという仮定です。ログの保存期間や削除の周期、急増する日も考えて、調査・整理・容量追加に必要な時間を残します。この短い実験だけでは、その傾向までは確かめられません。

### チェックポイント

- どの保存先を、どの時刻に測ったかを記録する
- バイト単位の空きと inode の空きの違いを説明する
- 空きが少ない場合、使用率以外に何を確認して対応時期を決めるか考える
- この結果だけでは、Windows 全体の空き容量や保存失敗の原因を確定できないと説明する

<a id="guide-10-cpu-memory"></a>

## 8. CPU・メモリーと応答時間を比べる

### 困りごと

Kuma のグラフで、アプリの応答が遅くなっています。CPU が忙しいのでしょうか。それとも何かを待っているのでしょうか。遅くなった時間帯に、アプリが使っている資源も比べます。

### 小さな追加: 同じ時間帯の値を残す

`demo-health` と `demo-item` が Up であることを確認します。まず遅延を入れていない状態で、次のコマンドを実行します。

```powershell
Get-Date -Format o
docker compose stats --no-stream demo
docker compose stats --no-stream kuma
```

`--no-stream` は値を1回表示して終了する指定です。サービスは1つずつ指定します。`demo` がアプリ側、`kuma` が監視する側です。[Docker Compose stats](https://docs.docker.com/reference/cli/docker/compose/stats/)

`docker compose stats` が使えない場合は、[代替手順](#troubleshooting)で同じコンテナーを計測します。

- `CPU %`: コンテナーの CPU 使用率。Linux の表示では、複数の CPU を使うと100%を超える場合もある
- `MEM USAGE / LIMIT`: コンテナーのメモリ使用量と、Docker が報告する利用上限
- `MEM %`: その上限に対する使用量の割合

CPU の値は短い測定区間の値です。コマンドを実行していなかった間の最大値や平均値ではありません。Linux の CPU 使用率の計算は、CPU 数も考慮しています。[Docker CLI の計算処理](https://github.com/docker/cli/blob/master/cli/command/container/stats_helpers.go)

Linux コンテナーに対する Docker CLI のメモリ表示では、一部のキャッシュを差し引きます。`LIMIT` にはコンテナーの制限や、実行環境で利用できるメモリが関係します。アプリ専用に予約された量ではありません。[Docker stats の列とメモリ表示](https://docs.docker.com/reference/cli/docker/container/stats/)

ここでは `demo` と `kuma` の使用量をコンテナーごとに測ります。Windows のタスクマネージャーが示す PC 全体の使用量とは、測定範囲が異なります。

20秒ほど間を空けて、同じコマンドをもう一度実行します。同じ時間帯の `demo-item` の応答時間も記録します。Kuma の表示時刻とログの UTC、PowerShell の時刻のずれに注意して照合します。

### 安全な故障: 忙しくする代わりに待たせる

**戻すコマンドは `docker compose exec demo python labctl.py delay 0` です。** CPU の負荷試験や大量のメモリ確保はしません。

`demo-item` の現在の Request Timeout をメモし、実験中だけ **3秒**へ変更して保存します。次に、「5. 応答時間のグラフとタイムアウトを区別する」の章で使った待ち時間を入れます。

```powershell
docker compose exec demo python labctl.py delay 0.8
```

数回の監視結果を待ち、次の値を同じ時間帯のメモに残します。

```powershell
Get-Date -Format o
docker compose stats --no-stream demo
docker compose stats --no-stream kuma
docker compose logs --tail 10 demo
```

Kuma の `demo-item` の応答時間と、ログの `/items/1` の `duration_ms` を比べます。CPU・メモリーの値も正常時と比べてください。20秒ほど間を空けて、もう一度確認します。

この実験では、アプリの処理に待ち時間を入れています。応答の遅さに比べ、CPU 使用率の変化は小さい場合もあります。ただし、実行環境の別の処理や測定のタイミングにも左右されます。CPU・メモリーが必ず同じ値になる実験ではありません。

### 復旧

```powershell
docker compose exec demo python labctl.py delay 0
```

Request Timeout をメモした元の値へ戻します。`demo-item` が Up であることと、新しい応答時間が正常時に近づくことを確認します。CPU・メモリーも同じコマンドで確認し、「正常時・待ち時間あり・復旧後」の3つを比べます。

### 確かめた範囲

同じ時間帯の応答時間と CPU・メモリーを並べられました。ただし、一緒に増えたことだけで原因を確定できません。CPU 使用率が高くても利用者の待ち時間に影響がない場合や、使用率が低くても外部サービスを待って遅い場合があります。

メモリの1回の増加だけでメモリリークとは決めません。繰り返す操作に伴って増え続けるのか、落ち着くのかを長い時間で確かめる必要があります。今回の小さなアプリと少数の確認では、本番の負荷に耐えられる量は分かりません。

CPU・メモリーとも、一律に「80%を超えたら障害」と決めず、普段の値、続いた時間、応答時間やエラーへの影響を合わせて読みます。`stats --no-stream` はその場の観察であり、履歴保存や自動通知を追加したわけではありません。

### チェックポイント

- 正常時・待ち時間あり・復旧後について、時刻、応答時間、CPU、メモリーを並べる
- 応答が遅いだけでは CPU 不足と決められない理由を、今回の実験で説明する
- アプリ側と監視する側の値を区別する
- 短い観察だけでは、瞬間的な高負荷や長時間のメモリ増加を見逃すことを説明する

<a id="guide-11-network"></a>

## 9. ネットワークの応答とロスを見る

### 困りごと

アプリの応答が遅いとき、通信に時間が掛かっている可能性もあります。ただし HTTP の応答時間だけでは、ネットワークとアプリの処理時間を分けられません。Kuma と同じ場所から、名前の解決と短い通信を確かめます。

### 小さな追加: どこから、どこへ測るかを固定する

前章の待ち時間を戻し、`demo-health` と `demo-item` が Up であることを確認します。今回は **Kuma コンテナーから demo コンテナーへ**、Docker のネットワーク内を測ります。

```powershell
docker compose exec kuma getent hosts demo
```

`demo` に対応する IP アドレスが表示されれば、この時点で名前から宛先を引けています。アプリの動作までは確かめていません。同じ Compose ネットワークのサービスには、サービス名で接続できます。IP アドレスはコンテナーの作り直しで変わり得るため、教材では `demo` を使い続けます。[Compose の名前解決](https://docs.docker.com/compose/how-tos/networking/)

### 安全な観察: 3回だけ Ping する

**状態の変更は不要です。回線の切断、ファイアウォールの変更、通信を大量に送る実験は行いません。**

```powershell
Get-Date -Format o
docker compose exec kuma ping -c 3 -W 1 -w 5 demo
```

これは PowerShell からコンテナー内の Linux の `ping` を実行するコマンドです。Windows の `ping` のオプションとは異なります。教材で指定した Kuma 2.5.5 のイメージには `iputils-ping` が含まれます。[2.5.5 のイメージ定義](https://github.com/louislam/uptime-kuma/blob/2.5.5/docker/debian-base.dockerfile)

- `-c 3`: 送信を3回までにする
- `-W 1`: 応答がない場合の待ち時間を1秒にする
- `-w 5`: Ping の実行期限を5秒にする

最後の集計を読みます。

- `packets transmitted` / `received`: 送信した数と返ってきた数
- `packet loss`: この観察で返ってこなかった割合
- `rtt min/avg/max/mdev`: 往復時間の最小・平均・最大と、ばらつき。単位は ms

Ping は ICMP の要求と応答で、往復時間 **RTT** とロスを測ります。ここでのロスは「この測定で応答が返らなかった」という意味です。捨てられた場所までは分かりません。[Debian の ping マニュアル](https://manpages.debian.org/bookworm/iputils-ping/ping.8.en.html)

同じ時間帯の `demo-item` の HTTP 応答時間もメモします。HTTP の値には、通信に加えてアプリや DB の処理時間が含まれます。Ping の RTT と HTTP 応答時間は異なる測定なので、同じ数字になるとは限りません。差をそのまま正確なアプリ処理時間と扱うこともできません。

必要なら20秒ほど待って、3回の Ping をもう一度行います。**3回の結果でロスが0%でも、いつでも通信が正常だとは証明できません。** 1回返らなければ約33%になる小さな標本です。回数と観察時間を一緒に記録します。

#### 任意: Kuma にも Ping を1つ追加する

手動の Ping が成功したら、履歴を残す方法も試せます。Add New Monitor から次の監視を追加します。

- Monitor Type: **Ping**
- Friendly Name: `demo-network`
- Hostname: `demo`。URL やポート番号は付けない
- Heartbeat Interval: **20秒**
- Retries: **0**

保存後、Up と新しい応答時間の点が増えることを確認します。通知先が自動で選択されていれば、この比較用監視では選択を外して保存します。設定項目は [Kuma 2.5.5 の監視画面](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/pages/EditMonitor.vue)で確認できます。

`demo-network` の応答時間は Ping の値、`demo-item` は HTTP の値です。Kuma の稼働率を、そのままパケットロス率と読み替えないでください。

### 復旧

通信経路やアプリの状態は変えていないため、戻すコマンドはありません。2つの HTTP 監視で、新しい Up の結果が増えていることを確認します。追加した `demo-network` が不要なら、この監視だけを Pause にできます。

Ping が失敗しても、権限やファイアウォールを緩めて成功させようとしません。名前解決の結果とエラーを記録し、HTTP 監視やアプリログと比べます。ICMP が許可されていない場合にも Ping は失敗するため、アプリの停止とは決めつけられません。

### 確かめた範囲

今回分かったのは、Docker ネットワーク内の特定の2点間で、短い期間に得られた応答です。Windows のブラウザーからの経路、Wi-Fi、インターネット回線、別の利用者の経路は測っていません。

Ping が成功しても、TCP ポートが開いていることや、HTTP が成功すること、DB の値が正しいことは分かりません。以前の「間違ったデータが返る」故障を、Ping だけで検知できない理由も考えてみましょう。

RTT やロスが普段より増え、同じ時間帯に HTTP も遅くなっていたら、通信は調査候補になります。それだけで通信が唯一の原因とは言えません。観測地点、時刻、名前解決、HTTP、アプリログをつなげて、次に調べる場所を絞ります。

### チェックポイント

- どこからどこへ、何回、いつ測ったかを記録する
- HTTP の応答時間と Ping の RTT の違いを説明する
- Ping 成功でアプリ正常と決められず、Ping 失敗でアプリ停止とも決められない理由を挙げる
- 3回のロス率から、すべての時間帯や利用者の通信を判断できないと説明する

<a id="guide-07-watchdog"></a>

## 10. Uptime Kuma 自身が止まったら、誰が気づくか

### 困りごと

通知が来ないのは正常だからでしょうか。それとも監視が止まっているのでしょうか。Kuma も実行中のソフトウェアなので、止まることがあります。

### 小さな追加: 監視する側と、される側を分けて考える

まず `demo-health` と `demo-item` が Up であることを確認します。Kuma の設定と履歴は専用ボリュームにあるため、stop/start で失われません。

### 安全な故障: Kuma だけを止める

**復旧コマンドは `docker compose start kuma` です。**

```powershell
docker compose stop kuma
docker compose ps
```

ブラウザーで Kuma の画面を再読み込みすると、接続できなくなります。一方、[実験アプリの URL](http://127.0.0.1:18080/health)は開けます。

Kuma 自身が止まっているので、Kuma から「自分が止まった」という通知は出せません。開いたままの画面に最後の緑色が残っていても、新しい確認が続いている証拠にはなりません。

### 復旧

```powershell
docker compose start kuma
```

画面を開き直し、監視設定が残っていることと、新しい確認結果が増えることを確かめます。保存済みの設定を見ただけで復旧とせず、観測が再開したことまで見ます。

### 確かめた範囲

**Kuma とアプリが同じ PC / Docker Desktop にいると、PC 全体の停止で一緒に止まります。** 別コンテナーや別ターミナルにしただけでは、その障害から独立していません。

実運用でホスト停止を知るには、別ホストや外部サービスなど、同じ障害で一緒に止まらない地点から確認する設計が必要です。確認元の稼働、到達経路、認証、通知の到達性も考えます。本教材の実験用アプリをインターネットへ公開する方法は取りません。

通知履歴がないことだけを正常の証拠にせず、最後の確認時刻や履歴が新しいかも見ます。本章のブラウザー確認は手動実験であり、独立した外部監視を構築したわけではありません。

### チェックポイント

- アプリだけ停止した場合と Kuma だけ停止した場合を比べる
- 古い緑色の画面と、新しい成功確認の違いを説明する
- PC の電源断を知るには、誰がどこから確認する必要があるか考える

<a id="guide-08-review"></a>

## 整理と後片付け

### 手を動かした後で、名前を整理する

| 実際に行ったこと | よく使われる呼び方 | 答えていた問い |
|---|---|---|
| URL の応答を確認 | HTTP 監視・外形監視 | この地点から返事を受け取れるか |
| 本文・既知データを確認 | キーワード監視・操作監視の小さな例 | 必要な結果が返るか |
| 応答時間のグラフを確認 | レイテンシーの観測 | 正常時より待たされていないか |
| ログを調べる | 原因調査 | どこで何が起きたか |
| 保存先の容量・inode を読む | 容量の観測 | 保存する余裕はあるか |
| CPU・メモリーを時刻と比べる | 資源の観測 | 対象の使用量と遅さに関係があるか |
| 名前解決・Ping を確かめる | 通信の観測 | この地点からどこまで届くか |
| Kuma の停止を体験 | 監視自身の監視の設計 | 確認する側は動いているか |

呼び方はツールや組織によって重なります。最初から分類を暗記するより、確かめたい問いと、まだ答えられない問いを分けましょう。

### 次に Prometheus / Grafana が役立つ場面

Uptime Kuma で URL・内容・通知を扱いました。次に「多くの数値を継続して保存し、別の数値と同じ時間軸で比べたい」という要件が出たら、Prometheus による収集と Grafana による表示が候補になります。

Kuma には Prometheus 向けのメトリクス出力があります。ただし、それを取り込んだだけでホストの CPU・メモリー・ディスク容量などを全部収集できるわけではありません。必要な対象には、適切な exporter や別の収集方法が必要です。[公式の連携手順](https://github.com/louislam/uptime-kuma/wiki/Prometheus-Integration)は、その段階で参照します。

後半のコマンドで見た値を継続して保存したい場合は、次のように対象を分けます。

- Linux ホストの CPU・メモリー・ファイルシステム: [node_exporter](https://prometheus.io/docs/guides/node-exporter/) などで、その Linux ホストを対象にする
- コンテナー単位の使用量: [cAdvisor](https://github.com/google/cadvisor) など、コンテナーの実行環境に合う収集方法を選ぶ
- Windows ホスト: [windows_exporter](https://github.com/prometheus-community/windows_exporter) など、Windows に対応した収集方法を別に用意する
- アプリログ: メトリクスの収集とは別に、時刻・対象・検索方法をそろえる

どのホスト・コンテナー・保存先の値かをラベルで区別し、表示だけでなく担当者へ届く警告ルールも設計します。同じホストへ全部置くと、ホスト停止でまとめて観測できなくなる限界は残ります。

今回は Prometheus / Grafana の導入を前提にしません。必要な監視対象や通知条件を説明できるようになってから、機能と運用の負担を比較します。

### 最後の演習

自分が面倒を見る小さなサービスを1つ選び、次を埋めます。

1. 利用者ができなくなると困る操作
2. 最初に登録する監視対象と、期待する結果
3. 確認地点、間隔、待機上限
4. 異常の確定、再通知、復旧の扱い
5. 誰に何を知らせるか
6. 安全な故障の試し方と、戻し方
7. 成功しても証明できないことと、監視自身が止まった場合の確認元

### 一時停止する: データを残す

```powershell
docker compose --profile notifications stop
```

Kuma とアプリを再開する場合は次を実行します。

```powershell
docker compose start demo kuma
```

通知受信器も使う場合は、`docker compose --profile notifications up -d notification-sink` で起動します。故障設定は残るため、個別の解除コマンドで戻してください。

コンテナーとネットワークを片付け、**Kuma の設定・履歴と学習用データを残す**場合は、次を実行します。

```powershell
docker compose --profile notifications down
```

同じフォルダー・同じ Compose プロジェクト名で `up -d` すれば、名前付きボリュームのデータを再利用します。

### 完全に片付ける: 学習用データを消す

次のコマンドは **この Compose プロジェクトのボリュームを削除**します。Kuma の管理者アカウント、監視設定、履歴、学習用 DB が失われます。残したい場合は実行しないでください。

```powershell
docker compose --profile notifications down --volumes
```

機械全体のボリュームやコンテナーを一括削除するコマンドは不要です。複数の勉強会を同じ PC で試す場合は、対象のフォルダーとプロジェクト名を確認します。

Kuma v2 のバックアップを残す場合は、Kuma を停止してデータディレクトリー全体をバックアップする[公式の説明](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2)を参照します。旧版の JSON エクスポート画面がある前提にはしません。

<a id="appendix-custom-checker"></a>

## 補足: 自作監視の仕組みを読む

本編は Uptime Kuma を使います。この補足は、HTTP 確認、通知状態、最終観測時刻などの仕組みをコードで読みたい方向けです。**本編を終えるために実行する必要はありません。**

旧版の `monitor.py` と `watchdog.py` は配布 ZIP に残しています。Kuma が裏でこれらを実行しているわけではありません。通知条件も同一ではありません。

### 本編と環境を混ぜない

この補足では WSL 2 / Ubuntu の Bash と Python 3.10 以降を使います。本編で使ったシェルから本編の `compose.yaml` があるフォルダーに移動し、Compose を停止します。本編と補足はどちらも既定で 18080 番を使います。

本編に Windows の PowerShell を使った場合は、次のコマンドで停止してから Ubuntu に移ります。本編に Ubuntu の Bash を使った場合は、1行目だけを Bash で実行します。

```powershell
docker compose --profile notifications stop
wsl --list --verbose
wsl -d Ubuntu-24.04
```

Ubuntu の名前は自分の環境に合わせます。以後は **Ubuntu の Bash** です。本編と同じ配布 ZIP を Ubuntu のホーム配下の別フォルダーへ展開し、`app.py` がある場所に移動します。

```bash
python3 --version
python3 labctl.py init
python3 app.py
```

同じフォルダーを開いた別の Bash で確認します。

```bash
python3 monitor.py --path /health
python3 monitor.py --path /items/1 --expect-name monitoring-demo --count 30 --interval 2
```

内容確認は ID が整数の1であることと名前を比較します。ソケットの待機上限だけに頼らず、子プロセス全体にも上限を置きます。`--max-ms` はこの自作プログラム独自の条件です。Kuma に同名の設定や同じ通知機能があるという意味ではありません。

```bash
python3 monitor.py --path /items/1 --expect-name monitoring-demo --timeout 2 --max-ms 500 --count 30 --interval 2 --failures 3 --recoveries 2
```

監視の `CHECK` が表示されたら、監視を動かしたまま、同じフォルダーを開いた3つ目の Bash で実行します。

```bash
python3 watchdog.py --max-age 5
```

`--interval` は1回の確認後に待つ時間です。確認結果は毎回残し、通知は連続失敗と復旧の状態変化で出します。監視の最終観測記録は、成功・失敗の両方で更新します。同じホストの watchdog ではホスト全体の停止を検知できません。

停止は各ターミナルの Ctrl+C です。アプリと監視を止めてから `python3 labctl.py reset` を実行すると、このコピーの学習用状態を初期化できます。

詳しいオプションと制限は、<a href="./lab/README-appendix.md" download>自作監視の補足 README</a> を参照してください。

<a id="troubleshooting"></a>

## 困ったとき

### Docker の Server に接続できない

Docker Desktop が起動しているか、Linux コンテナーになっているか確認します。PowerShell の `docker version` で Client だけでなく Server も表示される必要があります。インストール・WSL 2 バックエンドの準備は[公式手順](https://docs.docker.com/desktop/setup/install/windows-install/)を確認します。

Docker Engine を直接導入した場合は、Ubuntu の Bash で `docker version` と `systemctl is-active docker` を実行します。デーモンの起動やグループ設定は [Vol.0 開発環境構築](../コンテナで構築する開発環境/index.md#vol0)を参照します。

### compose.yaml が見つからない

`Get-Location` と `Get-ChildItem` で、配布 ZIP の展開先を確認します。すべてのコマンドを同じ `compose.yaml` のある場所で実行します。フォルダー名だけでなく、プロジェクト名も同じものを使います。

### ポートが既に使われている

同じラボのコンテナーが起動済みか `docker compose ps` で確認します。別のサービスがポートを使っている場合は、`compose.yaml` の `ports` でホスト側の番号だけを空いている番号に変えます。たとえば `127.0.0.1:18080:18080` を `127.0.0.1:28080:18080` に変更します。この場合は Windows のブラウザーでも 28080 番を開きます。Kuma の監視先 `http://demo:18080/health` は引き続きコンテナー側の 18080 番を使います。

### Kuma の画面は開くが監視は Down

監視 URL を確認します。`demo-health` は `http://demo:18080/health`、`demo-item` は `http://demo:18080/items/1` です。Kuma 内の `localhost` は Kuma 自身を指すため、監視 URL には Compose のサービス名 `demo` を使います。

```powershell
docker compose ps
docker compose logs --tail 30 demo
docker compose logs --tail 30 kuma
```

### health は Up だが item は Down

前の故障が残っていないか確認します。

```powershell
docker compose exec demo python labctl.py inspect
docker compose exec demo python labctl.py db-unavailable off
docker compose exec demo python labctl.py wrong-data off
docker compose exec demo python labctl.py delay 0
```

起動し直すだけでは、保存された故障設定は消えません。[準備](#guide-00-prepare)の初期化手順は、必要な記録を保存してから実行します。

### Test は成功したのに Down 通知が来ない

通知先を監視へ割り当てて保存したか、まだ Pending 中ではないか確認します。Test は通知経路を試す操作です。監視状態の変化による通知は、別に試験します。

```powershell
docker compose --profile notifications ps
docker compose --profile notifications logs --tail 20 notification-sink
```

### 遅くなっても Up のまま

本文が正しく、タイムアウト以内に返れば Up になる場合があります。応答時間のグラフを見てください。500 ms を超えた成功応答への警告通知を、標準の HTTP 監視で設定したわけではありません。

### 通知が増え続ける

再通知の条件、複数の監視への通知割り当て、Test ボタンの操作を分けて確認します。通知の重複を避けたい実験では、Resend Notification を 0 にします。

### Kuma 再起動後の古い画面が気になる

ブラウザーを再読み込みし、最後の確認時刻や新しい履歴が増えることを確認します。過去の緑色だけで、現在も監視できているとは判断しません。

### stats コマンドが使えない

`docker compose version` と `docker compose stats --help` を確認します。古い Compose では利用できないことがあります。その場合は `docker compose ps` で `demo` と `kuma` が起動中であることを確認します。`NAME` 列のコンテナー名を `docker stats --no-stream` の引数に指定してください。以下は既定のプロジェクト名を使った場合の例です。

```powershell
docker stats --no-stream monitoring-intro-lab-demo-1
docker stats --no-stream monitoring-intro-lab-kuma-1
```

### df の空き容量が Windows と違う

`/lab/.state` を含む Linux 側のファイルシステムを読んでいます。Windows のドライブ空き容量と同じ表示になるとは限りません。コンテナーのディスク容量やメモリー上限を、ホスト全体の余裕と読み替えないでください。

### Ping に失敗するが HTTP は成功する

ICMP と HTTP は別の確認です。ICMP が許可されない環境や、途中の制限によって Ping だけ失敗することがあります。教材のためにファイアウォールやネットワーク権限を変更せず、監視地点と対象、HTTP の実測を確認してください。

<a id="facilitator"></a>

## 講師用ガイド

### 教材の中心

本編では Uptime Kuma を利用します。監視コードの自作は補足です。最初に製品の全機能を説明せず、URL を1件登録し、緑色を確認してから停止と復旧を体験します。

各章では「この監視の成功から何を言えるか」「成功しても何は分からないか」を問いかけます。前半は URL・停止・内容・通知・遅さ、後半はログ・容量・CPU/メモリー・通信・監視自身を扱う、3〜4時間の構成です。2回に分けても構いません。

### 資源観測を後半に置く理由

基本的な5項目を暗記する順ではなく、利用者の困りごとから調べる順です。「サービスが使えない」という症状を先に確認し、その時刻のログと対象の状態から原因を絞ります。容量、CPU、メモリー、通信は、その問いを具体化するために足します。

後半のコマンドは、対象を限定した一時点の読み取りです。1回の値だけで障害原因を断定せず、通常時・異常時の比較と監視対象の範囲を説明させます。資源を枯渇させる実験や OS 全体の変更は行いません。

Docker Desktop の場合、`df` やコンテナー統計は Linux コンテナー側の情報です。Windows の物理ディスク空き容量やホスト全体の CPU・メモリーを監視したことにはなりません。実際の OS・ファイルシステム・制限値を講師が確認してください。

### 開催前の準備

- Docker で Linux コンテナーを起動でき、`docker compose`（v2 または v5）が使える
- ZIP の展開と PowerShell の作業場所をそろえられる
- 13001 / 18080 番が空いている
- Uptime Kuma 2.5.5 のイメージを取得できる
- SQLite 選択と実験用アカウントの初期設定を受講者自身ができる
- GUI の項目を英語表示で照合できる
- `docker compose stats --no-stream demo` と `docker compose stats --no-stream kuma` で対象を分けて表示できる
- コンテナー内の `df` / `getent` / `ping` が使える
- ローカル Webhook の Test と、実際の Down / Up を確認できる
- 各故障の解除、設定保持、データを消す後片付けを区別できる

#### Docker Desktop で開催する場合の通し確認

開催前に、受講者と同じ Windows・Docker Desktop の構成で、公開ページからダウンロードした ZIP を使って確認します。既存のラボがある場合は、配布 README の手順で検証用のプロジェクト名とホスト側ポートを分けてください。

1. PowerShell で[準備](#guide-00-prepare)の手順を実行し、Windows のブラウザーで Kuma と実験アプリを開く。Kuma で SQLite と実験用アカウントを設定し、`demo-health` が Up になることを確認する
2. [通知の章](#guide-05-alerts)に沿って Webhook を登録する。Test の受信を確認し、実験アプリを停止・再開して、実際の Down と Up が受信ログに残ることを確認する
3. [後片付け](#guide-08-review)に沿ってボリュームを残したまま再起動し、監視設定が残ることを確認する。確認後は検証用ラボのボリュームを削除する

確認日、Windows と Docker Desktop のバージョン、`docker version` と `docker compose version` の結果、各項目の成否を記録します。リポジトリ内の検証記録には WSL 2 上の Docker Engine での結果を掲載しています。

### 安全上の約束

本編は PowerShell で示します。WSL の Docker Engine を使う場合の読み替えは[準備](#guide-00-prepare)に記載しています。Docker 内部の `demo` という名前と、Windows のブラウザーで使う `127.0.0.1` を区別します。

故障は専用アプリの停止、学習用 SQLite ファイルの退避、既知データの変更、最大2秒の待ち時間に限定します。ディスクを満杯にする操作、機械全体の負荷試験、共有サービスの停止は行いません。

通知先は同じ Compose 内の受信器です。受講者の実際のメール・Slack 設定や秘密の Webhook URL を集める必要はありません。画面撮影には管理者パスワードを含めないでください。

### 説明を取り違えない

- Retries 2 は、最初の2失敗を Pending とし、3回目で Down にする設定
- 通知の Test 成功と、本当の Down / Up 通知成功は別
- 応答時間グラフと Request Timeout は別の用途
- 成功応答の 500 ms 超えへの独立した通知設定があるとは説明しない
- SQLite ファイルの退避を PostgreSQL サービス停止として説明しない
- 別コンテナーでも、同じ PC 全体の停止では一緒に止まる

### 成果物

受講者には正常・故障・復旧の画面や時刻、通知の受信、ログの証拠を短く記録してもらいます。最後は自分のサービスで最初に1件追加する監視を設計します。

<a id="references"></a>

## 参考資料

本編は **Uptime Kuma 2.5.5** を対象にしています。参照資料もリリースの版を合わせます。

### 導入とデータ保存

- [Uptime Kuma 2.5.5 リリース](https://github.com/louislam/uptime-kuma/releases/tag/2.5.5)
- [2.5.5 の README](https://github.com/louislam/uptime-kuma/blob/2.5.5/README.md)
- [初期データベース選択画面](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/pages/SetupDatabase.vue)
- [Kuma v2 の移行・バックアップに関する説明](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2)
- [Docker Desktop の Windows 導入手順](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Docker Compose のネットワーク](https://docs.docker.com/compose/how-tos/networking/)
- [Docker Compose down とボリューム削除](https://docs.docker.com/reference/cli/docker/compose/down/)

### 設定と通知の意味を確認する

- [2.5.5 の監視設定画面](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/pages/EditMonitor.vue): HTTP、Keyword、JSON Query、間隔、再試行、タイムアウト
- [2.5.5 の監視実行処理](https://github.com/louislam/uptime-kuma/blob/2.5.5/server/model/monitor.js): Pending / Down / Up と通知の判定
- [2.5.5 の Webhook 通知](https://github.com/louislam/uptime-kuma/blob/2.5.5/server/notification-providers/webhook.js)
- [2.5.5 の日本語訳](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/lang/ja.json): 英語の項目名との対応

### 容量・CPU・メモリー・通信の観察

- [Debian bookworm: df](https://manpages.debian.org/bookworm/coreutils/df.1.en.html): 容量と inode、指定した保存先を含むファイルシステム
- [Docker Compose stats](https://docs.docker.com/reference/cli/docker/compose/stats/): サービスを1つ指定する単発の統計表示
- [Docker stats](https://docs.docker.com/reference/cli/docker/container/stats/): CPU・メモリーの列と Linux のキャッシュの扱い
- [Docker Desktop の WSL 2 バックエンド](https://docs.docker.com/desktop/features/wsl/): Windows と Linux コンテナーの実行環境
- [Debian bookworm: ping](https://manpages.debian.org/bookworm/iputils-ping/ping.8.en.html): 回数・待機時間・期限、往復時間と損失
- [Kuma 2.5.5 のイメージ定義](https://github.com/louislam/uptime-kuma/blob/2.5.5/docker/debian-base.dockerfile): 同梱の iputils-ping

### 実験アプリと次の学習

- [Python の http.server](https://docs.python.org/3.12/library/http.server.html): 学習用サーバー。本番利用は推奨されていません
- [Python の sqlite3](https://docs.python.org/3.12/library/sqlite3.html): ファイル型 DB と読み取り専用接続
- [Prometheus: Linux host metrics](https://prometheus.io/docs/guides/node-exporter/)
- [cAdvisor](https://github.com/google/cadvisor)
- [windows_exporter](https://github.com/prometheus-community/windows_exporter)
- [Uptime Kuma の Prometheus 連携](https://github.com/louislam/uptime-kuma/wiki/Prometheus-Integration)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

分類や用語を一度に暗記するより、自分が検知できた故障と、見逃した故障に結び付けて読みます。
