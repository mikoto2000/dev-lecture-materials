# 9. ネットワークの応答とロスを見る

## 困りごと

アプリの応答が遅いとき、通信に時間が掛かっている可能性もあります。ただし HTTP の応答時間だけでは、ネットワークとアプリの処理時間を分けられません。Kuma と同じ場所から、名前の解決と短い通信を確かめます。

## 小さな追加: どこから、どこへ測るかを固定する

前章の待ち時間を戻し、`demo-health` と `demo-item` が Up であることを確認します。今回は **Kuma コンテナーから demo コンテナーへ**、Docker のネットワーク内を測ります。

```powershell
docker compose exec kuma getent hosts demo
```

`demo` に対応する IP アドレスが表示されれば、この時点で名前から宛先を引けています。アプリの動作までは確かめていません。同じ Compose ネットワークのサービスには、サービス名で接続できます。IP アドレスはコンテナーの作り直しで変わり得るため、教材では `demo` を使い続けます。[Compose の名前解決](https://docs.docker.com/compose/how-tos/networking/)

## 安全な観察: 3回だけ Ping する

**状態の変更は不要です。回線の切断、ファイアウォールの変更、通信を大量に送る実験は行いません。**

```powershell
Get-Date -Format o
docker compose exec kuma ping -c 3 -W 1 -w 5 demo
```

これは PowerShell からコンテナー内の Linux の `ping` を実行するコマンドです。Windows の `ping` のオプションとは異なります。教材で指定した Kuma 2.5.5 のイメージには `iputils-ping` が含まれます。[2.5.5 のイメージ定義](https://github.com/louislam/uptime-kuma/blob/2.5.5/docker/debian-base.dockerfile)

- `-c 3`: 送信を3回までにする
- `-W 1`: 応答がない場合の待ち時間を1秒にする
- `-w 5`: Ping の実行期限を5秒にする

最後の集計を読みます。

- `packets transmitted` / `received`: 送信した数と返ってきた数
- `packet loss`: この観察で返ってこなかった割合
- `rtt min/avg/max/mdev`: 往復時間の最小・平均・最大と、ばらつき。単位は ms

Ping は ICMP の要求と応答で、往復時間 **RTT** とロスを測ります。ここでのロスは「この測定で応答が返らなかった」という意味です。捨てられた場所までは分かりません。[Debian の ping マニュアル](https://manpages.debian.org/bookworm/iputils-ping/ping.8.en.html)

同じ時間帯の `demo-item` の HTTP 応答時間もメモします。HTTP の値には、通信に加えてアプリや DB の処理時間が含まれます。Ping の RTT と HTTP 応答時間は異なる測定なので、同じ数字になるとは限りません。差をそのまま正確なアプリ処理時間と扱うこともできません。

必要なら20秒ほど待って、3回の Ping をもう一度行います。**3回の結果でロスが0%でも、いつでも通信が正常だとは証明できません。** 1回返らなければ約33%になる小さな標本です。回数と観察時間を一緒に記録します。

### 任意: Kuma にも Ping を1つ追加する

手動の Ping が成功したら、履歴を残す方法も試せます。Add New Monitor から次の監視を追加します。

- Monitor Type: **Ping**
- Friendly Name: `demo-network`
- Hostname: `demo`。URL やポート番号は付けない
- Heartbeat Interval: **20秒**
- Retries: **0**

保存後、Up と新しい応答時間の点が増えることを確認します。通知先が自動で選択されていれば、この比較用監視では選択を外して保存します。設定項目は [Kuma 2.5.5 の監視画面](https://github.com/louislam/uptime-kuma/blob/2.5.5/src/pages/EditMonitor.vue)で確認できます。

`demo-network` の応答時間は Ping の値、`demo-item` は HTTP の値です。Kuma の稼働率を、そのままパケットロス率と読み替えないでください。

## 復旧

通信経路やアプリの状態は変えていないため、戻すコマンドはありません。2つの HTTP 監視で、新しい Up の結果が増えていることを確認します。追加した `demo-network` が不要なら、この監視だけを Pause にできます。

Ping が失敗しても、権限やファイアウォールを緩めて成功させようとしません。名前解決の結果とエラーを記録し、HTTP 監視やアプリログと比べます。ICMP が許可されていない場合にも Ping は失敗するため、アプリの停止とは決めつけられません。

## 確かめた範囲

今回分かったのは、Docker ネットワーク内の特定の2点間で、短い期間に得られた応答です。Windows のブラウザーからの経路、Wi-Fi、インターネット回線、別の利用者の経路は測っていません。

Ping が成功しても、TCP ポートが開いていることや、HTTP が成功すること、DB の値が正しいことは分かりません。以前の「間違ったデータが返る」故障を、Ping だけで検知できない理由も考えてみましょう。

RTT やロスが普段より増え、同じ時間帯に HTTP も遅くなっていたら、通信は調査候補になります。それだけで通信が唯一の原因とは言えません。観測地点、時刻、名前解決、HTTP、アプリログをつなげて、次に調べる場所を絞ります。

## チェックポイント

- どこからどこへ、何回、いつ測ったかを記録する
- HTTP の応答時間と Ping の RTT の違いを説明する
- Ping 成功でアプリ正常と決められず、Ping 失敗でアプリ停止とも決められない理由を挙げる
- 3回のロス率から、すべての時間帯や利用者の通信を判断できないと説明する

[8. CPU・メモリと応答時間を比べる](./10-cpu-memory.md) / [10. 監視自身を確かめる](./07-watchdog.md)
