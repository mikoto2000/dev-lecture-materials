<a id="top"></a>

# Dev Container で構築する開発環境

Docker・Docker Compose の基礎から、Dev Container を使った開発環境づくりまで学ぶ教材です。各章を順に進めてください。

## 目次

- [イントロダクション](#introduction)
- [Vol.0 開発環境構築](#vol0)
- [Vol.1 Docker / Docker Compose 入門](#vol1)
- [Vol.2 Dev Container 入門](#vol2)
- [まとめ](#summary)

[教材一覧へ戻る](../index.md)

<a id="introduction"></a>

## イントロダクション

### Description

プロジェクトの開発環境構築をする／させる際に、手順ミスやアドリブで環境差異が発生してしまい、てこずった経験はありませんか。
Dev container を使うと、開発環境の構成をコードで共有でき、チームのメンバーが同じ手順で開発を始められます。
本シリーズでは、Docker を使った開発環境構築の基礎から、Dev container を用いた再現性の高い開発環境の設計・共有までを、段階的に学びます。
プロジェクトの開発環境構築に苦労している方、Dev container に興味がある方はぜひご参加ください。
シリーズ終了時には、Spring Boot + PostgreSQL を想定した Dev container 構成を作り、チームで再利用できるテンプレートとして持ち帰れる状態を目指します。Vol.2 では Spring Boot プロジェクト自体は作成せず、開発コンテナと DB への接続までを確認します。

### Outline

Dev container による開発環境の構築方法を解説します。前提となる Docker と Docker Compose の基礎から、VS Code での Dev container の使い方までを、全 2 回のワークショップで扱います。

#### 話すこと

- 開発環境構築（事前準備資料として配布）
  - Docker on WSL2 のセットアップ
- Docker 入門
  - Docker コンテナを使ってみる
  - Docker Compose を使ってみる
- Dev container 入門
  - Dev container の概要
  - Dev container の設定方法
  - Dev container の利用方法

#### 話さないこと

- コンテナ技術の理論的な説明
- Docker / Docker Compose の高度な使い方
- VS Code の一般的な操作方法

#### 対象者

- （プロジェクトメンバの）開発環境構築に苦労している人
- プロジェクトの技術的取りまとめをしている人
- Dev container に興味がある人
- ターミナル操作に抵抗が無い人（基本的なコマンド操作ができればOK）

#### このテーマを取り上げる理由

プロジェクトの開発環境構築をする／させる際に、手順ミスやアドリブで環境差異が発生してしまい、そのサポートに時間を取られた経験がある方も多いでしょう。
その解決方法として、Dev container を使った開発環境の構築方法を導入し、比較的スムーズに環境構築ができるようになった経験を共有したいと考え、本セッションを企画しました。

#### 講演の概要

- Vol.0 開発環境構築（事前準備資料として配布）
  - Docker on WSL2
  - Hello World コンテナを動かしてみる
- Vol.1 Docker / Docker Compose 入門
  - Docker コンテナ概要
  - Docker コンテナを使ってみる
    - Web サーバコンテナを動かしてみる
      - ポートフォワーディング
      - ボリュームマウント
  - Docker Compose を使ってみる
    - 複数サービスの定義
    - ポートフォワーディング
    - ボリュームマウント
- Vol.2 Dev container 入門
  - Dev container の概要
  - Dev container の設定方法
  - Dev container の利用方法

### 自身について

#### 概要

仕事と趣味でプログラミングをやっているプログラマー。
一生を Getting Started の実施で過ごす人。
最近プライベートではギョームの素振りばかりやっています。

<a id="vol0"></a>

## 開発環境構築

### 前提条件

- Windows 11 の PC（WSL 2 が利用できること。Home エディションでも可）

### VS Code のインストール

次の公式サイトから VS Code をインストールしてください。

[Visual Studio Code 公式サイト](https://code.visualstudio.com/)

インストール時に、次のチェックボックスを ON にするのを推奨（便利）。

- `エクスプローラーのファイルコンテキストメニューに[Code で開く]アクションを追加する`
- `エクスプローラーのディレクトリコンテキストメニューに[Code で開く]アクションを追加する`

インストール後、VS Code が起動できることを確認してください。

### WSL のインストール

#### WSL の有効化

WSL (Windows Subsystem for Linux) と Ubuntu 24.04 LTS をインストールします。すでに Ubuntu 24.04 をインストールしている場合は、次の「Ubuntu 24.04 の起動」へ進んでください。

Windows Terminal を管理者として起動し、PowerShell で次のコマンドを実行します。

```powershell
wsl.exe --install -d Ubuntu-24.04
```

「ユーザーアカウント制御」のダイアログが表示された場合は「はい」をクリックします。

再起動を求められた場合は、作業中のファイルを保存してから PC を再起動します。

#### Ubuntu の初期設定

Ubuntu の画面が自動で開かなければ、PowerShell で次のコマンドを実行します。

```powershell
wsl.exe -d Ubuntu-24.04
```

初回起動時に、Ubuntu のユーザー名とパスワードを設定します。

Linux のシェルが起動したら、インストール成功です。

:::warning BIOS の仮想化支援機能が無効の場合
この時点で BIOS の仮想化支援機能を無効にしていると、エラーメッセージが表示されることもあります。その場合は、セクション「BIOS の仮想化支援機能の有効化」を参照して BIOS の設定を変更し、もう一度 WSL のインストールをやり直してください。

:::

### BIOS の仮想化支援機能の有効化

WSL 2 を使用するためには、BIOS の仮想化支援機能が有効になっている必要があります。
この章では、BIOS の仮想化支援機能を有効にする手順を説明します。


#### BIOS 設定画面へのアクセス

1. Windows メニュー → 設定 → システム → 回復 を選択
2. 項目 `PC の起動方法をカスタマイズする` の、ボタン `今すぐ再起動` をクリック
3. `デバイスを再起動するため作業内容を保存します` のダイアログが表示されたら、`今すぐ再起動` をクリック
4. オプション選択画面で、`トラブルシューティング` → `詳細オプション` → `UEFI ファームウェア設定` を選択
5. `再起動` ボタンをクリックして、BIOS 設定画面に入る


#### 仮想化支援機能の有効化

BIOS 設定画面で、仮想化支援機能を有効にします。

##### 注意

BIOS 設定画面の操作方法は PC のメーカーやモデルによって異なります。次の手順で操作できない場合は、運営に問い合わせてください。

また、 BIOS 設定は PC の基本設定に影響します。本資料で指定していない項目は**絶対に**変更しないでください。

##### 手順

次のような名前のセクションを探して開いてください。

- Advanced
- Advanced BIOS Features
- Advanced → CPU Configuration
- Northbridge / Chipset

そのセクションの中から、次のような名前の設定項目を探してください。

- Intel Virtualization Technology
- Intel VT-x
- SVM Mode（AMD）
- CPU Virtualization
- Virtualization Technology

項目の値が `Disabled` になっている場合、`Enabled` に変更してください。

変更が完了したら、BIOS 設定画面を保存して終了し、PC を再起動してください。

BIOS のどこかに `Save & Exit` という名前のメニューがあるはずです。

再起動が完了したら、再度 WSL のインストールを試みてください。


### Ubuntu 24.04 の起動

インストールが成功した場合、すでに Ubuntu 24.04 のシェルが起動しているはずです。
ここでは、改めて Ubuntu 24.04 を起動する手順を説明します。

Ubuntu 24.04 を起動するには、スタートメニューから Ubuntu 24.04 を選択して起動します。

Windows の PowerShell で `wsl.exe -l -v` を実行し、`Ubuntu-24.04` の `VERSION` が `2` であることを確認してください。既存の Ubuntu 24.04 が WSL 1 の場合は、[Microsoft の移行手順](https://learn.microsoft.com/ja-jp/windows/wsl/install#upgrade-version-from-wsl-1-to-wsl-2)を参照してください。

### Docker のインストール

Ubuntu 24.04 の起動後、[Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/) の手順に従って、Docker をインストールします。

以降のコマンドは Ubuntu のシェルで実行します。このシリーズでは Ubuntu 内の Docker Engine を使います。事前に `ps -p 1 -o comm=` を実行し、`systemd` が表示されることを確認します。別の名前が表示された場合は、[WSL で systemd を有効にする手順](https://learn.microsoft.com/ja-jp/windows/wsl/systemd)を参照してください。

#### apt リポジトリの登録

Docker インストールに必要な apt リポジトリを Ubuntu に登録します。

```sh
# Add Docker's official GPG key:
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
```

#### Docker エンジンのインストール

Docker エンジンをインストールします。

```sh
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Docker デーモンの状態を `systemctl is-active docker` で確認します。`activating` が表示されたら数秒待って再確認します。停止している場合は `sudo systemctl start docker` で起動し、`active` になってから進みます。

この教材では、Docker コマンドを `sudo` なしで実行できるように、現在のユーザーを `docker` グループに追加します。このグループのメンバーは Docker を通じて Ubuntu の root 相当の権限を持ちます。[Docker Engine のインストール後の設定](https://docs.docker.com/engine/install/linux-postinstall/)

```sh
sudo gpasswd -a "$(id -un)" docker
```

`newgrp docker` を実行して、現在のシェルでグループの変更を反映します。`id -nG` の出力に `docker` が含まれることを確認してください。

VS Code など、グループ追加前から Ubuntu 内で動いているプロセスにも変更を反映するには、Ubuntu を再起動します。作業を保存してから、Windows の PowerShell で `wsl.exe --terminate Ubuntu-24.04` を実行します。このコマンドで対象の Ubuntu 内のプロセスがすべて停止します。その後、Ubuntu を開き直してください。


#### Docker の動作確認

Docker が正しくインストールされたか確認するため、 Hello World コンテナを実行してみます。

```sh
docker run --rm hello-world
```

次のようなメッセージが表示されたら、動作確認成功です。

```sh
Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```

以上で、Docker のインストールと動作確認は完了です。お疲れさまでした。

`docker compose version` で、Docker CLI に統合された Compose v2 または v5 のバージョンが表示されることを確認します。[Docker Compose のバージョン](https://docs.docker.com/compose/intro/history/)


### 参考資料

- [WSL のインストール | Microsoft Learn](https://learn.microsoft.com/ja-jp/windows/wsl/install)
- [WSL のトラブルシューティング | Microsoft Learn](https://learn.microsoft.com/ja-jp/windows/wsl/troubleshooting)
- [Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/)

<a id="vol1"></a>

## Docker/Docker Compose 入門

### 前提条件

- [Vol.0 開発環境構築](#vol0)を完了していること

以降のコマンドは、WSL 2 の Ubuntu 24.04 のシェルで実行します。ホームディレクトリー配下に教材専用の作業場所を作り、移動してください。すでに同じ名前のディレクトリーがある場合は、別の名前を使います。

```sh
mkdir -p ~/docker-handson/site
cd ~/docker-handson
```


### Docker コンテナ概要

この章では、開発環境として Docker コンテナを利用する際に知っておくべき基本的な概念を説明します。


#### Docker コンテナとは

「Docker コンテナ = 使い捨てのアプリケーション実行環境」と考えてください。
Docker イメージと言われるテンプレートからコンテナを起動し、その中でアプリケーションを実行します。


#### Docker イメージとは

「Docker イメージ = コンテナの設計図」と考えてください。
プログラムでいうところのクラスのようなもので、イメージからコンテナを起動（インスタンス化）します。
自分でイメージを作るときは、Dockerfile に構築手順を書いてビルドできます。この章では、公開済みのイメージを取得して使う方法と、自分でビルドする方法の両方を試します。


#### Dockerfile とは

「Dockerfile = イメージの構築手順書」と考えてください。
プログラムでいうところのソースコードです。どのようにアプリケーション実行環境を構築するかを記述します。


```text
Dockerfile ── docker build ──> イメージ
イメージ   ── docker run   ──> コンテナ（実行するたびに新規作成）
```


### Docker コンテナを使ってみる

本シリーズの最終目標は Dev container を使った開発環境構築ですが、その前提として Docker コンテナの基本的な使い方を学びます。

今回は Apache HTTP Server コンテナを使って、Web サーバコンテナを動かしてみましょう。

#### Apache HTTP Server コンテナの起動

```sh
docker run --rm httpd:2.4
```

`httpd:2.4` は Apache 2.4 系のパッチ更新を取り込むタグです。下の起動ログに出るパッチ番号は、取得したイメージによって変わります。

次のような実行結果が表示されます。これで Apache HTTP Server コンテナが起動します。

```sh
AH00558: httpd: Could not reliably determine the server's fully qualified domain name, using 172.17.0.2. Set the 'ServerName' directive globally to suppress this message
AH00558: httpd: Could not reliably determine the server's fully qualified domain name, using 172.17.0.2. Set the 'ServerName' directive globally to suppress this message
[Fri Jan 09 10:39:26.403849 2026] [mpm_event:notice] [pid 1:tid 1] AH00489: Apache/2.4.66 (Unix) configured -- resuming normal operations
[Fri Jan 09 10:39:26.403951 2026] [core:notice] [pid 1:tid 1] AH00094: Command line: 'httpd -D FOREGROUND'
```

この起動方法ではホストのポートをコンテナへ割り当てていないため、Windows のブラウザーから `http://127.0.0.1:8080` でこの Apache には接続できません。
Apache はフォアグラウンドで動くため、このシェルにはプロンプトが戻りません。Ctrl+C で停止すると、`--rm` の指定によりコンテナも削除されます。


#### ポートフォワーディングでアクセスできるようにする

ホスト OS からコンテナへアクセスするために、ポートフォワーディングを設定します。
ポートフォワーディングを設定すると、ホスト OS の特定のポートへのアクセスをコンテナ内の特定のポートに転送できます。

```sh
docker run --rm -p 127.0.0.1:8080:80 httpd:2.4
```

`-p 127.0.0.1:8080:80` は、Docker ホストである Ubuntu のループバックアドレスの 8080 番ポートを、コンテナ内の 80 番ポートへ転送する指定です。通常の WSL 2 の設定では、Windows からもループバックアドレスで接続できます。[WSL のネットワーク設定](https://learn.microsoft.com/ja-jp/windows/wsl/networking)

Windows のブラウザーで `http://127.0.0.1:8080` にアクセスしてみましょう。
`It works!` と表示されたら成功です。

```text
Windows のブラウザー → Ubuntu の 127.0.0.1:8080 → Apache コンテナの 80 番
```


#### バインドマウントでコンテンツを変更できるようにする

バインドマウントを使うと、Ubuntu 上のファイルをコンテナ内の指定した場所から参照できます。この例では、公開する HTML を置く `site` ディレクトリーだけをマウントします。

前のコンテナが動いたままなら、そのターミナルで Ctrl + C を押して停止します。同じポート 8080 は同時に使えないためです。

| Ubuntu 上のファイル | コンテナ内で参照するパス |
|---|---|
| `site/index.html` | `/usr/local/apache2/htdocs/index.html` |

作業ディレクトリーの `site/index.html` に、次の内容を記述します。

```html
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8">
    <title>It's my created file!</title>
  </head>
  <body>
    <p>It's my created file!</p>
  </body>
</html>
```

作業ディレクトリーで次のコマンドを実行します。

```sh
docker run --rm -p 127.0.0.1:8080:80 -v "$(pwd)/site:/usr/local/apache2/htdocs:ro" httpd:2.4
```

`$(pwd)` は現在の作業ディレクトリーの絶対パスに展開されます。`-v` は `site` を Apache のドキュメントルートにマウントする指定です。末尾の `:ro` により、コンテナからの書き込みはできません。

`http://127.0.0.1:8080` を開き、`It's my created file!` が表示されることを確認します。Ubuntu 側で `site/index.html` を編集してブラウザーを再読み込みすると、コンテナを作り直さずに変更が反映されます。確認後は、次の手順でも同じファイルを使うため、内容を元に戻してください。


#### カスタム Docker イメージの作成

Docker イメージの基本的な使い方は理解できたはずです。
次に、カスタム Docker イメージを作成してみましょう。

##### Dockerfile の作成

`httpd` イメージと同じように、 Apache HTTP Server を動作させるカスタム Docker イメージを作成します。
まず、カレントディレクトリに `Dockerfile` という名前のファイルを作成し、次の内容を記述します。

```dockerfile
# ベースイメージを指定
# ベースイメージは、 Docker Hub で公開されている ubuntu イメージを使用
FROM ubuntu:24.04

# Apache HTTP Server をインストール
RUN apt-get update \
 && apt-get install -y --no-install-recommends apache2 \
 && rm -rf /var/lib/apt/lists/*

# apache HTTP Server の起動に必要なディレクトリを作成
RUN mkdir -p /var/run/apache2 /var/lock/apache2

# コンテナが使用するポートを明示する
EXPOSE 80

# Apache HTTP Server をフォアグラウンドで起動
# Ubuntu のサービスとして起動するわけではないため、
# 起動時に一工夫している
CMD ["sh", "-c", ". /etc/apache2/envvars && exec apache2 -DFOREGROUND"]
```


##### Docker イメージのビルド

次に、カスタム Docker イメージをビルドします。
カレントディレクトリで、次のコマンドを実行します。

```sh
docker build -t my-httpd:latest .
```

- `-t my-httpd:latest`: ビルドするイメージに `my-httpd:latest` という名前を付ける
- `.` はビルド時に参照できるファイルの範囲（ビルドコンテキスト）として、現在のディレクトリーを指定する。この例では、その直下の `Dockerfile` が使われる

次に、`docker images` コマンドで、ビルドしたイメージが作成されていることを確認します。

表示される列は Docker のバージョンやイメージストアによって異なります。イメージ名とタグでビルドしたイメージを確認してください。
次のように `my-httpd:latest` イメージが表示されれば成功です。

```sh
# docker images
IMAGE                                                                                                                      ID             DISK USAGE   CONTENT SIZE   EXTRA
my-httpd:latest                                                                                                            bb045a3f673c        242MB             0B
```


##### カスタム Docker イメージの起動

最後に、ビルドしたカスタム Docker イメージを起動します。
前の手順で起動したコンテナが残っているとポート 8080 が使われます。そのターミナルで Ctrl + C を押すか、`docker ps` で確認したコンテナ ID を `docker stop <コンテナID>` で停止してください。

次のコマンドを実行します。

```sh
docker run --rm -p 127.0.0.1:8080:80 -v "$(pwd)/site:/var/www/html:ro" my-httpd:latest
```

`/var/www/html` は Ubuntu の `apache2` パッケージの既定のドキュメントルートです。先ほどと同じ `site` を読み取り専用でマウントします。

再度 Web ブラウザで `http://127.0.0.1:8080` にアクセスしてみましょう。
`It's my created file!` と表示されれば成功です。

これで、カスタム Docker イメージの作成と起動ができました。


### Docker Compose を使ってみる

Docker Compose は、複数のサービスで構成されるアプリケーションを定義し、関連するコンテナをまとめて管理するツールです。この演習では、サービスごとにコンテナを1つ起動します。

本ワークショップでは、 Dev container を使った開発環境構築を見越して、「開発環境」と「Web サーバー環境」のふたつのサービスを定義してみましょう。


#### 複数サービスの定義

前述の通り、「開発環境」と「Web サーバー環境」のふたつのサービスを定義します。
サービスの内容としては、次の通りです。

- 開発環境: curl クライアントをインストールしたコンテナ
- Web サーバー環境: Apache HTTP Server コンテナ

##### compose.yaml の作成

それでは、サービス定義をしていきましょう。
カレントディレクトリに `compose.yaml` という名前のファイルを作成し、次の内容を記述します。

```yaml
services:
  # curl がインストールされた開発環境コンテナ
  app:
    image: curlimages/curl:8.18.0
    # 起動コマンドを指定し、接続して作業できるように常駐させる
    entrypoint: ["sleep", "infinity"]

  web:
    image: httpd:2.4
    # ポートフォワーディング設定
    ports:
      - "127.0.0.1:8080:80"
    # バインドマウント設定
    volumes:
      - ./site:/usr/local/apache2/htdocs:ro
```

```text
app の curl           → web:80
Windows のブラウザー → 127.0.0.1:8080 → web:80
```

#### Docker Compose の起動

次に、 Docker Compose を起動します。
前の節で起動したコンテナを Ctrl + C で停止し、ポート 8080 を空けます。続いて、`compose.yaml` のある作業ディレクトリーで次のコマンドを実行します。

```sh
docker compose up -d
```

#### サービスの動作確認

##### web サービスの動作確認

web サービスが動いているかを確認します。
Web ブラウザで `http://127.0.0.1:8080` にアクセスしてみましょう。

`It's my created file!` と表示されれば成功です。


##### app サービスの動作確認

app サービスが動いているかを確認します。
app サービスに接続し、 curl コマンドで web サービスにアクセスしてみましょう。

次のコマンドで、 app サービスに接続します。

```sh
docker compose exec app sh
```

接続ができたら、次のコマンドで web サービスにアクセスします。

```sh
curl http://web:80
```

`It's my created file!` と表示されれば成功です。

`http://web` の `web` は、`compose.yaml` で定義したサービス名です。同じ Compose ネットワークに接続しているコンテナは、サービス名で互いに接続できます。
ここでは `app` から `web` のコンテナ内ポート 80 へ接続しています。公開ポート 8080 を使うのは Windows のブラウザーから接続するときです。


app サービスと web サービスのふたつのサービスを定義し、動作確認まで行いました。
今回は app サービスに curl が入ったイメージを使いましたが、実際の開発環境では Java や Node.js などの開発ツールをインストールします。

##### Docker Compose の停止

動作確認ができたら、`exit` で app コンテナのシェルを抜けます。Ubuntu のシェルに戻り、`compose.yaml` のある作業ディレクトリーで次のコマンドを実行します。

```sh
docker compose down
```

### まとめ

今回は、 Docker コンテナの基本的な使い方と Docker Compose の基本的な使い方を学びました。
次回は、この知識を活かして、 Dev container を使った開発環境構築を学びます。


### 参考資料

- [httpd - Official Image | Docker Hub](https://hub.docker.com/_/httpd)
- [ubuntu - Official Image | Docker Hub](https://hub.docker.com/_/ubuntu)
- [docker | Docker Docs](https://docs.docker.com/reference/cli/docker/)
- [docker compose | Docker Docs](https://docs.docker.com/reference/cli/docker/compose/)
- [ポート公開 | Docker Docs](https://docs.docker.com/engine/network/port-publishing/)

<a id="vol2"></a>

## Dev container 入門

### 前提条件

- [Vol.0 開発環境構築](#vol0)を完了していること
- [Vol.1 Docker/Docker Compose 入門](#vol1)相当の知識を有していること
  - （基本的な Docker/Docker Compose の使い方がわかれば OK）
- VS Code に **Dev Containers** 拡張機能をインストールしていること
  - WSL 上のフォルダーを開くため、**WSL** 拡張機能も必要である
  - 拡張機能ビューで `Dev Containers` と `WSL` を検索してインストールする

### Dev container 概要

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

### 作業用ディレクトリの作成

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


### Dev container の設定方法

今回は、 Spring Boot + PostgreSQL を使った Web アプリケーションの開発環境を構築していきます。

使用するサーバーを列挙すると、次のようになります。

- AP サーバー: Spring Boot 組み込み Tomcat
- DB サーバー: PostgreSQL

このように複数サーバーが必要になるため、 Docker Compose で環境を定義し、それを基に Dev container の設定を進めていきます。


#### compose.yaml の作成

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

Java 21、PostgreSQL 18、Debian Trixie の組み合わせの中で更新を取り込むため、上のイメージタグはパッチ版を指定していません。取得した時期によって、Java や PostgreSQL のパッチ番号は変わります。

#### devcontainer.json の作成

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


### VS Code の起動

プロジェクトルート（`.devcontainer` の親ディレクトリ）に移動し、次のコマンドを実行してください。

```sh
code .
```

初回や VS Code の更新直後は、WSL 内に VS Code Server をダウンロードしてインストールする場合があります。ターミナルに進行状況が表示されるので、VS Code の起動まで待ちます。

VS Code の左下に `WSL: Ubuntu-24.04` と表示されることを確認します。ワークスペースの信頼を尋ねられた場合は、自分で作成した教材用フォルダーを開いていることを確認し、`Yes, I trust the authors` を選びます。制限モード（Restricted Mode）のバナーが表示された場合は、「管理」（Manage）から同じフォルダーの信頼を設定します。


### Dev container 開発環境の起動

1. Ctrl+Shift+P でコマンドパレットを開く
2. `Dev Containers: Reopen in Container`（日本語表示では「開発コンテナー: コンテナーで再度開く」）を選択する
3. 信頼確認が表示された場合は、自分で作成した教材用フォルダーであることを確認し、「フォルダーを信頼して続行」を選ぶ

VS Code のウィンドウがリロードされます。左下の接続先に `Dev Container: Java Dev Container`（日本語表示では「開発コンテナー: Java Dev Container」）が出るまで待ちます。

これで、 Dev container による開発環境の立ち上げが完了しました。

このように、事前にいろいろと作るものはありますが、誰かがつくったものを使うだけであれば、 VS Code を開いてから数手で環境の立ち上げが完了します。

### Dev container 開発環境の動作確認

`app` コンテナの Java と、`db` への接続を確認します。VS Code 左下の接続先が `Java Dev Container` になったら、新しい統合ターミナルを開きます。`java -version` で Java 21 が表示されることを確認してください。

#### PostgreSQL クライアントのインストール

同じターミナルで次のコマンドを実行してください。
コンテナ上に `psql` コマンドがインストールされます。

```sh
sudo apt update
sudo apt install -y postgresql-client
```

旧版の `mcr.microsoft.com/devcontainers/java:21` イメージでは、Yarn リポジトリーの署名エラーにより `apt update` が失敗しました。同じエラーが出たら、`compose.yaml` の `app` を上記のイメージ指定に更新し、`Dev Containers: Rebuild Container` を実行します。[Java Dev Container イメージ](https://github.com/devcontainers/images/blob/main/src/java/README.md)

ここで追加したパッケージは、開発コンテナを作り直すと失われます。チーム全員の環境に含めるには、Dockerfile などの構成にインストール手順を記述します。

#### PostgreSQL コンテナへの接続

app コンテナには環境変数が設定されていますので、活用しましょう。

```sh
PGPASSWORD="$MAIN_DB_PASSWORD" psql -U "$MAIN_DB_USER" -h "$MAIN_DB_HOSTNAME" -d "$MAIN_DB_NAME"
```

`appdb=#` が表示されたら接続成功です。`\conninfo` で接続先を確認し、`\q` でシェルに戻ります。接続を拒否された場合は、PostgreSQL の初期化を数秒待ってから再試行してください。

この構成で Spring Boot の開発を始めるときは、プロジェクトを `.devcontainer` のある作業ディレクトリーに置きます。`MAIN_DB_*` は教材で定義した環境変数なので、Spring Boot から使うにはデータソース設定で明示的に参照します。


### 開発環境の共有方法

開発環境の共有方法は簡単で、プロジェクトのリポジトリ（Git リポジトリなど）に `.devcontainer` を含めるだけです。

こうすることで、 `git clone` をしたのち、プロジェクトディレクトリを VS Code + Dev container 拡張機能を使って開くだけで共通の開発環境を使用できます。

<a id="summary"></a>

## まとめ

本シリーズ「コンテナで構築する開発環境」では、
Dev container を用いた再現性の高い開発環境の設計・共有を目標に、
段階的に環境構築の方法を学んできました。

### Vol.0: 開発環境構築

Vol.0 では、以降のハンズオンをスムーズに進めるための前提環境を整えました。

- WSL2 の導入
- Linux（Ubuntu）環境の準備
- Docker のインストールと動作確認

ここでのポイントは、Docker を導入することで、
OS や PC の違いによる環境差異を最小限にする土台を作ったことです。

### Vol.1: Docker / Docker Compose 入門

Vol.1 では、Dev container の前提となる Docker/Docker Compose の基本を確認しました。

- Docker コンテナ / イメージの考え方
- ポートフォワーディングとボリュームマウント
- Dockerfile によるカスタムイメージ作成
- Docker Compose による複数サービス構成
- サービス間通信（app → web）

Docker Compose では、開発用ツールと Web サーバーを別々のサービスとして定義し、まとめて起動できることを確認しました。

### Vol.2: Dev container 入門

Vol.2 では、Vol.1 で学んだ Docker と Docker Compose の使い方を、新しい Dev Container 構成に応用しました。

- devcontainer.json の役割
- Docker Compose と Dev container の関係
- VS Code をコンテナに接続して作業する仕組み
- 「WSL2 上のファイルシステムで作業する」重要性
- Spring Boot + PostgreSQL を想定した開発環境構成
- psql による DB 接続確認

Java の開発コンテナと PostgreSQL を起動するための構成を、チーム内で共有できる形にしました。

### このシリーズで持ち帰れるもの

本シリーズを通して、次のものを持ち帰ることができます。

- Docker / Docker Compose / Dev container を使った開発環境構成の考え方
- Spring Boot + PostgreSQL 向け Dev container 構成のひな形
- 環境構築手順を README ではなくコードで管理する発想
- 新しいメンバーが参加しても「環境構築で詰まらない」仕組み

Spring Boot プロジェクトで使うときは、アプリケーションが PostgreSQL に接続するためのデータソース設定を追加します。

### 次のステップ

この先の発展としては、次のようなことが考えられます。

- Spring Boot プロジェクトを組み込んだテンプレート化
- Flyway / Liquibase による DB マイグレーション管理
- 本番環境（CI/CD）との役割分担整理
- Dev container を前提としたチーム開発フローの整備

Dev container は「便利なツール」ではなく、
開発体験そのものを標準化するための仕組みです。

ぜひ、今回作成した構成をベースに、
自分たちのプロジェクトに合った開発環境を育てていってください。
