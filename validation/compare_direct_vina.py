#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable comparison of native CHIPIX and direct Vina output."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from compare_results import compare


def main(reuse_output=False,executable=None):
    example=ROOT/'validation/1iep'
    settings=json.loads((example/'config.json').read_text())
    engine=Path(executable).resolve() if executable else ROOT/'engines/vina_1.2.7_mac_aarch64'
    output=example/'direct-vina.pdbqt'
    candidate=example/'reference-vina.pdbqt'
    locator=example/'chimerax-run-location.json'
    if locator.exists():
        manifest=example/json.loads(locator.read_text())['manifest']
        data=json.loads(manifest.read_text())
        candidate=manifest.parent/data['output']
    command=[str(engine),'--receptor',str(example/'1iep_receptor.pdbqt'),
             '--ligand',str(example/'1iep_ligand.pdbqt'),'--out',str(output)]
    for axis,center,size in zip('xyz',settings['center'],settings['size']):
        command.extend([f'--center_{axis}',str(center),f'--size_{axis}',str(size)])
    for option in ('exhaustiveness','num_modes','energy_range','seed','cpu'):
        command.extend([f'--{option}',str(settings[option])])
    if not reuse_output:
        with open(example/'direct-vina.log','w') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
    report=compare(output,candidate,energy_tolerance=0,rmsd_tolerance=0)
    report['reference']='validation/1iep/direct-vina.pdbqt'
    report['candidate']='validation/1iep/reference-vina.pdbqt'
    report['validation_kind']='native-chimerax-tool-vs-direct-engine'
    report['engine_version']=settings['engine_version']
    report['settings']=settings
    report['note']='Identical prepared inputs, seed, CPU and parameters. This does not compare a PyMOL execution or establish biological accuracy.'
    (example/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    if candidate != example/'reference-vina.pdbqt':
        import shutil
        shutil.copyfile(candidate,example/'reference-vina.pdbqt')
    print(json.dumps({'passed':report['passed'],'pose_count':report['candidate_pose_count'],
                      'max_energy_difference':max(row['energy_difference'] for row in report['poses']),
                      'max_rmsd':max(row['rmsd'] for row in report['poses'])},indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--reuse-output',action='store_true',help='Compare existing outputs without repeating docking')
    parser.add_argument('--vina',help='Compatible Vina 1.2.7 executable for this platform')
    args=parser.parse_args()
    raise SystemExit(main(args.reuse_output,args.vina))
