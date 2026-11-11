# 4. 止める・再開する・作り直す

## この章のゴール

DB を使わないときは止め、必要になったら再開します。さらに、コンテナーを作り直しても学習データが残ることを確認します。

## 今日の作業を終える

psql の中なら `\q` で抜けてから、PowerShell で実行します。

```powershell
wslc container stop wslc-workshop-db
wslc container list --all
```

対象が停止状態になったことを確認します。停止中は DB に接続できません。コンテナーとボリュームはまだ残っています。

## 翌日の作業を始める

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

## コンテナーだけ作り直す

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

## なぜ残ったのか

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
`POSTGRES_PASSWORD` や `POSTGRES_DB` は、空の保存先で初期化するときの設定です。同じボリュームで環境変数だけ変えて再作成しても、既存のパスワードや DB は変更されません。ログインできなくなったとき、データを消して直そうとせず、[困ったときは](../troubleshooting.md)を見ます。

:::

## 講義の区切り

「起動設定は再利用でき、DB のデータは別に残せる」を自分の言葉で説明できれば成功です。

[次へ: 自分のアプリから接続する](./05-connect.md)
