# 困ったとき

## 画面が開かない、ログが出ない

この教材の Grafana は13010番です。前の教材の13000番とは異なります。Explore のラベルも `{job="security-log-lab"}` を使います。

```powershell
docker compose ps --all
docker compose logs --tail 50 demo traffic alloy loki grafana
```

基本的な接続の調べ方は[アクセスログ教材の困ったとき](../access-log-monitoring/troubleshooting.md)も参照してください。そちらのポート番号とシナリオ操作は読み替えます。

## シナリオが変わらない

`compose.yaml` のある security-log-lab フォルダーで実行します。

```powershell
docker compose exec -T demo python /lab/security_demo.py mode normal
```

demo と traffic は同じシナリオ設定を参照します。再起動後も残るので、明示的に normal に戻します。ログの直近1分には以前のシナリオも残ります。

## 認証失敗の警報が復旧しない

normal の自動アクセスでは、数秒ごとに同じアカウントの認証成功を記録します。traffic が動いているか、同じ `client_ip` と `account` の新しい認証イベントがあるかを確認します。

データが途絶しただけでは Keep Last State で直前の状態を保ちます。正常な認証を観測したことと、何も観測できないことは別です。Security logs missing も確認してください。

## 通知の送信元 IP が例と異なる

IP は実際のコンテナーネットワークの値なので変わります。固定 IP をコピーせず、自分のログと通知を照合します。

## 完全にやり直す

この教材専用の保存データが消えることを確認して実行します。

```powershell
docker compose down --volumes
docker compose up -d
```

[教材トップ](./index.md)
