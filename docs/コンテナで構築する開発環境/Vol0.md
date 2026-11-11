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

WSL (Windows Subsystem for Linux) と Ubuntu 24.04 LTS をインストールします。すでに Ubuntu 24.04 をインストールしている場合は、次の「Ubuntu 24.04 の起動」へ進んでください。

Windows Terminal を管理者として起動し、PowerShell で次のコマンドを実行します。

```powershell
wsl.exe --install -d Ubuntu-24.04
```

「ユーザーアカウント制御」のダイアログが表示された場合は「はい」をクリックします。

再起動を求められた場合は、作業中のファイルを保存してから PC を再起動します。

### Ubuntu の初期設定

Ubuntu の画面が自動で開かなければ、PowerShell で次のコマンドを実行します。

```powershell
wsl.exe -d Ubuntu-24.04
```

初回起動時に、Ubuntu のユーザー名とパスワードを設定します。

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

Windows の PowerShell で `wsl.exe -l -v` を実行し、`Ubuntu-24.04` の `VERSION` が `2` であることを確認してください。既存の Ubuntu 24.04 が WSL 1 の場合は、[Microsoft の移行手順](https://learn.microsoft.com/ja-jp/windows/wsl/install#upgrade-version-from-wsl-1-to-wsl-2)を参照してください。

## Docker のインストール

Ubuntu 24.04 の起動後、[Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/) の手順に従って、Docker をインストールします。

以降のコマンドは Ubuntu のシェルで実行します。このシリーズでは Ubuntu 内の Docker Engine を使います。事前に `ps -p 1 -o comm=` を実行し、`systemd` が表示されることを確認します。別の名前が表示された場合は、[WSL で systemd を有効にする手順](https://learn.microsoft.com/ja-jp/windows/wsl/systemd)を参照してください。

### apt リポジトリの登録

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

### Docker エンジンのインストール

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

`docker compose version` で Compose のバージョンも表示されることを確認し、[Vol.1](./Vol1.md) に進みます。


## 参考資料

- [WSL のインストール | Microsoft Learn](https://learn.microsoft.com/ja-jp/windows/wsl/install)
- [WSL のトラブルシューティング | Microsoft Learn](https://learn.microsoft.com/ja-jp/windows/wsl/troubleshooting)
- [Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/)
