# SPDX-License-Identifier: GPL-3.0-or-later
"""Native customization panels. Scientific box coordinates stay in the scene frame."""
import csv
from dataclasses import asdict
import json
from pathlib import Path
from Qt.QtCore import QTimer, Qt
from Qt.QtGui import QColor, QIcon, QPixmap
from Qt.QtWidgets import QCheckBox, QColorDialog, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QSizePolicy, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget
from .core.box_geometry import BoxStyle, box_bild
from .core.models import SearchBox
from .core.runner import write_json


class CustomizationMixin:
    def _collapsible(self, title):
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        toggle = QToolButton()
        toggle.setCheckable(True)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        toggle.setStyleSheet('QToolButton { text-align: left; padding: 6px; }')
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 4, 0, 6)
        body.setVisible(False)

        def update():
            toggle.setText(('− ' if toggle.isChecked() else '+ ') + self.tr(title))
            toggle.setAccessibleName(self.tr(title))

        def expand(checked):
            body.setVisible(checked)
            update()

        toggle.toggled.connect(expand)
        self._text_bindings.append(update)
        update()
        layout.addWidget(toggle)
        layout.addWidget(body)
        return section, toggle, body, body_layout

    def _check(self, text, checked=True):
        widget = QCheckBox(self.tr(text))
        widget.setChecked(checked)
        self._text_bindings.append(lambda:widget.setText(self.tr(text)))
        return widget

    def _combo(self, entries):
        widget = QComboBox()
        for text, value in entries:
            self._combo_item(widget, text, value)
        return widget

    def _color_button(self, attr, initial):
        setattr(self, attr, initial)
        button = self._button('Elegir color…', lambda:self._choose_color(attr, button))
        self._paint_color(button, initial)
        return button

    @staticmethod
    def _paint_color(button, rgb):
        css = ','.join(str(round(v*255)) for v in rgb)
        button.setStyleSheet(f'QPushButton {{ border-left: 12px solid rgb({css}); padding: 4px; }}')
        swatch = QPixmap(18,18)
        swatch.fill(QColor.fromRgbF(*rgb))
        button.setIcon(QIcon(swatch))

    def _choose_color(self, attr, button):
        color = QColorDialog.getColor(QColor.fromRgbF(*getattr(self, attr)), self.tool_window.ui_area)
        if color.isValid():
            value = (color.redF(), color.greenF(), color.blueF())
            setattr(self, attr, value)
            self._paint_color(button, value)
            if attr == 'background_rgb':
                self.background.setCurrentIndex(self.background.findData('custom'))
            self._queue_box()
            self._refresh_distances()

    def _box_controls(self, layout):
        self.rotation_section, self.rotation_toggle, self.rotation_body, rotation_layout = self._collapsible('Rotación XYZ (°)')
        self.rotations = []
        row = QWidget()
        horizontal = QHBoxLayout(row)
        horizontal.setContentsMargins(0,0,0,0)
        for axis in 'XYZ':
            horizontal.addWidget(self._label(axis))
            spin = self._decimal(0, -180, 180)
            spin.setSingleStep(5)
            horizontal.addWidget(spin)
            self.rotations.append(spin)
        rotation_layout.addWidget(row)
        rotation_layout.addWidget(self._button('Restablecer orientación', self._reset_rotation))
        layout.addWidget(self.rotation_section)
        self.residue_section, self.residue_toggle, self.residue_body, residue_layout = self._collapsible('Residuos o especificación de átomos')
        self.residue_spec = QLineEdit()
        self._placeholder(self.residue_spec, '#1/A:45,67-72')
        residue_layout.addWidget(self.residue_spec)
        self.whole_residues = self._check('Incluir residuos completos')
        residue_layout.addWidget(self.whole_residues)
        residue_layout.addWidget(self._button('Definir caja desde residuos', self._box_from_residues))
        layout.addWidget(self.residue_section)

    def _box_customization(self, preparation_layout):
        self.box_options, self.box_options_toggle, self.box_options_body, layout = self._collapsible('Personalizar caja')
        preparation_layout.addWidget(self.box_options)
        layout.addWidget(self._label('Los cambios de caja se muestran en vivo. Las esferas son manejadores; la frontera de búsqueda sigue siendo rectangular.'))
        form = QFormLayout()
        self.box_mode = self._combo([('Contorno', 'outline'), ('Malla superficial', 'mesh'),
                                     ('Caras transparentes', 'solid'), ('Oculta', 'hidden')])
        self._form_row(form, 'Aspecto de la caja', self.box_mode)
        self.box_color_button = self._color_button('box_rgb', (1.,.75,.1))
        self._form_row(form, 'Color de la caja', self.box_color_button)
        self.handle_color_button = self._color_button('handle_rgb', (.15,.8,.65))
        self._form_row(form, 'Color de manejadores', self.handle_color_button)
        self.edge_radius = self._decimal(.08, .01, 2)
        self.mesh_spacing = self._decimal(2, .1, 1000)
        self.face_opacity = self._decimal(.3, 0, 1)
        self.handle_radius = self._decimal(.45, .05, 5)
        for text, control in [('Radio de aristas (Å)', self.edge_radius), ('Espaciado visual de malla (Å)', self.mesh_spacing),
                              ('Opacidad de caras (0–1)', self.face_opacity), ('Radio de manejadores (Å)', self.handle_radius)]:
            self._form_row(form, text, control)
        self.rounded_edges = self._check('Uniones redondeadas')
        self.show_handles = self._check('Mostrar manejadores esféricos')
        form.addRow(self.rounded_edges)
        form.addRow(self.show_handles)
        self.move_step = self._decimal(1., .01, 100)
        self._form_row(form, 'Paso de movimiento (Å)', self.move_step)
        layout.addLayout(form)
        nudges = QHBoxLayout()
        for axis in range(3):
            for sign in (-1, 1):
                nudges.addWidget(self._button(f'{"XYZ"[axis]} {"−" if sign < 0 else "+"}', lambda a=axis,s=sign:self._nudge_box(a,s)))
        layout.addLayout(nudges)
        scaling = QHBoxLayout()
        scaling.addWidget(self._button('Reducir 10 %', lambda:self._scale_box(.9)))
        scaling.addWidget(self._button('Ampliar 10 %', lambda:self._scale_box(1.1)))
        layout.addLayout(scaling)
        mouse_form = QFormLayout()
        self.mouse_operation = self._combo([('Mover', 'move'), ('Redimensionar desde una esfera', 'resize'), ('Rotar', 'rotate')])
        self._form_row(mouse_form, 'Acción del botón derecho', self.mouse_operation)
        layout.addLayout(mouse_form)
        self.mouse_enabled = self._check('Editar caja con botón derecho', False)
        layout.addWidget(self.mouse_enabled)
        layout.addWidget(self._label('Arrastra con el botón derecho. Mayús permite mover en profundidad o rotar Z. Para redimensionar, arrastra una esfera de cara o esquina; la cara opuesta queda fija.'))
        layout.addWidget(self._label('La malla es una ayuda visual; su espaciado no cambia la discretización del motor.'))
        presets = QHBoxLayout()
        presets.addWidget(self._button('Guardar personalización…', self._save_customization))
        presets.addWidget(self._button('Cargar personalización…', self._load_customization))
        layout.addLayout(presets)
        self._mouse_mode, self._mouse_bindings = None, []
        self._box_timer = QTimer(self.tool_window.ui_area)
        self._box_timer.setSingleShot(True)
        self._box_timer.setInterval(60)
        self._box_timer.timeout.connect(self._safe(self._show_custom_box))
        for widget in (*self.centers, *self.sizes, *self.rotations, self.edge_radius, self.mesh_spacing, self.face_opacity, self.handle_radius):
            widget.valueChanged.connect(self._queue_box)
        for widget in (self.rounded_edges, self.show_handles):
            widget.toggled.connect(self._queue_box)
        self.box_mode.currentIndexChanged.connect(self._queue_box)
        self.mouse_enabled.toggled.connect(self._safe(self._toggle_box_mouse))

    def _customization_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        scene = QFormLayout()
        self.background = self._combo([('Fondo actual', 'current'), ('Blanco', 'white'), ('Negro', 'black'),
                                       ('Gris pizarra', 'slate'), ('Color personalizado', 'custom')])
        self._form_row(scene, 'Fondo', self.background)
        self.background_button = self._color_button('background_rgb', (.15,.18,.22))
        self._form_row(scene, 'Color de fondo', self.background_button)
        self.lighting = self._combo([('Iluminación actual', 'current'), ('Simple', 'simple'), ('Suave', 'soft'),
                                     ('Completa con sombras', 'full'), ('Plana', 'flat'), ('Predeterminada', 'default')])
        self._form_row(scene, 'Iluminación', self.lighting)
        layout.addLayout(scene)
        layout.addWidget(self._button('Aplicar fondo e iluminación a la vista', self._apply_scene))
        layout.addWidget(self._label('Exportar usa estas opciones temporalmente y después restaura la vista.'))
        export = QFormLayout()
        self.image_width, self.image_height = self._integer(1920,64,8192), self._integer(1080,64,8192)
        self.supersample = self._integer(3,1,4)
        self._form_row(export, 'Ancho (píxeles)', self.image_width)
        self._form_row(export, 'Alto (píxeles)', self.image_height)
        self._form_row(export, 'Suavizado por sobremuestreo', self.supersample)
        layout.addLayout(export)
        self.transparent_image = self._check('Fondo transparente (PNG/TIFF)', False)
        self.image_box = self._check('Incluir caja en la imagen')
        self.image_handles = self._check('Incluir manejadores en la imagen', False)
        self.image_distances = self._check('Incluir distancias en la imagen')
        for widget in (self.transparent_image, self.image_box, self.image_handles, self.image_distances):
            layout.addWidget(widget)
        layout.addWidget(self._button('Exportar imagen 3D…', self._export_scene_image))
        layout.addStretch()
        self._tab(page, 'Escena e imagen')

    def _measurement_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._label('Selecciona exactamente dos átomos en ChimeraX; pueden pertenecer a modelos distintos. Las distancias se actualizan al mover los modelos.'))
        form = QFormLayout()
        self.distance_color_button = self._color_button('distance_rgb', (.2,1.,.7))
        self._form_row(form, 'Color de distancias', self.distance_color_button)
        self.distance_radius = self._decimal(.06,.01,2)
        self.distance_dashes = self._integer(9,0,50)
        self.distance_label_size = self._integer(32,8,128)
        self._form_row(form, 'Radio de líneas (Å)', self.distance_radius)
        self._form_row(form, 'Guiones (0 = línea continua)', self.distance_dashes)
        self._form_row(form, 'Tamaño de etiquetas', self.distance_label_size)
        self.distance_labels = self._check('Mostrar valores en 3D')
        form.addRow(self.distance_labels)
        layout.addLayout(form)
        layout.addWidget(self._button('Medir entre dos átomos seleccionados', self._add_distance))
        self.distance_table = self._table(['Átomo A', 'Átomo B', 'Distancia (Å)'])
        layout.addWidget(self.distance_table)
        buttons = QHBoxLayout()
        buttons.addWidget(self._button('Eliminar distancia seleccionada', self._remove_distance))
        buttons.addWidget(self._button('Limpiar distancias CHIPIX', self.host.clear_distances))
        buttons.addWidget(self._button('Exportar distancias CSV…', self._export_distances))
        layout.addLayout(buttons)
        self._tab(page, 'Distancias 3D')
        self._distance_timer = QTimer(self.tool_window.ui_area)
        self._distance_timer.setInterval(400)
        self._distance_timer.timeout.connect(self._refresh_distances)
        self._distance_timer.start()

    def _queue_box(self, *_):
        if not getattr(self, '_sync_box', False) and hasattr(self, '_box_timer'):
            self._box_timer.start()

    def _box_style(self):
        return BoxStyle(self.box_mode.currentData(), tuple(self.box_rgb), self.edge_radius.value(),
                        self.mesh_spacing.value(), self.face_opacity.value(), self.rounded_edges.isChecked(),
                        self.show_handles.isChecked(), self.handle_radius.value(), tuple(self.handle_rgb))

    def _show_custom_box(self):
        self.host.show_box(self._box(), self._box_style())

    def _set_box(self, box):
        self._sync_box = True
        try:
            for widget, value in zip(self.centers+self.sizes+self.rotations, box.center+box.size+box.rotation):
                widget.setValue(value)
        finally:
            self._sync_box = False
        self._show_custom_box()

    def _nudge_box(self, axis, sign):
        box = self._box()
        center = list(box.center)
        center[axis] += sign*self.move_step.value()
        self._set_box(SearchBox(tuple(center), box.size, box.rotation))

    def _scale_box(self, factor):
        box = self._box()
        self._set_box(SearchBox(box.center, tuple(max(.01, min(100000,v*factor)) for v in box.size), box.rotation))

    def _reset_rotation(self):
        box = self._box()
        self._set_box(SearchBox(box.center, box.size))

    def _box_from_residues(self):
        self._set_box(self.host.residue_box(self.residue_spec.text(), self.padding.value(),
                                           self._box().rotation, self.whole_residues.isChecked()))

    def _toggle_box_mouse(self):
        modes = self.session.ui.mouse_modes
        if self.mouse_enabled.isChecked():
            from .box_mouse import BoxMouseMode
            self._mouse_mode = BoxMouseMode(self)
            self._mouse_bindings = [(modifiers, modes.mode('right',modifiers,exact=True)) for modifiers in ([],['shift'])]
            for modifiers, old_mode in self._mouse_bindings:
                modes.bind_mouse_mode('right', modifiers, self._mouse_mode)
            self._show_custom_box()
        else:
            self._restore_box_mouse()

    def _restore_box_mouse(self):
        if self._mouse_mode is not None:
            modes = self.session.ui.mouse_modes
            for modifiers, old_mode in self._mouse_bindings:
                if modes.mode('right', modifiers, exact=True) is self._mouse_mode:
                    modes.bind_mouse_mode('right', modifiers, old_mode)
        self._mouse_mode, self._mouse_bindings = None, []

    def _scene_options(self):
        color = {'current':None, 'white':(1.,1.,1.), 'black':(0.,0.,0.), 'slate':(.15,.18,.22),
                 'custom':tuple(self.background_rgb)}[self.background.currentData()]
        light = self.lighting.currentData()
        return {'background':color, 'lighting':None if light == 'current' else light}

    def _apply_scene(self):
        self.host.apply_scene(**self._scene_options())

    def _customization_data(self):
        return {'schema_version':1, 'application':'CHIPIX', 'box':asdict(self._box()), 'style':asdict(self._box_style()),
                'background':self.background.currentData(), 'background_rgb':self.background_rgb,
                'lighting':self.lighting.currentData(), 'image':{'width':self.image_width.value(),
                'height':self.image_height.value(), 'supersample':self.supersample.value(),
                'transparent':self.transparent_image.isChecked(), 'box':self.image_box.isChecked(),
                'handles':self.image_handles.isChecked(), 'distances':self.image_distances.isChecked()},
                'distances':{'color':self.distance_rgb,'radius':self.distance_radius.value(),
                'dashes':self.distance_dashes.value(),'label_size':self.distance_label_size.value(),
                'labels':self.distance_labels.isChecked()}}

    def _save_customization(self, path=None):
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area,self.tr('Guardar personalización…'),'chipix-style.json','JSON (*.json)')
        if path:
            write_json(path, self._customization_data())

    def _load_customization(self, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self.tool_window.ui_area,self.tr('Cargar personalización…'),'','JSON (*.json)')
        if not path:
            return
        from .core.presets import validate_customization
        data = validate_customization(json.loads(Path(path).read_text(encoding='utf-8')))
        box, style = SearchBox(**data['box']), BoxStyle(**data['style'])
        self._sync_box = True
        try:
            self.box_rgb, self.handle_rgb, self.background_rgb, self.distance_rgb = style.color, style.handle_color, data['background_rgb'], data['distances']['color']
            for button, value in ((self.box_color_button,self.box_rgb),(self.handle_color_button,self.handle_rgb),(self.background_button,self.background_rgb),(self.distance_color_button,self.distance_rgb)):
                self._paint_color(button,value)
            for combo, value in ((self.box_mode,style.mode),(self.background,data['background']),(self.lighting,data['lighting'])):
                combo.setCurrentIndex(combo.findData(value))
            for widget, value in ((self.edge_radius,style.radius),(self.mesh_spacing,style.spacing),(self.face_opacity,style.opacity),
                                  (self.handle_radius,style.handle_radius),(self.image_width,data['image']['width']),
                                  (self.image_height,data['image']['height']),(self.supersample,data['image']['supersample']),
                                  (self.distance_radius,data['distances']['radius']),(self.distance_dashes,data['distances']['dashes']),
                                  (self.distance_label_size,data['distances']['label_size'])):
                widget.setValue(value)
            for widget, value in ((self.rounded_edges,style.rounded),(self.show_handles,style.handles),
                                  (self.transparent_image,data['image']['transparent']),(self.image_box,data['image']['box']),
                                  (self.image_handles,data['image']['handles']),(self.image_distances,data['image']['distances']),
                                  (self.distance_labels,data['distances']['labels'])):
                widget.setChecked(value)
        finally:
            self._sync_box = False
        self._set_box(box)
        self._refresh_distances()

    def _export_scene_image(self, path=None):
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area,self.tr('Exportar imagen 3D…'),'chipix-scene.png',
                                                 'PNG (*.png);;TIFF (*.tif *.tiff);;JPEG (*.jpg *.jpeg)')
        if path:
            # Apply the current numeric box before the native renderer captures it.
            self._show_custom_box()
            self.host.export_image(path, width=self.image_width.value(), height=self.image_height.value(),
                                   supersample=self.supersample.value(), transparent=self.transparent_image.isChecked(),
                                   include_box=self.image_box.isChecked(), include_handles=self.image_handles.isChecked(),
                                   include_distances=self.image_distances.isChecked(), **self._scene_options())
            data = self._customization_data()
            view = self.session.main_view
            data['camera'] = {'position_matrix':view.camera.position.matrix.tolist(), 'name':view.camera.name}
            options = self._scene_options()
            data['export_scene'] = {'background':list(options['background']) if options['background'] is not None else list(view.background_color[:3]),
                                    'lighting_preset':options['lighting'],
                                    'note':'Camera and styling record; this JSON does not contain molecular models.'}
            write_json(str(path)+'.json', data)
            self._status('Imagen y parámetros de visualización guardados.')

    def _add_distance(self):
        self.host.add_distance()
        self._refresh_distances()

    def _refresh_distances(self):
        if not hasattr(self, 'distance_table') or self._deleted:
            return
        self.host.style_distances(self.distance_rgb, self.distance_radius.value(), self.distance_dashes.value(),
                                  self.distance_label_size.value(), self.distance_labels.isChecked())
        bonds = self.host.distances()
        old_row = self.distance_table.currentRow()
        self.distance_table.setRowCount(len(bonds))
        self._distance_bonds = bonds
        for row, bond in enumerate(bonds):
            for col, value in enumerate((str(bond.atoms[0]),str(bond.atoms[1]),f'{bond.length:.3f}')):
                item = self.distance_table.item(row,col)
                if item is None:
                    self.distance_table.setItem(row,col,QTableWidgetItem(value))
                elif item.text() != value:
                    item.setText(value)
        if 0 <= old_row < len(bonds):
            self.distance_table.selectRow(old_row)

    def _remove_distance(self):
        row = self.distance_table.currentRow()
        if 0 <= row < len(getattr(self,'_distance_bonds',[])):
            bond = self._distance_bonds[row]
            if not bond.deleted:
                bond.delete()
        self._refresh_distances()

    def _export_distances(self):
        path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area,self.tr('Exportar distancias CSV…'),'chipix-distances.csv','CSV (*.csv)')
        if path:
            with open(path,'w',newline='',encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(('atom_a','atom_b','distance_angstrom'))
                for bond in self.host.distances():
                    writer.writerow((str(bond.atoms[0]),str(bond.atoms[1]),bond.length))
