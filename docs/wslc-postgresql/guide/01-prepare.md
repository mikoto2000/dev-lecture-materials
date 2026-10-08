# 1. 事前準備

## この章のゴール

`wslc version` が実行でき、学習用イメージを取得できる状態にします。環境の準備は勉強会の前日までに済ませるのがおすすめです。

## 用意するもの

- WSL を利用できる Windows PC。WSL **2.9.3 以降**
- Windows PowerShell または PowerShell と、本文を見るブラウザー
- イメージを取得できるネットワークと、空きディスク容量
- 必要ならテキストエディター（VS Code の指定なし）

Docker Desktop、ホスト側の PostgreSQL、psql、Java、Node.js は、このハンズオンの受講には不要です。Node.js が必要なのは教材を Rspress で編集・表示する講師だけです。

## WSL と wslc を確認する

PowerShell を開きます。

```powershell
wsl --version
wslc version
wslc run --help
wslc volume --help
```

`wsl --version` の **WSL バージョン**が 2.9.3 以上であることを確認します。`wsl -l -v` に出る `VERSION 2` は別の値です。

`wslc` がない場合は、[公式の導入手順](https://learn.microsoft.com/ja-jp/windows/wsl/tutorials/wsl-containers)に従ってください。既に WSL がある場合、更新コマンドは次です。更新や再起動に備え、授業開始直前の実行を避けてください。会社 PC は管理者のルールに従います。

```powershell
wsl --update
```

WSL 自体がない場合は[公式 WSL インストール手順](https://learn.microsoft.com/ja-jp/windows/wsl/install)で準備します。権限や組織の制限を回避する設定変更は行いません。

## イメージを先に取得する

```powershell
wslc image pull postgres:17
wslc image list
```

一覧に `postgres` の `17` があれば準備完了です。通信環境によって数分かかります。これは PostgreSQL 17 系の学習用指定で、最新版という意味ではありません。同じタグでも後日パッチの更新を含む場合があります。

## 名前の衝突を確認する

```powershell
wslc container list --all
wslc volume list
```

本文は `wslc-workshop-db` と `wslc-workshop-pgdata` を使います。同名の既存リソースがある場合、勝手に消したり、その中身を学習用として上書きしたりしないでください。自分が以前作ったこの教材のものか確認し、初参加なら講師と相談して全手順で名前をそろえて変更します。

## 開始前のチェック

- [ ] `wslc version` が表示された
- [ ] `postgres:17` を取得できた
- [ ] 同名の既存データがないことを確認した

[次へ: PostgreSQL を起動する](./02-start.md)
