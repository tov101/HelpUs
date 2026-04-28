import inspect
import os
import re

from PySide6 import QtCore, QtWidgets

from helpus.source.console.console import LOGGER


class Frames(QtCore.QObject):
    execute = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._frames = self.parent().lw_frames
        self._frames.currentRowChanged.connect(self.__refresh)

        self._objects = self.parent().tw_objects

        self.p_index = 0

        self._trace = []

        self._stack = []

    def __add_object(self, name, value, parent=None):
        if parent:
            parent = QtWidgets.QTreeWidgetItem(parent, [type(value).__name__, name])
        else:
            parent = QtWidgets.QTreeWidgetItem(self._objects, [type(value).__name__, name])

        if isinstance(value, list):
            for index, v in enumerate(value):
                self.__add_object(parent=parent, name=index, value=v)
        elif isinstance(value, dict):
            for k, v in value.items():
                self.__add_object(parent=parent, name=k, value=v)
        elif isinstance(value, set):
            for index, v in enumerate(value):
                self.__add_object(parent=parent, name=index, value=v)
        else:
            parent.setText(2, str(value))

    def __find_current_frame(self):
        # Find Current Frame in 'stdout'
        current_frame = None
        for line in self._trace:
            if not line.strip():
                continue
            # TODO: Need to be the relative path to something
            _frame = re.search(
                pattern=r"(?i)(?P<filename>\w+[.]py)\((?P<lineno>\d+)\)(?P<function>.*)\(\)", string=line
            )
            if _frame:
                filename = _frame.group("filename")
                lineno = _frame.group("lineno")
                function = _frame.group("function")
                current_frame = (function, os.path.basename(filename), lineno)
        return current_frame

    def trace(self, text):
        self._trace.append(text)

    def _get_pdb_locals(self):
        """Find the active Pdb instance and return its authoritative (locals, globals) dicts."""
        try:
            import pdb as _pdb
            for fi in inspect.stack():
                obj = fi.frame.f_locals.get("self")
                if (
                    obj is not None
                    and isinstance(obj, _pdb.Pdb)
                    and getattr(obj, "curframe", None) is not None
                ):
                    return obj.curframe_locals, obj.curframe.f_globals
        except Exception:
            pass
        return None, None

    def _refresh_variables(self):
        """Refresh the variables panel for the currently selected frame without triggering navigation."""
        idx = self._frames.currentRow()
        if idx < 0:
            return
        current_item = self._frames.item(idx)
        if not current_item:
            return

        # For the top (current) frame use PDB's authoritative locals dict so that
        # assignments made at the PDB prompt (e.g. "x = 5") are reflected immediately.
        pdb_locals, pdb_globals = self._get_pdb_locals()

        frame = None
        for f in inspect.stack():
            if f"{f.function}, {os.path.basename(f.filename)}:{f.lineno}" == current_item.text():
                frame = f[0]
                break

        self._objects.clear()
        if idx == 0 and pdb_locals is not None:
            for name, value in pdb_locals.items():
                self.__add_object(name=name, value=value)
            for name, value in (pdb_globals or {}).items():
                self.__add_object(name=name, value=value)
        elif frame is not None:
            for name, value in frame.f_locals.items():
                self.__add_object(name=name, value=value)
            for name, value in frame.f_globals.items():
                self.__add_object(name=name, value=value)

        for i in range(self._objects.columnCount()):
            self._objects.resizeColumnToContents(i)

    def update(self):
        # Restore the saved frame list after a PDB up/down navigation command.
        if self._stack:
            with QtCore.QSignalBlocker(self._frames):
                self._frames.clear()
                for frame in self._stack:
                    self._frames.addItem(frame)
                self._stack = []
                self._frames.setCurrentRow(0)
            self.p_index = 0
            self._refresh_variables()
            return

        current_frame = self.__find_current_frame()
        self._trace = []

        if current_frame:
            with QtCore.QSignalBlocker(self._frames):
                self._frames.clear()
                found = False
                for frame in inspect.stack():
                    _frame = f"{frame.function}, {os.path.basename(frame.filename)}:{frame.lineno}"
                    frame_filename = os.path.basename(frame.filename).lower()
                    current_function, current_filename, current_lineno = current_frame
                    if (
                        current_function.lower() == frame.function.lower()
                        # May be .py or .pyc
                        and current_filename.lower() in (frame_filename, f"{frame_filename}c")
                        and str(current_lineno) == str(frame.lineno)
                    ) or found:
                        self._frames.addItem(_frame)
                        found = True
                self._frames.setCurrentRow(0)
            self.p_index = 0

        # Always refresh variables — covers both "frame found" and "expression-only" prompts.
        self._refresh_variables()

    def __refresh(self, index):
        command = None
        current_item = self._frames.item(index)
        if not current_item:
            return
        if self.p_index > index:
            command = "down"
        elif self.p_index < index:
            command = "up"

        if command:
            # Save Stack
            for row in range(self._frames.count()):
                self._stack.append(self._frames.item(row).text())
            for n in range(abs(index - self.p_index)):
                self.__request(command)

        frame = None
        for f in inspect.stack():
            frame_description = f"{f.function}, {os.path.basename(f.filename)}:{f.lineno}"
            if frame_description == current_item.text():
                frame = f
                break

        if not frame:
            return
        frame = frame[0]

        self._objects.clear()
        # Add Locals
        for name, value in frame.f_locals.items():
            self.__add_object(name=name, value=value)

        # Add Globals
        for name, value in frame.f_globals.items():
            self.__add_object(name=name, value=value)

        # Resize
        for i in range(self._objects.columnCount()):
            self._objects.resizeColumnToContents(i)

        self.p_index = index

    def __request(self, command):
        self.execute.emit(command)
