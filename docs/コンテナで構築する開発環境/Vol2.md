---
title: "Dev container 入門"
author: mikoto2000
date: 2026/1/13
---

# Dev container 入門

## 前提条件

- Vol.0 開発環境構築 を完了していること
- Vol.1 Docker/Docker Compose 入門 相当の知識を有していること
  - （基本的な Docker/Docker Compose の使い方がわかれば OK）
- VS Code に **Dev Containers** 拡張機能をインストールしていること
  - WSL 上のフォルダーを開くため、**WSL** 拡張機能も必要である
  - 拡張機能ビューで `Dev Containers` と `WSL` を検索してインストールする

## Dev container 概要

この章では、 Dev container を使い始める前に概要を説明します。

Dev container とは、誤解を恐れず言うと、
「docker や docker compose コマンドで立ち上げたコンテナに、 VS Code を転送して作業するための仕組み」
です。

ファイル編集やコマンド実行はコンテナ上に転送した VS Code で行い、その結果を見る UI だけがホスト OS 上で動きます。

Dev container では `devcontainer.json` という設定ファイルを使い、
コンテナ上の開発環境設定をコードとして管理します。
(VS Code の設定やインストールする拡張機能・拡張機能設定など)

単に Docker コンテナを起動するだけでは、エディタ設定やツール構成までは共有できません。
`devcontainer.json` を定義すれば、開発環境そのものを再現可能な形でチームに共有できます。

![Dev Container](./images/vol2/dev-container.png)

## 作業用ディレクトリの作成

これ以降の作業は、 WSL2 のファイルシステム上に作業用ディレクトリを作成し、そこで進めます。
WSL2 の Ubuntu 24.04 を起動し、次のコマンドで作業用ディレクトリを作成してください。

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

AP サーバー兼開発サーバーの `app` と、 DB サーバーの `db` をサービスとして定義します。

`.devcontainer/compose.yaml` に、次の内容を記述してください。

```yaml
services:
  # AP サーバー兼開発コンテナ定義
  app:
    # Microsoft が提供している Dev container 向けの Java イメージ
    image: mcr.microsoft.com/devcontainers/java:21
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

# コンテナの再起動をしてもデータが残るように、ボリュームを定義
volumes:
  pgdata:
```

### devcontainer.json の作成

次に、主に「VS Code でどのコンテナに接続し、どんな拡張機能を使うか」を定義していきます。
`.devcontainer/devcontainer.json` に、次の内容を記述してください。

```json
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

`Do you trust the authors of the files in this folder?` というダイアログが表示されます。`Yes, I trust the authors` をクリックしてください。

VS Code が表示され、左下に `WSL: Ubuntu-24.04` と表示されます。


## Dev container 開発環境の起動

1. Ctrl+Shift+P -> `Open Folder in Container` と入力
2. 候補に表示される `Dev Containers: Open Folder in Container...` を選択
3. 作成した作業ディレクトリが表示されるので、そのまま Enter を押下

すでに VS Code でそのフォルダーを開いている場合は、同じメニューの `Dev Containers: Reopen in Container` でも起動できます。

VS Code のウィンドウがリロードされ、左下に `Dev Container: Java Dev Container` と表示されます。

これで、 Dev container による開発環境の立ち上げが完了しました。

このように、事前にいろいろと作るものはありますが、誰かがつくったものを使うだけであれば、 VS Code を開いてから数手で環境の立ち上げが完了します。

## Dev container 開発環境の動作確認

Spring Boot プロジェクトを作って DB へ接続するのは時間がかかりすぎます。
代わりに app コンテナへ PostgreSQL クライアントをインストールし、そこから psql で DB に繋がることを確認します。

### PostgreSQL クライアントのインストール

VS Code でターミナルを開き、次のコマンドを実行してください。
コンテナ上に `psql` コマンドがインストールされます。

```sh
sudo apt update
sudo apt install -y postgresql-client
```

### PostgreSQL コンテナへの接続

app コンテナには環境変数が設定されていますので、活用しましょう。

```sh
PGPASSWORD=${MAIN_DB_PASSWORD} psql -U ${MAIN_DB_USER} -h ${MAIN_DB_HOSTNAME} -d ${MAIN_DB_NAME}
```

DB に接続できたら OK です。

後は、 Spring Initializr などで Spring Boot プロジェクトを作成し、 `.devcontainer` と同じディレクトリに格納します。これで Spring Boot + PostgreSQL のプロジェクトの開発ができます。


## 開発環境の共有方法

開発環境の共有方法は簡単で、プロジェクトのリポジトリ（Git リポジトリなど）に `.devcontainer` を含めるだけです。

こうすることで、 `git clone` をしたのち、プロジェクトディレクトリを VS Code + Dev container 拡張機能を使って開くだけで共通の開発環境を使用できます。

