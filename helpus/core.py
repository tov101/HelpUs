import io
import logging
import os
import queue
import sys
import threading
import time

from PyQt5 import QtGui, QtCore, QtWidgets

from helpus import icon_file_path
from helpus.utils.utils import XStream
from helpus.utils.remote import RCServer
from helpus import __version__

LOGGER = logging.getLogger('HelpUs')


def get_qtconsole_object():
    if isinstance(sys.stdin, HelpUs):
        return sys.stdin.console
    else:
        return HelpUs.console


def setup_breakpoint_hook(parent, method, redirect_streams=False, remote=False):
    def __method(*args, **kwargs):
        breakpoint()
        return method(*args, **kwargs)

    if not isinstance(sys.stdin, HelpUs):
        sys.stdin = HelpUs(parent=parent, remote=remote)
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
    HOOK_HEADER = '(Pdb) '
    HOOK_INTERACT = '>>> '
    HOOK_LINE_BREAK = '... '
    HOOK_ERROR = '***'
    HOOKS = [HOOK_HEADER, HOOK_INTERACT]

    CLEAR_SCREEN = 'cls'
    BUTTONS = [
        'Continue',
        'Next',
        'Step',
        'Where',
        'Up',
        'Down'
    ]

    def __init__(
            self,
            parent=None,
            remote: bool = False
    ):

        super().__init__()

        if not parent:
            self.parentWidget = QtWidgets.QMainWindow()
        else:
            self.parentWidget = parent

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
        self.console = QtWidgets.QTextEdit(parent)
        self.console.insertPlainText = self.__insert_plain_text
        self.console.keyPressEvent = self.__key_press_event
        self.ConsoleLayout.addWidget(self.console)

        # Create buttons
        for button_text in self.BUTTONS:
            # Create Button Name
            button_name = 'button_%s' % button_text.lower()
            setattr(self, button_name, QtWidgets.QPushButton(button_text))
            getattr(self, button_name).clicked.connect(self.__push_button)

            # Add Button to Widget
            self.ButtonsLayout.addWidget(getattr(self, button_name))

        # Init Buffer
        self.buffer = io.StringIO()
        self.__set_enable_gui(False)

        # RC Server
        self.__remote = None
        self.__send_queue = queue.PriorityQueue()
        self.__event_ready_to_go = threading.Event()
        if remote:
            self.__remote = RCServer()
            self.__remote.start()
            self.__remote_exchange()

        self.showNormal()

    def __set_enable_gui(self, state=True):
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
            self.__set_enable_gui(True)
        # Reset Buffer
        self.__reset_buffer()
        # Check Position
        while self.buffer.tell() == 0:
            QtCore.QCoreApplication.processEvents()
        value = self.buffer.getvalue()
        # Log all Inputs from Buffer
        LOGGER.info(value)
        return value

    def __key_press_event(self, event):
        """

        :param event:
        :return:
        """
        # Get Last Line
        document = self.console.document()
        line_index = document.lineCount()
        raw_last_line = document.findBlockByLineNumber(line_index - 1).text()

        text = ''
        current_hook = ''
        # Exclude first 6 chars: (Pdb)\s
        if raw_last_line:
            for hook in self.HOOKS:
                if raw_last_line.startswith(hook):
                    current_hook = hook
                    text = raw_last_line[len(hook):]
                    break
            else:
                text = raw_last_line

        # Get Cursor position
        line_from_zero = line_index - 1
        current_cursor_line = self.console.textCursor().blockNumber()
        current_cursor_column = self.console.textCursor().columnNumber()

        # If Enter was pressed -> Process Expression
        if event.key() == QtCore.Qt.Key_Return and text:
            # Consider Custom Clear Screen Command
            if text == self.CLEAR_SCREEN:
                self.__clear_screen(raw_last_line)
                return

            # Replace Line Break with Enter
            if self.HOOK_LINE_BREAK == text:
                text = '\r\n'
            elif self.HOOK_LINE_BREAK in text:
                # Replace Line Break with tab
                text = text.replace(self.HOOK_LINE_BREAK, '\t')
                current_hook = self.HOOK_LINE_BREAK

            self.__reset_buffer()
            self.buffer.write(text)
            self.__set_enable_gui(False)

        # If User want to delete something and there is no value in buffer -> Reject
        if event.key() == QtCore.Qt.Key_Backspace or event.key() == QtCore.Qt.Key_Delete:
            if current_cursor_line != line_from_zero or current_cursor_column <= len(current_hook):
                return

        if event.key() == QtCore.Qt.Key_Home and current_cursor_line == line_from_zero:
            if text:
                temp_cursor = self.console.textCursor()
                temp_cursor.movePosition(
                    QtGui.QTextCursor.MoveAnchor.StartOfLine,
                    QtGui.QTextCursor.MoveMode.MoveAnchor
                )
                temp_cursor.movePosition(
                    QtGui.QTextCursor.MoveOperation.Right,
                    QtGui.QTextCursor.MoveMode.MoveAnchor,
                    len(current_hook)
                )
                self.console.setTextCursor(temp_cursor)
            return

        # Set Console Text to Black
        self.console.setTextColor(QtCore.Qt.GlobalColor.black)
        # Execute default method
        QtWidgets.QTextEdit.keyPressEvent(self.console, event)

    def __remote_exchange(self):
        def __thread_poll():
            while True:
                # Receive Data
                data = self.__remote.receive()
                if data:
                    # Set Event Ready to Go -> Allow queue to store entries and send it back
                    self.__event_ready_to_go.set()
                    # Write Data into Buffer
                    self.__reset_buffer()
                    self.buffer.write(data)
                    # Write Data into Console also
                    self.console.insertPlainText('RC: {}\n'.format(data))
                    self.__set_enable_gui(False)

                    messages = []
                    # Wait to have something in queue
                    while self.__send_queue.empty():
                        time.sleep(0.01)
                    while not self.__send_queue.empty() and messages.count(self.HOOK_HEADER) <= 2:
                        __item = self.__send_queue.get_nowait()
                        if messages.count(self.HOOK_HEADER) > 1 and __item == self.HOOK_HEADER:
                            break
                        messages.append(__item)
                        # Give some time to fill all the value in queue
                        time.sleep(0.01)
                    message = ''.join(reversed(messages))
                    self.__remote.send(message)
                    self.__event_ready_to_go.clear()

        threading.Thread(name='HelpUs_RemoteReceive', target=__thread_poll, daemon=True).start()

    def __push_button(self):
        # Read text from Button and use it as pdb keyword
        button_scope = self.sender().text().lower()
        self.__reset_buffer()
        self.buffer.write(button_scope)
        self.__set_enable_gui(False)

    def __reset_buffer(self):
        if isinstance(self.buffer, io.StringIO):
            # Clear Buffer
            self.buffer.truncate(0)
            self.buffer.seek(0)
        else:
            self.buffer = io.StringIO()

    def __insert_plain_text(self, message):
        # Send Output To RCServer
        if self.__remote and self.__event_ready_to_go.is_set():
            self.__send_queue.put_nowait(item=message)

        # Do some stylistics
        if message.startswith(self.HOOK_HEADER):
            self.console.setTextColor(QtCore.Qt.GlobalColor.magenta)
            QtWidgets.QTextEdit.insertPlainText(self.console, message)
            return
        elif message.startswith(self.HOOK_INTERACT):
            self.console.setTextColor(QtCore.Qt.GlobalColor.darkMagenta)
            QtWidgets.QTextEdit.insertPlainText(self.console, message)
            return
        elif not message.startswith('RC: ') and message.strip():
            # Log outputs
            LOGGER.info(message)

        if message.startswith(self.HOOK_ERROR):
            self.console.setTextColor(QtCore.Qt.GlobalColor.red)

        QtWidgets.QTextEdit.insertPlainText(self.console, message)
        # AutoScroll
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def __clear_screen(self, text):
        current_hook = text
        for hook in self.HOOKS:
            if hook in current_hook:
                current_hook = hook
                break
        self.console.clear()
        self.console.insertPlainText(current_hook)


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
