---
title: "開発環境構築"
author: mikoto2000
date: 2026/1/8
---

# 開発環境構築

## 前提条件

- Windows 11 の PC（WSL 2 が利用できること。Home エディションでも可）

## VS Code のインストール

次の公式サイトから VS Code をインストールしてください。

[Visual Studio Code 公式サイト](https://code.visualstudio.com/)

インストール時に、次のチェックボックスを ON にするのを推奨（便利）。

- `エクスプローラーのファイルコンテキストメニューに[Code で開く]アクションを追加する`
- `エクスプローラーのディレクトリコンテキストメニューに[Code で開く]アクションを追加する`

インストール後、VS Code が起動できることを確認してください。

## WSL のインストール

### WSL の有効化

WSL (Windows Subsystem for Linux) をインストールします。

スタートメニューから Windows Terminal を起動し、次のコマンドを実行します。

```powershell
wsl.exe --install
```

「ユーザーアカウント制限」のダイアログが表示された場合は「はい」をクリックします。

インストールが完了したら、PC を再起動します。

### Linux ディストリビューションのインストール

今回は、 Ubuntu 24.04 LTS をインストールします。
再起動後、再度 Windows Terminal を起動し、次のコマンドを実行します。

```powershell
wsl.exe --install Ubuntu-24.04
```

インストールが完了したら、WSL の初期設定を促されるので、ユーザー名とパスワードを設定します。

Linux のシェルが起動したら、インストール成功です。

:::warning BIOS の仮想化支援機能が無効の場合
この時点で BIOS の仮想化支援機能を無効にしていると、エラーメッセージが表示されることもあります。その場合は、セクション「BIOS の仮想化支援機能の有効化」を参照して BIOS の設定を変更し、もう一度 WSL のインストールをやり直してください。

:::

## BIOS の仮想化支援機能の有効化

WSL 2 を使用するためには、BIOS の仮想化支援機能が有効になっている必要があります。
この章では、BIOS の仮想化支援機能を有効にする手順を説明します。


### BIOS 設定画面へのアクセス

1. Windows メニュー → 設定 → システム → 回復 を選択
2. 項目 `PC の起動方法をカスタマイズする` の、ボタン `今すぐ再起動` をクリック
3. `デバイスを再起動するため作業内容を保存します` のダイアログが表示されたら、`今すぐ再起動` をクリック
4. オプション選択画面で、`トラブルシューティング` → `詳細オプション` → `UEFI ファームウェア設定` を選択
5. `再起動` ボタンをクリックして、BIOS 設定画面に入る


### 仮想化支援機能の有効化

BIOS 設定画面で、仮想化支援機能を有効にします。

#### 注意

BIOS 設定画面の操作方法は PC のメーカーやモデルによって異なります。次の手順で操作できない場合は、運営に問い合わせてください。

また、 BIOS 設定は PC の基本設定に影響します。本資料で指定していない項目は**絶対に**変更しないでください。

#### 手順

次のような名前のセクションを探して開いてください。

- Advanced
- Advanced BIOS Features
- Advanced → CPU Configuration
- Northbridge / Chipset

そのセクションの中から、次のような名前の設定項目を探してください。

- Intel Virtualization Technology
- Intel VT-x
- VT-d
- SVM Mode（AMD）
- CPU Virtualization
- Virtualization Technology

項目の値が `Disabled` になっている場合、`Enabled` に変更してください。

変更が完了したら、BIOS 設定画面を保存して終了し、PC を再起動してください。

BIOS のどこかに `Save & Exit` という名前のメニューがあるはずです。

再起動が完了したら、再度 WSL のインストールを試みてください。


## Ubuntu 24.04 の起動

インストールが成功した場合、すでに Ubuntu 24.04 のシェルが起動しているはずです。
ここでは、改めて Ubuntu 24.04 を起動する手順を説明します。

Ubuntu 24.04 を起動するには、スタートメニューから Ubuntu 24.04 を選択して起動します。


## Docker のインストール

Ubuntu 24.04 の起動後、[Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/) の手順に従って、Docker をインストールします。

### apt リポジトリの登録

Docker インストールに必要な apt リポジトリを Ubuntu に登録します。

```sh
# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
```

### Docker エンジンのインストール

Docker エンジンをインストールします。

```sh
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

また、 Docker コマンドを sudo なしで実行できるように、現在のユーザーを `docker` グループに追加します。

```sh
sudo gpasswd -a <ユーザー名> docker
```

`<ユーザー名>` は、Ubuntu のユーザー名に置き換えてください。

変更を反映するため、Ubuntu を再起動するか、ログアウトして再度ログインしてください。


### Docker の動作確認

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


## 参考資料

- [Linux 用 Windows サブシステムに関する FAQ | Microsoft Learn](https://learn.microsoft.com/ja-jp/windows/wsl/faq#can-i-run-wsl-2-in-a-virtual-machine-)
- [Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/)
