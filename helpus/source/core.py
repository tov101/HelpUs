import logging
import os
import queue
import sys
import threading
import time

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import Qt

from helpus import icon_file_path
from helpus.version import __version__
from helpus.source.console.console import BaseConsole
from helpus.source.utils.remote import RCServer
from helpus.source.utils.utils import XStream

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
        sys.stdin.redirect_outerr_stream()
    return __method


class HelpUs(QtWidgets.QDialog):
    BUTTONS = (
        'Continue',
        'Next',
        'Step',
        'Where',
        'Up',
        'Down'
    )

    def __init__(self, parent=None, remote: bool = False, remote_host: str = None, remote_port: int = None):
        super().__init__()

        # SetParent
        self.parentWidget = QtWidgets.QMainWindow() if not parent else parent

        # Change Window Modality, otherwise parentWidget won't let you use this widget
        if self.parentWidget.windowModality() == QtCore.Qt.WindowModality.ApplicationModal:
            self.parentWidget.hide()
            self.parentWidget.setWindowModality(QtCore.Qt.WindowModality.NonModal)
            self.parentWidget.showNormal()

        # Set Icon
        if icon_file_path and os.path.exists(icon_file_path):
            self.setWindowIcon(QtGui.QIcon(icon_file_path))

        # Set Flags
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowCloseButtonHint
        )

        # Resize
        self.resize(513, 300)

        # Create Layout
        self.main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.main_layout)
        self.setWindowTitle("HelpUs {}".format(__version__))

        # Create Content Layouts
        self.ConsoleLayout = QtWidgets.QVBoxLayout()
        self.ButtonsLayout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.ButtonsLayout)
        self.main_layout.addLayout(self.ConsoleLayout)

        # Create OutputConsole
        self.console = BaseConsole(self.stream, parent)
        # self.console.keyPressEvent = self.__key_press_event
        self.ConsoleLayout.addWidget(self.console)

        # Create buttons
        for button_text in self.BUTTONS:
            # Create Button Name
            button_name = 'button_%s' % button_text.lower()
            _button = QtWidgets.QPushButton(button_text)
            _button.setFocusPolicy(Qt.NoFocus)
            setattr(self, button_name, _button)
            getattr(self, button_name).clicked.connect(self.__push_button)

            # Add Button to Widget
            self.ButtonsLayout.addWidget(getattr(self, button_name))

        # Set Focus on Console
        self.setFocusPolicy(Qt.NoFocus)
        self.console.setFocus()

        self.__enable_gui(False)

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

    def __enable_gui(self, state=True):
        """

        :param state:
        :return:
        """
        self.console.setEnabled(state)
        for button_text in self.BUTTONS:
            # Get Button Name
            button_name = 'button_%s' % button_text.lower()
            getattr(self, button_name).setEnabled(state)
        if state:
            self.console.setFocus()

    def __push_button(self):
        # Read text from Button and use it as pdb keyword
        button_scope = self.sender().text().lower()
        self.console.reset_stdin()
        self.console.stdin.write(button_scope)
        self.__enable_gui(False)

    def __remote_exchange(self):
        def __thread_poll():
            while True:
                # Receive Data
                data = self.__remote.receive()
                if data:
                    # Set Event Ready to Go -> Allow queue to store entries and send it back
                    self.__event_ready_to_go.set()
                    # Write Data into Buffer
                    self.console.reset_stdin()
                    self.console.stdin.write(data)
                    # Write Data into Console also
                    self.console.insertText('RC: {}\n'.format(data))
                    self.__enable_gui(False)

                    messages = []
                    # Wait to have something in queue
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

    def stream(self, text: str) -> None:
        # Send Output To RCServer
        if self.__remote and self.__event_ready_to_go.is_set():
            self.__send_queue.put_nowait(item=text)

    def redirect_outerr_stream(self):
        """

        :return:
        """
        # Link Stream Output
        XStream.stdout().messageWritten.connect(self.console.insertPlainText)
        XStream.stderr().messageWritten.connect(self.console.insertPlainText)

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
