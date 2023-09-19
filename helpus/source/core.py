import logging
import os
import queue
import sys
import threading
import time

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import Qt
from qtpy import uic

from helpus.source.frames import Frames
from helpus.source.utils.xstream import XStream
from helpus import icon_file_path
from helpus.source.buttons import Buttons
from helpus.version import __version__
from helpus.source.console.console import BaseConsole
from helpus.source.utils.remote import RCServer

LOGGER = logging.getLogger('HelpUs')


def get_qtconsole_object():
    if isinstance(sys.stdin, HelpUs):
        return sys.stdin.console
    else:
        return HelpUs.console


def setup_breakpoint_hook(
        parent,
        method,
        redirect_streams: bool = False,
        remote: bool = False,
        remote_host: str = None,
        remote_port: int = None
):
    """

    :param parent:
    :param method:
    :param redirect_streams:
    :param remote:
    :param remote_host:
    :param remote_port:
    :return:
    """

    def __method(*args, **kwargs):
        breakpoint()
        return method(*args, **kwargs)

    if not isinstance(sys.stdin, HelpUs):
        args = (parent, remote)
        if remote_host and remote_port:
            args = (parent, remote, remote_host, remote_port)
        sys.stdin = HelpUs(*args)
    else:
        # Restore Streams
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        raise Exception(
            "Multiple Instances are not allowed. Can be possible, but I'm to lazy to go deep with development."
        )

    if redirect_streams:
        sys.stdin.redirect_outerr_fd()
    return __method


class HelpUs(QtWidgets.QDialog):

    def __init__(self, parent=None, remote: bool = False, remote_host: str = None, remote_port: int = None):
        super().__init__()

        # Load UI
        ui_filepath = os.path.normpath(os.path.join(os.path.dirname(__file__), "..\\..\\helpus\\resource\\ui\\main.ui"))
        uic.loadUi(ui_filepath, self)

        self.setWindowTitle("HelpUs {}".format(__version__))
        # Set Icon
        if icon_file_path and os.path.exists(icon_file_path):
            self.setWindowIcon(QtGui.QIcon(icon_file_path))

        # SetParent
        self.parentWidget = QtWidgets.QMainWindow() if not parent else parent

        # Change Window Modality, otherwise parentWidget won't let you use this widget
        if self.parentWidget.windowModality() == QtCore.Qt.WindowModality.ApplicationModal:
            self.parentWidget.hide()
            self.parentWidget.setWindowModality(QtCore.Qt.WindowModality.NonModal)
            self.parentWidget.showNormal()

        # Set Flags
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowCloseButtonHint
        )

        # Create OutputConsole
        self.console = BaseConsole(parent)
        self.console.stream.connect(self.__stream)

        self.ConsoleLayout = self.te_console.parentWidget().layout()
        self.ConsoleLayout.replaceWidget(self.te_console, self.console)
        self.te_console.close()
        self.te_console.destroy()
        self.te_console.deleteLater()

        # Link Push Buttons
        self.buttons = Buttons(self)
        self.buttons.execute.connect(lambda command: self.__execute(command, False))

        # Link Frames Widget
        self.frames = Frames(self)
        self.frames.execute.connect(lambda command: self.__execute(command, False))
        self.console.stream.connect(self.frames.trace)
        self.console.header_printed.connect(self.frames.update)

        # Set Focus on Console
        self.setFocusPolicy(Qt.NoFocus)
        self.console.setFocus()

        # self.__enable_gui(False)

        # RC Server
        self.__remote = None
        self.__send_queue = queue.PriorityQueue()
        self.__event_ready_to_go = threading.Event()
        if remote:
            args = tuple()
            if remote_host and remote_port:
                args = (remote_host, remote_port)
            self.__remote = RCServer(*args)
            self.__remote.start()
            self.__remote_exchange()

        self.showNormal()

    def __connect_fd(self, fd, state=True):
        if state:
            getattr(XStream, fd)().output.connect(self.console.insertPlainText)
        else:
            getattr(XStream, fd)().output.disconnect(self.console.insertPlainText)

    def __enable_gui(self, state=True):
        """

        :param state:
        :return:
        """
        self.setEnabled(state)
        if state:
            self.console.setFocus()

    def __execute(self, command, rc=False):
        self.console.reset_stdin()
        self.console.stdin.write(command)
        if rc:
            # Write Data into Console also
            self.console.insertText('RC: {}\n'.format(command))
        self.__enable_gui(False)

    def __remote_exchange(self):
        def __thread_poll():
            while True:
                # Receive Data
                data = self.__remote.receive()
                if data:
                    # Set Event Ready to Go -> Allow queue to store entries and send it back
                    self.__event_ready_to_go.set()
                    self.__execute(command=data, rc=True)

                    messages = []
                    # Wait to have something in the queue
                    while self.__send_queue.empty():
                        time.sleep(0.01)
                    while not self.__send_queue.empty():
                        __item = self.__send_queue.get_nowait()
                        messages.append(__item)
                        # Give some time to fill all the value in queue
                        time.sleep(0.01)
                    message = ''.join(reversed(messages))
                    self.__remote.send(message)
                    self.__event_ready_to_go.clear()

        threading.Thread(name='HelpUs_RemoteReceive', target=__thread_poll, daemon=True).start()

    def __stream(self, text: str) -> None:
        # Send Output To RCServer
        if self.__remote and self.__event_ready_to_go.is_set():
            self.__send_queue.put_nowait(item=text)

    def redirect_outerr_fd(self):
        """

        :return:
        """
        # Link Stream Output
        self.__connect_fd('stdout', True)
        self.__connect_fd('stderr', True)

    def readline(self):
        """

        :return:
        """
        if not self.console.isEnabled():
            self.__enable_gui(True)
        # Reset Buffer
        self.console.reset_stdin()
        # Check Position
        while self.console.stdin.tell() == 0:
            QtCore.QCoreApplication.processEvents()
        value = self.console.stdin.getvalue()
        # Log all Inputs from Buffer
        LOGGER.info(f">> {value}")
        return value


if __name__ == '__main__':
    p = QtWidgets.QApplication(sys.argv)
    LOGGER.error('Ceva')

    # HelpUs().exec_()

    LOGGER.error = setup_breakpoint_hook(
        parent=None,
        method=LOGGER.error,
        redirect_streams=True,
        remote=True
    )
    # LOGGER.error = setup_breakpoint_hook(None, LOGGER.error, redirect_streams=True)

    x = 90
    LOGGER.error('Altceva')

    print(x)
