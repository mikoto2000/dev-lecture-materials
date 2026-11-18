# アクセスログ教材の検証記録

## Loki・Grafana版（2026-11-18）

固定版は Loki 3.7.10、Grafana 13.3.1、Grafana Alloy v1.22.0、Python 3.12.14-slim です。受講者の PC に言語ランタイムは不要です。

- Windows 上で全教材の textlint、ESLint、TypeScript、新教材のリンク・目次・ZIP整合性、Rspress のビルドに成功
- WSL 2 / Ubuntu 24.04 の Python 3.12 で、実 HTTP アプリ・ログ出力・通知受信器の単体試験5件に成功
- WSL 2 の Docker Engine 29.9.3 / Compose v5.7.0 で、専用一時プロジェクトとランダムなループバックポートを使用して実コンテナーを検査
- アプリのログを Alloy が読み取り、Loki に保存し、Grafana のデータソース経由でログ・件数・5xx率・遅い件数・p95を検索できることを確認
- エラーと遅延のルールで Firing と実際の firing 通知、解除後の正常と resolved 通知を確認
- 自動アクセス停止で直近1分が0件になり、ログ途絶の Firing と firing 通知、再開後の正常と resolved 通知を確認
- down で専用ボリュームを保持し、再起動後もダッシュボードが残ることを確認。試験終了後は専用プロジェクトを down --volumes で削除

ブラウザーの GUI 通し操作と Docker Desktop での通し操作は未実施です。API でのアラート検証と画面操作の検証は区別します。Windows の制限環境ではローカルソケット・一時ファイルの権限で単体試験を実行できず、許可された WSL 環境を使用しました。

## PowerShell版（置き換え前、2026-11-18）

Windows 上で、新規教材10ページと配布する2ファイルを確認しました。

| 対象 | 結果 |
|---|---|
| PowerShell 7.6.9 | 配布スクリプトの試験18件に成功 |
| Windows PowerShell 5.1 | 同じ試験18件に成功。プロセスに限り RemoteSigned を指定 |
| サンプルの再生 | 正常10件、異常10件、復旧10件の集計が本文の表と一致 |
| 判定の境界 | 5xx 率20%、遅いリクエスト3件、1000 ms の境界と閾値未満を確認 |
| 観測できない窓 | 0件は NO_DATA、3件は LOW_TRAFFIC。0件の率と p95 は null |
| 時刻 | UTC と +09:00 の同値、開始以上・終了未満の集計を確認 |
| 不正データ | 壊れた JSON、欠落項目、数値の型・範囲、タイムゾーンの欠落で行番号付きの失敗を確認 |
| 静的検査 | 全教材の textlint、ESLint、TypeScript、新教材の目次・リンク・配布先の検査に成功 |
| 既存教材 | Dev Container、wslc、インフラ監視の静的検査に成功 |
| サイト | Rspress ビルドに成功。教材の各ページと配布ファイルを出力 |

実行コマンドは `npm run test:access-log` と `powershell -NoProfile -ExecutionPolicy RemoteSigned -File scripts/test-access-log.ps1` です。後者は、サンドボックス内ではレジストリーの参照制限で開始できず、許可された制限外の実行で確認しました。永続的な実行ポリシーの変更は行っていません。

実 Web サーバーからのログ収集、常駐監視、自動通知、ローテーション追従、ブラウザーでの表示確認は未実施です。配布ログは架空の固定データであり、本番の負荷や障害を再現したものではありません。

[教材トップ](../docs/access-log-monitoring/index.md)
