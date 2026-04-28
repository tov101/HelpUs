# -*- coding: utf-8 -*-
"""
Autocompleter for the PDB console.

Provides Tab / Ctrl+Space completion using:
  - Python keywords and builtins (static list from PythonSyntax)
  - Names from the active Pdb frame's locals and globals (live, via pdb.Pdb.curframe_locals)
"""

import inspect
import re

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QStringListModel
from PySide6.QtWidgets import QCompleter, QScrollBar

from helpus.source.console.syntax import PythonSyntax


class PdbCompleter(QtCore.QObject):
    """Autocompletion overlay for a BaseConsole widget."""

    _STATIC_NAMES = sorted(set(PythonSyntax.keywords) | set(PythonSyntax.builtins))

    def __init__(self, console):
        super().__init__(console)
        self._console = console

        self._model = QStringListModel(self)
        self._completer = QCompleter(self)
        self._completer.setModel(self._model)
        self._completer.setWidget(console)
        self._completer.setCaseSensitivity(Qt.CaseSensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.activated.connect(self._insert_completion)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trigger(self) -> bool:
        """Trigger completion at the current cursor position.

        Returns True if the popup was shown or a single match was inserted.
        """
        if not self._console.isEnabled():
            return False
        prefix = self._get_prefix()
        if not prefix:
            return False
        candidates = self._get_candidates(prefix)
        if not candidates:
            return False
        if len(candidates) == 1:
            self._insert_completion(candidates[0])
            return True
        self._model.setStringList(candidates)
        self._completer.setCompletionPrefix(prefix)
        popup = self._completer.popup()
        popup.setCurrentIndex(self._completer.completionModel().index(0, 0))
        rect = self._console.cursorRect()
        rect.setWidth(
            popup.sizeHintForColumn(0)
            + popup.verticalScrollBar().sizeHint().width()
        )
        self._completer.complete(rect)
        return True

    def update_prefix(self) -> None:
        """Re-filter the visible popup after the user types or deletes a character."""
        if not self._completer.popup().isVisible():
            return
        prefix = self._get_prefix()
        if not prefix:
            self._completer.popup().hide()
            return
        self._completer.setCompletionPrefix(prefix)
        if self._completer.completionCount() == 0:
            self._completer.popup().hide()
        else:
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0)
            )

    def accept_current(self) -> bool:
        """Insert the currently highlighted popup item.

        Returns True if an item was accepted, False if popup was not visible.
        """
        popup = self._completer.popup()
        if not popup.isVisible():
            return False
        idx = popup.currentIndex()
        if not idx.isValid():
            idx = self._completer.completionModel().index(0, 0)
        if idx.isValid():
            self._insert_completion(self._completer.completionModel().data(idx))
        popup.hide()
        return True

    def is_popup_visible(self) -> bool:
        return self._completer.popup().isVisible()

    def hide_popup(self) -> None:
        self._completer.popup().hide()

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
        prefix = self._get_prefix()
        cursor = self._console.textCursor()
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(prefix))
        self._console.setTextCursor(cursor)
        self._console.insertText(completion)
        self._completer.popup().hide()
