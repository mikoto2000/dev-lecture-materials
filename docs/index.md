---
pageType: home

hero:
  name: "開発系勉強会テキスト集"
  text: "手を動かして、開発環境をつくる"
  tagline: "下の教材カードで目的と前提を比べて選んでください。ログを読む考え方は「アクセスログ分析」、収集・通知の仕組みは「アクセスログ監視」から学べます。"
  actions:
    - theme: brand
      text: Dev Container で構築する開発環境
      link: /コンテナで構築する開発環境/

    - theme: alt
      text: wslc を利用したコンテナ利用入門
      link: /wslc-postgresql/

    - theme: alt
      text: インフラ監視実践入門
      link: /monitoring-intro/

    - theme: alt
      text: アクセスログ監視入門
      link: /access-log-monitoring/

    - theme: alt
      text: 不正アクセス監視入門
      link: /security-log-monitoring/

    - theme: alt
      text: アクセスログ分析入門 - 不正アクセス検知編
      link: /access-log-analysis/

features:
  - title: アクセスログ分析入門 - 不正アクセス検知編
    details: 【目的】架空のログを分析し、不審なアクセスの根拠、誤検知の可能性、追加調査を考えます。【前提】ブラウザーの基本操作のみ。Docker やプログラミング言語の導入は不要です。90〜120分の教材です。
    link: /access-log-analysis/
  - title: Dev Container で構築する開発環境
    details: 【目的】Docker・Docker Compose の基礎から、チームで共有できる Dev Container の開発環境を作ります。【前提】Windows 11 と基本的なターミナル操作。WSL 2・Ubuntu・Docker Engine の導入から扱います。
    link: /コンテナで構築する開発環境/
  - title: wslc を利用したコンテナ利用入門
    details: 【目的】Windows 上で PostgreSQL を起動し、SQL とデータの永続化を体験します。【前提】PowerShell でコマンドを実行できること。WSL 2.9.3 以降と wslc を事前に用意します。Docker Desktop は不要です。60〜90分の教材です。
    link: /wslc-postgresql/
  - title: インフラ監視実践入門
    details: 【目的】Uptime Kuma の動作確認から、通知・遅さ・ログ・容量・CPU/メモリー・通信へ観測を広げます。【前提】PowerShell と Docker Desktop、または WSL 2 上の Docker Engine。Python の実装知識は不要です。
    link: /monitoring-intro/
  - title: アクセスログ監視入門
    details: 【目的】Loki・Grafana・Alloy でログの収集・検索・可視化を行い、アラートと復旧通知を体験します。【前提】Docker Compose を実行した経験。PowerShell と Docker Desktop、または WSL 2 上の Docker Engine を使います。
    link: /access-log-monitoring/
  - title: 不正アクセス監視入門
    details: 【目的】認証失敗や404の集中を検知し、誤検知の確認と調査につなげます。【前提】アクセスログ監視入門の続編です。先に Explore・LogQL・ダッシュボード・アラートの基本操作を学んでください。ラボは独立して起動します。
    link: /security-log-monitoring/
---
