---
title: "Docker/Docker Compose 入門"
author: mikoto2000
date: 2026/1/9
---

# Docker/Docker Compose 入門

## 前提条件

- Vol.0 開発環境構築 を完了していること


## Docker コンテナ概要

この章では、開発環境として Docker コンテナを利用する際に知っておくべき基本的な概念を説明します。


### Docker コンテナとは

「Docker コンテナ = 使い捨てのアプリケーション実行環境」と考えてください。
Docker イメージと言われるテンプレートからコンテナを起動し、その中でアプリケーションを実行します。


### Docker イメージとは

「Docker イメージ = コンテナの設計図」と考えてください。
プログラムでいうところのクラスのようなもので、イメージからコンテナを起動（インスタンス化）します。
Docker イメージ自体は、 Dockerfile というファイルから生成されます。


### Dockerfile とは

「Dockerfile = コンテナの構築手順書」と考えてください。
プログラムでいうところのソースコードです。どのようにアプリケーション実行環境を構築するかを記述します。


![Dockerfile, Docker イメージ, docker コンテナ](./images/vol1/dockerfile-docker-image-and-container.png)


## Docker コンテナを使ってみる

本シリーズの最終目標は Dev container を使った開発環境構築ですが、その前提として Docker コンテナの基本的な使い方を学びます。

今回は Apache HTTP Server コンテナを使って、Web サーバコンテナを動かしてみましょう。

### Apache HTTP Server コンテナの起動

```sh
docker run httpd:latest
```

次のような実行結果が表示されたと思います。これで Apache HTTP Server コンテナが起動します。

```sh
AH00558: httpd: Could not reliably determine the server's fully qualified domain name, using 172.17.0.2. Set the 'ServerName' directive globally to suppress this message
AH00558: httpd: Could not reliably determine the server's fully qualified domain name, using 172.17.0.2. Set the 'ServerName' directive globally to suppress this message
[Fri Jan 09 10:39:26.403849 2026] [mpm_event:notice] [pid 1:tid 1] AH00489: Apache/2.4.66 (Unix) configured -- resuming normal operations
[Fri Jan 09 10:39:26.403951 2026] [core:notice] [pid 1:tid 1] AH00094: Command line: 'httpd -D FOREGROUND'
[Fri Jan 09 10:42:08.567335 2026] [mpm_event:notice] [pid 1:tid 1] AH00491: caught SIGTERM, shutting down
```

ただし、コンテナ環境は隔離された状態なので、ホスト OS からはアクセスできません。
いったん Ctrl + C でコンテナを停止しましょう。


### ポートフォワーディングでアクセスできるようにする

ホスト OS からコンテナにアクセスするために、ポートフォワーディングを設定します。
ポートフォワーディング設定を行うことで、ホスト OS の特定のポートへのアクセスをコンテナ内の特定のポートに転送できます。

```sh
docker run -p 8080:80 httpd:latest
```

- `-p 8080:80`: ホスト OS のポート 8080 をコンテナ内のポート 80 に転送する設定

このように、ポートフォワーディング設定をすることで、ホストのポート 8080 から コンテナのポート 80(Apache HTTP Server) にアクセスできるようになります。
Web ブラウザで `http://localhost:8080` にアクセスしてみましょう。
`It works!` と表示されたら成功です。

![ポートフォワーディング](./images/vol1/port-forwarding.png)


### バインドマウントでコンテンツを変更できるようにする

ポートフォワーディング設定でコンテナにアクセスできるようになりましたが、
このままではコンテナに手元の資材を持ち込むことができません。
それでは開発環境として不便ですので、バインドマウントという仕組みを使い、
手元の資材をコンテナに持ち込めるようにしましょう。

```sh
docker run -p 8080:80 -v "$(pwd):/usr/local/apache2/htdocs" httpd:latest
```

- `$(pwd)`: カレントディレクトリの絶対パスに展開される
- `-v "$(pwd):/usr/local/apache2/htdocs"`: カレントディレクトリをコンテナ内の `/usr/local/apache2/htdocs` ディレクトリにマウントする設定

コンテナを起動したら、再度 Web ブラウザで `http://localhost:8080` にアクセスしてみましょう。
`It works!` の代わりに、カレントディレクトリのファイル一覧が表示されます。
これでカレントディレクトリをコンテナ上の Apache HTTP Server が参照していることが確認できました。

![バインドマウント](./images/vol1/bind-mount.png)

せっかくなのでファイルを作成し、 Apache HTTP Server から参照できることを確認してみましょう。
カレントディレクトリに `index.html` ファイルを作成し、次の内容を記述します。

```html
It's my created file!
```

ファイルが作成出来たら、再度 Web ブラウザで `http://localhost:8080` にアクセスしてみましょう。
`It's my created file!` と表示されます。


### カスタム Docker イメージの作成

Docker イメージの基本的な使い方は理解できたと思います。
次に、カスタム Docker イメージを作成してみましょう。

#### Dockerfile の作成

`httpd` イメージと同じように、 Apache HTTP Server を動作させるカスタム Docker イメージを作成します。
まず、カレントディレクトリに `Dockerfile` という名前のファイルを作成し、次の内容を記述します。

```dockerfile
# ベースイメージを指定
# ベースイメージは、 Docker Hub で公開されている ubuntu イメージを使用
FROM ubuntu:24.04

# Apache HTTP Server をインストール
RUN apt update \
 && apt install -y apache2

# apache HTTP Server の起動に必要なディレクトリを作成
RUN mkdir -p /var/run/apache2 /var/lock/apache2

# ポート 80 を公開
EXPOSE 80

# Apache HTTP Server をフォアグラウンドで起動
# Ubuntu のサービスとして起動するわけではないため、
# 起動時に一工夫している
CMD ["sh", "-c", ". /etc/apache2/envvars && exec apache2 -DFOREGROUND"]
```


#### Docker イメージのビルド

次に、カスタム Docker イメージをビルドします。
カレントディレクトリで、次のコマンドを実行します。

```sh
docker build -t my-httpd:latest .
```

- `-t my-httpd:latest`: ビルドするイメージに `my-httpd:latest` という名前を付ける
- `.`: カレントディレクトリにある `Dockerfile` を使用

次に、 docker images コマンドで、ビルドしたイメージが作成されていることを確認します。
次のように `my-httpd:latest` イメージが表示されれば成功です。

```sh
# docker images
IMAGE                                                                                                                      ID             DISK USAGE   CONTENT SIZE   EXTRA
my-httpd:latest                                                                                                            bb045a3f673c        242MB             0B        
```


#### カスタム Docker イメージの起動

最後に、ビルドしたカスタム Docker イメージを起動します。
次のコマンドを実行します。

```sh
docker run -p 8080:80 -v "$(pwd):/var/www/html" my-httpd:latest
```

- `-v "$(pwd):/var/www/html"`: カレントディレクトリをコンテナ内の `/var/www/html` ディレクトリにマウントする設定
  (`/var/www/html` は Ubuntu ベースの Apache HTTP Server のデフォルトのドキュメントルート)

再度 Web ブラウザで `http://localhost:8080` にアクセスしてみましょう。
`It's my created file!` と表示されれば成功です。

これで、カスタム Docker イメージの作成と起動ができました。


## Docker Compose を使ってみる

Docker Compose は、複数の Docker コンテナをまとめて管理するためのツールです。
ひとつひとつのコンテナを、「サービス」として定義し、複数のサービスをまとめて「アプリケーション」として定義します。

本ワークショップでは、 Dev container を使った開発環境構築を見越して、「開発環境」と「Web サーバー環境」のふたつのサービスを定義してみましょう。


### 複数サービスの定義

前述の通り、「開発環境」と「Web サーバー環境」のふたつのサービスを定義します。
サービスの内容としては、次の通りです。

- 開発環境: curl クライアントをインストールしたコンテナ
- Web サーバー環境: Apache HTTP Server コンテナ

#### compose.yaml の作成

それでは、サービス定義をしていきましょう。
カレントディレクトリに `compose.yaml` という名前のファイルを作成し、次の内容を記述します。

```yaml
services:
  # curl がインストールされた開発環境コンテナ
  app:
    image: curlimages/curl:8.18.0
    command: sleep infinity

  web:
    image: httpd:2.4
    # ポートフォワーディング設定
    ports:
      - "8080:80"
    # バインドマウント設定
    volumes:
      - ./:/usr/local/apache2/htdocs
```

![compose](./images/vol1/compose.png)

### Docker Compose の起動

次に、 Docker Compose を起動します。
カレントディレクトリで、次のコマンドを実行します。

```sh
docker compose up -d
```

### サービスの動作確認

#### web サービスの動作確認

web サービスが動いているかを確認します。
Web ブラウザで `http://localhost:8080` にアクセスしてみましょう。

`It's my created file!` と表示されれば成功です。


#### app サービスの動作確認

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

`http://web` の `web` は、compose.yaml で定義したサービス名です。Docker Compose では、サービス名がそのままホスト名として名前解決されます。


app サービスと web サービスのふたつのサービスを定義し、動作確認まで行いました。
今回は app サービスに curl コマンドをインストールしましたが、実際の開発環境では Java や Node.js などの開発ツールをインストールします。

#### Docker Compose の停止

サービスの動作確認ができたら、 Docker Compose を停止します。
カレントディレクトリで、次のコマンドを実行します。

```sh
docker compose down
```

## まとめ

今回は、 Docker コンテナの基本的な使い方と Docker Compose の基本的な使い方を学びました。
次回は、この知識を活かして、 Dev container を使った開発環境構築を学びます。


## 参考資料

- [httpd - Official Image | Docker Hub](https://hub.docker.com/_/httpd)
- [ubuntu - Official Image | Docker Hub](https://hub.docker.com/_/ubuntu)
- [docker | Docker Docs](https://docs.docker.com/reference/cli/docker/)
- [docker compose | Docker Docs](https://docs.docker.com/reference/cli/docker/compose/)

