# SPDX-License-Identifier: GPL-3.0-or-later
"""Strict readers: missing scores never become artificial zero energies."""
import math
from pathlib import Path
import re
from .models import Atom, Pose

_AD_ELEMENTS = {"A": "C", "C": "C", "N": "N", "NA": "N", "NS": "N",
                "OA": "O", "OS": "O", "O": "O", "S": "S", "SA": "S",
                "HD": "H", "HS": "H", "H": "H", "F": "F", "Cl": "Cl",
                "CL": "Cl", "Br": "Br", "BR": "Br", "I": "I", "P": "P",
                "Zn": "Zn", "ZN": "Zn", "Mg": "Mg", "MG": "Mg",
                "Mn": "Mn", "MN": "Mn", "Fe": "Fe", "FE": "Fe",
                "Ca": "Ca", "CA": "Ca", "Cu": "Cu", "CU": "Cu"}


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Se encontró un valor no finito en el archivo molecular.")
    return result


def read_poses(path, score_field=""):
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".pdbqt":
        return parse_pdbqt(content)
    if path.suffix.lower() in (".sdf", ".sd"):
        return parse_sdf(content, score_field)
    raise ValueError("Formato admitido: PDBQT o SDF V2000.")


def parse_pdbqt(content):
    blocks, current, explicit = [], [], False
    for line in content.splitlines():
        if line.startswith("MODEL "):
            if explicit or any(s.startswith(("ATOM  ", "HETATM")) for s in current):
                raise ValueError("Bloques MODEL anidados o incompletos.")
            current, explicit = [], True
        elif line.startswith("ENDMDL"):
            blocks.append(current)
            current, explicit = [], False
        else:
            current.append(line)
    if explicit:
        raise ValueError("Falta ENDMDL en el resultado PDBQT.")
    if any(line.startswith(("ATOM  ", "HETATM")) for line in current):
        blocks.append(current)
    poses = []
    for index, lines in enumerate(blocks, 1):
        atoms, score = [], None
        for line in lines:
            if line.startswith("REMARK VINA RESULT:"):
                fields = line.split(":", 1)[1].split()
                if not fields:
                    raise ValueError(f"Pose {index}: REMARK VINA RESULT no contiene score.")
                score = finite_float(fields[0])
            elif line.startswith(("ATOM  ", "HETATM")):
                atom_type = line[77:].strip().split()[0] if len(line) > 77 else line.split()[-1]
                if atom_type not in _AD_ELEMENTS:
                    raise ValueError(f"Tipo AutoDock no admitido: {atom_type}. Usa SDF para analizar esta molécula.")
                atoms.append(Atom(line[12:16].strip(), _AD_ELEMENTS[atom_type],
                                  tuple(finite_float(line[a:b]) for a, b in ((30, 38), (38, 46), (46, 54))),
                                  line[6:11].strip()))
        if score is None or not atoms:
            raise ValueError(f"Pose {index}: faltan átomos o REMARK VINA RESULT. Para ADFR usa SDF con su campo de score.")
        poses.append(Pose(index, score, tuple(atoms), (), "\n".join(lines)+"\n", "pdbqt"))
    if not poses:
        raise ValueError("No se encontraron poses PDBQT.")
    return tuple(poses)


def parse_sdf(content, score_field=""):
    poses = []
    for record in content.split("$$$$"):
        if not record.strip():
            continue
        # Preserve the possibly blank molecule title and both header lines.
        if poses and record.startswith("\r\n"):
            record = record[2:]
        elif poses and record.startswith("\n"):
            record = record[1:]
        lines = record.splitlines()
        if len(lines) < 4 or "V2000" not in lines[3]:
            raise ValueError("Se requiere SDF V2000; convierte V3000 conservando enlaces y scores.")
        try:
            na, nb = int(lines[3][:3]), int(lines[3][3:6])
            if na <= 0 or nb < 0 or len(lines) < 4+na+nb:
                raise ValueError("Conteos SDF inválidos.")
            atoms = tuple(Atom(str(i+1), line[31:34].strip(),
                               tuple(finite_float(line[a:b]) for a, b in ((0, 10), (10, 20), (20, 30))))
                          for i, line in enumerate(lines[4:4+na]))
            bonds = tuple((int(line[:3])-1, int(line[3:6])-1) for line in lines[4+na:4+na+nb])
        except (IndexError, ValueError) as error:
            raise ValueError(f"Registro SDF {len(poses)+1} inválido: {error}") from error
        if any(not a.element for a in atoms) or any(a == b or min(a,b) < 0 or max(a,b) >= na for a,b in bonds):
            raise ValueError("Elementos o enlaces SDF inválidos.")
        if not any(line.strip() == "M  END" for line in lines[4+na+nb:]):
            raise ValueError("Falta M  END en el registro SDF.")
        properties = {}
        for i, line in enumerate(lines):
            match = re.match(r">\s*<([^>]+)>", line)
            if match and i+1 < len(lines):
                properties[match.group(1)] = lines[i+1].strip()
        fields = [score_field] if score_field else ["minimizedAffinity", "SCORE", "vina_affinity", "affinity"]
        found = next((key for key in fields if key in properties), None)
        if found is None:
            raise ValueError(f"Registro SDF {len(poses)+1}: falta el campo de score {score_field or '/'.join(fields)}.")
        poses.append(Pose(len(poses)+1, finite_float(properties[found]), atoms, bonds,
                          "\n".join(lines)+"\n$$$$\n", "sdf"))
    if not poses:
        raise ValueError("No se encontraron poses SDF.")
    return tuple(poses)


def pose_pdb(pose):
    """Coordinates for display only; never use this PDB for docking preparation."""
    lines = []
    for i, atom in enumerate(pose.atoms, 1):
        x, y, z = atom.xyz
        # PDBQT often names every carbon "C"; unique PDB names avoid treating
        # these as duplicate atoms/alternate locations within the display residue.
        name = (atom.element+str(i))[:4]
        lines.append(f"HETATM{i:5d} {name:>4s} LIG A   1    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {atom.element:>2s}")
    for a, b in pose.bonds:
        lines.append(f"CONECT{a+1:5d}{b+1:5d}")
    return "\n".join(lines)+"\nEND\n"
