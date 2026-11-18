# 不正アクセス監視ラボ

Loki 3.7.10、Grafana 13.3.1、Alloy v1.22.0 を使います。Python 3.12.14 はコンテナー内のみで動きます。これは学習用の認証判定で、実際のアカウント、セッション、トークン発行、外部宛先への送信はありません。

この README と compose.yaml のあるフォルダーで起動します。

```powershell
docker compose up -d
docker compose ps --all
```

Grafana は http://127.0.0.1:13010/ です。ユーザー learner、パスワード access-log-local-only で入り、Security Log Lab を開きます。

シナリオは1つずつ切り替えます。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode login
docker compose exec -T demo python /lab/security_demo.py mode normal
docker compose exec -T demo python /lab/security_demo.py mode scan
docker compose exec -T demo python /lab/security_demo.py mode normal
docker compose exec -T demo python /lab/security_demo.py mode typo
docker compose exec -T demo python /lab/security_demo.py mode normal
```

login は学習用アカウントの認証失敗、scan は固定した3つの存在しないパス、typo はリンクミスを想定した1つのパスへ、低頻度のアクセスを発生させます。送信先は Compose 内部の demo に固定しています。宛先指定やパスワードリストの読み込み機能はありません。

通知は次で確認します。Ctrl+C は表示だけを終了します。

```powershell
docker compose logs --follow --tail 20 notification-sink
```

normal に戻した後も、直近1分のログが入れ替わるまで待ちます。故障モードは保存され、再起動だけでは normal に戻りません。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
docker compose down
```

保存データが不要なら、同じフォルダーで down --volumes を実行します。この教材専用のログ、Grafana の設定、読み取り位置、シナリオ設定が消えます。

```powershell
docker compose down --volumes
```

固定プロジェクト名 security-log-lab を使うので、複数コピーを同時起動しないでください。アクセスログ教材とは別プロジェクト、別ポート、別ボリュームです。
