#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run real Vina in a rotated box and audit scene-coordinate recovery."""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from core.box_geometry import to_scene
from core.formats import read_poses
from core.models import SearchBox
from core.runner import DockingConfig, digest, execute


def main(executable=None):
    engine = Path(executable).resolve() if executable else ROOT/'engines/vina_1.2.7_mac_aarch64'
    example = ROOT/'validation/1iep'
    box = SearchBox((15.190,53.903,16.917),(20,20,20),(15,20,35))
    target = ROOT/'validation/oriented'
    target.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='chipix-oriented-') as temp:
        config = DockingConfig('vina',str(engine),str(example/'1iep_receptor.pdbqt'),
                               str(example/'1iep_ligand.pdbqt'),'imatinib-1iep','1iep-scene',box,
                               exhaustiveness=1,num_modes=3,energy_range=10,seed=42,cpu=1)
        result = execute(config,temp)
        manifest = Path(result.manifest)
        data = json.loads(manifest.read_text())
        raw_path = manifest.parent/'engine-poses.pdbqt'
        raw = read_poses(raw_path)
        error = max(math.dist(to_scene(box,a.xyz),b.xyz)
                    for p,q in zip(raw,result.poses) for a,b in zip(p.atoms,q.atoms))
        scores_equal = [p.score for p in raw] == [p.score for p in result.poses]
        inputs_preserved = all(digest(manifest.parent/name) == digest(example/('1iep_'+name))
                               for name in ('receptor.pdbqt','ligand.pdbqt'))
        # A 3D rounding error is bounded by sqrt(3)*0.0005 Å.
        passed = error <= .000867 and scores_equal and inputs_preserved
        for source,name in ((raw_path,'engine-poses.pdbqt'),(Path(result.source),'poses.pdbqt')):
            shutil.copyfile(source,target/name)
        report = {'passed':passed,'validation_kind':'real-vina-oriented-frame-recovery',
                  'engine':'Vina 1.2.7','engine_sha256':digest(engine),'pose_count':len(result.poses),
                  'box':data['config']['box'],'coordinate_frame':data['coordinate_frame'],
                  'max_coordinate_recovery_error_angstrom':error,'scores_preserved':scores_equal,
                  'prepared_inputs_preserved':inputs_preserved,'inputs_sha256':data['inputs'],
                  'engine_output':'validation/oriented/engine-poses.pdbqt',
                  'engine_output_sha256':data['engine_output_sha256'],
                  'scene_output':'validation/oriented/poses.pdbqt','scene_output_sha256':data['output_sha256'],
                  'parameters':{'exhaustiveness':1,'num_modes':3,'energy_range':10,'seed':42,'cpu':1},
                  'note':'Checks real engine execution and coordinate recovery. Does not assert score invariance under rotation or biological accuracy.'}
        (target/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('passed','pose_count','max_coordinate_recovery_error_angstrom','scores_preserved','prepared_inputs_preserved')},indent=2))
        return 0 if passed else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--vina',help='Compatible Vina executable for the current platform')
    raise SystemExit(main(parser.parse_args().vina))
