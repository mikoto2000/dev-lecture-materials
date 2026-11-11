---
title: "Dev container 入門"
author: mikoto2000
date: 2026/1/13
---

# Dev container 入門

## 前提条件

- [Vol.0 開発環境構築](./Vol0.md)を完了していること
- [Vol.1 Docker/Docker Compose 入門](./Vol1.md)相当の知識を有していること
  - （基本的な Docker/Docker Compose の使い方がわかれば OK）
- VS Code に **Dev Containers** 拡張機能をインストールしていること
  - WSL 上のフォルダーを開くため、**WSL** 拡張機能も必要である
  - 拡張機能ビューで `Dev Containers` と `WSL` を検索してインストールする

## Dev container 概要

この章では、 Dev container を使い始める前に概要を説明します。

Dev Container は、コンテナを開発環境として使うための仕組みです。この教材では、VS Code の Dev Containers 拡張機能が Docker Compose で開発環境を起動し、開発用コンテナに接続します。

VS Code の画面は Windows 側で動き、コンテナ内の VS Code Server がワークスペースへのアクセスやターミナルの実行を受け持ちます。開発ツールとワークスペース用の拡張機能もコンテナ内で動きます。[VS Code の Dev Containers ガイド](https://code.visualstudio.com/docs/devcontainers/containers)

Dev container では `devcontainer.json` という設定ファイルを使い、
コンテナ上の開発環境設定をコードとして管理します。
（VS Code の設定やインストールする拡張機能・拡張機能設定など）

単に Docker コンテナを起動するだけでは、エディタ設定やツール構成までは共有できません。
`devcontainer.json` を定義すれば、開発環境そのものを再現可能な形でチームに共有できます。

| 接続元 | 接続先 |
|---|---|
| Windows の VS Code | `app` コンテナ内の VS Code Server |
| `app` コンテナ内の psql | `db` コンテナの PostgreSQL（`db:5432`） |

## 作業用ディレクトリの作成

これ以降の作業は、 WSL2 のファイルシステム上に作業用ディレクトリを作成し、そこで進めます。
WSL2 の Ubuntu 24.04 を起動し、`docker version` で Client と Server の両方が表示されることを確認します。続いて、次のコマンドで作業用ディレクトリを作成してください。すでに同じ名前のディレクトリがある場合は、未使用の名前を選びます。

```sh
mkdir -p ~/tmp/devcontainer-handson/.devcontainer
cd ~/tmp/devcontainer-handson
```

`mkdir` の `-p` は、途中のディレクトリもまとめて作成する指定です。以降のファイルは、この `~/tmp/devcontainer-handson` をプロジェクトルートとして作成します。

:::note
Windows のファイルシステム上でも実行は可能だが、パフォーマンスが著しく落ちるため、 WSL2 のファイルシステム上で作業するようにしましょう。

:::


## Dev container の設定方法

今回は、 Spring Boot + PostgreSQL を使った Web アプリケーションの開発環境を構築していきます。

使用するサーバーを列挙すると、次のようになります。

- AP サーバー: Spring Boot 組み込み Tomcat
- DB サーバー: PostgreSQL

このように複数サーバーが必要になるため、 Docker Compose で環境を定義し、それを基に Dev container の設定を進めていきます。


### compose.yaml の作成

Java の開発用コンテナ `app` と、PostgreSQL が動く `db` をサービスとして定義します。`app` は将来 Spring Boot を実行する場所です。この演習では、`app` のターミナルから `db` に接続するところまでを確認します。

`.devcontainer/compose.yaml` に、次の内容を記述してください。

```yaml
services:
  # Java の開発コンテナ定義
  app:
    # Microsoft が提供している Dev container 向けの Java イメージ
    image: mcr.microsoft.com/devcontainers/java:3-21-trixie
    init: true
    # 環境変数定義
    # 次では PostgreSQL への接続情報を設定している
    environment:
      MAIN_DB_HOSTNAME: db
      MAIN_DB_NAME: appdb
      MAIN_DB_USER: admin
      MAIN_DB_PASSWORD: password
    volumes:
      # プロジェクトルートを /workspace にマウント
      - ..:/workspace
    command: sleep infinity

  # DB サーバー定義
  db:
    # postgres v18 を使用
    image: postgres:18-trixie
    init: true
    # 環境変数定義
    # Docker Hub の postgres のページを見るとわかるが、
    # 環境変数によって実行する DB の設定変更が可能。
    # 次では DB 名・ユーザー名・パスワードを設定している
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      # 下段の「volumes」で定義したボリュームに PostgreSQL のデータを格納するように設定
      - pgdata:/var/lib/postgresql

# コンテナを作り直してもデータが残るように、ボリュームを定義
volumes:
  pgdata:
```

この `password` は学習用のサンプル値です。実在のパスワードを流用せず、実際のプロジェクトでは秘密管理の仕組みを使ってください。`db` のポートはホストへ公開していません。

`app` は Compose のサービス名 `db` をホスト名として、PostgreSQL の標準ポート 5432 に接続します。`postgres:18-trixie` は `/var/lib/postgresql` 配下のバージョン別ディレクトリにデータを保存します。PostgreSQL 17 の教材とはマウント先が異なります。[PostgreSQL 公式イメージの PGDATA の説明](https://hub.docker.com/_/postgres#pgdata)

### devcontainer.json の作成

次に、主に「VS Code でどのコンテナに接続し、どんな拡張機能を使うか」を定義していきます。
`.devcontainer/devcontainer.json` に、次の内容を記述してください。

```jsonc
{
  "name": "Java Dev Container",

  // 使用する compose.yaml を指定
  "dockerComposeFile": "compose.yaml",
  // VS Code で接続するサービスを指定
  "service": "app",
  // ワークスペースとするディレクトリを指定
  "workspaceFolder": "/workspace",

  "customizations": {
    // VS Code 固有の設定
    "vscode": {
      // インストールする拡張機能
      "extensions": [
        // java
        "vscjava.vscode-java-pack",
        // spring boot
        "vmware.vscode-boot-dev-pack"
      ]
    }
  }
}
```

これで、 Dev container 開発環境を起動する準備ができました。


## VS Code の起動

プロジェクトルート（`.devcontainer` の親ディレクトリ）に移動し、次のコマンドを実行してください。

```sh
code .
```

初回や VS Code の更新直後は、WSL 内に VS Code Server をダウンロードしてインストールする場合があります。ターミナルに進行状況が表示されるので、VS Code の起動まで待ちます。

VS Code の左下に `WSL: Ubuntu-24.04` と表示されることを確認します。ワークスペースの信頼を尋ねられた場合は、自分で作成した教材用フォルダーを開いていることを確認し、`Yes, I trust the authors` を選びます。制限モード（Restricted Mode）のバナーが表示された場合は、「管理」（Manage）から同じフォルダーの信頼を設定します。


## Dev container 開発環境の起動

1. Ctrl+Shift+P でコマンドパレットを開く
2. `Dev Containers: Reopen in Container`（日本語表示では「開発コンテナー: コンテナーで再度開く」）を選択する
3. 信頼確認が表示された場合は、自分で作成した教材用フォルダーであることを確認し、「フォルダーを信頼して続行」を選ぶ

VS Code のウィンドウがリロードされます。左下の接続先に `Dev Container: Java Dev Container`（日本語表示では「開発コンテナー: Java Dev Container」）が出るまで待ちます。

これで、 Dev container による開発環境の立ち上げが完了しました。

このように、事前にいろいろと作るものはありますが、誰かがつくったものを使うだけであれば、 VS Code を開いてから数手で環境の立ち上げが完了します。

## Dev container 開発環境の動作確認

`app` コンテナの Java と、`db` への接続を確認します。VS Code 左下の接続先が `Java Dev Container` になったら、新しい統合ターミナルを開きます。`java -version` で Java 21 が表示されることを確認してください。

### PostgreSQL クライアントのインストール

同じターミナルで次のコマンドを実行してください。
コンテナ上に `psql` コマンドがインストールされます。

```sh
sudo apt update
sudo apt install -y postgresql-client
```

旧版の `mcr.microsoft.com/devcontainers/java:21` イメージでは、Yarn リポジトリーの署名エラーにより `apt update` が失敗しました。同じエラーが出たら、`compose.yaml` の `app` を上記のイメージ指定に更新し、`Dev Containers: Rebuild Container` を実行します。[Java Dev Container イメージ](https://github.com/devcontainers/images/blob/main/src/java/README.md)

ここで追加したパッケージは、開発コンテナを作り直すと失われます。チーム全員の環境に含めるには、Dockerfile などの構成にインストール手順を記述します。

### PostgreSQL コンテナへの接続

app コンテナには環境変数が設定されていますので、活用しましょう。

```sh
PGPASSWORD="$MAIN_DB_PASSWORD" psql -U "$MAIN_DB_USER" -h "$MAIN_DB_HOSTNAME" -d "$MAIN_DB_NAME"
```

`appdb=#` が表示されたら接続成功です。`\conninfo` で接続先を確認し、`\q` でシェルに戻ります。接続を拒否された場合は、PostgreSQL の初期化を数秒待ってから再試行してください。

この構成で Spring Boot の開発を始めるときは、プロジェクトを `.devcontainer` のある作業ディレクトリーに置きます。`MAIN_DB_*` は教材で定義した環境変数なので、Spring Boot から使うにはデータソース設定で明示的に参照します。


## 開発環境の共有方法

開発環境の共有方法は簡単で、プロジェクトのリポジトリ（Git リポジトリなど）に `.devcontainer` を含めるだけです。

こうすることで、 `git clone` をしたのち、プロジェクトディレクトリを VS Code + Dev container 拡張機能を使って開くだけで共通の開発環境を使用できます。

