# SPDX-License-Identifier: GPL-3.0-or-later
"""Pairwise pose consensus, following DockingPie's RbR/AASS/Z-score equations.

Scores are normalized within each entire run, with population standard deviation.
Spatial comparisons never fit, rotate or translate the ligand independently.
"""
from dataclasses import asdict, dataclass
import csv
import itertools
import math
from statistics import fmean, pstdev

METHODS = ("rank", "autoscaled", "zscore")


def ordered_rmsd(first, second):
    a, b = first.heavy_atoms, second.heavy_atoms
    if not a or len(a) != len(b):
        raise ValueError("Las poses no tienen el mismo número de átomos pesados.")
    if first.format != second.format:
        raise ValueError("Para comparar formatos distintos usa SDF y RMSD por simetría.")
    keys_a = tuple((v.identity or v.name, v.name, v.element) for v in a)
    keys_b = tuple((v.identity or v.name, v.name, v.element) for v in b)
    if keys_a != keys_b or len({v.identity or v.name for v in a}) != len(a):
        raise ValueError("Identidad/orden de átomos diferente; usa SDF y RMSD por simetría.")
    return math.sqrt(sum(sum((u-v)**2 for u,v in zip(x.xyz,y.xyz)) for x,y in zip(a,b))/len(a))


def _graph(pose):
    if pose.format != "sdf":
        raise ValueError("El RMSD por simetría requiere SDF con enlaces explícitos.")
    indices = [i for i,a in enumerate(pose.atoms) if a.element not in ("H", "D")]
    mapping = {old: new for new, old in enumerate(indices)}
    neighbors = [set() for _ in indices]
    for a,b in pose.bonds:
        if a in mapping and b in mapping:
            x,y = mapping[a],mapping[b]
            neighbors[x].add(y)
            neighbors[y].add(x)
    atoms = [pose.atoms[i] for i in indices]
    return atoms, neighbors


def symmetry_rmsd(first, second, max_nodes=200000, cancelled=None):
    """Exact element/connectivity graph matching, like default spyrmsd adjacency.

    Bond orders and stereochemistry are not graph labels. Bound the search and
    fail explicitly if it cannot finish, rather than return an approximate RMSD.
    """
    a, ga = _graph(first)
    b, gb = _graph(second)
    if not a or len(a) != len(b):
        raise ValueError("Las poses no tienen el mismo número de átomos pesados.")
    def signature(atoms, graph, i):
        return atoms[i].element, len(graph[i]), tuple(sorted(atoms[j].element for j in graph[i]))
    sa = [signature(a,ga,i) for i in range(len(a))]
    sb = [signature(b,gb,i) for i in range(len(b))]
    choices = [[j for j,s in enumerate(sb) if s == key] for key in sa]
    if any(not c for c in choices):
        raise ValueError("Las poses tienen distinta conectividad molecular.")
    distance = [[sum((u-v)**2 for u,v in zip(x.xyz,y.xyz)) for y in b] for x in a]
    order = sorted(range(len(a)), key=lambda i: (len(choices[i]), -len(ga[i])))
    assigned, used, best, nodes = {}, set(), math.inf, 0
    def search(depth, cost):
        nonlocal best, nodes
        nodes += 1
        if cancelled and nodes % 1024 == 0 and cancelled():
            raise ValueError("Análisis cancelado.")
        if nodes > max_nodes:
            raise ValueError("La simetría excede el límite de búsqueda exacta; reduce el tamaño del análisis.")
        if cost >= best:
            return
        if depth == len(order):
            best = cost
            return
        i = order[depth]
        for j in sorted(choices[i], key=lambda j: distance[i][j]):
            if j in used or any((k in ga[i]) != (l in gb[j]) for k,l in assigned.items()):
                continue
            assigned[i] = j
            used.add(j)
            search(depth+1, cost+distance[i][j])
            used.remove(j)
            del assigned[i]
    search(0, 0.0)
    if not math.isfinite(best):
        raise ValueError("No existe correspondencia de conectividad entre las poses.")
    return math.sqrt(best/len(a))


def pose_scores(run, method):
    values = [p.score for p in run.poses]
    if not values or any(not math.isfinite(v) for v in values):
        raise ValueError("La ejecución contiene scores inválidos.")
    if method == "rank":
        # Stable ordinal ranks; equal energies retain the file's pose order.
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0]*len(values)
        for rank, index in enumerate(order, 1):
            ranks[index] = float(rank)
        return ranks
    if method == "autoscaled":
        low, high = min(values), max(values)
        if high == low:
            raise ValueError(f"{run.id}: AASS no está definido para scores constantes; usa Rank by Rank.")
        return [(v-low)/(high-low) for v in values]
    if method == "zscore":
        mean, std = fmean(values), pstdev(values)
        if std == 0:
            raise ValueError(f"{run.id}: Z-score no está definido para scores constantes; usa Rank by Rank.")
        return [(v-mean)/std for v in values]
    raise ValueError(f"Método de consenso desconocido: {method}")


@dataclass(frozen=True)
class ConsensusPair:
    run_a: str
    pose_a: int
    run_b: str
    pose_b: int
    ligand_id: str
    rmsd: object
    score_a: float
    score_b: float
    consensus: float
    method: str
    rmsd_mode: str
    rmsd_threshold: object
    context: str
    source_a_sha256: str
    source_b_sha256: str


def consensus(runs, method="rank", rmsd_mode="ordered", threshold=2.0, max_pairs=100000, cancelled=None):
    runs = tuple(runs)
    if len(runs) < 2 or len({r.id for r in runs}) != len(runs):
        raise ValueError("Selecciona al menos dos ejecuciones con identificadores únicos.")
    if rmsd_mode not in ("ordered", "symmetry", "none"):
        raise ValueError("Modo RMSD desconocido.")
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("El umbral RMSD debe ser finito y no negativo.")
    pairs = list(itertools.combinations(runs, 2))
    if any(not a.ligand_id or a.ligand_id != b.ligand_id for a,b in pairs):
        raise ValueError("El consenso de poses requiere el mismo ID de ligando en todas las ejecuciones.")
    if any(not a.context or a.context != b.context for a,b in pairs):
        raise ValueError("Las ejecuciones deben compartir ID de receptor/marco de coordenadas.")
    if sum(len(a.poses)*len(b.poses) for a,b in pairs) > max_pairs:
        raise ValueError("Demasiados pares de poses para un análisis interactivo.")
    scores = {r.id: pose_scores(r,method) for r in runs}
    rows = []
    distance = symmetry_rmsd if rmsd_mode == "symmetry" else ordered_rmsd
    for a,b in pairs:
        for i,p in enumerate(a.poses):
            for j,q in enumerate(b.poses):
                if cancelled and cancelled():
                    raise ValueError("Análisis cancelado.")
                if rmsd_mode == "none":
                    rmsd = None
                elif rmsd_mode == "symmetry":
                    rmsd = distance(p,q,cancelled=cancelled)
                else:
                    rmsd = distance(p,q)
                if rmsd is not None and rmsd > threshold:
                    continue
                rows.append(ConsensusPair(a.id,p.number,b.id,q.number,a.ligand_id,rmsd,
                                          p.score,q.score,fmean((scores[a.id][i],scores[b.id][j])),
                                          method,rmsd_mode,None if rmsd_mode == "none" else threshold,
                                          a.context,a.source_sha256,b.source_sha256))
    return sorted(rows,key=lambda row: (row.consensus, row.run_a, row.pose_a, row.run_b, row.pose_b))


def export_consensus(path, rows):
    with open(path,"w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(ConsensusPair.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
