# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Atom:
    name: str
    element: str
    xyz: tuple
    identity: str = ""


@dataclass(frozen=True)
class Pose:
    number: int
    score: float
    atoms: tuple
    bonds: tuple
    text: str
    format: str

    @property
    def heavy_atoms(self):
        return tuple(a for a in self.atoms if a.element not in ("H", "D"))


@dataclass(frozen=True)
class DockingRun:
    id: str
    engine: str
    ligand_id: str
    context: str
    poses: tuple
    source: str
    manifest: str = ""
    source_sha256: str = ""


@dataclass(frozen=True)
class SearchBox:
    center: tuple
    size: tuple
    rotation: tuple = (0.0, 0.0, 0.0)

    def __post_init__(self):
        if len(self.center) != 3 or len(self.size) != 3 or len(self.rotation) != 3:
            raise ValueError("La caja necesita tres coordenadas y tres dimensiones.")
        if not all(math.isfinite(v) for v in (*self.center, *self.size, *self.rotation)):
            raise ValueError("La caja contiene valores no finitos.")
        if any(v <= 0 for v in self.size):
            raise ValueError("Las dimensiones de la caja deben ser positivas (Å).")

    @classmethod
    def from_coordinates(cls, coordinates, padding=4.0, rotation=(0.0, 0.0, 0.0)):
        from .box_geometry import apply, rotation_matrix, transpose
        points = tuple(tuple(float(v) for v in point) for point in coordinates)
        if not points or not math.isfinite(padding) or padding <= 0:
            raise ValueError("Selecciona átomos y usa un margen positivo.")
        if any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in points):
            raise ValueError("Coordenadas de selección inválidas.")
        matrix = rotation_matrix(rotation)
        points = tuple(apply(transpose(matrix), p) for p in points)
        lo = tuple(min(p[i] for p in points) for i in range(3))
        hi = tuple(max(p[i] for p in points) for i in range(3))
        return cls(apply(matrix, tuple((a+b)/2 for a, b in zip(lo, hi))),
                   tuple(b-a+2*padding for a, b in zip(lo, hi)), tuple(rotation))
