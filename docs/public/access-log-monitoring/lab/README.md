# アクセスログ監視ラボ

Docker Compose で Loki 3.7.10、Grafana 13.3.1、Grafana Alloy v1.22.0 と学習用アプリを起動します。Python 3.12.14 はコンテナー内だけで使います。PC への言語ランタイムの導入は不要です。

## 起動

この README と compose.yaml のあるフォルダーで実行します。

```powershell
docker compose up -d
docker compose ps --all
```

Grafana: http://127.0.0.1:13000/ （ユーザー learner、パスワード access-log-local-only）

アプリ: http://127.0.0.1:18780/items

初回はイメージ取得と初期化に時間がかかります。画面が開いてから、1〜2分ほど正常なアクセスをためます。自動アクセスは traffic サービスが毎回1秒待って発生させます。外部サービスにはアクセスしません。

## 実験と解除

```powershell
docker compose exec -T demo python /lab/demo.py mode error
docker compose exec -T demo python /lab/demo.py mode normal
docker compose exec -T demo python /lab/demo.py mode slow
docker compose exec -T demo python /lab/demo.py mode normal
```

実験は1つずつ行います。解除後も直近1分に異常のログが残るため、即座には正常に戻りません。

通知を確認します。

```powershell
docker compose logs --follow --tail 20 notification-sink
```

Ctrl+C は表示だけを終了します。過去の通知も表示されるので received_at、status、alertname を確認します。

ログ途絶の実験と解除を試します。

```powershell
docker compose stop traffic
docker compose start traffic
```

ブラウザーからアプリにアクセスしてもログが増えます。途絶の実験中はアクセスしないでください。

## 復旧と後片付け

```powershell
docker compose start demo loki alloy grafana notification-sink traffic
docker compose exec -T demo python /lab/demo.py mode normal
docker compose down
```

down だけなら、ログ・読み取り位置・Grafana の設定・実験モードは専用ボリュームに残ります。再開は up -d です。完全にやり直す場合は、このラボのフォルダーで次を実行します。専用ボリュームのデータが消えます。

```powershell
docker compose down --volumes
```

固定名 access-log-lab を使用するため、別コピーとの同時起動は避けてください。アプリ、Loki、通知先のアドレスは Compose 内部のサービス名です。ホストの Docker ソケットはマウントしていません。認証なしの Loki と通知受信器はホストに公開していません。
