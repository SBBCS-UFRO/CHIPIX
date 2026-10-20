# SPDX-License-Identifier: GPL-3.0-or-later
"""Native dockable Qt tool. Engine processes and consensus work are asynchronous."""
import csv
from pathlib import Path
from queue import SimpleQueue
import threading
from chimerax.core.settings import Settings
from chimerax.core.tools import ToolInstance
from chimerax.core.errors import UserError
from chimerax.ui import MainToolWindow
from Qt.QtCore import Qt, QProcess, QTimer
from Qt.QtGui import QColor, QPixmap, QRegion
from Qt.QtWidgets import QScrollArea
from Qt.QtWidgets import QAbstractItemView, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from .core.consensus import consensus, export_consensus
from .core.models import SearchBox
from .core.runner import DockingConfig, finish_run, import_run, load_run, now, prepare_run, update_run
from .host import ChimeraXHost
from .branding import COPYRIGHT, TOOL_NAME, VERSIONED_NAME
from .i18n import LANGUAGES, Translator
from .customization import CustomizationMixin

class ChipixSettings(Settings):
    EXPLICIT_SAVE = {'vina': 'vina', 'smina': 'smina', 'output': '', 'language': 'en'}

class ChipixTool(CustomizationMixin, ToolInstance):
    SESSION_ENDURING = False
    SESSION_SAVE = False
    help = 'help:user/tools/chipix.html'

    def __init__(self, session, tool_name=TOOL_NAME):
        super().__init__(session, tool_name)
        self.settings = ChipixSettings(session, 'CHIPIX')
        self.translator = Translator(self.settings.language)
        self.host = ChimeraXHost(session,translate=self.translator)
        self._text_bindings = []
        self._status_raw = 'Listo. Configura el motor y los archivos preparados.'
        self._caption_raw = 'Sin análisis calculado.'
        self.runs = {}
        self.consensus_rows = []
        self.process = None
        self.manifest = None
        self.log_stream = None
        self.cancelled = False
        self._deleted = False
        self._consensus_cancel = threading.Event()
        self._consensus_queue = SimpleQueue()
        self._consensus_active = False
        self.tool_window = MainToolWindow(self)
        self._build_ui()
        self.tool_window.manage('side')

    def _safe(self, function):

        def invoke(*_):
            try:
                return function()
            except (ValueError, OSError, KeyError, TypeError, UserError) as error:
                self._error(str(error))
        return invoke

    def _error(self, message):
        message = self.tr(message)
        self.session.logger.warning(f'CHIPIX: {message}')
        QMessageBox.warning(self.tool_window.ui_area, 'CHIPIX', message)

    def _button(self, text, callback):
        button = QPushButton(self.tr(text))
        self._text_bindings.append(lambda:button.setText(self.tr(text)))
        button.clicked.connect(self._safe(callback))
        return button

    def _path_row(self, value='', *, directory=False, save=False, file_filter='Todos (*)'):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        edit = QLineEdit(value)

        def choose():
            if directory:
                path = QFileDialog.getExistingDirectory(self.tool_window.ui_area, self.tr('Seleccionar carpeta'), edit.text())
            else:
                dialog = QFileDialog.getSaveFileName if save else QFileDialog.getOpenFileName
                path, _ = dialog(self.tool_window.ui_area, self.tr('Seleccionar archivo'), edit.text(), self.tr(file_filter))
            if path:
                edit.setText(path)
        layout.addWidget(edit)
        layout.addWidget(self._button('Examinar…', choose))
        return (widget, edit)

    def _decimal(self, value, low=-100000, high=100000):
        box = QDoubleSpinBox()
        box.setRange(low, high)
        box.setDecimals(3)
        box.setValue(value)
        return box

    def _integer(self, value, low=1, high=10000):
        box = QSpinBox()
        box.setRange(low, high)
        box.setValue(value)
        return box

    def _table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels([self.tr(text) for text in headers])
        self._text_bindings.append(lambda:table.setHorizontalHeaderLabels([self.tr(text) for text in headers]))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        return table

    def tr(self, text):
        return self.translator(text)

    def _label(self, text):
        label = QLabel(self.tr(text))
        label.setWordWrap(True)
        self._text_bindings.append(lambda:label.setText(self.tr(text)))
        return label

    def _placeholder(self, widget, text):
        widget.setPlaceholderText(self.tr(text))
        self._text_bindings.append(lambda:widget.setPlaceholderText(self.tr(text)))

    def _form_row(self, form, text, widget):
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow(self._label(text),widget)

    def _retranslate_model_placeholder(self):
        selected = self.model_menu.value
        # The native chooser accepts this text at construction; preserve its
        # value while refreshing the same placeholder when the language changes.
        self.model_menu._no_value_button_text = self.tr('Selecciona un modelo molecular abierto.')
        if selected is None:
            self.model_menu.setText(self.model_menu._no_value_button_text)

    def _tab(self, page, title):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        index = self.tabs.addTab(scroll,self.tr(title))
        self._text_bindings.append(lambda:self.tabs.setTabText(index,self.tr(title)))

    def _combo_item(self, combo, text, value):
        index = combo.count()
        combo.addItem(self.tr(text),value)
        self._text_bindings.append(lambda:combo.setItemText(index,self.tr(text)))

    def _status(self, text):
        self._status_raw = text
        self.status.setText(self.tr(text))

    def _caption(self, text):
        self._caption_raw = text
        self.consensus_caption.setText(self.tr(text))

    def _language_changed(self, index):
        self.translator.language = self.language_menu.itemData(index)
        self.settings.language = self.translator.language
        self.settings.save()
        for update in self._text_bindings:
            update()
        self._status(self._status_raw)
        self._caption(self._caption_raw)
        suffix = '' if self.translator.language == 'en' else '-'+self.translator.language
        self.help = f'help:user/tools/chipix{suffix}.html'

    def _header(self, outer):
        header = QHBoxLayout()
        self.logo_label = QLabel()
        original = QPixmap(str(Path(__file__).parent/'assets/chipix-logo.png'))
        if not original.isNull():
            # Limit the displayed source rectangle to the artwork while keeping
            # the supplied PNG untouched in the package.
            region = QRegion(original.createMaskFromColor(QColor('white'),Qt.MaskMode.MaskOutColor))
            bounds = region.boundingRect().adjusted(-8,-8,8,8).intersected(original.rect())
            self.logo_label.setPixmap(original.copy(bounds).scaled(88,48,Qt.AspectRatioMode.KeepAspectRatio,
                                                                  Qt.TransformationMode.SmoothTransformation))
        self.logo_label.setAccessibleName('CHIPIX laboratory logo')
        header.addWidget(self.logo_label)
        self.title_label = QLabel(f'<b>{VERSIONED_NAME}</b>')
        header.addWidget(self.title_label)
        header.addStretch()
        outer.addLayout(header)
        language_row = QHBoxLayout()
        language_row.addWidget(self._label('Idioma'))
        self.language_menu = QComboBox()
        for code,name in LANGUAGES.items():
            self.language_menu.addItem(name,code)
        self.language_menu.setCurrentIndex(self.language_menu.findData(self.translator.language))
        language_row.addWidget(self.language_menu)
        language_row.addStretch()
        outer.addLayout(language_row)

    def _build_ui(self):
        outer = QVBoxLayout(self.tool_window.ui_area)
        self._header(outer)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)
        self._preparation_tab()
        self._docking_tab()
        self._results_tab()
        self._consensus_tab()
        self._customization_tab()
        self._measurement_tab()
        self.status = self._label('Listo. Configura el motor y los archivos preparados.')
        self.status.setWordWrap(True)
        outer.addWidget(self.status)
        self.copyright_label = QLabel(COPYRIGHT)
        self.copyright_label.setWordWrap(True)
        font = self.copyright_label.font()
        font.setPointSizeF(max(8.0,font.pointSizeF()-2))
        self.copyright_label.setFont(font)
        outer.addWidget(self.copyright_label)
        self.language_menu.currentIndexChanged.connect(self._language_changed)
        suffix = '' if self.translator.language == 'en' else '-'+self.translator.language
        self.help = f'help:user/tools/chipix{suffix}.html'

    def _preparation_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        from chimerax.atomic.widgets import AtomicStructureMenuButton
        self.model_menu = AtomicStructureMenuButton(self.session,
            no_value_button_text=self.tr('Selecciona un modelo molecular abierto.'))
        self._text_bindings.append(self._retranslate_model_placeholder)
        self._form_row(form, 'Modelo molecular', self.model_menu)
        layout.addLayout(form)
        layout.addWidget(self._button('Preparar modelo con Dock Prep…', lambda: self.host.dock_prep(self.model_menu.value)))
        layout.addWidget(self._button('Exportar modelo como PDB…', self._export_model))
        layout.addWidget(self._button('Exportar ligando seleccionado como MOL2…', self._export_ligand))
        note = self._label('Revisa protonación, aguas, cofactores y estados químicos. Después genera PDBQT con tu protocolo de AutoDockTools o Meeko. Dock Prep y exportar PDB/MOL2 son pasos previos a esa preparación.')
        note.setWordWrap(True)
        layout.addWidget(note)
        box_form = QFormLayout()
        self.centers, self.sizes = ([], [])
        for label, values, initial in (('Centro (Å)', self.centers, 0.0), ('Tamaño (Å)', self.sizes, 20.0)):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            for axis in 'XYZ':
                row_layout.addWidget(self._label(axis))
                spin = self._decimal(initial, 0.001 if values is self.sizes else -100000)
                values.append(spin)
                row_layout.addWidget(spin)
            self._form_row(box_form, label, row)
        self.padding = self._decimal(4.0, 0.001, 1000)
        self._form_row(box_form, 'Margen de selección (Å)', self.padding)
        layout.addLayout(box_form)
        layout.addWidget(self._button('Definir caja desde átomos seleccionados', self._box_from_selection))
        layout.addWidget(self._button('Mostrar caja', self._show_custom_box))
        self._box_controls(layout)
        self._box_customization(layout)
        layout.addStretch()
        self._tab(page, 'Preparación y caja')

    def _docking_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self.engine = QComboBox()
        self.engine.addItems(['vina', 'smina'])
        self._form_row(form, 'Motor', self.engine)
        self._engine_name = 'vina'
        row, self.executable = self._path_row(self.settings.vina)
        self._form_row(form, 'Ejecutable', row)
        self.engine.currentTextChanged.connect(self._engine_changed)
        row, self.receptor = self._path_row(file_filter='Receptor preparado (*.pdbqt)')
        self._form_row(form, 'Receptor PDBQT', row)
        row, self.ligand = self._path_row(file_filter='Ligando preparado (*.pdbqt)')
        self._form_row(form, 'Ligando PDBQT', row)
        self.ligand_id = QLineEdit()
        self._placeholder(self.ligand_id, 'Mismo ID para el mismo ligando en todos los motores')
        self._form_row(form, 'ID de ligando', self.ligand_id)
        self.context = QLineEdit()
        self._placeholder(self.context, 'Ej.: receptor_1 · misma orientación y coordenadas')
        self._form_row(form, 'ID de receptor/marco', self.context)
        row, self.output = self._path_row(self.settings.output or str(Path.home() / 'CHIPIX-runs'), directory=True)
        self._form_row(form, 'Guardar ejecuciones en', row)
        self.exhaustiveness = self._integer(8)
        self.num_modes = self._integer(9)
        self.energy_range = self._decimal(3.0, 0.001, 1000)
        self.seed = self._integer(42, 1, 2147483647)
        self.cpu = self._integer(1, 1, 1024)
        self.scoring = QComboBox()
        self.scoring.addItems(['vina', 'vinardo'])
        self.scoring.setEnabled(False)
        for label, widget in (('Exhaustividad', self.exhaustiveness), ('Máximo de poses', self.num_modes), ('Rango energético (kcal/mol)', self.energy_range), ('Semilla', self.seed), ('CPU', self.cpu), ('Función de puntuación', self.scoring)):
            self._form_row(form, label, widget)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        self.run_button = self._button('Ejecutar docking', self._start)
        self.cancel_button = self._button('Cancelar ejecución', self._cancel)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1500)
        layout.addWidget(self.log)
        self._tab(page, 'Docking')

    def _results_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self.import_engine = QComboBox()
        self.import_engine.addItems(['vina', 'smina', 'rxdock', 'adfr'])
        self._combo_item(self.import_engine, 'Otro', 'other')
        self._form_row(form, 'Motor del resultado externo', self.import_engine)
        self.score_field = QLineEdit()
        self._placeholder(self.score_field, 'Automático: minimizedAffinity, SCORE, vina_affinity, affinity')
        self._form_row(form, 'Campo de score SDF', self.score_field)
        note = self._label('Para importar, completa ID de ligando e ID de receptor/marco en Docking. Se interpreta que un score menor es mejor. Importa cada ligando en un archivo separado.')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addLayout(form)
        layout.addWidget(self._button('Importar poses PDBQT / SDF…', self._import_poses))
        layout.addWidget(self._button('Recuperar ejecución run.json…', self._load_run))
        self.results_table = self._table(['Ejecución', 'Motor', 'Ligando', 'Pose', 'Score'])
        self.results_table.cellDoubleClicked.connect(self._safe(self._show_result))
        layout.addWidget(self.results_table)
        layout.addWidget(self._button('Mostrar pose seleccionada', self._show_result))
        layout.addWidget(self._button('Exportar resultados CSV…', self._export_results))
        self._tab(page, 'Resultados')

    def _consensus_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._label('Selecciona ejecuciones del mismo ligando y receptor/marco:'))
        self.run_list = QListWidget()
        self.run_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.run_list)
        layout.addWidget(self._button('Retirar ejecuciones seleccionadas de la tabla', self._remove_runs))
        form = QFormLayout()
        self.method = QComboBox()
        for label, value in (('Rank by Rank', 'rank'), ('Average of Auto-Scaled Scores', 'autoscaled'), ('Z-scores', 'zscore')):
            self._combo_item(self.method, label, value)
        self._form_row(form, 'Consenso', self.method)
        self.rmsd_mode = QComboBox()
        for label, value in (('Identidad y orden de átomos', 'ordered'), ('Corregido por simetría (SDF)', 'symmetry'), ('Sin filtro espacial', 'none')):
            self._combo_item(self.rmsd_mode, label, value)
        self._form_row(form, 'RMSD de átomos pesados', self.rmsd_mode)
        self.threshold = self._decimal(2.0, 0, 1000)
        self._form_row(form, 'Umbral RMSD (Å)', self.threshold)
        layout.addLayout(form)
        note = self._label('Se comparan pares de poses entre ejecuciones, sin superponer el ligando. Un consenso menor es mejor. La corrección por simetría exige SDF con enlaces; PDBQT usa la identidad y el orden de sus átomos.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.consensus_button = self._button('Calcular consenso', self._calculate_consensus)
        layout.addWidget(self.consensus_button)
        self.consensus_cancel_button = self._button('Cancelar análisis', lambda: self._consensus_cancel.set())
        self.consensus_cancel_button.setEnabled(False)
        layout.addWidget(self.consensus_cancel_button)
        self.consensus_table = self._table(['Ejecución A', 'Pose A', 'Ejecución B', 'Pose B', 'RMSD (Å)', 'Consenso'])
        self.consensus_table.cellDoubleClicked.connect(self._safe(self._show_pair))
        self.consensus_caption = self._label('Sin análisis calculado.')
        self.consensus_caption.setWordWrap(True)
        layout.addWidget(self.consensus_caption)
        layout.addWidget(self.consensus_table)
        layout.addWidget(self._button('Mostrar par seleccionado', self._show_pair))
        layout.addWidget(self._button('Exportar consenso CSV…', self._export_consensus))
        self._tab(page, 'Consenso')

    def _engine_changed(self, name):
        setattr(self.settings, self._engine_name, self.executable.text())
        self._engine_name = name
        self.executable.setText(getattr(self.settings, name))
        self.scoring.setEnabled(name == 'smina')
        if name == 'vina':
            self.scoring.setCurrentText('vina')

    def _box(self):
        return SearchBox(tuple(w.value() for w in self.centers), tuple(w.value() for w in self.sizes), tuple(w.value() for w in self.rotations))

    def _box_from_selection(self):
        self._set_box(self.host.selection_box(self.padding.value(), self._box().rotation))

    def _export_model(self):
        path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area, self.tr('Exportar receptor'), 'receptor.pdb', self.tr('PDB (*.pdb)'))
        if path:
            self.host.export_model(self.model_menu.value, path)

    def _export_ligand(self):
        path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area, self.tr('Exportar selección'), 'ligand.mol2', self.tr('MOL2 (*.mol2)'))
        if path:
            self.host.export_selected_ligand(path)

    def _start(self):
        if self.process is not None:
            raise ValueError('Ya hay una ejecución en curso.')
        config = DockingConfig(self.engine.currentText(), self.executable.text(), self.receptor.text(), self.ligand.text(), self.ligand_id.text().strip(), self.context.text().strip(), self._box(), self.exhaustiveness.value(), self.num_modes.value(), self.energy_range.value(), self.seed.value(), self.cpu.value(), self.scoring.currentText())
        if not self.output.text().strip():
            raise ValueError('Selecciona una carpeta para las ejecuciones.')
        self.manifest = prepare_run(config, self.output.text())
        data = update_run(self.manifest, state='running', started=now())
        setattr(self.settings, self.engine.currentText(), self.executable.text())
        self.settings.output = self.output.text()
        self.settings.save()
        self.log.clear()
        self.cancelled = False
        self.log_stream = open(self.manifest.parent / 'engine.log', 'wb')
        process = QProcess(self.tool_window.ui_area)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.setWorkingDirectory(str(self.manifest.parent))
        process.readyReadStandardOutput.connect(self._read_log)
        process.finished.connect(lambda code, status: self._finished(process, code, status))
        process.errorOccurred.connect(lambda error: self._process_error(process, error))
        self.process = process
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self._status(f"Ejecutando {data['id']}…")
        process.start(data['command'][0], data['command'][1:])

    def _read_log(self):
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput())
        if self.log_stream:
            self.log_stream.write(data)
            self.log_stream.flush()
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(data.decode('utf-8', errors='replace'))
        self.log.setTextCursor(cursor)

    def _process_error(self, process, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._finished(process, -1, QProcess.ExitStatus.CrashExit)

    def _finished(self, process, code, status):
        if self.process is not process:
            return
        self._read_log()
        if self.log_stream:
            self.log_stream.close()
            self.log_stream = None
        self.process = None
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        try:
            if status == QProcess.ExitStatus.CrashExit and code == 0:
                code = -1
            run = finish_run(self.manifest, code, self.cancelled)
            if run:
                self._add_run(run)
                self._status(f'{run.id}: {len(run.poses)} poses. Guardado en {self.manifest.parent}')
            else:
                self._status('Ejecución cancelada. Se conservaron entradas y registro.')
        except (ValueError, OSError) as error:
            self._status('La ejecución falló. Revisa el registro del motor.')
            if not self._deleted:
                self._error(str(error))
        process.deleteLater()

    def _cancel(self):
        if self.process is not None:
            self.cancelled = True
            process = self.process
            process.terminate()
            QTimer.singleShot(2000, lambda: p_kill(process))
            self._status('Cancelando ejecución…')

    def _add_run(self, run):
        if run.id in self.runs:
            raise ValueError('Esta ejecución ya está cargada.')
        self.runs[run.id] = run
        item = QListWidgetItem(f'{run.id} · {run.engine} · {run.ligand_id}')
        item.setData(Qt.ItemDataRole.UserRole, run.id)
        self.run_list.addItem(item)
        item.setSelected(True)
        for pose in run.poses:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self._fill_row(self.results_table, row, [run.id, run.engine, run.ligand_id, pose.number, pose.score], (run.id, pose.number))

    def _fill_row(self, table, row, values, data):
        for column, value in enumerate(values):
            item = QTableWidgetItem()
            item.setData(Qt.ItemDataRole.DisplayRole, value if value is not None else '—')
            item.setData(Qt.ItemDataRole.UserRole, data)
            table.setItem(row, column, item)

    def _import_poses(self):
        ligand_id, context = (self.ligand_id.text().strip(), self.context.text().strip())
        if not ligand_id or not context:
            raise ValueError('Completa ID de ligando e ID de receptor/marco en Docking antes de importar.')
        path, _ = QFileDialog.getOpenFileName(self.tool_window.ui_area, self.tr('Importar resultados'), '', self.tr('Poses (*.pdbqt *.sdf *.sd)'))
        if path:
            if not self.output.text().strip():
                raise ValueError('Selecciona en Docking una carpeta para conservar la importación.')
            engine = self.import_engine.currentData() or self.import_engine.currentText()
            run = import_run(path, engine, ligand_id, context, self.output.text(), self.score_field.text().strip())
            self._add_run(run)
            self._status(f'Importadas {len(run.poses)} poses. Copia y run.json en {Path(run.manifest).parent}')

    def _load_run(self):
        path, _ = QFileDialog.getOpenFileName(self.tool_window.ui_area, self.tr('Recuperar ejecución'), '', self.tr('Manifiesto (run.json)'))
        if path:
            self._add_run(load_run(path))

    def _entry(self, key):
        identifier, number = key
        run = self.runs[identifier]
        return (run, next((p for p in run.poses if p.number == number)))

    def _remove_runs(self):
        if self._consensus_active:
            raise ValueError('Espera a que termine el análisis o cancélalo antes de retirar ejecuciones.')
        identifiers = {item.data(Qt.ItemDataRole.UserRole) for item in self.run_list.selectedItems()}
        for row in reversed(range(self.run_list.count())):
            if self.run_list.item(row).data(Qt.ItemDataRole.UserRole) in identifiers:
                self.run_list.takeItem(row)
        for identifier in identifiers:
            self.runs.pop(identifier, None)
        for row in reversed(range(self.results_table.rowCount())):
            if self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole)[0] in identifiers:
                self.results_table.removeRow(row)
        self.consensus_rows = []
        self.consensus_table.setRowCount(0)
        self._caption('Sin análisis calculado.')
        self._status('Tablas actualizadas. Los archivos de ejecución se conservan en disco.')

    def _show_result(self):
        row = self.results_table.currentRow()
        if row < 0:
            raise ValueError('Selecciona una pose en Resultados.')
        self.host.show_poses([self._entry(self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole))])

    def _calculate_consensus(self):
        if self._consensus_active:
            raise ValueError('Ya hay un análisis de consenso en curso.')
        runs = tuple((self.runs[item.data(Qt.ItemDataRole.UserRole)] for item in self.run_list.selectedItems()))
        method, mode, threshold = (self.method.currentData(), self.rmsd_mode.currentData(), self.threshold.value())
        self._analysis_label = f'Resultado: {self.method.currentText()} · {self.rmsd_mode.currentText()}'
        if mode != 'none':
            self._analysis_label += f' · RMSD ≤ {threshold:g} Å'
        self._consensus_cancel.clear()
        cancel = self._consensus_cancel
        queue = self._consensus_queue

        def work():
            try:
                rows = consensus(runs, method, mode, threshold, cancelled=cancel.is_set)
                queue.put((rows, None))
            except Exception as error:
                queue.put((None, str(error)))
        self._consensus_active = True
        self.consensus_button.setEnabled(False)
        self.consensus_cancel_button.setEnabled(True)
        self._status('Calculando consenso…')
        threading.Thread(target=work, daemon=True).start()
        QTimer.singleShot(100, self._poll_consensus)

    def _poll_consensus(self):
        if self._deleted:
            return
        if self._consensus_queue.empty():
            QTimer.singleShot(100, self._poll_consensus)
            return
        rows, error = self._consensus_queue.get()
        self._consensus_active = False
        self.consensus_button.setEnabled(True)
        self.consensus_cancel_button.setEnabled(False)
        if error:
            self._status('Análisis sin completar.')
            self._error(error)
            return
        self.consensus_rows = rows
        self._caption(self._analysis_label)
        self.consensus_table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            self._fill_row(self.consensus_table, index, [row.run_a, row.pose_a, row.run_b, row.pose_b, None if row.rmsd is None else round(row.rmsd, 4), round(row.consensus, 6)], row)
        self._status(f'Consenso: {len(rows)} pares dentro del criterio. Un score menor es mejor.')

    def _show_pair(self):
        row = self.consensus_table.currentRow()
        if row < 0:
            raise ValueError('Selecciona un par de poses en Consenso.')
        pair = self.consensus_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.host.show_poses([self._entry((pair.run_a, pair.pose_a)), self._entry((pair.run_b, pair.pose_b))])

    def _export_results(self):
        path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area, self.tr('Exportar resultados'), 'chipix-results.csv', self.tr('CSV (*.csv)'))
        if path:
            with open(path, 'w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(['run', 'engine', 'ligand_id', 'context', 'pose', 'score', 'source'])
                for run in self.runs.values():
                    for pose in run.poses:
                        writer.writerow([run.id, run.engine, run.ligand_id, run.context, pose.number, pose.score, run.source])

    def _export_consensus(self):
        if not self.consensus_rows:
            raise ValueError('Primero calcula un consenso con pares válidos.')
        path, _ = QFileDialog.getSaveFileName(self.tool_window.ui_area, self.tr('Exportar consenso'), 'chipix-consensus.csv', self.tr('CSV (*.csv)'))
        if path:
            export_consensus(path, self.consensus_rows)

    def delete(self):
        self._deleted = True
        self._box_timer.stop()
        self._distance_timer.stop()
        self._restore_box_mouse()
        self._consensus_cancel.set()
        if self.process is not None:
            self.cancelled = True
            self.process.kill()
            self.process.waitForFinished(1000)
        if self.log_stream:
            self.log_stream.close()
            self.log_stream = None
        self.host.close()
        super().delete()

def p_kill(process):
    try:
        if process.state() != QProcess.ProcessState.NotRunning:
            process.kill()
    except RuntimeError:
        pass
