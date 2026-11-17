# 開発系勉強会テキスト集

開発環境づくりを学ぶハンズオン教材を、コンテンツごとに格納するリポジトリです。

## 教材

- [Dev Container で構築する開発環境](docs/コンテナで構築する開発環境/index.md): Docker・Docker Compose の基礎から Dev Container まで

- [wslc を利用したコンテナ利用入門](docs/wslc-postgresql/index.md): PostgreSQL の起動・SQL・永続化を体験する60〜90分の教材

- [インフラ監視実践入門](docs/monitoring-intro/index.md): Uptime Kuma による動作確認から、通知・遅さ・ログ・容量・CPU/メモリー・通信へ段階的に広げる教材

## 構成と公開URL

- `docs/index.md`: 教材を選ぶ共通トップページ
- `docs/_nav.json`: 教材間を移動する共通ナビゲーション
- `docs/<教材ディレクトリ>/`: 教材本文・画像・教材独自の `_meta.json`
- 教材ごとにサイドバーを分けます。新しい教材は専用ディレクトリに追加してください
- 既存の `docs/CONTENTS.md` と `docs/コンテナで構築する開発環境/` の各章・画像は同じパスで維持します
- リポジトリ名は `dev-lecture-materials`、公開baseは `/dev-lecture-materials/` です
- 公開教材: https://mikoto2000.github.io/dev-lecture-materials/
- 改名により旧GitHub Pages URLの `/devcontainer-handson/` は自動転送されません。外部の教材リンクは新しいbaseへ更新してください。各章のbaseより後ろのパスは維持しています

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
npm run check:monitoring
npm run test:monitoring
npm run check:monitoring-compose
npm run test:monitoring-compose
npm run build
npm run preview
```

ビルド時にリンク切れを検査します。教材追加時には共通トップからの導線、教材固有の目次、前後の章へのリンク、既存公開URLも確認してください。

PR では全教材の textlint、教材ごとの静的検査、監視ラボの試験、サイトビルドを実行します。GitHub Pages への公開時も、公開対象のコミットで同じ検証を実行します。

`npm run check` は Biome の検査を実行します。修正も適用する場合は `npm run check:fix` を使います。

## wslc 教材の配布資料

SQL と PowerShell の例は `docs/public/wslc-postgresql/examples/` に格納し、教材トップからダウンロードできます。教材を読む受講者に Node.js は不要です。

開催前は、講師用ガイドに沿って受講環境で確認してください。[講師用ガイド](docs/wslc-postgresql/facilitator.md)

## インフラ監視教材の実験用ファイル

`docs/public/monitoring-intro/lab/` に Uptime Kuma 2.5.5 と学習用アプリの Compose 環境を格納します。本編は Windows PowerShell / Docker Desktop を基本とし、WSL 2 上の Docker Engine で進める手順もあります。監視は Kuma の GUI で設定します。受講者向けには教材トップから ZIP を配布します。ラボを変更したら `npm run package:monitoring` で ZIP を再生成します。

自作の `monitor.py` / `watchdog.py` は任意の補足です。本編の監視には使用しません。

章の表示順は `docs/monitoring-intro/_meta.json` で管理します。ファイル名は公開 URL の維持に使うため、表示順と異なる場合があります。たとえば `07-watchdog.md` は第10章です。

`npm run test:monitoring` は Python 3.10 以降が必要です。`check:monitoring-compose` は Docker CLI と Compose（v2 または v5）、`test:monitoring-compose` は Docker の実行環境も必要です。後者は試験専用のプロジェクトとボリュームを作成し、終了時に削除します。
