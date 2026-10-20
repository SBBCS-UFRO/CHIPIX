#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build complete offline language catalogs from reviewed translation rows."""
import json
from pathlib import Path
from string import Formatter

ROOT = Path(__file__).resolve().parents[1]
CODES = ('en','de','fr','zh','ja','pt')


def fields(text):
    return {field for _,field,_,_ in Formatter().parse(text) if field is not None}


def main():
    directory = ROOT/'src/locales'
    source = json.loads((directory/'_source.json').read_text(encoding='utf-8'))
    catalogs = {code:{} for code in (*CODES,'es')}
    seen = set()
    for line in (ROOT/'tools/translations.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        index,*values = line.split('|')
        index = int(index)
        if index in seen or len(values) != len(CODES):
            raise ValueError(f'Invalid translation row {index}')
        seen.add(index)
        key = source[index]
        for code,value in zip(CODES,values):
            if fields(value) != fields(key):
                raise ValueError(f'Placeholder mismatch: {code}, row {index}')
            catalogs[code][key] = value
        catalogs['es'][key] = key
    if seen != set(range(len(source))):
        raise ValueError(f'Missing translation rows: {set(range(len(source)))-seen}')
    catalogs['es'].update({'Score':'Puntuación','Rank by Rank':'Promedio de rangos (RbR)',
                           'Average of Auto-Scaled Scores':'Promedio de puntuaciones autoescaladas',
                           'Z-scores':'Puntuaciones Z'})
    for code,catalog in catalogs.items():
        (directory/f'{code}.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(source)} messages × {len(catalogs)} complete language catalogs')


if __name__ == '__main__':
    main()
