# 3. SQL を実行する

## この章のゴール

DB に接続し、自分で登録したデータを読み出します。SQL を覚えるより、開発用 DB をすぐ試せる状態になったことを体験しましょう。

## コンテナー内の psql を使う

PowerShell で実行します。ホストに psql を入れる必要はありません。

```powershell
wslc exec -it wslc-workshop-db psql -h 127.0.0.1 -U postgres -d workshop -W
```

`Password for user postgres:` に `workshop-local-only` を入力して Enter を押します。入力文字が表示されなくても正常です。

`workshop=#` が出たら、今いるのは psql の画面です。`-h 127.0.0.1` は **コンテナー内**の TCP 接続を指定しています。前章の Windows 側 15432 番を通る接続ではありません。`-W` はパスワード入力を要求します。2章では初回の TCP 認証方式も指定しています。`-W` 自体がサーバーの認証を有効にするわけではありません。

```sql
SELECT current_database(), current_user;
```

`workshop` と `postgres` が表示されます。

## テーブルを用意する

```sql
CREATE TABLE IF NOT EXISTS tasks (
  id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title text NOT NULL UNIQUE,
  done boolean NOT NULL DEFAULT false
);
```

`CREATE TABLE` が表示されます。再実行時には「既にある」という通知の出る場合があります。この手順では問題ありません。

## データを登録して読む

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

## データを変更する

```sql
UPDATE tasks SET done = true WHERE title = 'Start PostgreSQL';
SELECT title, done FROM tasks ORDER BY id;
```

`UPDATE 1` が表示され、`Start PostgreSQL` の `done` が `t`（true）になれば成功です。

## 自分のデータを1つ追加する

```sql
INSERT INTO tasks (title)
VALUES ('My first container database')
ON CONFLICT (title) DO NOTHING;
SELECT count(*) FROM tasks;
```

他に追加していなければ `3` が表示されます。次の章では、この3行が残るか確認します。

## psql を終了する

```text
\q
```

PowerShell の表示に戻ります。**psql を終了しても DB は動き続けています。** クライアントを閉じる操作と、DB を止める操作は別です。

困ったときは、途中の SQL 入力を Ctrl+C で取り消せます。`workshop-#` のままなら、まだ文の入力が終わっていない可能性があります。

[次へ: 止める・再開する・作り直す](./04-persist.md)
