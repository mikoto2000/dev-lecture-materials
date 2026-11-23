<a id="top"></a>

# アクセスログ監視入門

Web サイトが「開ける」だけで、利用者が困っていないと言えるでしょうか。この教材では **Loki と Grafana** を使い、アクセスログから失敗や遅さを見つけ、実際のアラートと復旧通知まで確認します。

Windows PowerShell と Docker Desktop の Linux コンテナーで進める、90〜120分のハンズオンです。Docker Compose を実行したことがある方を想定しています。PC への Ruby・Python・Node.js の直接インストールや、外部サービスへの登録は不要です。

## 使うものと役割

```text
自動アクセス → 実験用Webアプリ → アクセスログのファイル
                                      ↓ 読み取る
                                Grafana Alloy
                                      ↓ 送る
                                    Loki
                                      ↑ 検索・集計
                                   Grafana → ローカル通知受信器
```

| 役割 | 使用するもの |
|---|---|
| ログの収集・転送 | Grafana Alloy v1.22.0 |
| ログの保存・検索 | Loki 3.7.10 |
| グラフ表示・アラート・通知 | Grafana 13.3.1 |
| 実験用アプリ・自動アクセス・通知受信器 | Python 3.12.14 のコンテナー。追加 pip パッケージなし |

Alloy はファイルを読み、Loki へ送ります。Grafana は Loki へ問い合わせます。Grafana 自体がアクセスログのファイルを収集するわけではありません。

## できるようになること

- Grafana Explore でログを表示し、LogQL で対象を絞る
- アクセス数・5xx 率・遅いリクエスト数をダッシュボードで比べる
- 実験用アプリにエラーや遅延を発生させ、アラートと復旧通知を確認する
- 母数不足、ログの途絶、検索の失敗を正常と区別する
- 収集・保存・表示のどこで止まったかを切り分ける

## 学習の順番

| 章 | 体験すること | 目安 |
|---|---|---|
| [準備](#guide-00-prepare) | Compose を起動し、Grafana へログインする | 15分 |
| [1. 1行を読む](#guide-01-read) | Explore で実際のログを表示する | 10分 |
| [2. 時間と条件で絞る](#guide-02-filter) | エラーと遅さを LogQL で探す | 15分 |
| [3. 件数と割合を比べる](#guide-03-measure) | ダッシュボードで正常・異常を比べる | 15分 |
| [4. 監視の条件を確かめる](#guide-04-monitor) | 発火・復旧・ログ途絶の通知を見る | 30分 |
| [5. 調査と後片付け](#guide-05-review) | 調査先と保存データを整理する | 10分 |

表の目安は合計95分です。講師用ガイドには、通知の確認と振り返りに余裕を持たせた105分の進行例を載せています。

初回のイメージ取得は別途時間がかかります。自分の PC だけで試すための単一構成です。本番向けの認証、冗長化、大量ログの処理までは扱いません。

## 配布資料

- <a href="./access-log-lab.zip" download>Compose と設定ファイル一式（ZIP）</a>
- <a href="./lab/README.md" download>起動・復旧・後片付けの手順</a>
- [困ったとき](#troubleshooting)
- [講師用ガイド](#facilitator)
- [参考資料](#references)

ダッシュボード、データソース、アラート、ローカル通知先は設定済みです。まず動くものを見て、設定の意味を確認します。これらを GUI から新規作成することを前提にはしません。

続編の[不正アクセス監視入門](../security-log-monitoring/index.md)では、認証失敗や404の集中を検知し、誤検知の確認と調査を学びます。

[準備を始める](#guide-00-prepare) / [教材一覧](../index.md)

<a id="guide-00-prepare"></a>

## 準備: Loki・Grafana・Alloy を起動する

### この章のゴール

実験環境を起動し、Grafana のダッシュボードでアクセスの記録を確認します。

### ファイルと Docker を準備する

[教材トップ](#top)の ZIP をダウンロードして展開します。展開先の `access-log-lab` フォルダーには `compose.yaml`、`config.alloy`、`loki.yaml`、`demo.py`、`grafana` フォルダーがあります。

Docker Desktop を Linux コンテナーモードで起動します。PowerShell で、展開した `compose.yaml` のあるフォルダーへ移動します。保存先は自分の環境に合わせて変更してください。

```powershell
cd "$HOME\Downloads\access-log-lab"
docker version
docker compose version
docker compose up -d
docker compose ps --all
```

`demo`、`traffic`、`alloy`、`loki`、`grafana`、`notification-sink` の6サービスが起動します。`Exited` や `Restarting` があれば[困ったとき](#troubleshooting)を確認します。初回はイメージの取得と初期化を待ってください。

WSL 2 の Docker Engine を使う場合は、ZIP を Linux のホーム配下に展開し、Bash で同じ `docker compose` コマンドを実行します。以降の Compose コマンドもそのまま使えます。

### Grafana を開く

ブラウザーで [Grafana](http://127.0.0.1:13000/) を開きます。

| 項目 | 値 |
|---|---|
| ユーザー名 | `learner` |
| パスワード | `access-log-local-only` |

ローカル演習専用のアカウントです。画面名は英語で説明します。ホームに **Access Log Lab** が表示されなければ、サイドメニューの **Dashboards** から同名のダッシュボードを開きます。

右上の時間範囲を **Last 15 minutes**、自動更新を **5s** にします。起動後1〜2分待つと、Requests のグラフが増え、下の Access logs に JSON の行が現れます。

### 記録を発生させる

[実験用アプリ](http://127.0.0.1:18780/items)をブラウザーで開くと、`status` と `request_id` が返ります。このアクセスも記録されます。

自動アクセス役の `traffic` も、各リクエストの完了後に1秒待ってアクセスします。10回に1回は `/missing` へアクセスして404を発生させます。エラー実験をしていない状態でも404が少しあるのは仕様です。

Loki はホストへ公開していません。Grafana からは Compose 内部の `http://loki:3100` を使います。Grafana のデータソース URL を `localhost:3100` へ変えないでください。`localhost` は Grafana コンテナー自身を指します。

### 保存と安全な範囲

ブラウザーへ公開するのは、ループバックの13000番と18780番だけです。実験に使うログは、このアプリへのアクセスから作る練習用データです。本番のログや認証情報は追加しません。

ログ、Alloy の読み取り位置、Loki のデータ、Grafana の設定、故障モードは専用ボリュームへ保存します。Loki の保持期間は24時間ですが、アクセスログの元ファイルは自動で削除しません。短い演習として使い、終了後に後片付けを行ってください。

`access-log-lab` という固定プロジェクト名を使うため、複数コピーの同時起動は避けます。

<a id="guide-01-read"></a>

## 1. アクセスログの1行を読む

### この章のゴール

Alloy が集めたログを Grafana Explore で表示し、各項目の意味を説明します。

### Explore でログを表示する

1. サイドメニューの **Explore** を開く
2. データソースに **Loki** を選ぶ
3. クエリーの入力を **Code** に切り替える
4. 時間範囲を **Last 15 minutes** にして、次の式を入力する

```text
{job="access-log-lab"}
```

**Run query** を押すと、JSON のログが表示されます。行の左側を開くと、ログの内容やラベルを確認できます。

```json
{"time":"2026-11-18T00:00:00.123456Z","method":"GET","path":"/items","status":200,"request_time_ms":2.4,"request_id":"example-id"}
```

これは形式の例です。時刻、処理時間、ID、件数は実行環境と操作によって変わります。固定した過去のログを再生する演習ではありません。

| 項目 | 意味 | 注意点 |
|---|---|---|
| `time` | アプリが応答を書き終えた時刻 | `Z` は UTC。Grafana の表示時刻とはタイムゾーンが違う場合がある |
| `method` | HTTP メソッド | このアプリは GET を記録する |
| `path` | クエリー文字列を除いたパス | 実運用ではパス自体の個人情報にも注意する |
| `status` | アプリが返した HTTP ステータス | 200でも内容の正しさまでは保証しない |
| `request_time_ms` | アプリ側で測った処理時間 | ミリ秒。ブラウザーの表示完了時間とは異なる |
| `request_id` | リクエストの識別子 | アプリログとの照合に使う手がかり |

### ラベルと JSON の項目を区別する

`job="access-log-lab"` は収集時に付けたラベルです。まずラベルで検索するログの集合を選び、その後で JSON の項目を調べます。

`request_id` や時刻を取り込み時のラベルにすると、値の種類が非常に多くなります。この教材ではラベルにせず、ログ本文に残します。検索時に `| json` で取り出します。

Alloy は `config.alloy` の `stage.timestamp` で JSON の `time` を読み、Loki のログ時刻として使います。転送された時刻と、出来事が起きた時刻は同じとは限りません。

### 記録地点と分かる範囲

本教材はアプリのアクセスログです。CDN やリバースプロキシのアクセスログではありません。HTTP 5xx はサーバー側の失敗、404は存在しないパスなどを示しますが、原因まで一意には決まりません。

DNS 障害やアプリまで届かない通信、応答が完了していないリクエストは、このログだけでは分かりません。実際の Nginx の `$request_time` は秒単位です。別のログを扱うときは、項目と単位を最初に確認します。

<a id="guide-02-filter"></a>

## 2. LogQL で時間と条件を絞る

### この章のゴール

エラーと遅い応答を実際に発生させ、Explore で対象のログを探します。

### 先に解除方法を確認する

異常を解除するコマンドは、いつでも次の1行です。`compose.yaml` のあるフォルダーで実行します。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

`python` はコンテナー内で実行するため、PC にインストールする必要はありません。故障モードは再起動後も残ります。異常の実験は1つずつ行い、終わったら `normal` へ戻します。

### 5xx を発生させる

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

### 200のまま遅い応答を探す

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

<a id="guide-03-measure"></a>

## 3. ダッシュボードで件数と割合を比べる

### この章のゴール

Access Log Lab のグラフで、失敗と遅さを区別します。

### 正常なときの値を確認する

`normal` のまま1〜2分待ち、**Dashboards → Access Log Lab** を開きます。時間範囲は **Last 15 minutes**、更新間隔は **5s** にします。

| パネル | 見るもの |
|---|---|
| Requests / 1m | 直近1分の有効なログの件数 |
| 5xx / 1m (%) | 直近1分の5xx件数 ÷ 全件数 × 100 |
| Slow requests / 1m | 直近1分の1000 ms 以上の件数 |
| p95 / 1m (ms) | 直近1分の処理時間の95パーセンタイル |
| Access logs | 個別のログ |

自動アクセスだけなら、正常時は1分でおよそ60件です。環境や手動アクセスによって変わるため、固定した件数を成功条件にはしません。

### 集計の式を読む

Explore で次の式を実行します。メトリクスのクエリーなので、ログの行ではなく数値やグラフが返ります。

```text
sum(count_over_time({job="access-log-lab"} | json | __error__="" [1m]))
```

`[1m]` は各評価時刻の直前1分です。Loki の範囲は左端を含まず、右端を含みます。画面の **Last 15 minutes** は、これを表示する時間の長さです。表示範囲を変えても、式の `[1m]` は変わりません。

5xx 率は次の式です。5xx がない窓では分子を0にしますが、分母まで0に置き換えることはしません。

```text
100 *
(sum(count_over_time({job="access-log-lab"} | json | status >= 500 | __error__="" [1m])) or vector(0))
/
sum(count_over_time({job="access-log-lab"} | json | __error__="" [1m]))
```

`__error__=""` は数値比較の後に置きます。JSON の解析だけでなく、`status` の数値変換で発生したエラーも除外するためです。変換エラーが残ると、Loki のメトリクスクエリーは失敗します。配布設定の遅い件数も、数値比較の後でエラーを除きます。

4xx は母数に入りますが、5xx の件数には入りません。404がある正常時でも、5xx 率は0%です。これを「すべての操作が成功した」と読み替えないでください。

### 正常・異常・復旧を比べる

1. 第2章の `mode error` を実行し、1〜2分観察する
2. 5xx 率の上昇と503のログを確認し、時刻をメモする
3. `mode normal` に戻し、グラフが戻るまで待つ
4. `mode slow` を実行し、遅い件数と p95 を確認する
5. 5xx 率は上がらなくても遅くなることを確かめ、`mode normal` に戻す

直近1分を繰り返し評価するため、解除直後にも古い異常が残ります。また、slow では1回の応答を待つ分だけ自動アクセスの頻度が下がります。これは固定負荷の性能試験ではありません。

### 母数と p95 に注意する

1件中1件の失敗も、1000件中1000件の失敗も100%です。割合と一緒に件数を見ます。実運用ではヘルスチェックが大量にあると利用者の操作の失敗が薄まるため、重要なパスごとの集計も検討します。

p95 は約95%の応答が収まる処理時間を表します。少数のログでは値が安定しません。Loki のパーセンタイルと別ツールの計算結果が、常に完全一致するとも限りません。この教材のアラートは p95 ではなく、遅いリクエストの件数を使います。

<a id="guide-04-monitor"></a>

## 4. アラートと通知を確かめる

### この章のゴール

Grafana が繰り返し評価するルールを読み、発火と復旧の通知を確認します。

### 登録済みのルールを読む

サイドメニューの **Alerting → Alert rules** を開き、Access Log Lab の3件を確認します。ファイルから自動登録したルールは GUI では編集できません。まず詳細画面でクエリーと判定条件を読みます。

| ルール名 | 調べる条件 |
|---|---|
| Access errors | 直近1分が10件以上で、5xx 率が20%以上 |
| Access slow | 直近1分が10件以上で、1000 ms 以上が3件以上 |
| Access logs missing | 直近1分の有効なログが0件 |

評価間隔は **10秒**、Pending の期間は **20秒** です。条件を満たすと Pending になり、その状態が続くと Firing になります。画面では正常を Normal と表示します。評価 API では inactive、通知では resolved という名前も使います。

最初の2ルールのクエリーは、`>= bool` で条件に合うと1、合わないと0を返します。`and (全件数 >= 10)` で母数を確認し、Grafana は値が0より大きいと異常にします。件数不足では判定値を返しません。

これは演習用の閾値です。通常のアクセス数と許容する失敗・遅延に合わせて決めます。低頻度でも失敗を見逃せない操作には、別の条件や外形監視が必要です。

### 通知先を確認する

**Alerting → Contact points** の **local-webhook** が通知先です。Compose 内部の `http://notification-sink:8081` へ送信します。外部のメールや Slack は使いません。

別の PowerShell を開き、同じラボのフォルダーで受信ログを表示します。

```powershell
docker compose logs --follow --tail 20 notification-sink
```

画面で Contact point の **Test** が使える場合は、先にテストします。テスト通知と実際のアラートは `alertname` で区別してください。テスト成功だけで実際の異常を検知できたとは扱いません。

通知ポリシーは、ルール名ごとにまとめ、初回は5秒待ちます。グループ更新の間隔は10秒、同じ異常の再通知は1時間です。Firing の表示と通知の到着は同時とは限りません。

### エラーの発火と復旧を見る

始める前に `normal` の状態で、Access errors が Normal になるまで待ちます。受信ログの現在の時刻を控えます。

```powershell
docker compose exec -T demo python /lab/demo.py mode error
```

1. ダッシュボードで5xx 率の上昇を確認する
2. Alert rules で Access errors の Pending → Firing を確認する
3. 受信ログで `alertname` が `Access errors`、`status` が `firing` の通知を探す

1〜2分が目安です。発火を確認したら解除します。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

直近1分の値が閾値を下回ると Normal に戻ります。同じルールの `resolved` が届くことを確認します。復旧の待機期間は追加していないため、20秒間の正常継続を要求する設定ではありません。

### 遅さの発火と復旧を見る

```powershell
docker compose exec -T demo python /lab/demo.py mode slow
```

今度は Access slow の Firing と通知を確認します。HTTP 200のままでも異常になることを確かめ、解除後の `resolved` まで確認します。

```powershell
docker compose exec -T demo python /lab/demo.py mode normal
```

### ログの途絶を正常と区別する

最初の2件が Normal に戻ってから、自動アクセスを止めます。実験中はブラウザーでアプリを開かないでください。

```powershell
docker compose stop traffic
```

最後のアクセスから1分以上経つと、Access logs missing が Pending → Firing になります。`firing` の通知を確認します。元のログファイルが残っていても、直近1分に新しいログがなければ異常です。

エラー率のグラフに値がないことは、0%と同じではありません。最初の2ルールはデータ不足のとき **Keep Last State** とし、以前の状態を維持します。データが消えただけで復旧したことにせず、途絶は別のルールで通知します。

```powershell
docker compose start traffic
```

ログ途絶の `resolved` と、新しいログを確認します。元のルールに十分な母数が戻るまでにも少し時間が必要です。

Loki 自体が止まった場合はクエリーの実行エラーです。これは0件とは違います。設定は **Error** 扱いで、Grafana の DatasourceError として調べます。Grafana 自体が停止するとこの通知もできないため、監視基盤への外形監視は別に必要です。

<a id="guide-05-review"></a>

## 5. 調査と後片付け

### この章のゴール

ログに書かれた事実と原因の候補を分け、観測できる範囲を整理します。

### 通知から調査へ

通知のルール名と時刻から、Explore の時間範囲を絞ります。`status >= 500` などで対象を探し、パス、処理時間、リクエスト ID を確認します。

このラボの503は故障モードで発生させたものです。実際のログで同じ値を見ても、DB 故障とは断定できません。同じ ID のアプリログ、プロキシのエラーログ、依存先の状態や変更履歴を調べます。

| 観測した事実 | 次に確認すること |
|---|---|
| 5xx が増えた | 例外、依存先の失敗、デプロイ時刻 |
| 200のまま遅くなった | DB、外部 API、待ち行列、資源の履歴 |
| 404が増えた | URL の分布、リンク変更、配信設定 |
| ログが来ない | 自動アクセス、アプリ、Alloy、転送遅延、保存先 |
| Loki のクエリーが失敗した | Loki の稼働、接続先、クエリーの構文 |

同時刻に CPU が高くても、それだけで原因とは決められません。[インフラ監視実践入門](../monitoring-intro/index.md)の外形監視や資源の観測と組み合わせて調べます。

### 収集器を運用するときの確認点

Alloy の読み取り位置を残すと、再起動時に続きから読みやすくなります。ただし、これは未送信ログの永続的な保管や、欠損・重複の完全な防止を保証するものではありません。このラボは Loki 停止中の長期保存を保証する構成にはしていません。

実運用では、ローテーションの追従、収集停止中の保持容量、送信バッファー、再試行、時計のずれ、壊れた行の扱いを検証します。ログを残す元ファイルと、Loki の保存データには別々の保持・削除方針が必要です。

個人情報、Cookie、Authorization ヘッダー、トークン、検索語は不用意に記録しません。アクセス制限、保存期間、共有時のマスクも決めます。リクエスト ID も他の情報と照合できるため、無条件に公開しないでください。

### 振り返り

- Alloy、Loki、Grafana がそれぞれ担当する役割
- 5xx 率と一緒に母数を見る理由
- HTTP 200の遅さを発見した方法
- 0件と、クエリー実行エラーの違い
- ログが消えただけで復旧としないための設定

答えの例は[講師用ガイド](#facilitator)にあります。

### 後片付け

故障モードを戻し、自動アクセスを再開しておきます。

```powershell
docker compose start traffic
docker compose exec -T demo python /lab/demo.py mode normal
docker compose down
```

`down` はこのプロジェクトのコンテナーとネットワークを削除します。専用ボリュームのデータは残ります。再開は `docker compose up -d` です。

演習を完全にやり直す、または保存データが不要なら、同じフォルダーで次を実行します。**このラボの専用ボリュームにあるログ・Grafana の設定・読み取り位置・故障モードが消えます。**

```powershell
docker compose down --volumes
```

他のプロジェクトへ影響する `docker system prune` などは不要です。Grafana とアプリの画面が開かなくなることを確認します。

次の教材は[不正アクセス監視入門](../security-log-monitoring/index.md)です。基本操作を活用し、検知した兆候と不正利用の判断を分けて学びます。

<a id="troubleshooting"></a>

## 困ったとき

### Docker につながらない

Docker Desktop が Linux コンテナーモードで起動しているか、`docker version` の Server が表示されるかを確認します。WSL 2 の Docker Engine を使う場合は、Docker が動いているディストリビューションで実行します。

### ポートが使用中と言われる

13000番または18780番が競合しています。このラボの `compose.yaml` にあるホスト側のポートだけを変更します。たとえば `127.0.0.1:13001:3000` なら、ブラウザーは13001番で開きます。コンテナー側の3000番や内部 URL は変更しません。

### 起動直後にログイン画面が開かない

初期化を待ち、状態とログを確認します。

```powershell
docker compose ps --all
docker compose logs --tail 50 grafana loki alloy
```

別のコピーを同時に起動していないかも確認します。この教材の Compose 名は `access-log-lab` で固定しています。

### ログが表示されない

Explore のデータソースが Loki、時間範囲が Last 15 minutes になっているかを確認します。ラベルは `{job="access-log-lab"}` です。PC の時計のずれも調べます。

```powershell
docker compose start traffic
docker compose exec -T demo python /lab/demo.py mode normal
docker compose exec -T demo tail -n 3 /logs/access.jsonl
docker compose logs --tail 50 traffic alloy loki
```

ファイルに新しい行があるのに Explore に出なければ、Alloy と Loki の間を調べます。ファイルに増えなければ、traffic と demo を先に確認します。古いファイルだけを見て正常と判断しないでください。

### 解除したのに異常が残る

クエリーの直近1分には、解除前の異常も残ります。正常なリクエストが増えるまで待ちます。故障モードはボリュームに保存されるため、再起動だけでは解除できません。`mode normal` を実行します。

### Firing なのに通知が見つからない

ルール名と受信時刻を確認します。同じ異常の再通知間隔は1時間です。初回の5秒待機やグループ更新の10秒間隔もあります。

```powershell
docker compose logs --tail 50 notification-sink grafana
```

Contact point の URL は `http://notification-sink:8081` です。`localhost` に変更しないでください。通知ログの表示を Ctrl+C で止めても、受信器自体は動いています。

### ルールやダッシュボードを編集できない

配布ファイルから自動登録しているためです。本文では設定を読み、実験します。変更を試す場合は、ダッシュボードをコピーするか、配布設定のコピーで検証してください。

### 完全に初期状態へ戻す

保存データが消えることを確認し、このラボのフォルダーで実行します。

```powershell
docker compose down --volumes
docker compose up -d
```

<a id="facilitator"></a>

## 講師用ガイド

### 開催前の確認

受講者と同じ Docker 環境で、配布 ZIP の起動から後片付けまで試します。イメージを事前に取得するなら `docker compose pull` を実行します。ポート13000番と18780番の競合、時計のずれ、イメージ取得先への接続も確認してください。

Grafana のログイン、Explore、ダッシュボード、3つのアラートの表示を確認します。エラー・遅さ・途絶の各ケースで、Firing と `firing` 通知、Normal と `resolved` 通知まで試してください。テスト通知だけでは代用できません。

### 進行例

105分の場合、準備15分、ログの読み方10分、絞り込み15分、集計15分、通知35分、整理15分を目安にします。学習の順番の表に対し、通知と整理を各5分長く取った配分です。通知の待ち時間で、時間窓・母数・Pending・通知の待機を説明します。

自動アクセスは応答の完了後に1秒待ちます。slow モードではアクセス数も変わるため、固定件数や固定パーセントを期待値にはしません。異常を解除した瞬間にグラフも戻る、とは説明しないでください。

第2〜3章でもアラートは動作しています。第4章では既存の受信時刻を控え、新しい故障実験の通知を区別します。

### 設定ファイルを読む場所

- `config.alloy`: ファイルの発見、読み取り、ログ時刻の抽出、Loki への転送
- `loki.yaml`: 単一構成の保存先と24時間の保持期間
- `grafana/provisioning`: データソース、アラート、通知先、通知ポリシー
- `grafana/dashboards/access-log.json`: 配布ダッシュボード

配布設定を変える場合は、コピーを用意して対象を限定します。ファイルから登録したアラートを GUI で直接編集できるとは案内しません。

### 振り返りの答えの例

- Alloy は収集・転送、Loki は保存・検索、Grafana は問い合わせ・表示・評価・通知
- 同じ100%でも1件中1件と1000件中1000件では影響が異なるため、母数と対象の操作も必要
- 処理時間の条件でログを絞り、遅い件数と p95 を比べた
- 0件は問い合わせできたが対象ログがない状態。実行エラーは問い合わせ自体を正常に完了できない状態
- Keep Last State とログ途絶の別ルールを使う。ただし、低アクセス時の長い状態維持が適切かはサービスごとに検討する

### リポジトリの検査

`npm run package:access-log` で設定と ZIP を再生成し、`npm run check:access-log` で本文のリンク・目次・配布資料を検査します。`npm run test:access-log` は Python の単体試験、`npm run test:access-log-compose` は実 Docker 環境での統合試験です。開発者向けの検査には Python 3.10 以降が必要です。

統合試験は一時ディレクトリー、固有の Compose 名、ループバックのランダムポートを使います。終了時に試験用プロジェクトのボリュームだけを削除します。ブラウザーの操作確認と、API による機能検証は区別して記録します。

<a id="references"></a>

## 参考資料

- [Loki の概要](https://grafana.com/docs/loki/latest/get-started/overview/): ログの保存とラベルによる検索
- [LogQL](https://grafana.com/docs/loki/latest/query/): ログ検索とメトリクスのクエリー
- [LogQL のメトリクスクエリー](https://grafana.com/docs/loki/latest/query/metric_queries/): count_over_time、unwrap、quantile_over_time
- [Alloy の概要](https://grafana.com/docs/alloy/latest/introduction/): 収集と転送の役割
- [Alloy でファイルのログを収集する](https://grafana.com/docs/alloy/latest/monitor/monitor-logs-from-file/): loki.source.file などの構成
- [Alloy の loki.process](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.process/): JSON とタイムスタンプの処理
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/): ルール、通知先、通知ポリシー
- [ファイルからアラートを登録する](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/): 配布したアラート設定の仕組み
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html): 機密情報とログの扱い

教材は固定版で検証します。上記の latest の資料では、画面や設定が教材の固定版と異なる場合があります。
