# 開発系勉強会テキスト集

開発環境づくりを学ぶハンズオン教材を、コンテンツごとに格納するリポジトリです。

## 教材

- [Dev Container で構築する開発環境](docs/コンテナで構築する開発環境/index.md): Docker・Docker Compose の基礎から Dev Container まで

- [wslc を利用したコンテナ利用入門](docs/wslc-postgresql/index.md): PostgreSQL の起動・SQL・永続化を体験する60〜90分の教材

- [インフラ監視実践入門](docs/monitoring-intro/index.md): URL の確認から、操作・応答時間・通知・監視自身へ段階的に広げる教材

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

```bash
npm run lint
npx tsc --noEmit
npm run check:wslc
npm run check:monitoring
npm run test:monitoring
npm run build
npm run preview
```

ビルド時にリンク切れを検査します。教材追加時には共通トップからの導線、教材固有の目次、前後の章へのリンク、既存公開URLも確認してください。

`npm run textlint` は既存教材に未解消の指摘があります。無関係な文体の修正は教材の再構成と分けて扱います。

## wslc 教材の配布資料と実機確認

SQL と PowerShell の例は `docs/public/wslc-postgresql/examples/` に格納し、教材トップからダウンロードできます。教材を読む受講者に Node.js は不要です。

Windows / WSL / wslc と PostgreSQL 実サービスの操作試験は未実施です。[講師用ガイド](docs/wslc-postgresql/facilitator.md)と[検証記録](docs/wslc-postgresql/verification.md)を確認し、開催前に実機で確認してください。

## インフラ監視教材の実験用ファイル

`docs/public/monitoring-intro/lab/` に Python 標準ライブラリーだけで動くローカル実験を格納します。受講者向けには教材トップから ZIP を配布し、Node.js は不要です。Python ファイルを変更したら `npm run package:monitoring` で配布 ZIP を再生成します。

`npm run test:monitoring` は Python 3.10 以降が必要です。自動試験と Windows / WSL での実機確認の範囲は、[検証記録](docs/monitoring-intro/verification.md)を参照してください。
