#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare same-engine docking outputs from PyMOL and ChimeraX; no hosts needed."""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/"src"))
from core.formats import read_poses
from core.consensus import ordered_rmsd, symmetry_rmsd
from core.runner import digest


def compare(reference,candidate,mode="ordered",energy_tolerance=.001,rmsd_tolerance=.01,
            reference_field="",candidate_field=""):
    if any(not math.isfinite(v) or v < 0 for v in (energy_tolerance,rmsd_tolerance)):
        raise ValueError("Las tolerancias deben ser finitas y no negativas.")
    if mode not in ("ordered","symmetry"):
        raise ValueError("Modo RMSD desconocido.")
    a = sorted(read_poses(reference,reference_field),key=lambda p:(p.score,p.number))
    b = sorted(read_poses(candidate,candidate_field),key=lambda p:(p.score,p.number))
    distance = symmetry_rmsd if mode == "symmetry" else ordered_rmsd
    rows = []
    for rank,(p,q) in enumerate(zip(a,b),1):
        rmsd = distance(p,q)
        delta = abs(p.score-q.score)
        rows.append({"rank":rank,"reference_pose":p.number,"candidate_pose":q.number,
                     "reference_score":p.score,"candidate_score":q.score,
                     "energy_difference":delta,"rmsd":rmsd,
                     "passed":delta<=energy_tolerance and rmsd<=rmsd_tolerance})
    return {"reference":str(Path(reference).resolve()),"reference_sha256":digest(reference),
            "candidate":str(Path(candidate).resolve()),"candidate_sha256":digest(candidate),
            "reference_pose_count":len(a),"candidate_pose_count":len(b),"rmsd_mode":mode,
            "energy_tolerance":energy_tolerance,"rmsd_tolerance":rmsd_tolerance,
            "passed":len(a)==len(b) and all(row["passed"] for row in rows),"poses":rows}


def main():
    parser = argparse.ArgumentParser(description="Compara salidas del mismo motor obtenidas desde PyMOL y ChimeraX, por orden de score.")
    parser.add_argument("reference",help="Resultado de referencia PyMOL: PDBQT o SDF")
    parser.add_argument("candidate",help="Resultado ChimeraX: PDBQT o SDF")
    parser.add_argument("--rmsd-mode",choices=("ordered","symmetry"),default="ordered")
    parser.add_argument("--energy-tolerance",type=float,default=.001)
    parser.add_argument("--rmsd-tolerance",type=float,default=.01)
    parser.add_argument("--reference-field",default="")
    parser.add_argument("--candidate-field",default="")
    parser.add_argument("--report",help="Guardar informe JSON")
    args = parser.parse_args()
    try:
        report = compare(args.reference,args.candidate,args.rmsd_mode,args.energy_tolerance,
                         args.rmsd_tolerance,args.reference_field,args.candidate_field)
        result = json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
        if args.report:
            Path(args.report).write_text(result,encoding="utf-8")
        print(result,end="")
        return 0 if report["passed"] else 1
    except (ValueError,OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
