<img src="../../src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">

# CHIPIX 1.0.0

## Installation

[English](../../docs/en/README.md) · [Español](../../docs/es/README.md) · [Deutsch](../../docs/de/README.md) · [Français](../../docs/fr/README.md) · [简体中文](../../docs/zh/README.md) · [日本語](../../docs/ja/README.md) · [Português](../../docs/pt/README.md)

## Voraussetzungen

ChimeraX ab Version 1.8 ist erforderlich. Getestet wurde die Integration mit ChimeraX 1.12, Python 3.11 und Qt6 auf macOS Apple Silicon. Andere Systeme und Versionen müssen validiert werden. Analyse und Import verwenden die Python-Standardbibliothek. Zum Docking sind zusätzlich eine passende externe Vina- oder Smina-Datei und vorbereitete PDBQT-Eingaben nötig.

1. CHIPIX-1.0.0.zip herunterladen und entpacken. Den Ordner mit bundle_info.xml, README.md und dist/ finden.

2. ChimeraX öffnen und die Befehlszeile einblenden.

3. Den folgenden Installationsbefehl ausführen und den Pfad durch den tatsächlichen entpackten Ordner ersetzen. Die Wheel-Datei aus dist/ verwenden.

4. chipix ausführen. Der Menüeintrag lautet Tools → Binding Analysis → CHIPIX.

5. Unter Sprache English, Español, Deutsch, Français, 简体中文, 日本語 oder Português wählen. Die Auswahl wird gespeichert.

6. Unter Docking die ausführbare Engine-Datei, vorbereitete Rezeptor- und Liganden-PDBQT-Dateien sowie einen Ausgabeordner auswählen.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"
chipix
```

Dieses Quell-ZIP enthält die offizielle Vina-1.2.7-Datei für macOS Apple Silicon unter engines/. Das Wheel enthält nur das Plugin. Für Windows, Linux oder Intel-Macs die passende offizielle Engine herunterladen und mit Durchsuchen auswählen. Smina wird separat konfiguriert. Fehlen einer kopierten Datei unter macOS/Linux Ausführungsrechte, im Terminal chmod +x auf diese Datei anwenden.

Zum Aktualisieren toolshed install mit reinstall true wiederholen und ChimeraX neu starten. Zum Entfernen toolshed uninstall ChimeraX-CHIPIX verwenden. Gespeicherte Laufordner bleiben erhalten.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true
toolshed uninstall ChimeraX-CHIPIX
```

```text
devel install "/FULL/PATH/CHIPIX-1.0.0" editable true
```

## GitHub

Für GitHub das ZIP entpacken und den Inhalt von CHIPIX-1.0.0 als Repository-Hauptverzeichnis hochladen. Das Wheel aus dist/ an eine GitHub Release anhängen. Die Veröffentlichung übernimmt der Repository-Eigentümer; eine GitHub-Adresse wird nicht vorausgesetzt.

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
