# コンテナで構築する開発環境の検証記録

## 実機で確認した範囲

2026-11-11 に、Windows 11、WSL 3.0.5.0、Ubuntu 24.04.5、Docker Engine 29.9.3、Compose v5.7.0 で確認しました。

- Vol.0 の APT リポジトリー登録とパッケージ導入を使い捨ての Ubuntu 24.04 コンテナで確認し、WSL 上で `hello-world` を実行
- Vol.1 の Apache を Windows から表示し、HTML の編集反映、Dockerfile からのビルド、Compose のサービス間通信を確認
- Vol.2 の構成を Dev Containers CLI で起動し、Java 21 コンテナに `postgresql-client` を導入して PostgreSQL 18 に接続

WSL と Docker Engine は導入済みの環境を使用しました。初回確認では、WSL の新規インストールと VS Code の画面操作は未実施です。

### 手順修正後の再確認（2026-11-11）

同じ Windows 11 / Ubuntu 環境で、検証専用のフォルダーと Docker リソースを使用しました。

- Vol.0 は使い捨ての Ubuntu 24.04 コンテナで APT リポジトリーの登録とパッケージの導入を再確認。WSL 側では `systemd`、Docker の稼働状態、`docker` グループを確認し、`hello-world` と `docker compose version` を実行
- Vol.1 は Windows の `curl.exe` で `127.0.0.1:8080` に接続。読み取り専用マウントでの HTML の編集反映、独自イメージの起動、`app` から `web:80` への通信を確認
- Vol.2 は VS Code 1.145.3 で WSL 上のフォルダーを開き、VS Code Server の更新と制限モードの表示を確認
- Vol.2 のコンテナ起動は Dev Containers CLI 0.89.0 で実行。`/workspace` への書き込みと Java 21.0.13.0.2 の表示に成功
- `app` に導入した psql 17 から `db:5432` の PostgreSQL 18.6 に接続。ホストへのポート公開がなく、データが `/var/lib/postgresql/18/docker` に書き込まれることを確認

この再確認での VS Code の画面操作は、WSL でフォルダーを開くところまででした。

### VS Code の画面操作（2026-11-11）

VS Code 1.145.3 と Dev Containers 拡張機能 0.469.0 を使い、WSL 上の検証用フォルダーを開きました。日本語のコマンドパレットで「開発コンテナー: コンテナーで再度開く」を選択しました。

- 制限モードからコマンドを実行すると信頼確認が表示された。検証用フォルダーを信頼して続行すると `/workspace` が開き、左下に「開発コンテナー: Java Dev Container」と表示された
- VS Code が起動した `app` と `db` を `docker compose ps` で確認。`app` の `java -version` は Java 21.0.13.0.2 と表示された

Java・Spring Boot 拡張機能を使った開発作業は未確認です。
