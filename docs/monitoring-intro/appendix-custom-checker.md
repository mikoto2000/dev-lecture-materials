# 補足: 自作監視の仕組みを読む

本編は Uptime Kuma を使います。この補足は、HTTP 確認、通知状態、最終観測時刻などの仕組みをコードで読みたい方向けです。**本編を終えるために実行する必要はありません。**

旧版の `monitor.py` と `watchdog.py` は配布 ZIP に残しています。Kuma が裏でこれらを実行しているわけではありません。通知条件も同一ではありません。

## 本編と環境を混ぜない

この補足だけは WSL 2 / Ubuntu の Bash と Python 3.10 以降を使います。PowerShell で本編の Compose を停止してから、別のフォルダーへ ZIP を展開してください。どちらも 18080 番を使うため、同時には起動しません。

**Windows の PowerShell:**

```powershell
docker compose --profile notifications stop
wsl --list --verbose
wsl -d Ubuntu-24.04
```

Ubuntu の名前は自分の環境に合わせます。以後は **Ubuntu の Bash** です。配布ファイルを Ubuntu のホーム配下へコピーし、そのフォルダーに移動します。

```bash
python3 --version
python3 labctl.py init
python3 app.py
```

同じフォルダーを開いた別の Bash で確認します。

```bash
python3 monitor.py --path /health
python3 monitor.py --path /items/1 --expect-name monitoring-demo --count 30 --interval 2
```

内容確認は ID が整数の1であることと名前を比較します。ソケットの待機上限だけに頼らず、子プロセス全体にも上限を置きます。`--max-ms` はこの自作プログラム独自の条件です。Kuma に同名の設定や同じ通知機能があるという意味ではありません。

```bash
python3 monitor.py --path /items/1 --expect-name monitoring-demo --timeout 2 --max-ms 500 --count 30 --interval 2 --failures 3 --recoveries 2
python3 watchdog.py --max-age 5
```

`--interval` は1回の確認後に待つ時間です。確認結果は毎回残し、通知は連続失敗と復旧の状態変化で出します。監視の最終観測記録は、成功・失敗の両方で更新します。同じホストの watchdog ではホスト全体の停止を検知できません。

停止は各ターミナルの Ctrl+C です。アプリと監視を止めてから `python3 labctl.py reset` を実行すると、このコピーの学習用状態を初期化できます。

詳しいオプションと制限は、<a href="./lab/README-appendix.md" download>自作監視の補足 README</a> を参照してください。

[教材トップ](./index.md)
