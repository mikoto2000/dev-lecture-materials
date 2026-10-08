# 勉強会テキスト

開発環境づくりを学ぶハンズオン教材を、コンテンツごとに格納するリポジトリです。

## 教材

- [Dev Container で構築する開発環境](docs/コンテナで構築する開発環境/index.md): Docker・Docker Compose の基礎から Dev Container まで

## 構成と公開URL

- `docs/index.md`: 教材を選ぶ共通トップページ
- `docs/_nav.json`: 教材間を移動する共通ナビゲーション
- `docs/<教材ディレクトリ>/`: 教材本文・画像・教材独自の `_meta.json`
- 教材ごとにサイドバーを分けます。新しい教材は専用ディレクトリに追加してください
- 既存の `docs/CONTENTS.md` と `docs/コンテナで構築する開発環境/` の各章・画像は同じパスで維持します
- リポジトリ名 `devcontainer-handson`、公開base `/devcontainer-handson/`、GitHub Pages設定は変更しません

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
npm run build
npm run preview
```

ビルド時にリンク切れを検査します。教材追加時には共通トップからの導線、教材固有の目次、前後の章へのリンク、既存公開URLも確認してください。

`npm run textlint` は既存教材に未解消の指摘があります。無関係な文体の修正は教材の再構成と分けて扱います。
