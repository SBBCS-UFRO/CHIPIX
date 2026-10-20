<img src="../../src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">

# CHIPIX 1.0.0

## Installation

[English](../../docs/en/README.md) · [Español](../../docs/es/README.md) · [Deutsch](../../docs/de/README.md) · [Français](../../docs/fr/README.md) · [简体中文](../../docs/zh/README.md) · [日本語](../../docs/ja/README.md) · [Português](../../docs/pt/README.md)

## Requirements

ChimeraX 1.8 or later is required. Integration was tested on ChimeraX 1.12 with Python 3.11 and Qt6 on macOS Apple Silicon. Other operating systems and ChimeraX versions need validation. Analysis and import use the Python standard library. Running docking additionally requires a compatible external Vina or Smina executable and prepared PDBQT inputs.

1. Download CHIPIX-1.0.0.zip and extract it. Locate the folder containing bundle_info.xml, README.md and dist/.

2. Open ChimeraX and display its command line.

3. Run the installation command below, replacing the path with the actual extracted folder. Use the wheel in dist/.

4. Run chipix. The menu entry is Tools → Binding Analysis → CHIPIX.

5. Select English, Español, Deutsch, Français, 简体中文, 日本語 or Português using Language. The choice is remembered.

6. In Docking, browse to the engine executable, select the prepared receptor and ligand PDBQT files, and choose an output folder.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"
chipix
```

This source ZIP includes the official Vina 1.2.7 executable for macOS Apple Silicon in engines/. The wheel contains the plugin only. For Windows, Linux or Intel Macs, obtain the matching engine from its official release and select it with Browse. Smina is configured separately. If a copied macOS/Linux binary lacks execute permission, use chmod +x on that executable in a terminal.

To update an installed copy, repeat toolshed install with reinstall true, then restart ChimeraX. To remove the plugin, use toolshed uninstall ChimeraX-CHIPIX. Saved run folders remain available.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true
toolshed uninstall ChimeraX-CHIPIX
```

```text
devel install "/FULL/PATH/CHIPIX-1.0.0" editable true
```

## GitHub

For GitHub, extract the ZIP and upload the contents of its CHIPIX-1.0.0 folder as the repository root. Attach the wheel from dist/ to a GitHub Release so users can install it directly. Publishing is performed by the repository owner; no GitHub URL is assumed.

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
