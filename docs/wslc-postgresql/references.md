# 参考資料と検証範囲

確認日: 2026-10-08。

## 公式資料

- [Microsoft: WSL コンテナー概要](https://learn.microsoft.com/ja-jp/windows/wsl/wsl-container?tabs=csharp)
- [Microsoft: WSL コンテナーの使用を開始する](https://learn.microsoft.com/ja-jp/windows/wsl/tutorials/wsl-containers) — WSL 2.9.3 以降、基本的な run / exec / stop
- [Microsoft/WSL: VolumeCommand.h](https://github.com/microsoft/WSL/blob/master/src/windows/wslc/commands/VolumeCommand.h) — ボリュームのサブコマンド
- [Microsoft/WSL: ContainerRunCommand.cpp](https://github.com/microsoft/WSL/blob/master/src/windows/wslc/commands/ContainerRunCommand.cpp) — run のオプション
- [Microsoft/WSL: ContainerExecCommand.cpp](https://github.com/microsoft/WSL/blob/master/src/windows/wslc/commands/ContainerExecCommand.cpp) — exec の対話オプション
- [Microsoft/WSL: マウント構文の単体テスト](https://github.com/microsoft/WSL/blob/master/test/windows/wslc/WSLCCLIMountParserUnitTests.cpp) — 名前付きボリュームの構文
- [Microsoft/WSL: 公開ポート構文の単体テスト](https://github.com/microsoft/WSL/blob/master/test/windows/wslc/WSLCPortParserUnitTests.cpp) — 明示的なホスト IP
- [PostgreSQL Docker Official Image](https://hub.docker.com/_/postgres) — 初期化変数・保存先・17以前と18以降の違い
- [Microsoft/WSL: 名前付きボリュームの E2E テスト](https://github.com/microsoft/WSL/blob/master/test/windows/wslc/e2e/WSLCE2EContainerRunTests.cpp) — コンテナー削除後もデータを再利用
- [PostgreSQL: initdb](https://www.postgresql.org/docs/17/app-initdb.html) — 初期化時の TCP 認証方式
- [PostgreSQL: psql](https://www.postgresql.org/docs/17/app-psql.html)
- [PostgreSQL: pg_isready](https://www.postgresql.org/docs/17/app-pg-isready.html)
- [Rspress: Quick start](https://rspress.rs/guide/start/getting-started)

公式イメージの説明にある Docker コマンドをそのまま wslc に置き換えたわけではありません。wslc 側の引数は Microsoft の実装・テストと照合しています。ただし master ブランチは変わるため、手元の版の `--help` と実機確認を優先してください。

## 構成の参考

[mikoto2000 / Practical-Introduction-to-Spring-Boot](https://github.com/mikoto2000/Practical-Introduction-to-Spring-Boot) の Rspress 2.0.1、左サイドバー、日本語ハンズオン、講義の区切りを参考にしています。本教材は独立したコンテンツとして、この教材集に収録しています。

## 検証の境界

[検証記録](./verification.md) に、教材ビルド・静的チェックの結果を記録しています。Windows の wslc 操作、PostgreSQL 実サービスへの接続、永続化と削除の実機試験は未実施です。開催前には講師用チェックリストを実行してください。
