# 2. PostgreSQL を起動する

## この章のゴール

開発用 PostgreSQL を起動し、接続を受け付けていることを確認します。

## 必要な言葉を3つだけ

| 言葉 | 今回の役割 |
|---|---|
| イメージ | PostgreSQL と必要なファイルをまとめた、起動のもと |
| コンテナー | イメージから起動した、DB が動く環境 |
| ボリューム | DB のデータをコンテナーと分けて残す保存場所 |

起動の設定はコマンドに残し、データはボリュームに残します。コンテナーを作り直せることと、データを捨ててよいことは別です。

## 保存場所を作る

```powershell
wslc volume create wslc-workshop-pgdata
wslc volume inspect wslc-workshop-pgdata
```

作成した名前と詳細が表示されます。このボリュームは wslc が管理します。Windows の好きなフォルダーを DB の保存先にする手順ではありません。

## DB を起動する

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

## 起動完了を確認する

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

## 講義の区切り

「PostgreSQL のインストーラーを操作せずに、DB が起動した」を確認できればこの章は終了です。

[次へ: SQL を実行する](./03-sql.md)
