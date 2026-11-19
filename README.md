# 開発系勉強会テキスト集

開発環境づくりを学ぶハンズオン教材を、コンテンツごとに格納するリポジトリです。

## 教材

- [Dev Container で構築する開発環境](docs/コンテナで構築する開発環境/index.md): Docker・Docker Compose の基礎から Dev Container まで

- [wslc を利用したコンテナ利用入門](docs/wslc-postgresql/index.md): PostgreSQL の起動・SQL・永続化を体験する60〜90分の教材

- [インフラ監視実践入門](docs/monitoring-intro/index.md): Uptime Kuma による動作確認から、通知・遅さ・ログ・容量・CPU/メモリー・通信へ段階的に広げる教材

- [アクセスログ監視入門](docs/access-log-monitoring/index.md): Loki・Grafana・Alloy で収集・検索・可視化し、失敗・遅さ・ログ途絶のアラートと復旧通知を体験する90〜120分の教材

- [不正アクセス監視入門](docs/security-log-monitoring/index.md): 同じ OSS 構成で認証失敗・404の集中を検知し、誤検知の確認と調査を学ぶ90〜120分の続編

## 構成と公開URL

- `docs/index.md`: 教材を選ぶ共通トップページ
- `docs/_nav.json`: 教材間を移動する共通ナビゲーション
- `docs/<教材ディレクトリ>/index.md`: 教材本文・補足・講師用ガイドをまとめた1つの Markdown
- 新しい教材は専用ディレクトリの `index.md` に追加し、章は同じファイルの見出しで分けます
- `docs/CONTENTS.md` は Dev Container 教材の章へのリンク集です。章へのリンクは各教材の `index.md` 内のアンカーを使います
- リポジトリ名は `dev-lecture-materials`、公開baseは `/dev-lecture-materials/` です
- 公開教材: https://mikoto2000.github.io/dev-lecture-materials/
- 改名により旧GitHub Pages URLの `/devcontainer-handson/` は自動転送されません。外部の教材リンクは新しいbaseへ更新してください。統合前の章別URLは、公開サイト上で各教材の該当章へ転送します。新しいリンクには教材トップと該当章のアンカーを使ってください

## 編集・プレビュー

Node.js 20.19以降（20系）または22.12以降を使用してください。Node.js 22 LTSを推奨します。

```bash
npm ci
npm run dev
```

## 検証

一連の検証は Linux で実行します。Windows では、Docker Engine を利用できる WSL 2 の Ubuntu を開き、その中で `npm ci` を実行してから進めてください。Python ラボの実行テストもこの Linux 環境を使います。

```bash
npm run lint
npx tsc --noEmit
npm run textlint
npm run check:devcontainer
npm run check:wslc
npm run check:access-log
npm run test:access-log
npm run test:access-log-compose
npm run check:security-log
npm run test:security-log
npm run test:security-log-compose
npm run check:monitoring
npm run test:monitoring
npm run check:monitoring-compose
npm run test:monitoring-compose
npm run build
npm run preview
```

ビルド時にリンク切れを検査します。`scripts/legacy-routes.json` に定義した旧章 URL の転送 HTML を生成し、転送先の章と HTML の ID 重複も検査します。教材追加時には共通トップからの導線、教材固有の目次、章へのアンカー、配布資料へのリンクも確認してください。

PR では全教材の textlint、教材ごとの静的検査、監視ラボの試験、サイトビルドを実行します。GitHub Pages への公開時も、公開対象のコミットで同じ検証を実行します。

アクセスログ教材の受講者には Docker Compose があればよく、PC への言語ランタイムの導入は不要です。開発者向けの `test:access-log`、`package:access-log` は Python 3.10 以降、`test:access-log-compose` はさらに Docker の実行環境が必要です。配布ファイルを変更したら `npm run package:access-log` で Grafana 設定と ZIP を再生成します。

不正アクセス教材も同じ要件です。`npm run package:security-log` で専用の ZIP を再生成します。共通のアクセスログラボの資材を変更した場合は、両方の ZIP を再生成してください。展開後の不正アクセスラボは、前の教材のファイルに依存せず単独で起動できます。

`npm run check` は Biome の検査を実行します。修正も適用する場合は `npm run check:fix` を使います。

## wslc 教材の配布資料

SQL と PowerShell の例は `docs/public/wslc-postgresql/examples/` に格納し、教材トップからダウンロードできます。教材を読む受講者に Node.js は不要です。

開催前は、講師用ガイドに沿って受講環境で確認してください。[講師用ガイド](docs/wslc-postgresql/index.md#facilitator)

## インフラ監視教材の実験用ファイル

`docs/public/monitoring-intro/lab/` に Uptime Kuma 2.5.5 と学習用アプリの Compose 環境を格納します。本編は Windows PowerShell / Docker Desktop を基本とし、WSL 2 上の Docker Engine で進める手順もあります。監視は Kuma の GUI で設定します。受講者向けには教材トップから ZIP を配布します。ラボを変更したら `npm run package:monitoring` で ZIP を再生成します。

自作の `monitor.py` / `watchdog.py` は任意の補足です。本編の監視には使用しません。

章の順番は各教材の `index.md` 内で管理します。`_meta.json` は教材全文へのリンクを定義します。

`npm run test:monitoring` は Python 3.10 以降が必要です。`check:monitoring-compose` は Docker CLI と Compose（v2 または v5）、`test:monitoring-compose` は Docker の実行環境も必要です。後者は試験専用のプロジェクトとボリュームを作成し、終了時に削除します。
