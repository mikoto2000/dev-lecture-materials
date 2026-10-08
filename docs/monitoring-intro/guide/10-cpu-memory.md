# 8. CPU・メモリと応答時間を比べる

## 困りごと

Kuma のグラフで、アプリの応答が遅くなっています。CPU が忙しいのでしょうか。それとも何かを待っているのでしょうか。遅くなった時間帯に、アプリが使っている資源も比べます。

## 小さな追加: 同じ時間帯の値を残す

`demo-health` と `demo-item` が Up であることを確認します。まず遅延を入れていない状態で、次のコマンドを実行します。

```powershell
Get-Date -Format o
docker compose stats --no-stream demo
docker compose stats --no-stream kuma
```

`--no-stream` は値を1回表示して終了する指定です。サービスは1つずつ指定します。`demo` がアプリ側、`kuma` が監視する側です。[Docker Compose stats](https://docs.docker.com/reference/cli/docker/compose/stats/)

- `CPU %`: コンテナーの CPU 使用率。Linux の表示では、複数の CPU を使うと100%を超える場合もある
- `MEM USAGE / LIMIT`: コンテナーのメモリ使用量と、Docker が報告する利用上限
- `MEM %`: その上限に対する使用量の割合

CPU の値は短い測定区間の値です。コマンドを実行していなかった間の最大値や平均値ではありません。Linux の CPU 使用率の計算は、CPU 数も考慮しています。[Docker CLI の計算処理](https://github.com/docker/cli/blob/master/cli/command/container/stats_helpers.go)

Linux コンテナーに対する Docker CLI のメモリ表示では、一部のキャッシュを差し引きます。`LIMIT` にはコンテナーの制限や、実行環境で利用できるメモリが関係します。アプリ専用に予約された量ではありません。[Docker stats の列とメモリ表示](https://docs.docker.com/reference/cli/docker/container/stats/)

**ここで測るのは Docker Desktop 内の Linux コンテナーです。** Windows 全体の CPU・メモリ使用量ではありません。タスクマネージャーの値と同じ意味だと思って比べないでください。

20秒ほど間を空けて、同じコマンドをもう一度実行します。同じ時間帯の `demo-item` の応答時間も記録します。Kuma の表示時刻とログの UTC、PowerShell の時刻のずれに注意して照合します。

## 安全な故障: 忙しくする代わりに待たせる

**戻すコマンドは `docker compose exec demo python labctl.py delay 0` です。** CPU の負荷試験や大量のメモリ確保はしません。

`demo-item` の現在の Request Timeout をメモし、実験中だけ **3秒**へ変更して保存します。次に、前の章で使った待ち時間を入れます。

```powershell
docker compose exec demo python labctl.py delay 0.8
```

数回の監視結果を待ち、次の値を同じ時間帯のメモに残します。

```powershell
Get-Date -Format o
docker compose stats --no-stream demo
docker compose stats --no-stream kuma
docker compose logs --tail 10 demo
```

Kuma の `demo-item` の応答時間と、ログの `/items/1` の `duration_ms` を比べます。CPU・メモリの値も正常時と比べてください。20秒ほど間を空けて、もう一度確認します。

この実験では、アプリの処理に待ち時間を入れています。応答の遅さに比べ、CPU 使用率の変化は小さい場合もあります。ただし、実行環境の別の処理や測定のタイミングにも左右されます。CPU・メモリが必ず同じ値になる実験ではありません。

## 復旧

```powershell
docker compose exec demo python labctl.py delay 0
```

Request Timeout をメモした元の値へ戻します。`demo-item` が Up であることと、新しい応答時間が正常時に近づくことを確認します。CPU・メモリも同じコマンドで確認し、「正常時・待ち時間あり・復旧後」の3つを比べます。

## 確かめた範囲

同じ時間帯の応答時間と CPU・メモリを並べられました。ただし、一緒に増えたことだけで原因を確定できません。CPU 使用率が高くても利用者の待ち時間に影響がない場合や、使用率が低くても外部サービスを待って遅い場合があります。

メモリの1回の増加だけでメモリリークとは決めません。繰り返す操作に伴って増え続けるのか、落ち着くのかを長い時間で確かめる必要があります。今回の小さなアプリと少数の確認では、本番の負荷に耐えられる量は分かりません。

CPU・メモリとも、一律に「80%を超えたら障害」と決めず、普段の値、続いた時間、応答時間やエラーへの影響を合わせて読みます。`stats --no-stream` はその場の観察であり、履歴保存や自動通知を追加したわけではありません。

## チェックポイント

- 正常時・待ち時間あり・復旧後について、時刻、応答時間、CPU、メモリを並べる
- 応答が遅いだけでは CPU 不足と決められない理由を、今回の実験で説明する
- アプリ側と監視する側の値を区別する
- 短い観察だけでは、瞬間的な高負荷や長時間のメモリ増加を見逃すことを説明する

[7. 保存先の空き容量を確かめる](./09-disk.md) / [9. ネットワークの応答とロスを見る](./11-network.md)
