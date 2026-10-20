# SPDX-License-Identifier: GPL-3.0-or-later
"""All ChimeraX model/scene operations live at this boundary."""
from io import BytesIO, StringIO
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import tempfile
from .core.formats import pose_pdb
from .core.models import SearchBox
from .core.box_geometry import BoxStyle, box_bild


class ChimeraXHost:
    def __init__(self, session, translate=str):
        self.session = session
        self.tr = translate
        self.box_models = []
        self.pose_models = []
        self.distance_group = None
        self.box_style = BoxStyle()
        self.box = None
        self._distance_styles = {}

    def selection_box(self, padding, rotation=(0, 0, 0)):
        from chimerax.atomic import selected_atoms
        # Scene coordinates agree with PDB/Mol2 exports (including model transforms).
        return SearchBox.from_coordinates(selected_atoms(self.session).scene_coords, padding, rotation)

    def residue_box(self, specification, padding, rotation=(0, 0, 0), whole_residues=True):
        from chimerax.atomic import AtomsArg
        from chimerax.core.errors import UserError
        try:
            atoms, _, rest = AtomsArg.parse(specification.strip(), self.session)
        except (UserError, ValueError) as error:
            raise ValueError("Especificación de residuos inválida.") from error
        if rest.strip() or not len(atoms):
            raise ValueError("Especificación de residuos inválida.")
        if whole_residues:
            atoms = atoms.unique_residues.atoms
        return SearchBox.from_coordinates(atoms.scene_coords, padding, rotation)

    def _close(self, models):
        alive = [m for m in models if not m.deleted]
        if alive:
            self.session.models.close(alive)
        models.clear()

    def show_box(self, box, style=None):
        from chimerax.bild.bild import read_bild
        style = style or self.box_style
        bild = box_bild(box, style)  # Validate before replacing the visible box.
        models = []
        if bild:
            models,_ = read_bild(self.session,BytesIO(bild.encode()),self.tr("CHIPIX · caja"))
            self.session.models.add(models)
        self._close(self.box_models)
        self.box_models = models
        self.box, self.box_style = box, style

    def add_distance(self):
        from chimerax.atomic import selected_atoms
        atoms = selected_atoms(self.session)
        if len(atoms) != 2:
            raise ValueError("Selecciona exactamente dos átomos para medir una distancia.")
        group = self.distance_group
        if group is None or group.deleted:
            group = self.session.pb_manager.get_group('CHIPIX distances')
            self.session.models.add([group])
            self.distance_group = group
        for bond in group.pseudobonds:
            if set(bond.atoms) == set(atoms):
                return bond
        return group.new_pseudobond(*atoms)

    def distances(self):
        group = self.distance_group
        return list(group.pseudobonds) if group is not None and not group.deleted else []

    def style_distances(self, color=(.2, 1., .7), radius=.06, dashes=9, label_size=32, labels=True):
        bonds = self.distances()
        if not bonds:
            return
        from chimerax.label.label3d import labels_model, PseudobondLabel
        group = self.distance_group
        group.dashes = dashes
        rgba = tuple(round(v*255) for v in color)+(255,)
        existing = labels_model(group, create=False)
        if existing is None:
            self._distance_styles.clear()
        model = existing if existing is not None else labels_model(group, create=True)
        next_styles = {}
        for bond in bonds:
            text = f'{bond.length:.3f} Å' if labels else ''
            signature = (rgba, radius, dashes, label_size, text)
            next_styles[bond] = signature
            if self._distance_styles.get(bond) == signature:
                continue
            bond.color, bond.radius = rgba, radius
            model.add_labels([bond], PseudobondLabel, self.session.main_view,
                             settings={'text':text,
                                       'color':rgba, 'size':label_size, 'height':None})
        self._distance_styles = next_styles

    def clear_distances(self):
        if self.distance_group is not None and not self.distance_group.deleted:
            self.session.models.close([self.distance_group])
        self.distance_group = None
        self._distance_styles.clear()

    @contextmanager
    def image_scene(self, background=None, lighting=None, include_box=True, include_distances=True, include_handles=False):
        """Temporarily customize only the requested render and always restore the scene."""
        view = self.session.main_view
        old_background = view.background_color
        old_lighting = dict(vars(view.lighting))
        old_silhouette = {k:v for k,v in vars(view.silhouette).items() if not k.startswith('_')}
        old_box, old_style = self.box, self.box_style
        group = self.distance_group
        old_display = group.display if group is not None and not group.deleted else None
        try:
            self.apply_scene(background, lighting)
            if old_box:
                self.show_box(old_box, replace(old_style, mode=old_style.mode if include_box else 'hidden',
                                               handles=old_style.handles and include_handles))
            if old_display is not None:
                group.display = old_display and include_distances
            yield
        finally:
            view.background_color = old_background
            vars(view.lighting).update(old_lighting)
            vars(view.silhouette).update(old_silhouette)
            view.update_lighting = True
            view.redraw_needed = True
            if old_box:
                self.show_box(old_box, old_style)
            if old_display is not None and not group.deleted:
                group.display = old_display

    def apply_scene(self, background=None, lighting=None):
        if background is not None:
            self.session.main_view.background_color = tuple(background)+(1.,)
        if lighting:
            from chimerax.std_commands.lighting import lighting as set_lighting
            set_lighting(self.session, preset=lighting)

    def export_image(self, path, *, width=1920, height=1080, supersample=3, transparent=False, **scene):
        from chimerax.image_formats.save import save_image
        if transparent and Path(path).suffix.lower() not in ('.png', '.tif', '.tiff'):
            raise ValueError("El fondo transparente requiere PNG o TIFF.")
        path = Path(path)
        with tempfile.TemporaryDirectory(prefix='.chipix-image-',dir=path.parent) as temp:
            temporary = Path(temp)/path.name
            with self.image_scene(**scene):
                save_image(self.session, str(temporary), width=width, height=height, supersample=supersample,
                           transparent_background=transparent)
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise ValueError('No se pudo guardar la imagen 3D.')
            temporary.replace(path)

    def show_poses(self, entries):
        self._close(self.pose_models)
        colors = ((70,190,255,255),(255,150,60,255))
        for index,(run,pose) in enumerate(entries):
            title = f"{run.id} · pose {pose.number} · {pose.score:g}"
            if pose.format == "sdf":
                from chimerax.sdf.sdf import read_sdf
                models,_ = read_sdf(self.session,StringIO(pose.text),title)
            else:
                from chimerax.pdb import open_pdb
                models,_ = open_pdb(self.session,StringIO(pose_pdb(pose)),file_name=title)
            self.session.models.add(models)
            for model in models:
                model.name = title
                model.atoms.draw_modes = model.atoms.STICK_STYLE
                # Distinguish poses without losing heteroatom element colors.
                carbon = model.atoms.filter(model.atoms.element_names == "C")
                carbon.colors = colors[index % len(colors)]
            self.pose_models.extend(models)
        return self.pose_models

    def export_model(self, model, path):
        if model is None or model.deleted:
            raise ValueError("Selecciona un modelo molecular abierto.")
        from chimerax.pdb import save_pdb
        save_pdb(self.session,str(path),models=[model])

    def export_selected_ligand(self, path):
        from chimerax.atomic import selected_atoms
        from chimerax.mol2.io import write_mol2
        atoms = selected_atoms(self.session)
        if not len(atoms):
            raise ValueError("Selecciona los átomos de un único ligando.")
        if len(atoms.unique_structures) != 1:
            raise ValueError("Selecciona un ligando de un único modelo.")
        write_mol2(self.session,str(path),atoms=atoms)

    def dock_prep(self, model):
        if model is None or model.deleted:
            raise ValueError("Selecciona un modelo molecular abierto.")
        from chimerax.dock_prep.cmd import dock_prep_caller
        dock_prep_caller(self.session,[model],nogui=False)

    def close(self):
        self.clear_distances()
        self._close(self.box_models)
        self._close(self.pose_models)
