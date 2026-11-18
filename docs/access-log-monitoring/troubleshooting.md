# 困ったとき

## Docker につながらない

Docker Desktop が Linux コンテナーモードで起動しているか、`docker version` の Server が表示されるかを確認します。WSL 2 の Docker Engine を使う場合は、Docker が動いているディストリビューションで実行します。

## ポートが使用中と言われる

13000番または18780番が競合しています。このラボの `compose.yaml` にあるホスト側のポートだけを変更します。たとえば `127.0.0.1:13001:3000` なら、ブラウザーは13001番で開きます。コンテナー側の3000番や内部 URL は変更しません。

## 起動直後にログイン画面が開かない

初期化を待ち、状態とログを確認します。

```powershell
docker compose ps --all
docker compose logs --tail 50 grafana loki alloy
```

別のコピーを同時に起動していないかも確認します。この教材の Compose 名は `access-log-lab` で固定しています。

## ログが表示されない

Explore のデータソースが Loki、時間範囲が Last 15 minutes になっているかを確認します。ラベルは `{job="access-log-lab"}` です。PC の時計のずれも調べます。

```powershell
docker compose start traffic
docker compose exec -T demo python /lab/demo.py mode normal
docker compose exec -T demo tail -n 3 /logs/access.jsonl
docker compose logs --tail 50 traffic alloy loki
```

ファイルに新しい行があるのに Explore に出なければ、Alloy と Loki の間を調べます。ファイルに増えなければ、traffic と demo を先に確認します。古いファイルだけを見て正常と判断しないでください。

## 解除したのに異常が残る

クエリーの直近1分には、解除前の異常も残ります。正常なリクエストが増えるまで待ちます。故障モードはボリュームに保存されるため、再起動だけでは解除できません。`mode normal` を実行します。

## Firing なのに通知が見つからない

ルール名と受信時刻を確認します。同じ異常の再通知間隔は1時間です。初回の5秒待機やグループ更新の10秒間隔もあります。

```powershell
docker compose logs --tail 50 notification-sink grafana
```

Contact point の URL は `http://notification-sink:8081` です。`localhost` に変更しないでください。通知ログの表示を Ctrl+C で止めても、受信器自体は動いています。

## ルールやダッシュボードを編集できない

配布ファイルから自動登録しているためです。本文では設定を読み、実験します。変更を試す場合は、ダッシュボードをコピーするか、配布設定のコピーで検証してください。

## 完全に初期状態へ戻す

保存データが消えることを確認し、このラボのフォルダーで実行します。

```powershell
docker compose down --volumes
docker compose up -d
```

[教材トップ](./index.md)
