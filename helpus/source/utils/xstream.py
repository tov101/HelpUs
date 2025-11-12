import sys

from PySide6 import QtCore


def not_used(item):
    assert item == item


class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None

    # messageWritten = ENGINE.QtCore.pyqtSignal(str)
    output = QtCore.Signal(str)

    @staticmethod
    def flush():
        pass

    @staticmethod
    def fileno():
        return -1

    def write(self, msg):
        if not self.signalsBlocked():
            self.output.emit(msg)

    @staticmethod
    def stdout():
        if not XStream._stdout:
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

    @staticmethod
    def stderr():
        if not XStream._stderr:
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr
