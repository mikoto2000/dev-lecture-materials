---
title: "INTRODUCTION"
author: mikoto2000
date: 2026/1/8
---

# INTRODUCTION

## Description

プロジェクトの開発環境構築をする／させる際に、手順ミスやアドリブで環境差異が発生してしまい、てこずった経験はありませんか？
Dev container を使うことで、開発環境をコード化し、誰でも同じ環境を一瞬で立ち上げることが可能になります。
本シリーズでは、Docker を使った開発環境構築の基礎から、Dev container を用いた再現性の高い開発環境の設計・共有までを、段階的に学びます。
プロジェクトの開発環境構築に苦労している方、Dev container に興味がある方はぜひご参加ください。
シリーズ終了時には、Spring Boot + PostgreSQL を想定した Dev container 構成を作り、チームで再利用できるテンプレートとして持ち帰れる状態を目指します。Vol.2 では Spring Boot プロジェクト自体は作成せず、開発コンテナと DB への接続までを確認します。

## Outline

Dev container を使った開発環境構築方法について、その前提の Docker, Docker Compose の触りから、VS Code での Dev container 利用方法を、全 2 回のワークショップで解説します。

### 話すこと

- 開発環境構築(事前準備資料として配布)
  - Docker on WSL2 のセットアップ
- Docker 入門
  - Docker コンテナを使ってみる
  - Docker Compose を使ってみる
- Dev container 入門
  - Dev container の概要
  - Dev container の設定方法
  - Dev container の利用方法

### 話さないこと

- コンテナ技術の理論的な説明
- Docker / Docker Compose の高度な使い方
- VS Code の一般的な操作方法

### 対象者

- (プロジェクトメンバの)開発環境構築に苦労している人
- プロジェクトの技術的取りまとめをしている人
- Dev container に興味がある人
- ターミナル操作に抵抗が無い人（基本的なコマンド操作ができればOK）

### このテーマを取り上げる理由

プロジェクトの開発環境構築をする／させる際に、手順ミスやアドリブで環境差異が発生してしまい、そのサポートに時間を取られた経験がある方は多いと思います。
その解決方法として、Dev container を使った開発環境構築方法を導入し、比較的スムーズに環境構築ができるようになった経験を共有したいと思い、本セッションを企画しました。

### 講演の概要

- Vol.0 開発環境構築(事前準備資料として配布)
  - Docker on WSL2
  - Hello World コンテナを動かしてみる
- Vol.1 Docker / Docker Compose 入門
  - Docker コンテナ概要
  - Docker コンテナを使ってみる
    - Web サーバコンテナを動かしてみる
      - ポートフォワーディング
      - ボリュームマウント
  - Docker Compose を使ってみる
    - 複数サービスの定義
    - ポートフォワーディング
    - ボリュームマウント
- Vol.2 Dev container 入門
  - Dev container の概要
  - Dev container の設定方法
  - Dev container の利用方法

## 自身について

### 概要

仕事と趣味でプログラミングをやっているプログラマー。
一生を Getting Started の実施で過ごす人。
最近プライベートではギョームの素振りばかりやっています。
