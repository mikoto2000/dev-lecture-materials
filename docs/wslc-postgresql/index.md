<a id="top"></a>

# wslc を利用したコンテナ利用入門

## この勉強会でできるようになること

「アプリの開発を始めたいのに、まず DB のインストールで止まってしまう」。そんなときに、必要な開発環境をコンテナーで用意してみましょう。

今回は **PostgreSQL が動く開発用データベースを、Windows 上で用意する**ことがゴールです。SQL を試し、作業を中断し、翌日再開できるところまで体験します。

- Windows に PostgreSQL 本体や psql を直接インストールせずに起動する
- コンテナーに入っている psql でデータを保存・検索する
- コンテナーを作り直しても、学習データを残す
- 自分のアプリに渡す接続情報を説明する

## 対象者と前提知識

PowerShell でコマンドをコピーして実行できる方が対象です。コンテナーと SQL が初めてでも進められます。サーバー運用や本番環境の構築は扱いません。

ここでは WSL に同梱されるコンテナー CLI、`wslc.exe` を使います。公式の前提条件は **WSL 2.9.3 以降**です。WSL パッケージのバージョンと、ディストリビューションの実行方式である WSL 1 / WSL 2 は別のものです。[Microsoft の WSL コンテナー導入手順](https://learn.microsoft.com/ja-jp/windows/wsl/tutorials/wsl-containers)

## 学習の進め方

| 章 | やること | 目安 |
|---|---|---:|
| 事前準備 | ツールと通信を確認 | 開始前に実施 |
| 起動 | 保存場所を用意して PostgreSQL を起動 | 15分 |
| SQL | テーブル・登録・検索・更新 | 20分 |
| 再開と作り直し | データが残ることを確認 | 15分 |
| アプリへの接続 | ホストとポートを理解 | 10分 |
| 後片付け・ふりかえり | 残すものと消すものを選ぶ | 10分 |

事前準備を済ませた状態で、進行に応じて 60〜90 分を想定しています。

## コマンドの読み方

`powershell` の枠は **Windows の PowerShell** で実行します。Ubuntu のターミナルではありません。

`sql` の枠は **psql の画面**に貼り付けます。`workshop=#` などの表示は入力しません。

複数行の PowerShell は末尾のバッククォートでつながっています。バッククォートの後ろに空白を入れないでください。不安な場合は<a href="./examples/commands.ps1.txt" download>PowerShell コマンド集</a> にある一行版を使います。

SQL はセミコロンまで入力します。表示例のバージョン番号、ID、時刻は環境で変わります。


[1. 事前準備へ進む](#guide-01-prepare)

## 配布資料

- <a href="./examples/01-tasks.sql" download>SQL サンプル</a>
- <a href="./examples/commands.ps1.txt" download>PowerShell コマンド集</a>

[教材一覧へ戻る](../index.md)

<a id="guide-01-prepare"></a>

## 1. 事前準備

### この章のゴール

`wslc version` が実行でき、学習用イメージを取得できる状態にします。環境の準備は勉強会の前日までに済ませるのがおすすめです。

### 用意するもの

- WSL を利用できる Windows PC。WSL **2.9.3 以降**
- Windows PowerShell または PowerShell と、本文を見るブラウザー
- イメージを取得できるネットワークと、空きディスク容量
- 必要ならテキストエディター（VS Code の指定なし）

Docker Desktop、ホスト側の PostgreSQL、psql、Java、Node.js は、このハンズオンの受講には不要です。Node.js が必要なのは教材を Rspress で編集・表示する講師だけです。

### WSL と wslc を確認する

PowerShell を開きます。

```powershell
wsl --version
wslc version
wslc run --help
wslc volume --help
```

`wsl --version` の **WSL バージョン**が 2.9.3 以上であることを確認します。`wsl -l -v` に出る `VERSION 2` は別の値です。

2.9.3 は Microsoft が示す最低要件です。教材の手順は WSL / wslc 3.0.5.0 で実機確認しました。

`wslc` がない場合は、[公式の導入手順](https://learn.microsoft.com/ja-jp/windows/wsl/tutorials/wsl-containers)に従ってください。既に WSL がある場合、更新コマンドは次です。更新や再起動に備え、授業開始直前の実行を避けてください。会社 PC は管理者のルールに従います。

```powershell
wsl --update
```

WSL 自体がない場合は[公式 WSL インストール手順](https://learn.microsoft.com/ja-jp/windows/wsl/install)で準備します。権限や組織の制限を回避する設定変更は行いません。

### イメージを先に取得する

```powershell
wslc image pull postgres:17
wslc image list
```

一覧に `postgres` の `17` があれば準備完了です。通信環境によって数分かかります。これは PostgreSQL 17 系の学習用指定で、最新版という意味ではありません。同じタグでも後日パッチの更新を含む場合があります。

### 名前の衝突を確認する

```powershell
wslc container list --all
wslc volume list
```

本文は `wslc-workshop-db` と `wslc-workshop-pgdata` を使います。新しく始めるときに同名のコンテナーやボリュームがあれば、講師と相談して、全手順で未使用の名前にそろえます。自分が以前作った学習用 DB の続きを行うときは、[4章](#guide-04-persist)でコンテナーが残っている場合とボリュームだけが残っている場合の手順を確認します。

### 開始前のチェック

- [ ] `wslc version` が表示された
- [ ] `postgres:17` を取得できた
- [ ] 同名の既存データがないことを確認した

<a id="guide-02-start"></a>

## 2. PostgreSQL を起動する

### この章のゴール

開発用 PostgreSQL を起動し、接続を受け付けていることを確認します。

### 必要な言葉を3つだけ

| 言葉 | 今回の役割 |
|---|---|
| イメージ | PostgreSQL と必要なファイルをまとめた、起動のもと |
| コンテナー | イメージから起動した、DB が動く環境 |
| ボリューム | DB のデータをコンテナーと分けて残す保存場所 |

起動の設定はコマンドに残し、データはボリュームに残します。コンテナーを作り直せることと、データを捨ててよいことは別です。

### 保存場所を作る

```powershell
wslc volume create wslc-workshop-pgdata
wslc volume inspect wslc-workshop-pgdata
```

作成した名前と詳細が表示されます。このボリュームは wslc が管理します。Windows の好きなフォルダーを DB の保存先にする手順ではありません。

### DB を起動する

次のパスワードは、この PC の使い捨て学習 DB 専用の公開されたサンプル値です。実アカウントのパスワードを入力したり、この値を他の環境で再利用したりしないでください。環境変数やコマンド履歴から見えるため、秘密の管理方法としては使いません。

```powershell
wslc run -d --name wslc-workshop-db `
  -e POSTGRES_PASSWORD=workshop-local-only `
  -e POSTGRES_DB=workshop `
  -e POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 `
  -p 127.0.0.1:15432:5432 `
  -v wslc-workshop-pgdata:/var/lib/postgresql/data `
  postgres:17
```

長い ID が出れば、起動処理が始まっています。**まだ接続できるとは限りません。**

| 指定 | 意味 |
|---|---|
| `-d` | DB をバックグラウンドで動かす |
| `--name` | 後で操作するときの名前 |
| `POSTGRES_PASSWORD` | 初回に作られる DB 管理者 `postgres` のパスワード |
| `POSTGRES_DB` | 初回に作るデータベース名 |
| `POSTGRES_INITDB_ARGS` | 初回に TCP 接続のパスワード認証方式を設定 |
| `127.0.0.1:15432:5432` | この PC の 15432 番からコンテナーの 5432 番へ接続 |
| `-v` | 指定したボリュームを DB のデータ保存先に接続 |
| `postgres:17` | PostgreSQL 17 系のイメージ |

`127.0.0.1` を省略しないでください。別の PC から接続させる設定は、この教材では行いません。開発用アカウントは強い権限を持つため、業務データを入れないでください。

### 起動完了を確認する

```powershell
wslc container list
wslc container logs wslc-workshop-db
wslc exec wslc-workshop-db pg_isready -h 127.0.0.1 -U postgres -d workshop
```

`accepting connections` が出れば進めます。準備中なら数秒待って `pg_isready` を再実行します。初回のログには一時的な停止・再起動も含まれるため、途中の1行だけで失敗と判断しません。

`pg_isready` は受付状態の確認です。パスワードが正しいことは次章の接続で確認します。

:::warning 保存先を勝手に変えない
この教材の `postgres:17` は `/var/lib/postgresql/data` にマウントします。PostgreSQL 18 以降の公式イメージは保存先の構成が異なります。`latest` や `18` に置き換えたり、同じボリュームを別メジャー版で起動したりしないでください。メジャー更新は別途移行が必要です。

:::

### 講義の区切り

「PostgreSQL のインストーラーを操作せずに、DB が起動した」を確認できればこの章は終了です。

<a id="guide-03-sql"></a>

## 3. SQL を実行する

### この章のゴール

DB に接続し、自分で登録したデータを読み出します。SQL を覚えるより、開発用 DB をすぐ試せる状態になったことを体験しましょう。

### コンテナー内の psql を使う

PowerShell で実行します。ホストに psql を入れる必要はありません。

```powershell
wslc exec -it wslc-workshop-db psql -h 127.0.0.1 -U postgres -d workshop -W
```

`Password:` と表示されたら、`workshop-local-only` を入力して Enter を押します。入力文字は画面に表示されません。

`workshop=#` が出たら、今いるのは psql の画面です。`-h 127.0.0.1` は **コンテナー内**の TCP 接続を指定しています。前章の Windows 側 15432 番を通る接続ではありません。`-W` はパスワード入力を要求します。2章では初回の TCP 認証方式も指定しています。`-W` 自体がサーバーの認証を有効にするわけではありません。

```sql
SELECT current_database(), current_user;
```

`workshop` と `postgres` が表示されます。

### テーブルを用意する

```sql
CREATE TABLE IF NOT EXISTS tasks (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title text NOT NULL UNIQUE,
  done boolean NOT NULL DEFAULT false
);
```

`CREATE TABLE` が表示されます。再実行時には「既にある」という通知の出る場合があります。この手順では問題ありません。

### データを登録して読む

```sql
INSERT INTO tasks (title)
VALUES ('Start PostgreSQL'), ('Connect from my app')
ON CONFLICT (title) DO NOTHING;

SELECT id, title, done FROM tasks ORDER BY id;
```

初回は2行が表示され、`done` は `f`（false）です。ID は手順の再実行などで変わることがあります。

```text
 id |        title        | done
----+---------------------+------
  1 | Start PostgreSQL    | f
  2 | Connect from my app | f
(2 rows)
```

### データを変更する

```sql
UPDATE tasks SET done = true WHERE title = 'Start PostgreSQL';
SELECT title, done FROM tasks ORDER BY id;
```

`UPDATE 1` が表示され、`Start PostgreSQL` の `done` が `t`（true）になれば成功です。

### 自分のデータを1つ追加する

```sql
INSERT INTO tasks (title)
VALUES ('My first container database')
ON CONFLICT (title) DO NOTHING;
SELECT count(*) FROM tasks;
```

他に追加していなければ `3` が表示されます。自分のデータをさらに追加した場合は、ここで表示された行数を控えてください。次の章では、同じ行数と `done` の更新が残るか確認します。

### psql を終了する

```text
\q
```

PowerShell の表示に戻ります。**psql を終了しても DB は動き続けています。** クライアントを閉じる操作と、DB を止める操作は別です。

困ったときは、途中の SQL 入力を Ctrl+C で取り消せます。`workshop-#` のままなら、まだ文の入力が終わっていない可能性があります。

<a id="guide-04-persist"></a>

## 4. 止める・再開する・作り直す

### この章のゴール

DB を使わないときは止め、必要になったら再開します。さらに、コンテナーを作り直しても学習データが残ることを確認します。

### 今日の作業を終える

psql の中なら `\q` で抜けてから、PowerShell で実行します。

```powershell
wslc container stop wslc-workshop-db
wslc container list --all
```

対象が停止状態になったことを確認します。停止中は DB に接続できません。コンテナーとボリュームはまだ残っています。

### 翌日の作業を始める

`wslc container list --all` で対象を確認します。すでに動いていれば `start` を省略します。コンテナーを削除済みでボリュームが残っている場合は、この章の「コンテナーだけ作り直す」で、ボリュームの確認から始めます。

```powershell
wslc container start wslc-workshop-db
wslc exec wslc-workshop-db pg_isready -h 127.0.0.1 -U postgres -d workshop
```

`no response` なら数秒待って `pg_isready` を再実行します。`accepting connections` が出たら、前章と同じ方法で接続します。

```powershell
wslc exec -it wslc-workshop-db psql -h 127.0.0.1 -U postgres -d workshop -W
```

パスワードは `workshop-local-only` です。

```sql
SELECT title, done FROM tasks ORDER BY id;
```

前章で確認した行数（例では3行）と更新した `done` が残っていることを確認し、`\q` で戻ります。

### コンテナーだけ作り直す

ここで削除するのは **この教材の停止したコンテナーだけ**です。DB のボリュームは消しません。名前を一文字ずつ確認してから実行します。

すでに停止している場合は `stop` を、すでに削除している場合は `stop` と `remove` を省略し、`volume inspect` から進めます。

```powershell
wslc container stop wslc-workshop-db
wslc container remove wslc-workshop-db
wslc volume inspect wslc-workshop-pgdata
```

ボリュームが残っていることを確認したら、2章と同じ設定で新しいコンテナーを作ります。名前や Windows 側の公開ポートを変更して進めた場合は、ここでも変更後の値を使ってください。

```powershell
wslc run -d --name wslc-workshop-db `
  -e POSTGRES_PASSWORD=workshop-local-only `
  -e POSTGRES_DB=workshop `
  -e POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 `
  -p 127.0.0.1:15432:5432 `
  -v wslc-workshop-pgdata:/var/lib/postgresql/data `
  postgres:17
```

```powershell
wslc exec wslc-workshop-db pg_isready -h 127.0.0.1 -U postgres -d workshop
```

`accepting connections` が出るまで待ち、同じ接続コマンドと SELECT で、行数と `done` の更新をもう一度確認します。コンテナーの ID は変わっても、ボリュームに保存したデータは残ります。

### なぜ残ったのか

| 操作 | コンテナー | 名前付きボリュームの DB データ |
|---|---|---|
| psql の `\q` | 動いたまま | 残る |
| `container stop` | 止まる | 残る |
| `container start` | 再開する | 同じデータを使う |
| `container remove`（この章の指定） | 消える | 残る |
| 同じボリュームを指定して `run` | 新しく作る | 既存データを使う |
| 最終章の `volume remove` | 先に削除が必要 | **失われる** |

永続化はバックアップではありません。PC の故障やボリューム削除からは守れません。重要なデータには別のバックアップが必要です。

:::tip パスワード変更と初期化は別
`POSTGRES_PASSWORD` や `POSTGRES_DB` は、空の保存先で初期化するときの設定です。同じボリュームで環境変数だけ変えて再作成しても、既存のパスワードや DB は変更されません。ログインできなくなったとき、データを消して直そうとせず、[困ったときは](#troubleshooting)を見ます。

:::

### 講義の区切り

「起動設定は再利用でき、DB のデータは別に残せる」を自分の言葉で説明できれば成功です。

<a id="guide-05-connect"></a>

## 5. 自分のアプリから接続する

### この章のゴール

用意した DB を、Windows 上の開発中のアプリから使うときの接続情報を確認します。アプリの作成や GUI の追加インストールは不要です。

### Windows 側の入口を確認する

コンテナーが起動して接続を受け付けている状態で、Windows の PowerShell から実行します。[ポートの競合](#troubleshooting)で公開ポートを変更した場合は、この章のコマンド、接続設定、JDBC URL の `15432` を変更後の番号に読み替えてください。

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 15432
```

`TcpTestSucceeded : True` が目安です。これは TCP ポートの確認で、SQL の実行やパスワード認証の確認ではありません。

Windows 上で動くアプリや、既に導入済みの PostgreSQL 対応 GUI には、次の情報を設定します。

| 項目 | 値 |
|---|---|
| ホスト | `127.0.0.1` |
| ポート | `15432` |
| データベース | `workshop` |
| ユーザー | `postgres` |
| パスワード | `workshop-local-only`（学習用のみ） |

例えば Java の JDBC URL は次です。パスワードは URL に書き込みません。

```text
jdbc:postgresql://127.0.0.1:15432/workshop
```

すでに Windows に psql がある人だけ、追加で次を試せます。ない人はインストールせず次へ進めます。

```powershell
psql -h 127.0.0.1 -p 15432 -U postgres -d workshop -W
```

GUI を使う場合も、新しい PostgreSQL 接続を作って上の値を入力し、3章の SELECT を実行します。学習用の接続とわかる名前を付け、実環境の接続と混同しないようにします。

### 接続先は「どこから接続するか」で変わる

- **Windows のアプリから:** `127.0.0.1:15432`
- **この DB コンテナー内の psql から:** `127.0.0.1:5432`（省略時の標準ポート）
- **別のコンテナーから:** そのコンテナー自身の `127.0.0.1` を指すため、ネットワーク設計が別途必要
- **WSL ディストリビューション内のアプリから:** Windows と同じ経路とは限らず、この教材での接続確認の対象外

まずは Windows 側で開発しているアプリから使う構成に限定します。認証を通す目的で `trust` を使ったり、公開アドレスを `0.0.0.0` へ広げたりしないでください。

### ふりかえり

1. ホスト側の PostgreSQL を入れ替えず、開発用 DB を用意できたか
2. 同じ起動コマンドとイメージの指定を、他の参加者と共有できるか
3. 自分のアプリが必要とする DB 名・バージョン・接続設定は何か

<a id="guide-06-cleanup"></a>

## 6. 後片付け

### この章のゴール

開発を続けるか、学習データを完全に捨てるかを選びます。以下を全部実行する必要はありません。

psql を開いている場合は `\q` で PowerShell に戻ります。準備でコンテナー名やボリューム名を変えた場合は、自分が作った学習用リソースの名前を使ってください。

### A. また使う場合（おすすめ）

DB を止めます。

```powershell
wslc container stop wslc-workshop-db
```

コンテナー・ボリューム・イメージが残ります。次回は `wslc container start wslc-workshop-db` で再開できます。

### B. コンテナーだけ片付ける場合

4章と同じく停止後に対象だけ削除します。

```powershell
wslc container stop wslc-workshop-db
wslc container remove wslc-workshop-db
```

データは残ります。次回は [4章](#guide-04-persist)の「コンテナーだけ作り直す」で、`volume inspect` から進めます。既に停止・削除済みなら、その操作は飛ばします。

### C. 学習データを完全に捨てる場合

:::danger 最後のボリューム削除は取り消せません
以下の操作で、この教材の DB に保存した全データを失います。残したいデータがないこと、対象名が `wslc-workshop-pgdata` であることを確認してから進めてください。他のボリュームやコンテナーは削除しません。

:::

まず B の手順でコンテナーを削除します。その後、対象を確認して、ボリュームだけ削除します。

```powershell
wslc volume inspect wslc-workshop-pgdata
```

ここでいったん止まり、データを捨ててよいか判断します。削除すると決めた場合だけ次を実行します。

```powershell
wslc volume remove wslc-workshop-pgdata
wslc volume list
```

対象が一覧から消えたら終了です。`prune` や、他のリソースをまとめて消す操作は使いません。

### イメージのキャッシュについて

ボリュームを削除しても、取得した `postgres:17` のイメージは残り、ディスクを使います。他の開発作業でも使えるため、この教材ではイメージを自動削除しません。WSL の仮想ディスクのファイルサイズが、削除直後にその分だけ小さくなるとは限りません。

### まとめ

必要になったら起動し、接続して試し、使わないときは止める。この一連の流れを用意できれば、アプリの開発に取りかかれます。

<a id="troubleshooting"></a>

## 困ったときは

### まず確認すること

エラーの前後と、次の結果を講師に見せます。パスワード、個人情報、業務データが入った出力は共有しないでください。

```powershell
wsl --version
wslc version
wslc container list --all
wslc container logs wslc-workshop-db
```

### wslc が見つからない

Windows の PowerShell か確認します。WSL のパッケージバージョンを確認し、公式手順で更新します。`wsl -l -v` の `2` だけでは条件を満たしたと判断できません。

### オプションが認識されない

```powershell
wslc run --help
wslc container --help
wslc volume --help
```

本文は公式の現行ソースと照合していますが、インストール版との差があり得ます。Docker のオプションを推測で足さず、版と help を講師と確認します。

### イメージを取得できない

名前を `postgres:17` にそろえます。ネットワーク、レジストリーの利用制限、組織のプロキシを確認します。ファイアウォールや証明書検証を無効にしません。認証が必要になったら、画面と組織の正式な手順を確認します。

### 名前が既に使われている

`wslc container list --all` で確認します。自分の同じ教材のコンテナーなら `start` で再開できます。他の作業のものや由来不明なものは削除せず、講師と相談します。

### ポートが使用中

15432 番を他のプロセスが使っている可能性があります。学習用コンテナーが起動していないことを確認し、起動コマンドの公開先を `127.0.0.1:15433:5432` に変更します。その後の Windows 側接続先も 15433 にそろえます。DB 内部の 5432 は変更しません。他人のプロセスを強制終了しません。

起動失敗のあとも同名コンテナーの残る場合があります。`wslc container list --all` で確認します。今回の失敗で作られた学習用コンテナーだと確認できた場合だけ、次へ進んでください。必要なら先に `wslc container stop wslc-workshop-db` を実行します。続いて `wslc container remove wslc-workshop-db` を実行します。ボリュームは残し、変更した公開ポートで run を再実行します。由来不明な同名コンテナーは削除しません。

### Connection refused / no response

停止中や初期化中の可能性があります。コンテナー一覧・ログ・`pg_isready` を確認します。`run -d` で ID が出たことは、DB の準備完了を意味しません。

### パスワードが合わない / DB がない

接続先が学習 DB か確認します。初回に別のパスワードや DB 名で作ったボリュームなら、環境変数を変えても初期化し直されません。元の設定を確認してください。データを残す必要がある場合は、削除して解決しようとしません。

コンテナー内で `-h` を省略すると Unix ソケット接続になり、パスワードなしで接続できる場合があります。それは公開ポートの認証確認にはなりません。この教材は初回起動で `POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256` を指定し、`-h 127.0.0.1 -W` で確認します。既存ボリュームに後から初期化変数を足しても、認証設定は変わりません。

### SQL の入力が終わらない

`workshop-#` ならセミコロンが不足している可能性があります。文字列の閉じ忘れなどもあります。Ctrl+C で途中の入力を取り消し、SQL を貼り直します。`\q` は psql から抜けるコマンドです。PowerShell で実行しません。

### 作り直したらデータが見えない

間違った保存先や DB に接続している可能性があります。データを書き足す前に停止して確認します。

```powershell
wslc container inspect wslc-workshop-db
wslc volume inspect wslc-workshop-pgdata
```

ボリューム名、マウント先 `/var/lib/postgresql/data`、イメージ `postgres:17`、接続 DB `workshop` が同じか見ます。別メジャー版に変えないでください。

### ボリュームが使用中で消せない

コンテナーを止めるだけでは、参照が残ります。最終章でデータを捨てると決めた場合に限り、この教材のコンテナーを削除してから、同じボリューム名を指定して削除します。強制削除や全体の prune は使いません。

### 起動はできるが Windows から接続できない

DB 内部の接続と Windows 公開ポートは別経路です。`Test-NetConnection` と公開ポートの指定を確認し、実機の WSL/wslc 版とネットワーク設定を講師に伝えます。原因不明のまま全体の WSL 停止やセキュリティ設定変更を行わないでください。

<a id="facilitator"></a>

## 講師用ガイド

### ねらい

到達点は「開発用 PostgreSQL を必要なときに用意できる」です。コンテナーの操作網羅より、アプリ開発を始めるまでの短さに焦点を当てます。内部実装の解説や独自イメージの作成は、質問があったときの補足に回します。

### 開催前に必ず実機で通す

開催前には、受講者が使う Windows / WSL / wslc で全章を一度通し、以下を記録してください。

- Windows ビルド、`wsl --version`、`wslc version`
- イメージの `wslc image inspect postgres:17` の結果・確認日時（必要なら digest）
- 名前付きボリュームの作成、起動、ready、TCP パスワード接続
- SQL 3行と更新値、停止・再開・削除再作成後のデータ
- Windows 側 `Test-NetConnection` と、用意できればホストクライアントによる SQL
- 学習用コンテナーだけの削除、ボリュームだけの削除

受講者と同じバージョン・ネットワーク条件で先行確認してください。事前のイメージ取得を案内し、取得に時間がかかった場合のために余裕を取ります。実行環境が準備できない受講者には講師画面での見学と、後日の実施を用意します。

### 進行の例（70分 + 予備20分）

| 時間 | 説明・操作 | 見届けるポイント |
|---|---|---|
| 0〜5分 | ゴールと3つの用語 | 開発用 DB を作ると理解できる |
| 5〜20分 | 起動 | ready まで待てる |
| 20〜40分 | SQL | 3行と done=true を確認 |
| 40〜55分 | 再開と作り直し | データとコンテナーを区別 |
| 55〜65分 | 接続情報 | Windows 側 15432 / DB 側 5432 |
| 65〜70分 | 後片付けとふりかえり | 残すか消すかを自分で選べる |

### 説明を足すなら

- `run` は新しく作って開始し、`start` は既存のものを再開する
- SQL クライアントを閉じても DB サーバーは動いている
- DB はボリュームに残るが、コンテナーの設定は起動コマンドで再現する
- 環境変数は DB の初回初期化に使われる。パスワード変更手段ではない
- この学習用 `postgres` ユーザーは管理者。実アプリ用権限設計は次の課題

### 終了時の確認問題

1. psql を閉じたら PostgreSQL も止まるか（止まらない）
2. 同じ DB を明日再開するにはどうするか（`container start`）
3. コンテナーを作り直すとき、どの指定をそろえるか（ボリューム名、保存先、DBのメジャー版、公開先など）
4. ボリュームを消すと何が起きるか（保存データが失われる）
5. Windows のアプリには何番を渡すか（15432）

### 実運用との境界

使い捨てのダミーパスワード、管理者ユーザー、単一 PC の構成です。本番用の秘密管理、最小権限、バックアップ、更新・移行、監視は別途設計が必要です。Compose、Kubernetes、Dev Containers は前提にしません。wslc と Docker の完全な互換性も前提にしません。

<a id="references"></a>

## 参考資料

### 公式資料

- [Microsoft: WSL コンテナー概要](https://learn.microsoft.com/ja-jp/windows/wsl/wsl-container?tabs=csharp)
- [Microsoft: WSL コンテナーの使用を開始する](https://learn.microsoft.com/ja-jp/windows/wsl/tutorials/wsl-containers) — WSL 2.9.3 以降、基本的な run / exec / stop
- [Microsoft/WSL: VolumeCommand.h](https://github.com/microsoft/WSL/blob/master/src/windows/wslc/commands/VolumeCommand.h) — ボリュームのサブコマンド
- [Microsoft/WSL: ContainerRunCommand.cpp](https://github.com/microsoft/WSL/blob/master/src/windows/wslc/commands/ContainerRunCommand.cpp) — run のオプション
- [Microsoft/WSL: ContainerExecCommand.cpp](https://github.com/microsoft/WSL/blob/master/src/windows/wslc/commands/ContainerExecCommand.cpp) — exec の対話オプション
- [Microsoft/WSL: マウント構文の単体テスト](https://github.com/microsoft/WSL/blob/master/test/windows/wslc/WSLCCLIMountParserUnitTests.cpp) — 名前付きボリュームの構文
- [Microsoft/WSL: 公開ポート構文の単体テスト](https://github.com/microsoft/WSL/blob/master/test/windows/wslc/WSLCPortParserUnitTests.cpp) — 明示的なホスト IP
- [PostgreSQL Docker Official Image](https://hub.docker.com/_/postgres) — 初期化変数・保存先・17以前と18以降の違い
- [Microsoft/WSL: 名前付きボリュームの E2E テスト](https://raw.githubusercontent.com/microsoft/WSL/master/test/windows/wslc/e2e/WSLCE2EContainerRunTests.cpp) — コンテナー削除後もデータを再利用
- [PostgreSQL: initdb](https://www.postgresql.org/docs/17/app-initdb.html) — 初期化時の TCP 認証方式
- [PostgreSQL: psql](https://www.postgresql.org/docs/17/app-psql.html)
- [PostgreSQL: pg_isready](https://www.postgresql.org/docs/17/app-pg-isready.html)
- [Rspress: Quick start](https://rspress.rs/guide/start/getting-started)

手元の wslc で使える引数は `--help` で確認してください。

### 構成の参考

[mikoto2000 / Practical-Introduction-to-Spring-Boot](https://github.com/mikoto2000/Practical-Introduction-to-Spring-Boot) の Rspress 2.0.1、左サイドバー、日本語ハンズオン、講義の区切りを参考にしています。本教材は独立したコンテンツとして、この教材集に収録しています。
