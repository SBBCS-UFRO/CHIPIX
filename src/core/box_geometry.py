# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene/local box geometry, independent of Qt and ChimeraX."""
from dataclasses import dataclass
import itertools
import math


def apply(matrix, point):
    return tuple(sum(a*b for a, b in zip(row, point)) for row in matrix)


def transpose(matrix):
    return tuple(zip(*matrix))


def rotation_matrix(angles):
    if len(angles) != 3 or not all(math.isfinite(a) for a in angles):
        raise ValueError("La caja contiene valores no finitos.")
    x, y, z = (math.radians(a) for a in angles)
    cx, cy, cz, sx, sy, sz = math.cos(x), math.cos(y), math.cos(z), math.sin(x), math.sin(y), math.sin(z)
    # Column vectors, intrinsic XYZ (Rz Ry Rx), degrees.
    return ((cz*cy, cz*sy*sx-sz*cx, cz*sy*cx+sz*sx),
            (sz*cy, sz*sy*sx+cz*cx, sz*sy*cx-cz*sx), (-sy, cy*sx, cy*cx))


def to_scene(box, point):
    return tuple(a+b for a, b in zip(apply(rotation_matrix(box.rotation), point), box.center))


def to_local(box, point):
    return apply(transpose(rotation_matrix(box.rotation)), tuple(a-b for a, b in zip(point, box.center)))


CORNERS = tuple(itertools.product((-1, 1), repeat=3))
FACES = tuple(tuple(sign if i == axis else 0 for i in range(3)) for axis in range(3) for sign in (-1, 1))


def handles(box):
    return [(signs, to_scene(box, tuple(s*v/2 for s, v in zip(signs, box.size))))
            for signs in (*CORNERS, *FACES, (0, 0, 0))]


def resize(box, signs, scene_delta):
    """Drag a corner or face; the opposite face/corner stays fixed."""
    from .models import SearchBox
    delta = apply(transpose(rotation_matrix(box.rotation)), scene_delta)
    size = tuple(max(.01, old + s*d) if s else old for old, s, d in zip(box.size, signs, delta))
    shift = apply(rotation_matrix(box.rotation), tuple(s*(new-old)/2 for s, new, old in zip(signs, size, box.size)))
    return SearchBox(tuple(a+b for a, b in zip(box.center, shift)), size, box.rotation)


def pick_handle(box, start, end, radius):
    direction = tuple(b-a for a, b in zip(start, end))
    norm = sum(v*v for v in direction)
    if not norm:
        return None
    hits = []
    for signs, center in handles(box):
        t = sum((c-a)*d for c, a, d in zip(center, start, direction))/norm
        if 0 <= t <= 1:
            d2 = sum((a+t*d-c)**2 for a, d, c in zip(start, direction, center))
            if d2 <= radius*radius:
                hits.append((t, signs))
    return min(hits)[1] if hits else None


@dataclass(frozen=True)
class BoxStyle:
    mode: str = 'outline'
    color: tuple = (1.0, .75, .1)
    radius: float = .08
    spacing: float = 2.0
    opacity: float = .3
    rounded: bool = True
    handles: bool = True
    handle_radius: float = .45
    handle_color: tuple = (.15, .8, .65)

    def __post_init__(self):
        if self.mode not in ('outline', 'mesh', 'solid', 'hidden'):
            raise ValueError("Estilo de caja inválido.")
        values = (*self.color, *self.handle_color, self.radius, self.spacing, self.opacity, self.handle_radius)
        if len(self.color) != 3 or len(self.handle_color) != 3 or not all(math.isfinite(v) for v in values):
            raise ValueError("Estilo de caja inválido.")
        if not all(0 <= v <= 1 for v in (*self.color, *self.handle_color, self.opacity)) or not (.01 <= self.radius <= 2 and .1 <= self.spacing <= 1000 and .05 <= self.handle_radius <= 5):
            raise ValueError("Estilo de caja inválido.")
        if type(self.rounded) is not bool or type(self.handles) is not bool:
            raise ValueError("Estilo de caja inválido.")


def box_bild(box, style):
    """Rounded joins are visual; the scientific boundary stays rectangular."""
    if style.mode == 'hidden':
        return ''
    def coords(p):
        return ' '.join(f'{v:.8g}' for v in to_scene(box, p))
    points = {s:tuple(a*b/2 for a, b in zip(s, box.size)) for s in CORNERS}
    lines = ['.color ' + ' '.join(str(v) for v in style.color)]
    def cylinder(a, b, radius):
        lines.append(f'.cylinder {coords(a)} {coords(b)} {radius:g}')
    for i, a in enumerate(CORNERS):
        for b in CORNERS[i+1:]:
            if sum(x != y for x, y in zip(a, b)) == 1:
                cylinder(points[a], points[b], style.radius)
    if style.rounded:
        for p in points.values():
            lines.append(f'.sphere {coords(p)} {style.radius:g}')
    if style.mode == 'mesh':
        # Bound geometry independently of box size and the requested spacing.
        count = sum(max(0, math.ceil(v/style.spacing)-1) for v in box.size)*4
        if count > 4000:
            raise ValueError("La malla es demasiado densa; aumenta su espaciado.")
        for axis in range(3):
            others = [i for i in range(3) if i != axis]
            for j in range(1, math.ceil(box.size[axis]/style.spacing)):
                value = -box.size[axis]/2+j*style.spacing
                for fixed, varying in (others, others[::-1]):
                    for sign in (-1, 1):
                        a, b = [0.0]*3, [0.0]*3
                        a[axis] = b[axis] = value
                        a[fixed] = b[fixed] = sign*box.size[fixed]/2
                        a[varying], b[varying] = -box.size[varying]/2, box.size[varying]/2
                        cylinder(a, b, style.radius*.45)
    if style.mode == 'solid':
        lines.append(f'.transparency {1-style.opacity:g}')
        for axis in range(3):
            other = [i for i in range(3) if i != axis]
            for sign in (-1, 1):
                face = []
                for u, v in ((-1,-1),(1,-1),(1,1),(-1,1)):
                    p = [0.0]*3
                    p[axis], p[other[0]], p[other[1]] = sign*box.size[axis]/2, u*box.size[other[0]]/2, v*box.size[other[1]]/2
                    face.append(coords(p))
                lines.append('.polygon ' + ' '.join(face))
        lines.append('.transparency 0')
    if style.handles:
        lines.append('.color ' + ' '.join(str(v) for v in style.handle_color))
        for signs, center in handles(box):
            lines.append('.sphere ' + ' '.join(f'{v:.8g}' for v in center) + f' {style.handle_radius:g}')
    return '\n'.join(lines)+'\n'


def transform_pdbqt(text, box, inverse=False):
    """Transform only fixed-column coordinates, retaining torsion/scoring records."""
    output = []
    for line in text.splitlines(keepends=True):
        if line.startswith(('ATOM  ', 'HETATM')):
            try:
                point = tuple(float(line[i:i+8]) for i in (30, 38, 46))
                result = to_scene(box, point) if inverse else to_local(box, point)
                fields = tuple(f'{v:8.3f}' for v in result)
                if any(len(f) != 8 for f in fields) or not all(math.isfinite(v) for v in result):
                    raise ValueError()
            except (ValueError, IndexError) as error:
                raise ValueError("Coordenadas PDBQT inválidas para transformar la caja.") from error
            line = line[:30]+''.join(fields)+line[54:]
        output.append(line)
    return ''.join(output)
