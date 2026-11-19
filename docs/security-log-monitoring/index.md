<a id="top"></a>

# 不正アクセス監視入門

「404が増えた」「ログイン失敗が続いた」という事実から、どこまで分かるでしょうか。この教材では **Loki・Grafana・Alloy** を使い、不正利用を疑う兆候を検知し、誤検知の可能性を確認して調査へつなげます。

[アクセスログ監視入門](../access-log-monitoring/index.md)の続編です。Explore、LogQL、ダッシュボード、アラートの基本操作を前提にします。目安は90〜120分です。

## できるようになること

- 認証失敗と単なる HTTP エラーを区別する
- 送信元や学習用アカウントごとにログを集計する
- 認証失敗の集中と404の集中でアラートを発火させる
- 同じ警報でも、探索的なアクセスとリンクミスでは判断が違うことを確かめる
- 証拠、影響、次の調査先を記録する

## 使用する環境

前の教材と同じ Loki 3.7.10、Grafana 13.3.1、Alloy v1.22.0 を使います。受講者の PC に Ruby・Python・Node.js を直接インストールする必要はありません。Docker Compose で、独立した実験環境を起動します。

通常アクセス、認証失敗、探索を模したアクセス、リンクミスの4シナリオを切り替えます。送信先は Compose 内の実験アプリに固定しています。実際のサイトやアカウントへ攻撃を試す教材ではありません。自動遮断は扱わず、検知と調査の判断を学びます。

## 学習の順番

| 章 | 体験すること | 目安 |
|---|---|---|
| [準備と観測の範囲](#guide-00-prepare) | 専用ラボと記録項目を確認する | 15分 |
| [1. 認証失敗の集中を見つける](#guide-01-auth) | アカウントと送信元で集計・通知する | 20分 |
| [2. 探索的なアクセスを調べる](#guide-02-paths) | 404の集中とパスの分布を読む | 20分 |
| [3. 誤検知を確かめる](#guide-03-triage) | リンクミスと比較し、調査メモを書く | 20分 |
| [4. 運用と後片付け](#guide-04-review) | 限界、対応方針、保存データを整理する | 15分 |

## 配布資料

- <a href="./security-log-lab.zip" download>不正アクセス監視ラボ一式（ZIP）</a>
- <a href="./lab/README.md" download>起動・シナリオ・後片付け</a>
- [困ったとき](#troubleshooting)
- [講師用ガイド](#facilitator)
- [参考資料](#references)

この教材で検出するのは、決めた条件に合う兆候です。攻撃の断定、侵入成功の証明、すべての不正利用の検出を保証するものではありません。

[準備を始める](#guide-00-prepare) / [教材一覧](../index.md)

<a id="guide-00-prepare"></a>

## 準備と観測の範囲

### この章のゴール

専用の Grafana を開き、アクセスログに加えて記録する認証イベントを確認します。

### 独立したラボを起動する

[教材トップ](#top)の ZIP を展開し、`compose.yaml` のある `security-log-lab` フォルダーで実行します。前の教材のフォルダーとは分けてください。

```powershell
cd "$HOME\Downloads\security-log-lab"
docker compose up -d
docker compose ps --all
```

Linux コンテナーを使います。WSL 2 の Docker Engine では Linux のホーム配下に展開し、同じ Compose コマンドを実行します。

[Grafana](http://127.0.0.1:13010/)を開き、`learner` / `access-log-local-only` でログインします。**Security Log Lab** ダッシュボードを開き、**Last 15 minutes**、更新間隔 **5s** にします。起動後1〜2分待ちます。

アプリはループバックの18790番、Grafana は13010番だけに公開します。Loki や通知受信器はホストへ公開しません。前の教材と別のプロジェクトとボリュームを使います。

### Explore で確認する

**Explore → Loki → Code** で実行します。

```text
{job="security-log-lab"} | json
```

アプリの通常アクセスに加え、5回に1回程度、学習用認証の成功イベントが出ます。認証の成功・失敗はアプリが判定したものであり、HTTP ステータスから推測した値ではありません。

| 項目 | この教材での意味 |
|---|---|
| `event` | `access` または `auth` |
| `outcome` | 認証では `success` または `failure` |
| `account` | 固定の `demo-user` または `other`。通常アクセスは空欄 |
| `client_ip` | アプリが TCP 接続の相手として見た IP |
| `time` / `request_id` | 発生時刻とリクエストの照合用 ID |

学習用の認証処理はセッションやトークンを発行しません。パスワードや要求の本文をログへ保存しません。実サービスでは、アクセスログとは別の認証ログが必要になることもあります。

### 送信元を読み違えない

`client_ip` はこのラボの自動アクセスコンテナーの IP です。値は環境で変わるので、教材の固定値を期待しません。

実際のサービスでは、プロキシや NAT の背後の利用者が同じ IP に見える場合があります。送信元 IP は人の識別子ではありません。外部から届いた `X-Forwarded-For` を無条件で信用せず、信頼するプロキシが設定した値だけを採用する設計が必要です。

<a id="guide-01-auth"></a>

## 1. 認証失敗の集中を見つける

### この章のゴール

同じ送信元とアカウントへの認証失敗を集計し、通知を確認します。

### シナリオと解除方法

最初に、解除コマンドを確認します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

次に認証失敗のシナリオへ切り替えます。固定の学習用アカウントに対し、固定の誤った値を送ります。外部の宛先やパスワードリストは使いません。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode login
```

Explore で認証失敗を探します。

```text
{job="security-log-lab"} | json | event="auth" | outcome="failure" | __error__=""
```

`account`、`client_ip`、時刻を確認します。401だけを検索する方法と違い、何の処理が失敗したかをアプリのイベントで確かめています。

### 送信元とアカウントで集計する

```text
sum by (client_ip, account) (
  count_over_time({job="security-log-lab"} | json | event="auth" | outcome="failure" | __error__="" [1m])
)
```

直近1分の失敗を、送信元とアカウントの組ごとに数えます。1つの IP を決め打ちして検索するより、新しい送信元にも気づきやすくなります。取り込み時のラベルにはせず、検索時に JSON から取り出しています。

この条件では、複数 IP から1つのアカウントへ分散する試行や、1つの IP から多くのアカウントへ少数ずつ試す動きを見逃します。実運用では、アカウント単位、送信元単位などの別集計も必要です。

### アラートと復旧を確認する

**Alerting → Alert rules** の **Repeated login failures** は、各組で **直近1分の失敗が10件以上** のとき異常とします。評価間隔は10秒、Pending は20秒です。

通知を別の PowerShell で表示します。

```powershell
docker compose logs --follow --tail 20 notification-sink
```

Firing と、同じ `alertname` の `firing` 通知を確認します。通知の `client_ip` と `account` も控えてください。1〜2分が目安です。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

正常な認証を再開すると、直近1分の失敗が減り、Normal と `resolved` 通知を確認できます。配布クエリーは同じ組の認証イベントがある間、失敗がない場合に0を補います。

認証の集計結果がすべて空になると **No Data** です。このルールは **Keep Last State** で直前の状態を保ちます。**Security logs missing** は、認証以外も含む有効なログ全体の件数を調べます。直近1分が0件なら異常と判定します。通常のアクセスログが続き、認証イベントだけが途絶した場合は、この途絶ルールでは検知できません。

一部の組だけが消え、別の組の認証イベントが続く場合は **MissingSeries** です。消えた組の警報は、一定回数の評価後に Normal へ移り、発火中なら `resolved` 通知が出ます。Keep Last State による全系列の No Data の扱いとは異なります。警報の履歴で `grafana_state_reason` が `MissingSeries` かを確認します。

`resolved` は条件を下回った場合にも、系列が消失した場合にも届きます。第三者が侵入していない、被害がない、と確認できた意味ではありません。実運用では、送信元やアカウントごとの観測が途絶した場合の確認方法も決めます。

<a id="guide-02-paths"></a>

## 2. 探索的なアクセスを調べる

### この章のゴール

404の集中を検知し、どのパスを探しているかを調べます。

### 固定したパスへのアクセスを発生させる

前のシナリオを `normal` に戻してから実行します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode scan
```

このシナリオは、存在しない `/unknown-a`、`/unknown-b`、`/unknown-c` の3つだけを繰り返します。脆弱性の悪用や外部サイトのスキャンは行いません。

Explore で404を探します。

```text
{job="security-log-lab"} | json | status = 404 | __error__=""
```

パスと送信元の分布を集計します。

```text
sum by (client_ip, path) (
  count_over_time({job="security-log-lab"} | json | status = 404 | __error__="" [1m])
)
```

同じ送信元から3つのパスへのアクセスが見つかれば成功です。具体的な IP と件数は実行時に変わります。

### 警報を確かめる

**Repeated missing paths** は、送信元ごとの404が **直近1分で20件以上** だと異常です。Pending を経た Firing と、受信ログの `firing` を確認します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

解除したら、Normal と `resolved` 通知まで待ちます。404が0でも、その送信元の有効なログがある間は0を補います。

### 404の多さだけでは断定しない

実際の探索では、短時間に多様なパスへアクセスする場合があります。ただし、このルールは件数だけを見ています。パスの種類や内容まで判定していません。

また、存在するページの探索では200や403が返る場合もあり、404だけでは検知できません。公開直後のリンク切れや、正規のクローラーも404増加の要因です。次の章では、同じ警報をリンクミスでも発生させます。

<a id="guide-03-triage"></a>

## 3. 誤検知を確かめ、調査する

### この章のゴール

アラートの発火と、不正アクセスだという判断を分けます。

### リンクミスのシナリオ

前の実験が Normal に戻ってから実行します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode typo
```

存在しない `/old-help` という1つのパスへアクセスします。これはリンク変更の反映漏れで利用者が404に遭う、という想定です。

件数が増えると、前の章と同じ **Repeated missing paths** が Firing になります。通知はルールどおりに出ていますが、それだけでは探索行為と判断できません。

第2章の式でパス別に集計します。切り替え時刻を控え、2分以上待ってから、Explore の時間範囲を絶対時刻で「開始: 切り替えの1分後」「終了: 現在時刻」に設定して再実行します。各評価時刻の直前1分を集計するため、開始時刻も1分後にずらして前のシナリオを除きます。

Last 15 minutes のままでは、待つだけで過去の scan の集計結果がグラフから消えるわけではありません。現在時点の直近1分と、グラフ全体の表示範囲を区別します。

| 比較する情報 | scan のシナリオ | typo のシナリオ |
|---|---|---|
| 404の件数 | 増える | 増える |
| パスの分布 | 固定した3つへ分散 | `/old-help` へ集中 |
| 教材で与えた背景 | 探索を模したもの | リンクミスを模したもの |
| 実運用で追加する調査 | パスの意味、頻度、他の兆候 | リンク元、公開・変更履歴 |

パスが1つなら安全、3つなら攻撃、というルールでもありません。教材では背景を知っていますが、実際には追加の情報を集めます。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

`resolved` 通知まで確認します。

### 調査メモを作る

次の項目を埋めます。想像で埋めず、未確認のことは未確認と書きます。

| 項目 | 記録すること |
|---|---|
| 検知 | ルール名、発火時刻、タイムゾーン |
| 範囲 | 時間窓、送信元、対象アカウントやパス |
| 事実 | 件数、成功・失敗の結果、関連するリクエスト ID |
| 仮説 | 探索、リンク切れ、設定変更などの候補 |
| 追加確認 | 認証成功履歴、変更履歴、プロキシ・WAF・アプリログ |
| 判断と次の行動 | 継続観測、担当者への確認、対応手順の適用 |

認証失敗が続いた後に成功があれば、その成功の正当性を追加で確認します。失敗の減少だけを見て調査を終了しないでください。本ラボでは侵入後の操作や実際の被害調査までは再現しません。

### 対応を急ぐ場合にも残すもの

影響が続く場合は、組織の対応手順に沿って関係者へ連絡し、必要な保護を検討します。送信元 IP だけで一律に遮断すると、NAT 配下の正規利用者も止める場合があります。根拠、対象範囲、解除条件を記録します。

この教材は自動遮断を設定しません。MFA、レート制限、WAF などは予防や緩和の別の層として検討します。

<a id="guide-04-review"></a>

## 4. 運用と後片付け

### この章のゴール

今回の条件の限界と、運用で追加すべき観測を整理します。

### 何を検知したか

認証失敗の警報は送信元とアカウントの組ごとの件数です。404の警報は送信元ごとの件数です。どちらも直近1分を10秒ごとに評価し、20秒の Pending を使いました。

閾値に満たない低頻度の試行、複数送信元への分散、200で成功する不正操作は、この条件で拾えるとは限りません。許可したアカウントからの不正利用も、失敗の監視だけでは分かりません。

通知先と再通知間隔は前の教材と同じです。ローカル Webhook に送り、初回5秒待機、グループ更新10秒、同じ異常の再通知は1時間としています。通知を読める人と、次の調査先も運用では決めます。

### ログの信頼性を確認する

`client_ip`、アカウント、User-Agent、パスは同じ信頼度ではありません。User-Agent は任意に設定できます。IP は利用者本人を保証しません。アカウント名に含まれる個人情報にも注意します。必要に応じて識別子へ置き換えます。

ログの停止、改変、時計のずれ、収集の遅延にも備えます。閲覧権限、転送中と保存時の保護、保持期間、証拠を残す手順を決めます。パスワード、セッショントークン、Authorization ヘッダーは記録しません。

このラボの認証処理は JSON の形式が壊れた要求や大きすぎる要求を、通常の認証イベントとして記録しません。演習で扱う正常な形式の要求が対象です。本番では、そのような拒否や解析エラーも別途観測する設計が必要です。

### 振り返り

- HTTP 401と、アプリの認証失敗イベントを区別する理由
- 送信元とアカウントの両方で集計する利点と、見逃す動き
- 同じ404の警報でも、scan と typo で追加調査が変わる理由
- `resolved` と、被害がないことの確認の違い
- 自動遮断を導入する前に確認する影響範囲と解除条件

### 後片付け

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
docker compose down
```

専用ボリュームは残ります。再開は `docker compose up -d` です。ログ・シナリオ設定・Grafana のデータが不要なら、同じフォルダーで次を実行します。

```powershell
docker compose down --volumes
```

この教材のプロジェクト名は `security-log-lab` です。前の教材とは別ボリュームなので、前の教材のデータは削除されません。ラボの保存元ファイルはローテーションしないため、短い演習として使い、終了後に削除してください。

<a id="troubleshooting"></a>

## 困ったとき

### 画面が開かない、ログが出ない

この教材の Grafana は13010番です。前の教材の13000番とは異なります。Explore のラベルも `{job="security-log-lab"}` を使います。

```powershell
docker compose ps --all
docker compose logs --tail 50 demo traffic alloy loki grafana
```

基本的な接続の調べ方は[アクセスログ教材の困ったとき](../access-log-monitoring/index.md#troubleshooting)も参照してください。そちらのポート番号とシナリオ操作は読み替えます。

### シナリオが変わらない

`compose.yaml` のある security-log-lab フォルダーで実行します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

demo と traffic は同じシナリオ設定を参照します。再起動後も残るので、明示的に normal に戻します。ログの直近1分には以前のシナリオも残ります。

### 認証失敗の警報が復旧しない

normal の自動アクセスでは、数秒ごとに同じアカウントの認証成功を記録します。traffic が動いているか、同じ `client_ip` と `account` の新しい認証イベントがあるかを確認します。

認証の集計結果がすべて空なら、Keep Last State で直前の状態を保ちます。一部の組だけが消えた場合は MissingSeries として復旧通知が出ることもあります。正常な認証を観測したことと、何も観測できないことは別です。Security logs missing はログ全体の途絶を検知するため、認証イベントだけの途絶も別に確認してください。

### 通知の送信元 IP が例と異なる

IP は実際のコンテナーネットワークの値なので変わります。固定 IP をコピーせず、自分のログと通知を照合します。

### 完全にやり直す

この教材専用の保存データが消えることを確認して実行します。

```powershell
docker compose down --volumes
docker compose up -d
```

<a id="facilitator"></a>

## 講師用ガイド

### 開催前の確認

アクセスログ教材を終えた受講者を想定します。配布 ZIP を独立したフォルダーへ展開し、13010番の Grafana で3つのルールを確認してください。比較用に前の教材を同時起動する必要はありません。

login、scan、typo を1つずつ実行し、発火・通知・normal に戻した後の復旧通知を確認します。異常を出す前に前ケースの復旧を待ち、受信時刻を控えます。

シナリオの送信先は内部の demo に固定しています。外部サイトの調査や、実ユーザーの認証情報を試す作業は不要です。

### 説明で強調すること

scan と typo のどちらも同じ警報を出すことが、この教材の重要な体験です。警報が誤動作したという説明にはしません。「404が20件」という条件は成立しています。それを攻撃と判断するには追加の情報が必要です。

認証失敗のルールは IP とアカウントの組ごとです。分散した試行や、成功する不正利用まで検知できるとは説明しません。IP による遮断には巻き添えがあり、解除や例外の手順も必要です。

### 振り返りの答えの例

- 401は認証以外の実装やプロキシでも返り得る。アプリが何を判定したかは認証イベントで確かめる
- 集計で対象を絞れるが、IP やアカウントを分散する試行は別の軸で見る必要がある
- 件数だけではパスの分布や変更履歴が分からず、行動の意味を判断できないため
- resolved は検知条件を外れた場合や系列が消失した場合に届く。認証成功の正当性や被害の確認は別の調査
- 正規利用者への影響、根拠、範囲、通知先、解除条件を先に確認する

### 開発者向けの検査

`npm run package:security-log` で共通のアクセスログラボの資材と専用設定をまとめた ZIP を作ります。展開後の ZIP は単独で動作し、前の教材のファイルを実行時に取得しません。

`npm run check:security-log` は本文・目次・配布先・ZIP の整合性、`npm run test:security-log` はアプリの単体試験です。`npm run test:security-log-compose` は一時プロジェクトで、各シナリオのアラートと実際の通知を確認します。開発者向けの検査には Python 3.10 以降が必要です。

<a id="references"></a>

## 参考資料

- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html): 認証イベント、記録項目、機密情報、ログの保護
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html): 認証の監視と多要素認証、試行回数の制限
- [LogQL のログ検索](https://grafana.com/docs/loki/latest/query/log_queries/): JSON の解析とフィルター
- [LogQL の集計](https://grafana.com/docs/loki/latest/query/metric_queries/): 時間窓と集計の軸
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/): アラートの状態と通知
- [Grafana のデータ欠損の扱い](https://grafana.com/docs/grafana/latest/alerting/guides/missing-data/): No Data と MissingSeries の違い
- [アクセスログ監視入門](../access-log-monitoring/index.md): この教材の前提となる収集・検索・通知
