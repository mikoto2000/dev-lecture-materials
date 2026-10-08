import * as path from 'node:path';
import { defineConfig } from '@rspress/core';
import { pluginGoogleAnalytics } from 'rsbuild-plugin-google-analytics';

export default defineConfig({
  root: path.join(__dirname, 'docs'),
  base: '/devcontainer-handson/',
  title: 'Dev Container で構築する開発環境',
  logoText: 'Dev Container で構築する開発環境',
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
