<img src="../../src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">

# CHIPIX 1.0.0

## Instalación

[English](../../docs/en/README.md) · [Español](../../docs/es/README.md) · [Deutsch](../../docs/de/README.md) · [Français](../../docs/fr/README.md) · [简体中文](../../docs/zh/README.md) · [日本語](../../docs/ja/README.md) · [Português](../../docs/pt/README.md)

## Requisitos

Requiere ChimeraX 1.8 o posterior. La integración se probó con ChimeraX 1.12, Python 3.11 y Qt6 en macOS Apple Silicon. Otros sistemas y versiones necesitan validación. El análisis y la importación usan la biblioteca estándar de Python. Para ejecutar docking se necesita además un Vina o Smina compatible y entradas PDBQT preparadas.

1. Descarga CHIPIX-1.0.0.zip y descomprímelo. Localiza la carpeta que contiene bundle_info.xml, README.md y dist/.

2. Abre ChimeraX y muestra su línea de comandos.

3. Ejecuta el comando de instalación siguiente, sustituyendo la ruta por la carpeta extraída. Usa el archivo wheel de dist/.

4. Ejecuta chipix. La entrada de menú es Tools → Binding Analysis → CHIPIX.

5. Elige English, Español, Deutsch, Français, 简体中文, 日本語 o Português en Idioma. La elección queda guardada.

6. En Docking, selecciona el ejecutable del motor, los PDBQT preparados del receptor y del ligando y una carpeta de salida.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"
chipix
```

Este ZIP de código incluye el ejecutable oficial Vina 1.2.7 para macOS Apple Silicon en engines/. El wheel contiene únicamente el complemento. Para Windows, Linux o Mac Intel, obtén el motor correspondiente desde su distribución oficial y selecciónalo con Examinar. Smina se configura aparte. Si un ejecutable copiado en macOS/Linux no tiene permiso de ejecución, aplica chmod +x a ese archivo desde una terminal.

Para actualizar, repite toolshed install con reinstall true y reinicia ChimeraX. Para quitar el complemento, usa toolshed uninstall ChimeraX-CHIPIX. Las carpetas de ejecuciones guardadas se conservan.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true
toolshed uninstall ChimeraX-CHIPIX
```

```text
devel install "/FULL/PATH/CHIPIX-1.0.0" editable true
```

## GitHub

Para GitHub, descomprime el ZIP y sube el contenido de CHIPIX-1.0.0 como raíz del repositorio. Adjunta el wheel de dist/ a una GitHub Release para facilitar la instalación. La publicación la realiza el propietario del repositorio; no se presupone una URL de GitHub.

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
