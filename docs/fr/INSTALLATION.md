<img src="../../src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">

# CHIPIX 1.0.0

## Installation

[English](../../docs/en/README.md) · [Español](../../docs/es/README.md) · [Deutsch](../../docs/de/README.md) · [Français](../../docs/fr/README.md) · [简体中文](../../docs/zh/README.md) · [日本語](../../docs/ja/README.md) · [Português](../../docs/pt/README.md)

## Prérequis

ChimeraX 1.8 ou ultérieur est requis. L’intégration a été testée sur ChimeraX 1.12, Python 3.11 et Qt6 sous macOS Apple Silicon. Les autres systèmes et versions restent à valider. L’analyse et l’import utilisent la bibliothèque standard Python. L’exécution du docking nécessite un exécutable externe Vina ou Smina compatible et des entrées PDBQT préparées.

1. Téléchargez CHIPIX-1.0.0.zip et décompressez-le. Repérez le dossier contenant bundle_info.xml, README.md et dist/.

2. Ouvrez ChimeraX et affichez sa ligne de commande.

3. Exécutez la commande d’installation ci-dessous en remplaçant le chemin par celui du dossier extrait. Utilisez le wheel dans dist/.

4. Exécutez chipix. Le menu est Tools → Binding Analysis → CHIPIX.

5. Choisissez English, Español, Deutsch, Français, 简体中文, 日本語 ou Português dans Langue. Ce choix est mémorisé.

6. Dans Docking, sélectionnez l’exécutable du moteur, les PDBQT préparés du récepteur et du ligand, et un dossier de sortie.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"
chipix
```

Ce ZIP source contient le binaire officiel Vina 1.2.7 pour macOS Apple Silicon dans engines/. Le wheel contient uniquement le plugin. Pour Windows, Linux ou Mac Intel, obtenez le binaire officiel adapté et sélectionnez-le avec Parcourir. Smina se configure séparément. Si un binaire copié sous macOS/Linux n’a pas la permission d’exécution, appliquez chmod +x à ce fichier dans un terminal.

Pour mettre à jour, répétez toolshed install avec reinstall true, puis redémarrez ChimeraX. Pour supprimer le plugin, utilisez toolshed uninstall ChimeraX-CHIPIX. Les dossiers de calculs enregistrés sont conservés.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true
toolshed uninstall ChimeraX-CHIPIX
```

```text
devel install "/FULL/PATH/CHIPIX-1.0.0" editable true
```

## GitHub

Pour GitHub, décompressez le ZIP et téléversez le contenu de CHIPIX-1.0.0 à la racine du dépôt. Joignez le wheel de dist/ à une GitHub Release. La publication est effectuée par le propriétaire du dépôt ; aucune URL GitHub n’est présumée.

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
