# CHIPIX 1.0.0 validation

The 1iep test uses official prepared inputs from AutoDock Vina v1.2.7. CHIPIX does not chemically re-prepare them.

- [Official tutorial](https://github.com/ccsb-scripps/AutoDock-Vina/blob/v1.2.7/docs/source/docking_basic.rst).
- [Receptor](https://github.com/ccsb-scripps/AutoDock-Vina/blob/v1.2.7/example/basic_docking/solution/1iep_receptor.pdbqt): SHA-256 `f13cf3b36f61d87c3b58983e0b8ecf1c3456a685eb86dfe9ccfb139c7bdc2586`.
- [Ligand](https://github.com/ccsb-scripps/AutoDock-Vina/blob/v1.2.7/example/basic_docking/solution/1iep_ligand.pdbqt): SHA-256 `15fb35648d8c18c70317842f3a0631b73a19429c710a037ab07310084d579bb8`.
- `1iep/config.json` records the search box and parameters. The Vina binary and Apache-2.0 license are in `../engines/`.

The release includes the native-tool output `1iep/reference-vina.pdbqt`, direct output `1iep/direct-vina.pdbqt` and portable report `1iep/comparison.json`. Machine-specific run folders, location indexes and logs are excluded from the ZIP.

From the plugin root, compare recorded outputs without repeating docking:

```bash
python3 validation/compare_direct_vina.py --reuse-output
```

To reproduce the native-tool run, use ChimeraX Python:

```bash
python3.11 tests/chimerax_smoke.py --real-vina engines/vina_1.2.7_mac_aarch64
python3 validation/compare_direct_vina.py
```

For another platform, supply its Vina 1.2.7 executable to `--real-vina` and `--vina`. ChimeraX 1.12 on macOS Apple Silicon is the validated integration platform.

The recorded four poses have maximum energy difference 0, maximum ordered RMSD 0 Å and identical output SHA-256. This verifies conservation of engine output, not biological accuracy or full parity with a different PyMOL preparation workflow. Native model tests verify that the real pose retains all atoms. Offscreen tests do not validate OpenGL rendering.

The customization checks cover rotated local/scene transforms, resize anchors, mesh bounds, PDBQT preservation, validated presets and native Qt integration. Native integration also exercises residue specifications, moving inter-model distances and labels, actual mouse-event callbacks, restored mouse bindings, and render scene restoration after an exception.

The real oriented Vina run is recorded in [oriented/report.json](oriented/report.json). Two poses were generated with rotation (15°, 20°, 35°), and scene recovery had a maximum coordinate rounding error of 0.000714 Å. Input copies and raw scores were preserved. This verifies frame recovery; changing orientation can change the docking search and map discretization, so equal scores across orientations are not asserted. Reproduce it from the plugin root:

```bash
python3 validation/validate_oriented_vina.py --vina engines/vina_1.2.7_mac_aarch64
```

Real OpenGL export was additionally tested with the native macOS `cocoa` graphics platform on ChimeraX 1.12: 960×720 PNG, transparent RGBA PNG, and restoration of scene styling. The rendered synthetic test scene and image metadata are in `docs/screenshots/chipix-scene*`; the two atoms are test data. Run with ChimeraX Python on a graphical desktop:

```bash
QT_QPA_PLATFORM=cocoa python3.11 tests/chimerax_smoke.py --render-image docs/screenshots/chipix-scene.png
```

Use the native Qt graphics platform for your operating system. The offscreen Qt plugin cannot substitute for a functioning OpenGL context.

Guides: [English](../docs/en/DOCUMENTATION.md), [Español](../docs/es/DOCUMENTATION.md), [Deutsch](../docs/de/DOCUMENTATION.md), [Français](../docs/fr/DOCUMENTATION.md), [简体中文](../docs/zh/DOCUMENTATION.md), [日本語](../docs/ja/DOCUMENTATION.md), [Português](../docs/pt/DOCUMENTATION.md).

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
