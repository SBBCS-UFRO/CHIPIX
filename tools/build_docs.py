#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate Markdown guides and offline ChimeraX help in all seven languages."""
from html import escape
from pathlib import Path
import shutil
from documentation_content import CONTENT
from customization_content import CUSTOMIZATION

ROOT = Path(__file__).resolve().parents[1]
CODES = ('en','es','de','fr','zh','ja','pt')
COPYRIGHT = '© 2026 Structural Bioinformatics & Bioactive Compound Synthesis Lab - UFRO'
INSTALL = 'toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl"\nchipix'
UPDATE = 'toolshed install "/FULL/PATH/CHIPIX-1.0.0/dist/chimerax_chipix-1.0.0-py3-none-any.whl" reinstall true'
BUILD = 'python3 -m unittest discover -s tests -v\n# ChimeraX Python:\npython3.11 build_bundle.py\npython3.11 tests/chimerax_smoke.py'
COMPARE = 'python3 compare_results.py pymol.pdbqt chipix.pdbqt \\\n  --energy-tolerance 0.001 --rmsd-tolerance 0.01 --report comparison.json'


def nav(prefix=''):
    return ' · '.join(f'[{CONTENT[code]["name"]}]({prefix}docs/{code}/README.md)' for code in CODES)


def banner(prefix=''):
    return f'<img src="{prefix}src/assets/chipix-logo.png" width="80" align="right" alt="CHIPIX laboratory logo">\n\n# CHIPIX 1.0.0\n\n'


def section(title,text):
    return f'## {title}\n\n{text}\n\n'


def bullets(values):
    return '\n'.join(f'- {value}' for value in values)


def numbered(values):
    return '\n\n'.join(f'{index}. {value}' for index,value in enumerate(values,1))


def readme(code,prefix=''):
    d=CONTENT[code]
    text=banner(prefix)+f'**{d["tagline"]}**\n\n{d["intro"]}\n\n{nav(prefix)}\n\n'
    text+=section(d['features'],bullets(d['feature_list']))
    title, paragraphs = CUSTOMIZATION[code]
    text+=section(title,paragraphs[0])
    text+=section(d['install'],d['steps'][0]+'\n\n'+d['steps'][1]+'\n\n'+d['steps'][2]+f'\n\n```text\n{INSTALL}\n```\n\n'+d['steps'][4])
    text+=f'[{d["install"]}]({prefix}docs/{code}/INSTALLATION.md) · [{d["guide"]}]({prefix}docs/{code}/DOCUMENTATION.md)\n\n'
    text+=f'![CHIPIX 1.0.0]({prefix}docs/screenshots/chipix-{code}.png)\n\n'
    text+=section(d['requirements'],d['requirement_text']+'\n\n'+d['engine_text'])
    text+=section(d['limits'],bullets(d['limit_list']))
    text+=section(d['validation'],d['validation_text'])
    text+=section('GitHub',d['github_text'])
    text+=section(d['credits'],d['credits_text']+'\n\n[DockingPie publication](https://doi.org/10.1093/bioinformatics/btac452) · [ChimeraX bundles](https://chimerax.readthedocs.io/en/latest/writing_bundles.html) · [AutoDock Vina](https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.7)')
    return text+COPYRIGHT+'\n'


def installation(code,prefix=''):
    d=CONTENT[code]
    return (banner(prefix)+f'## {d["install"]}\n\n{nav(prefix)}\n\n'+section(d['requirements'],d['requirement_text'])+
            numbered(d['steps'])+f'\n\n```text\n{INSTALL}\n```\n\n'+d['engine_text']+'\n\n'+d['upgrade']+
            f'\n\n```text\n{UPDATE}\ntoolshed uninstall ChimeraX-CHIPIX\n```\n\n'+
            '```text\ndevel install "/FULL/PATH/CHIPIX-1.0.0" editable true\n```\n\n'+
            section('GitHub',d['github_text'])+COPYRIGHT+'\n')


def documentation(code,prefix=''):
    d=CONTENT[code]
    text=banner(prefix)+f'## {d["guide"]}\n\n{nav(prefix)}\n\n{d["intro"]}\n\n'
    text+=section(d['workflow'],numbered(d['workflow_steps']))
    title, paragraphs = CUSTOMIZATION[code]
    text+=section(title,'\n\n'.join(paragraphs))
    text+=f'![CHIPIX]({prefix}docs/screenshots/chipix-customization-{code}.png)\n\n'
    text+=f'![CHIPIX]({prefix}docs/screenshots/chipix-image-{code}.png)\n\n'
    text+=section(d['methods'],d['method_text']+'\n\n'+d['rmsd_text'])
    text+=section(d['outputs'],d['output_text'])
    text+=section(d['languages'],d['steps'][4])
    text+=section(d['limits'],bullets(d['limit_list']))
    text+=section(d['validation'],d['validation_text']+'\n\n'+d['comparison_text']+f'\n\n```bash\n{COMPARE}\n```')
    text+=section(d['development'],d['development_text']+f'\n\n```bash\n{BUILD}\n```')
    text+=section(d['credits'],d['credits_text'])
    return text+COPYRIGHT+'\n'


def help_html(code):
    d=CONTENT[code]
    def p(value): return '<p>'+escape(value)+'</p>'
    def heading(value): return '<h2>'+escape(value)+'</h2>'
    def listing(values,tag='ul'): return '<'+tag+'>'+''.join('<li>'+escape(v)+'</li>' for v in values)+'</'+tag+'>'
    links=' · '.join(f'<a href="chipix{("-"+c) if c!="en" else ""}.html">{escape(CONTENT[c]["name"])}</a>' for c in CODES)
    text=f'''<!doctype html><html lang="{code}"><head><meta charset="utf-8"><title>CHIPIX 1.0.0 — {escape(d['guide'])}</title>
<style>body{{font:16px system-ui,sans-serif;line-height:1.6;max-width:980px;margin:2em auto;padding:0 1em;color:#182922;background:#fff}}header{{display:flex;align-items:center;gap:16px}}header img{{width:90px;height:48px;object-fit:cover}}h1,h2{{color:#178653}}pre{{padding:1em;background:#eef5f1;overflow:auto}}li{{margin:.5em 0}}footer{{font-size:12px;color:#53645a;margin-top:2em}}a{{color:#126c43}}</style></head><body>
<header><img src="chipix-logo.png" alt="CHIPIX laboratory logo"><h1>CHIPIX 1.0.0</h1></header><nav>{links}</nav>'''
    text+=p(d['intro'])+heading(d['install'])+listing(d['steps'],'ol')+'<pre>'+escape(INSTALL)+'</pre>'+p(d['requirement_text'])+p(d['engine_text'])
    text+=heading(d['workflow'])+listing(d['workflow_steps'],'ol')+heading(d['methods'])+p(d['method_text'])+p(d['rmsd_text'])
    title, paragraphs = CUSTOMIZATION[code]
    text+=heading(title)+''.join(p(value) for value in paragraphs)
    text+=heading(d['outputs'])+p(d['output_text'])+heading(d['limits'])+listing(d['limit_list'])
    text+=heading(d['validation'])+p(d['validation_text'])+p(d['comparison_text'])+'<pre>'+escape(COMPARE)+'</pre>'
    text+=heading(d['credits'])+p(d['credits_text'])+'<footer>'+escape(COPYRIGHT)+'</footer></body></html>\n'
    return text


def main():
    if set(CONTENT)!=set(CODES):
        raise ValueError('Incomplete documentation languages')
    expected=set(CONTENT['en'])
    for code in CODES:
        if set(CONTENT[code])!=expected:
            raise ValueError(f'Incomplete documentation fields: {code}')
        directory=ROOT/'docs'/code
        directory.mkdir(parents=True,exist_ok=True)
        for filename,builder in [('README.md',readme),('INSTALLATION.md',installation),('DOCUMENTATION.md',documentation)]:
            (directory/filename).write_text(builder(code,'../../'),encoding='utf-8')
        filename='README.md' if code=='en' else f'README.{code}.md'
        (ROOT/filename).write_text(readme(code),encoding='utf-8')
    for filename,builder in [('INSTALLATION.md',installation),('DOCUMENTATION.md',documentation)]:
        (ROOT/filename).write_text(builder('en'),encoding='utf-8')
    help_dir=ROOT/'src/docs/user/tools'
    help_dir.mkdir(parents=True,exist_ok=True)
    for obsolete in ('dockingpie.html',):
        (help_dir/obsolete).unlink(missing_ok=True)
    for code in CODES:
        filename='chipix.html' if code=='en' else f'chipix-{code}.html'
        (help_dir/filename).write_text(help_html(code),encoding='utf-8')
    shutil.copy2(ROOT/'src/assets/chipix-logo.png',help_dir/'chipix-logo.png')
    print('Generated README, installation, documentation and offline help in seven languages')


if __name__=='__main__':
    main()
