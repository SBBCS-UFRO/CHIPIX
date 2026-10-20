<img src="../../src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">

# CHIPIX 1.0.0

## Instalação

[English](../../docs/en/README.md) · [Español](../../docs/es/README.md) · [Deutsch](../../docs/de/README.md) · [Français](../../docs/fr/README.md) · [简体中文](../../docs/zh/README.md) · [日本語](../../docs/ja/README.md) · [Português](../../docs/pt/README.md)

## Requisitos

Requer ChimeraX 1.8 ou posterior. A integração foi testada no ChimeraX 1.12, Python 3.11 e Qt6 em macOS Apple Silicon. Outros sistemas e versões precisam de validação. A análise e a importação usam a biblioteca padrão do Python. Executar docking exige também um Vina ou Smina externo compatível e entradas PDBQT preparadas.

1. Baixe CHIPIX-1.0.0.zip e extraia seu conteúdo. Localize a pasta com bundle_info.xml, README.md e dist/.

2. Abra o ChimeraX e exiba sua linha de comando.

3. Execute o comando de instalação abaixo, substituindo o caminho pela pasta extraída. Use o wheel em dist/.

4. Execute chipix. A entrada do menu é Tools → Binding Analysis → CHIPIX.

5. Escolha English, Español, Deutsch, Français, 简体中文, 日本語 ou Português em Idioma. A escolha é salva.

6. Em Docking, selecione o executável do motor, os PDBQT preparados do receptor e do ligante e uma pasta de saída.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"
chipix
```

Este ZIP de código inclui o executável oficial Vina 1.2.7 para macOS Apple Silicon em engines/. O wheel contém somente o plugin. Para Windows, Linux ou Mac Intel, obtenha o motor oficial correspondente e selecione-o com Procurar. Smina é configurado separadamente. Se um binário copiado em macOS/Linux não tiver permissão de execução, aplique chmod +x a esse arquivo em um terminal.

Para atualizar, repita toolshed install com reinstall true e reinicie o ChimeraX. Para remover, use toolshed uninstall ChimeraX-CHIPIX. As pastas das execuções salvas são preservadas.

```text
toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true
toolshed uninstall ChimeraX-CHIPIX
```

```text
devel install "/FULL/PATH/CHIPIX-1.0.0" editable true
```

## GitHub

Para GitHub, extraia o ZIP e envie o conteúdo de CHIPIX-1.0.0 como raiz do repositório. Anexe o wheel de dist/ a uma GitHub Release para facilitar a instalação. A publicação é feita pelo proprietário do repositório; nenhuma URL GitHub é presumida.

© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO
