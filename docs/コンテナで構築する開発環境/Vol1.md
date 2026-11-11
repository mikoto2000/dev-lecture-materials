---
title: "Docker/Docker Compose 入門"
author: mikoto2000
date: 2026/1/9
---

# Docker/Docker Compose 入門

## 前提条件

- [Vol.0 開発環境構築](./Vol0.md)を完了していること

以降のコマンドは、WSL 2 の Ubuntu 24.04 のシェルで実行します。ホームディレクトリー配下に教材専用の作業場所を作り、移動してください。すでに同じ名前のディレクトリーがある場合は、別の名前を使います。

```sh
mkdir -p ~/docker-handson/site
cd ~/docker-handson
```


## Docker コンテナ概要

この章では、開発環境として Docker コンテナを利用する際に知っておくべき基本的な概念を説明します。


### Docker コンテナとは

「Docker コンテナ = 使い捨てのアプリケーション実行環境」と考えてください。
Docker イメージと言われるテンプレートからコンテナを起動し、その中でアプリケーションを実行します。


### Docker イメージとは

「Docker イメージ = コンテナの設計図」と考えてください。
プログラムでいうところのクラスのようなもので、イメージからコンテナを起動（インスタンス化）します。
自分でイメージを作るときは、Dockerfile に構築手順を書いてビルドできます。この章では、公開済みのイメージを取得して使う方法と、自分でビルドする方法の両方を試します。


### Dockerfile とは

「Dockerfile = イメージの構築手順書」と考えてください。
プログラムでいうところのソースコードです。どのようにアプリケーション実行環境を構築するかを記述します。


```text
Dockerfile ── docker build ──> イメージ
イメージ   ── docker run   ──> コンテナ（実行するたびに新規作成）
```


## Docker コンテナを使ってみる

本シリーズの最終目標は Dev container を使った開発環境構築ですが、その前提として Docker コンテナの基本的な使い方を学びます。

今回は Apache HTTP Server コンテナを使って、Web サーバコンテナを動かしてみましょう。

### Apache HTTP Server コンテナの起動

```sh
docker run --rm httpd:2.4
```

次のような実行結果が表示されます。これで Apache HTTP Server コンテナが起動します。

```sh
AH00558: httpd: Could not reliably determine the server's fully qualified domain name, using 172.17.0.2. Set the 'ServerName' directive globally to suppress this message
AH00558: httpd: Could not reliably determine the server's fully qualified domain name, using 172.17.0.2. Set the 'ServerName' directive globally to suppress this message
[Fri Jan 09 10:39:26.403849 2026] [mpm_event:notice] [pid 1:tid 1] AH00489: Apache/2.4.66 (Unix) configured -- resuming normal operations
[Fri Jan 09 10:39:26.403951 2026] [core:notice] [pid 1:tid 1] AH00094: Command line: 'httpd -D FOREGROUND'
```

この起動方法ではホストのポートをコンテナへ割り当てていないため、Windows のブラウザーから `http://127.0.0.1:8080` でこの Apache には接続できません。
Apache はフォアグラウンドで動くため、このシェルにはプロンプトが戻りません。Ctrl+C で停止すると、`--rm` の指定によりコンテナも削除されます。


### ポートフォワーディングでアクセスできるようにする

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


### バインドマウントでコンテンツを変更できるようにする

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


### カスタム Docker イメージの作成

Docker イメージの基本的な使い方は理解できたはずです。
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

# コンテナが使用するポートを明示する
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
- `.` はビルド時に参照できるファイルの範囲（ビルドコンテキスト）として、現在のディレクトリーを指定する。この例では、その直下の `Dockerfile` が使われる

次に、`docker images` コマンドで、ビルドしたイメージが作成されていることを確認します。
次のように `my-httpd:latest` イメージが表示されれば成功です。

```sh
# docker images
IMAGE                                                                                                                      ID             DISK USAGE   CONTENT SIZE   EXTRA
my-httpd:latest                                                                                                            bb045a3f673c        242MB             0B        
```


#### カスタム Docker イメージの起動

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


## Docker Compose を使ってみる

Docker Compose は、複数のサービスで構成されるアプリケーションを定義し、関連するコンテナをまとめて管理するツールです。この演習では、サービスごとにコンテナを1つ起動します。

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

### Docker Compose の起動

次に、 Docker Compose を起動します。
前の節で起動したコンテナを Ctrl + C で停止し、ポート 8080 を空けます。続いて、`compose.yaml` のある作業ディレクトリーで次のコマンドを実行します。

```sh
docker compose up -d
```

### サービスの動作確認

#### web サービスの動作確認

web サービスが動いているかを確認します。
Web ブラウザで `http://127.0.0.1:8080` にアクセスしてみましょう。

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

`http://web` の `web` は、`compose.yaml` で定義したサービス名です。同じ Compose ネットワークに接続しているコンテナは、サービス名で互いに接続できます。
ここでは `app` から `web` のコンテナ内ポート 80 へ接続しています。公開ポート 8080 を使うのは Windows のブラウザーから接続するときです。


app サービスと web サービスのふたつのサービスを定義し、動作確認まで行いました。
今回は app サービスに curl が入ったイメージを使いましたが、実際の開発環境では Java や Node.js などの開発ツールをインストールします。

#### Docker Compose の停止

動作確認ができたら、`exit` で app コンテナのシェルを抜けます。Ubuntu のシェルに戻り、`compose.yaml` のある作業ディレクトリーで次のコマンドを実行します。

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
- [ポート公開 | Docker Docs](https://docs.docker.com/engine/network/port-publishing/)

