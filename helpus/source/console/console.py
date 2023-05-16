import io
import logging
import re
from typing import Callable

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QEvent
from PySide6.QtGui import QClipboard, Qt, QTextCursor
from PySide6.QtWidgets import QApplication

from helpus import not_used
from helpus.source.console.commandhistory import CommandHistory
from helpus.source.console.syntax import SyntaxHighlighter

LOGGER = logging.getLogger('HelpUs')


class BaseConsole(QtWidgets.QTextEdit):
    HOOK_PDB = "(Pdb) "
    HOOK_INTERACT = '>>> '
    HOOK_LINE_BREAK = '... '
    HOOK_ERROR = '***'
    HOOKS = [HOOK_PDB, ]

    CLEAR_SCREEN = 'cls'

    def __init__(self, stream: Callable = None, *args):
        super(BaseConsole, self).__init__(*args)
        # Vars
        self._current_header = BaseConsole.HOOK_PDB
        self._default_position = 0
        self._tab_chars = ' ' * 4

        # Do not Accept Rich Text
        self.setAcceptRichText(False)
        self.command_history = CommandHistory(self)
        # HelpUs Buffer
        self.stdin = io.StringIO()

        # Method for stream
        self.stream = stream

        # Event Filter
        self.installEventFilter(self)
        self._key_event_handlers = self._get_key_event_handlers()

        # Store Current Char Text Format
        self.__default_ctf = self.currentCharFormat()

        # Set Focus
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        SyntaxHighlighter(self.document())

    def show_header(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        # Do some stylistics
        self.setTextColor(QtCore.Qt.GlobalColor.magenta)
        QtWidgets.QTextEdit.insertPlainText(self, self._current_header)
        self._default_position = cursor.position()

    def insertPlainText(self, text: str) -> None:
        # Look for HOOK_PDB even if this comes from recursive debugger
        _result = re.search(pattern=r'\({1,}Pdb\){1,}\s', string=text)
        self._current_header = _result.group(0) if _result else BaseConsole.HOOK_PDB

        if text == self._current_header:
            self.show_header()
            self.stream('')
            return

        # Stream Data
        self.stream(text.strip())

        if text.startswith(BaseConsole.HOOK_ERROR):
            self.setTextColor(QtCore.Qt.GlobalColor.red)
        elif not text.startswith('RC: ') and text.strip():
            self.setTextColor(QtCore.Qt.GlobalColor.black)
        elif text.strip():
            LOGGER.info(text)
            self.setTextColor(QtCore.Qt.GlobalColor.magenta)

        QtWidgets.QTextEdit.insertPlainText(self, text)
        # AutoScroll
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        self.ensureCursorVisible()

    def insertText(self, text):
        # Do not move cursor at the end
        # cursor = self.textCursor()
        # cursor.movePosition(QTextCursor.End)
        # self.setTextCursor(cursor)
        self.textCursor().insertText(text, self.__default_ctf)

    def eventFilter(self, edit, event):
        """Intercepts events from the input control."""
        if event.type() == QEvent.KeyPress:
            return bool(self._filter_keyPressEvent(event))
        elif event.type() == QEvent.MouseButtonPress:
            return bool(self._filter_mousePressEvent(event))
        else:
            return False

    def _get_key_event_handlers(self):
        return {
            Qt.Key_Escape:    self._handle_escape_key,
            Qt.Key_Return:    self._handle_enter_key,
            Qt.Key_Enter:     self._handle_enter_key,
            Qt.Key_Backspace: self._handle_backspace_key,
            Qt.Key_Delete:    self._handle_delete_key,
            Qt.Key_Home:      self._handle_home_key,
            Qt.Key_Tab:       self._handle_tab_key,
            Qt.Key_Backtab:   self._handle_backtab_key,
            Qt.Key_Up:        self._handle_up_key,
            Qt.Key_Down:      self._handle_down_key,
            Qt.Key_Left:      self._handle_left_key,
            Qt.Key_C:         self._handle_c_key,
            Qt.Key_V:         self._handle_v_key,
        }

    def insertFromMimeData(self, mime_data):
        if mime_data and mime_data.hasText():
            self.insertText(mime_data.text())

    def _filter_mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData(QClipboard.Selection)
            self.insertFromMimeData(mime_data)
            return True

    def _filter_keyPressEvent(self, event):
        key = event.key()
        event.ignore()

        handler = self._key_event_handlers.get(key)
        intercepted = handler and handler(event)

        # Assumes that Control+Key is a movement command, i.e. should not be
        # handled as text insertion. However, on win10 AltGr is reported as
        # Alt+Control which is why we handle this case like regular
        # keypresses, see #53:
        if not event.modifiers() & Qt.ControlModifier or \
                event.modifiers() & Qt.AltModifier:
            self._reset_cursor()

            if not intercepted and event.text():
                intercepted = True
                self.insertText(event.text())
                # self.insertPlainText(event.text())

        return intercepted

    def _handle_escape_key(self, event):
        not_used(self)
        not_used(event)
        return True

    def _handle_enter_key(self, event):
        """
        Handle Enter Key -> Send data to stdin buffer and store the command in history
        :param event:
        :return:
        """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        if event.modifiers() & Qt.ShiftModifier:
            self.insertText('\n')
        else:
            # Read Buffer
            buffer = self.input_buffer()
            # Check if clear screen is needed
            if buffer == BaseConsole.CLEAR_SCREEN:
                self.clear()
                self.show_header()
                return True
            # Store Input
            self.reset_stdin()
            self.stdin.write(buffer)
            self.insertText('\n')
            # Store History Command
            if buffer.count('\n') < 1:
                self.command_history.add(buffer)
        return True

    def _handle_backspace_key(self, event):
        """
        Backspace Key.
        :param event:
        :return:
        """
        self._reset_cursor()
        cursor = self.textCursor()
        offset = self.cursor_offset()
        if not cursor.hasSelection() and offset >= 1:
            tab = self._tab_chars
            buf = self._get_line_until_cursor()
            if event.modifiers() == Qt.ControlModifier:
                cursor.movePosition(
                    QTextCursor.PreviousWord,
                    QTextCursor.KeepAnchor,
                    1
                )
                self._reset_cursor()
            else:
                # delete spaces to previous tabstop boundary:
                tabstop = len(buf) % len(tab) == 0
                num = len(tab) if tabstop and buf.endswith(tab) else 1
                cursor.movePosition(
                    QTextCursor.PreviousCharacter,
                    QTextCursor.KeepAnchor,
                    num
                )
        self._remove_selected_input(cursor)
        return True

    def _handle_delete_key(self, event):
        """
        Delete Key
        :param event:
        :return:
        """
        self._reset_cursor()
        cursor = self.textCursor()
        offset = self.cursor_offset()
        if not cursor.hasSelection() and offset < len(self.input_buffer()):
            tab = self._tab_chars
            left = self._get_line_until_cursor()
            right = self._get_line_after_cursor()
            if event.modifiers() == Qt.ControlModifier:
                cursor.movePosition(
                    QTextCursor.NextWord,
                    QTextCursor.KeepAnchor, 1
                )
                self._reset_cursor()
            else:
                # delete spaces to next tabstop boundary:
                tabstop = len(left) % len(tab) == 0
                num = len(tab) if tabstop and right.startswith(tab) else 1
                cursor.movePosition(
                    QTextCursor.NextCharacter,
                    QTextCursor.KeepAnchor, num
                )
        self._remove_selected_input(cursor)
        return True

    def _handle_tab_key(self, event):
        """
        Tab Key -> 4 spaces.
        :param event:
        :return:
        """
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.setTextCursor(self._indent_selection(cursor))
        else:
            # add spaces until next tabstop boundary:
            tab = self._tab_chars
            buf = self._get_line_until_cursor()
            num = len(tab) - len(buf) % len(tab)
            self.insertText(tab[:num])
        event.accept()
        return True

    def _handle_backtab_key(self, event):
        not_used(event)
        self.setTextCursor(self._indent_selection(self.textCursor(), False))
        return True

    def _indent_selection(self, cursor, indent=True):
        buf = self.input_buffer()
        tab = self._tab_chars
        pos0 = cursor.selectionStart() - self._default_position
        pos1 = cursor.selectionEnd() - self._default_position
        line0 = buf[:pos0].count('\n')
        line1 = buf[:pos1].count('\n')
        lines = buf.split('\n')
        for i in range(line0, line1 + 1):
            # Although it at first seemed appealing to me to indent to the
            # next tab boundary, this leads to losing relative sub-tab
            # indentations and is therefore not desirable. We should therefore
            # always indent by a full tab:
            line = lines[i]
            if indent:
                lines[i] = tab + line
            else:
                lines[i] = line[:len(tab)].lstrip() + line[len(tab):]
            num = len(lines[i]) - len(line)
            pos0 += num if i == line0 else 0
            pos1 += num
        self.clear_input_buffer()
        self.insertText('\n'.join(lines))
        cursor.setPosition(self._default_position + pos0)
        cursor.setPosition(self._default_position + pos1, QTextCursor.KeepAnchor)
        return cursor

    def _handle_home_key(self, event):
        """
        Move Cursor at start of line + default_position
        :param event:
        :return:
        """
        select = event.modifiers() & Qt.ShiftModifier
        self._move_cursor(self._default_position, select)
        return True

    def _handle_up_key(self, event):
        shift = event.modifiers() & Qt.ShiftModifier
        if shift or '\n' in self.input_buffer()[:self.cursor_offset()]:
            self._move_cursor(QTextCursor.Up, select=shift)
        else:
            self.command_history.dec(self.input_buffer())
        return True

    def _handle_down_key(self, event):
        shift = event.modifiers() & Qt.ShiftModifier
        if shift or '\n' in self.input_buffer()[self.cursor_offset():]:
            self._move_cursor(QTextCursor.Down, select=shift)
        else:
            self.command_history.inc()
        return True

    def _handle_left_key(self, _event):
        """
        Move cursor to left but no more than self._default_position
        :param _event:
        :return:
        """
        return self.cursor_offset() > self._default_position

    def _handle_c_key(self, event):
        intercepted = False
        if event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier:
            self.copy()
            intercepted = True
        return intercepted

    def _handle_v_key(self, event):
        if (
                event.modifiers() == Qt.ControlModifier
                or event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier
        ):
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData(QClipboard.Clipboard)
            self.insertFromMimeData(mime_data)
            return True
        return False

    def _reset_cursor(self):
        cursor = self.textCursor()
        if cursor.anchor() < self._default_position:
            cursor.setPosition(self._default_position)
        if cursor.position() < self._default_position:
            cursor.setPosition(self._default_position, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def input_buffer(self):
        """Retrieve current input buffer in string form."""
        text = self.toPlainText()[self._default_position:]
        return text

    def clear_input_buffer(self):
        """Clear input buffer."""
        cursor = self.textCursor()
        cursor.setPosition(self._default_position)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        self._remove_selected_input(cursor)
        self.setTextCursor(cursor)

    def reset_stdin(self):
        if isinstance(self.stdin, io.StringIO):
            # Clear Buffer
            self.stdin.truncate(0)
            self.stdin.seek(0)
        else:
            self.stdin = io.StringIO()

    def cursor_offset(self):
        """Get current cursor index within input buffer."""
        return self.textCursor().position() - self._default_position

    def _move_cursor(self, position, select=False):
        cursor = self.textCursor()
        mode = QTextCursor.KeepAnchor if select else QTextCursor.MoveAnchor
        if isinstance(position, QTextCursor.MoveOperation):
            cursor.movePosition(position, mode)
        else:
            cursor.setPosition(position, mode)
        self.setTextCursor(cursor)
        self._reset_cursor()

    def _get_line_until_cursor(self):
        """Get current line of input buffer, up to cursor position."""
        return self.input_buffer()[:self.cursor_offset()].rsplit('\n', 1)[-1]

    def _get_line_after_cursor(self):
        """Get current line of input buffer, after cursor position."""
        return self.input_buffer()[self.cursor_offset():].split('\n', 1)[0]

    def _remove_selected_input(self, cursor):
        not_used(self)
        if not cursor.hasSelection():
            return

        # num_lines = cursor.selectedText().replace(u'\u2029', '\n').count('\n')
        cursor.removeSelectedText()

        # if num_lines > 0:
        #     block = cursor.blockNumber() + 1
        #     del self._prompt_doc[block:block + num_lines]
