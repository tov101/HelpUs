import inspect
import os
import re

from qtpy import QtCore, QtWidgets


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
            parent = QtWidgets.QTreeWidgetItem(parent, [str(type(value)), name])
        else:
            parent = QtWidgets.QTreeWidgetItem(self._objects, [str(type(value)), name])

        if isinstance(value, list):
            for index, v in enumerate(value):
                self.__add_object(parent=parent, name=index, value=v)
        elif isinstance(value, dict):
            for k, v in enumerate(value):
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
            _frame = re.search(pattern=r"(?i)(?P<filename>\w+[.]py)\((?P<lineno>\d+)\)(?P<function>.*)\(\)", string=line)
            if _frame:
                filename = _frame.group("filename")
                lineno = _frame.group("lineno")
                function = _frame.group("function")
                current_frame = f"{function}, {os.path.basename(filename)}:{lineno}"
        return current_frame

    def trace(self, text):
        self._trace.append(text)

    def update(self):
        # Keep old stack.
        if self._stack:
            # Clear Frames ListWidget
            self._frames.clear()
            for frame in self._stack:
                self._frames.addItem(frame)
            self._stack = []
            return

        current_frame = self.__find_current_frame()
        if not current_frame:
            return

        # Clear Frames ListWidget
        self._frames.clear()

        found = False
        for frame in inspect.stack():
            frame = f"{frame.function}, {os.path.basename(frame.filename)}:{frame.lineno}"
            if frame == current_frame or found:
                self._frames.addItem(frame)
                found = True
        self._trace = []

        # Set Selected Current Frame
        self._frames.setCurrentRow(0)

    def __refresh(self, index):
        command = None
        current_item = self._frames.item(index)
        if not current_item:
            return
        if self.p_index > index:
            command = "down"
        elif self.p_index < index:
            command = 'up'

        if command:
            # Save Stack
            for row in range(self._frames.count()):
                self._stack.append(self._frames.item(row).text())
            for n in range(abs(index - self.p_index)):
                self.__request(command)

        frame = None
        for frame in inspect.stack():
            frame_description = f"{frame.function}, {os.path.basename(frame.filename)}:{frame.lineno}"
            if frame_description == current_item.text():
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
