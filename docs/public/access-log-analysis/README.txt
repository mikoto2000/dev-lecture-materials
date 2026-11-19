アクセスログ分析入門 - 不正アクセス検知編。

1. ZIPをすべて展開し、analyzer.htmlをEdge/Chrome/Firefoxで開きます。
2. 「01 正常時」から開始し、サンプルを切り替えて分析します。
3. samples内のJSONLはファイル選択でも読み込めます。

ネット接続、サーバー、Docker、追加ライブラリーは不要です。
ファイルを移動するときはcore.js、app.js、samples.js、style.cssも一緒に移動してください。
外部への送信や自動保存は行いません。学習用の架空ログ専用です。
入力はUTF-8のJSONL、2 MiB以下・10,000行以下です。
すべてUTCです。時間範囲は開始を含み、終了を含みません。
詳細な項目と演習・解説は同梱のlesson.mdを参照してください。
lesson.mdはMarkdownを表示できるエディターまたはテキストエディターで読めます。

再生成: npm run package:log-analysis。
検証: npm run test:log-analysis。
