import * as path from 'node:path';
import { defineConfig } from '@rspress/core';
import { pluginGoogleAnalytics } from 'rsbuild-plugin-google-analytics';

export default defineConfig({
  root: path.join(__dirname, 'docs'),
  base: '/devcontainer-handson/',
  title: '勉強会テキスト',
  lang: 'ja',
  description: '開発環境づくりを学ぶ勉強会のハンズオン教材集',
  logoText: '勉強会テキスト',
  themeConfig: {
    socialLinks: [],
  },
  globalStyles: path.join(__dirname, 'styles/global.css'),
  builderConfig: {
    plugins: [
      pluginGoogleAnalytics({
        id: 'G-X84SLVB4Q4',
      }),
    ],
  },
});
