# 準備: 安全に壊して戻せる場所をつくる

## 使う環境をそろえる

この教材の実行場所は **WSL 2 の Ubuntu 内の Bash** です。Ubuntu 24.04 LTS と Python 3.12 を想定し、スクリプトは Python 3.10 以降を対象にしています。Linux の Ubuntu でも同じコマンドを使えます。

Windows の PowerShell と Ubuntu の Bash は別のシェルです。以下の最初の枠だけ PowerShell で実行し、以後は Bash に統一します。PowerShell の `curl` や Windows 側の Python は使いません。

**Windows の PowerShell:**

```powershell
wsl --list --verbose
wsl -d Ubuntu-24.04
```

`Ubuntu-24.04` は、自分のディストリビューション名へ読み替えます。名前は `wsl --list --verbose` の結果で確認できます。VERSION 列が `2` であることも確認します。Ubuntu がない場合は、[Microsoft の WSL インストール手順](https://learn.microsoft.com/windows/wsl/install)で準備してから戻ってください。インストール・更新には管理者権限や再起動が必要になる場合があるので、勉強会の前に済ませます。

**ここから先は Ubuntu の Bash:**

```bash
python3 --version
python3 -c 'import http.server, http.client, sqlite3; print(sqlite3.sqlite_version)'
```

Python がない場合だけ、Ubuntu の公式パッケージから導入します。これは実験前の環境準備です。

```bash
sudo apt update
sudo apt install python3
```

以後の実験に `sudo` は不要です。

## ファイルを置く

[教材トップ](../index.md)から ZIP を Windows にダウンロードし、エクスプローラーで展開します。Ubuntu 側に専用フォルダーを作り、展開された `monitoring-lab` フォルダー内のファイルをコピーします。

```bash
mkdir -p ~/monitoring-workshop
cd ~/monitoring-workshop
explorer.exe .
```

この枠は Ubuntu の Bash で実行します。表示されたエクスプローラーが、Ubuntu のホームにある `monitoring-workshop` フォルダーです。その中へコピーしてください。Windows のダウンロード先で直接動かすのではなく、Ubuntu のホーム配下に置きます。

```bash
cd ~/monitoring-workshop
ls
```

`app.py`、`labctl.py`、`monitor.py`、`watchdog.py`、補助ファイル、`README.md` が見えることを確かめます。`monitoring-lab` が1つだけ見える場合は、その中のファイルをコピーするか、そのフォルダーへ移動してください。

Git を利用する方は、リポジトリの `docs/public/monitoring-intro/lab/` 内でも実行できます。受講するだけなら Node.js や npm は不要です。

## 壊す前に、戻し方を覚える

アプリと監視は、それぞれを起動したターミナルで **Ctrl+C** を押すと停止します。ほかの Python プロセスまで止める `killall` や `pkill` は使いません。

実験中の故障を解除するコマンドは次のとおりです。対応する故障を入れたら、同じ行を使って戻します。

```bash
python3 labctl.py db-unavailable off
python3 labctl.py wrong-data off
python3 labctl.py delay 0
```

最初からやり直すときは、先にアプリ・監視を Ctrl+C で止め、次を実行します。**学習用 DB と観測記録が初期状態になる**ので、残したい記録は先に別名で保存します。

```bash
python3 labctl.py reset
```

スクリプトのある場所の `.state/` に学習用ファイルを置きます。本番 DB、共有フォルダー、既存システムの設定には向けないでください。実験用 HTTP は `127.0.0.1:18080` のみで待ち受けます。ポートの公開やファイアウォールの変更は不要です。

## 二つのターミナルを使う

- ターミナル A: アプリを起動し、ログを見る
- ターミナル B: 確認コマンドを実行し、故障を設定・復旧する

どちらも同じ Ubuntu を開き、同じ `~/monitoring-workshop` へ移動します。第 2 章以降、監視を繰り返す間に故障を切り替えるため、ターミナル C も使います。

ターミナル B で初期化します。

```bash
python3 labctl.py init
```

ターミナル A でアプリを起動します。

```bash
python3 app.py
```

この画面が入力待ちに戻らないのは正常です。プロセスが動いています。ポート使用中のエラーが出た場合は、[困ったとき](../troubleshooting.md)へ進み、無関係なプロセスを止めないでください。

[教材トップ](../index.md) / [1. URL を確かめる](./01-url.md)
