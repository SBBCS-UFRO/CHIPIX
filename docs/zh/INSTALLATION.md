<img src="../../src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">

# CHIPIX 1.0.0

## 安装

[English](../../docs/en/README.md) · [Español](../../docs/es/README.md) · [Deutsch](../../docs/de/README.md) · [Français](../../docs/fr/README.md) · [简体中文](../../docs/zh/README.md) · [日本語](../../docs/ja/README.md) · [Português](../../docs/pt/README.md)

## 系统要求

需要 ChimeraX 1.8 或更高版本。已在 macOS Apple Silicon 上使用 ChimeraX 1.12、Python 3.11 和 Qt6 测试集成；其他系统和版本尚需验证。分析和导入仅使用 Python 标准库。运行对接还需要兼容的外部 Vina 或 Smina 可执行文件，以及已制备的 PDBQT 输入。

1. 下载并解压 CHIPIX-1.0.0.zip，找到包含 bundle_info.xml、README.md 和 dist/ 的文件夹。

2. 打开 ChimeraX 并显示命令行。

3. 执行下方安装命令，将路径替换为实际解压路径，使用 dist/ 中的 wheel 文件。

4. 运行 chipix。菜单项为 Tools → Binding Analysis → CHIPIX。

5. 通过语言菜单选择 English、Español、Deutsch、Français、简体中文、日本語或 Português。选择将被保存。

6. 在分子对接页选择引擎可执行文件、已制备的受体和配体 PDBQT，以及输出文件夹。

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"
chipix
```

此源码 ZIP 在 engines/ 中附带官方 Vina 1.2.7 的 macOS Apple Silicon 可执行文件。wheel 仅包含插件。Windows、Linux 或 Intel Mac 用户应从官方发布页取得对应引擎，再通过浏览选择。Smina 单独配置。若复制后的 macOS/Linux 可执行文件缺少执行权限，可在终端对该文件运行 chmod +x。

更新时，重新运行 toolshed install 并加上 reinstall true，然后重启 ChimeraX。卸载使用 toolshed uninstall ChimeraX-CHIPIX。已保存的运行文件夹会保留。

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true
toolshed uninstall ChimeraX-CHIPIX
```

```text
devel install "/FULL/PATH/CHIPIX-1.0.0" editable true
```

## GitHub

上传 GitHub 时，解压 ZIP，将 CHIPIX-1.0.0 文件夹的内容作为仓库根目录上传。将 dist/ 中的 wheel 附加到 GitHub Release，便于用户安装。发布由仓库所有者完成；此处不预设 GitHub 地址。

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
