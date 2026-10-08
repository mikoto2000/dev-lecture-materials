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

```powershell
wslc container start wslc-workshop-db
wslc exec wslc-workshop-db pg_isready -h 127.0.0.1 -U postgres -d workshop
```

`accepting connections` が出るまで待ってから、前章と同じ方法で接続します。

```powershell
wslc exec -it wslc-workshop-db psql -h 127.0.0.1 -U postgres -d workshop -W
```

パスワードは `workshop-local-only` です。

```sql
SELECT title, done FROM tasks ORDER BY id;
```

3行と更新した `done` が残っていることを確認し、`\q` で戻ります。

## コンテナーだけ作り直す

ここで削除するのは **この教材の停止したコンテナーだけ**です。DB のボリュームは消しません。名前を一文字ずつ確認してから実行します。

```powershell
wslc container stop wslc-workshop-db
wslc container remove wslc-workshop-db
wslc volume inspect wslc-workshop-pgdata
```

`remove` に `-v` や `--volumes` を追加しないでください。ボリュームが残っていることを確認したら、2章と同じ設定で新しいコンテナーを作ります。

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

準備完了後、同じ接続コマンドと SELECT で3行を確認します。コンテナーの ID は変わっても、ボリュームに保存したデータは残ります。

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
