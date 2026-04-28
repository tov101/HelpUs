# -*- coding: utf-8 -*-
"""
Autocompleter for the PDB console.

Provides Tab / Ctrl+Space completion using:
  - Python keywords and builtins (static list from PythonSyntax)
  - Names from the active Pdb frame's locals and globals (live, via pdb.Pdb.curframe_locals)

Uses a plain QListWidget tooltip-popup to avoid the focus-stealing and coordinate
mapping issues that QCompleter has when combined with QTextEdit.
"""

import inspect
import re

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from helpus.source.console.syntax import PythonSyntax


class _CompletionPopup(QtWidgets.QListWidget):
    """Borderless floating list used as the completion dropdown.

    Uses Qt.ToolTip window flag so it never steals keyboard focus from the
    text editor — all key events continue to arrive at the editor widget.
    """

    item_accepted = QtCore.Signal(str)

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.ToolTip)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.itemClicked.connect(lambda item: self.item_accepted.emit(item.text()))

    def populate(self, candidates: list) -> None:
        self.clear()
        for c in candidates:
            self.addItem(c)
        if self.count():
            self.setCurrentRow(0)
        # Resize to content (capped at 8 visible rows)
        rows = min(self.count(), 8)
        row_h = self.sizeHintForRow(0) if self.count() else 20
        col_w = self.sizeHintForColumn(0) + 24
        self.setFixedSize(max(col_w, 120), rows * row_h + 4)

    def select_next(self) -> None:
        row = self.currentRow()
        if row < self.count() - 1:
            self.setCurrentRow(row + 1)

    def select_prev(self) -> None:
        row = self.currentRow()
        if row > 0:
            self.setCurrentRow(row - 1)

    def current_text(self) -> str:
        item = self.currentItem()
        return item.text() if item else ""


class PdbCompleter(QtCore.QObject):
    """Autocompletion controller for a BaseConsole widget."""

    _STATIC_NAMES = sorted(set(PythonSyntax.keywords) | set(PythonSyntax.builtins))

    def __init__(self, console):
        super().__init__(console)
        self._console = console
        self._popup = _CompletionPopup()
        self._popup.item_accepted.connect(self._insert_completion)
        self._prefix = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trigger(self) -> bool:
        """Trigger completion at the current cursor position.

        Returns True if a popup was shown or a single match was inserted directly.
        """
        if not self._console.isEnabled():
            return False
        prefix = self._get_prefix()
        if not prefix:
            return False
        candidates = self._get_candidates(prefix)
        if not candidates:
            return False
        self._prefix = prefix
        if len(candidates) == 1:
            self._insert_completion(candidates[0])
            return True
        self._popup.populate(candidates)
        # cursorRect() is in viewport coordinates; map to global for a top-level popup
        cursor_rect = self._console.cursorRect()
        global_pos = self._console.viewport().mapToGlobal(cursor_rect.bottomLeft())
        self._popup.move(global_pos)
        self._popup.show()
        return True

    def update_prefix(self) -> None:
        """Re-filter the visible popup after the user types or deletes a character."""
        if not self._popup.isVisible():
            return
        prefix = self._get_prefix()
        if not prefix:
            self._popup.hide()
            return
        candidates = self._get_candidates(prefix)
        if not candidates:
            self._popup.hide()
            return
        self._prefix = prefix
        self._popup.populate(candidates)

    def accept_current(self) -> bool:
        """Insert the currently highlighted popup item.

        Returns True if an item was accepted, False if the popup was not visible.
        """
        if not self._popup.isVisible():
            return False
        text = self._popup.current_text()
        if text:
            self._insert_completion(text)
        else:
            self._popup.hide()
        return True

    def select_next(self) -> None:
        self._popup.select_next()

    def select_prev(self) -> None:
        self._popup.select_prev()

    def is_popup_visible(self) -> bool:
        return self._popup.isVisible()

    def hide_popup(self) -> None:
        self._popup.hide()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_prefix(self) -> str:
        buf = self._console._get_line_until_cursor()
        m = re.search(r"\w+$", buf)
        return m.group(0) if m else ""

    def _get_candidates(self, prefix: str) -> list:
        names = set(self._STATIC_NAMES)
        locs, globs = self._get_pdb_frame_names()
        names.update(locs)
        names.update(globs)
        return sorted(n for n in names if n.startswith(prefix))

    def _get_pdb_frame_names(self):
        """Return (locals_names, globals_names) from the active Pdb frame."""
        try:
            import pdb as _pdb
            for fi in inspect.stack():
                obj = fi.frame.f_locals.get("self")
                if (
                    obj is not None
                    and isinstance(obj, _pdb.Pdb)
                    and getattr(obj, "curframe", None) is not None
                ):
                    return list(obj.curframe_locals.keys()), list(obj.curframe.f_globals.keys())
        except Exception:
            pass
        return [], []

    def _insert_completion(self, completion: str) -> None:
        prefix = self._prefix or self._get_prefix()
        cursor = self._console.textCursor()
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(prefix))
        self._console.setTextCursor(cursor)
        self._console.insertText(completion)
        self._popup.hide()
        self._prefix = ""
