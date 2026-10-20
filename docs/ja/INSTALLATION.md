<img src="../../src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">

# CHIPIX 1.0.0

## インストール

[English](../../docs/en/README.md) · [Español](../../docs/es/README.md) · [Deutsch](../../docs/de/README.md) · [Français](../../docs/fr/README.md) · [简体中文](../../docs/zh/README.md) · [日本語](../../docs/ja/README.md) · [Português](../../docs/pt/README.md)

## 必要条件

ChimeraX 1.8 以降が必要です。macOS Apple Silicon の ChimeraX 1.12、Python 3.11、Qt6 で統合を検証しました。他の OS やバージョンは検証が必要です。解析と読み込みは Python 標準ライブラリを使用します。ドッキングの実行には、対応する外部 Vina または Smina の実行ファイルと前処理済み PDBQT が必要です。

1. CHIPIX-1.0.0.zip をダウンロードして展開し、bundle_info.xml、README.md、dist/ があるフォルダーを確認します。

2. ChimeraX を起動し、コマンドラインを表示します。

3. 下のインストールコマンドのパスを実際の展開先に置き換えて実行します。dist/ 内の wheel を使用します。

4. chipix を実行します。メニュー項目は Tools → Binding Analysis → CHIPIX です。

5. 言語で English、Español、Deutsch、Français、简体中文、日本語、Português を選択します。選択は保存されます。

6. ドッキングでエンジン実行ファイル、前処理済み受容体・リガンド PDBQT、出力フォルダーを選択します。

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"
chipix
```

このソース ZIP には、macOS Apple Silicon 用の公式 Vina 1.2.7 実行ファイルが engines/ に含まれます。wheel にはプラグインのみが含まれます。Windows、Linux、Intel Mac では、公式リリースから対応するエンジンを取得し、参照で選択してください。Smina は別に設定します。コピーした macOS/Linux の実行ファイルに実行権限がない場合は、ターミナルでそのファイルに chmod +x を実行します。

更新時は toolshed install に reinstall true を付けて再実行し、ChimeraX を再起動します。削除には toolshed uninstall ChimeraX-CHIPIX を使用します。保存済みの実行フォルダーは保持されます。

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true
toolshed uninstall ChimeraX-CHIPIX
```

```text
devel install "/FULL/PATH/CHIPIX-1.0.0" editable true
```

## GitHub

GitHub 用には ZIP を展開し、CHIPIX-1.0.0 フォルダーの内容をリポジトリのルートにアップロードします。dist/ の wheel を GitHub Release に添付すると利用者がインストールできます。公開はリポジトリ所有者が行います。GitHub URL は仮定していません。

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
