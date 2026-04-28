# -*- coding: utf-8 -*-
# Manually maintained — do NOT overwrite with pyside6-uic output.

from qtpy.QtCore import QCoreApplication, QMetaObject, QSize, Qt
from qtpy.QtGui import QFont, QIcon
from qtpy.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from . import resource_rc

# (label, attribute, pdb_command, tooltip)
_TOOLBAR_BUTTONS = [
    ("Continue", "pb_continue", "continue", "Continue execution  [c]"),
    ("Next",     "pb_next",     "next",     "Step over next line  [n]"),
    ("Step",     "pb_step",     "step",     "Step into function call  [s]"),
    ("Where",    "pb_where",    "where",    "Show current position  [w]"),
    ("Up",       "pb_up",       "up",       "Move up one stack frame  [u]"),
    ("Down",     "pb_down",     "down",     "Move down one stack frame  [d]"),
]


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(1200, 620)
        icon = QIcon()
        icon.addFile(":/snake.ico", QSize(), QIcon.Normal, QIcon.Off)
        Dialog.setWindowIcon(icon)

        # ── Root vertical layout ──────────────────────────────────────
        self.rootLayout = QVBoxLayout(Dialog)
        self.rootLayout.setContentsMargins(6, 6, 6, 6)
        self.rootLayout.setSpacing(4)

        # ── Toolbar ───────────────────────────────────────────────────
        self.toolbar = QFrame(Dialog)
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setFrameShape(QFrame.StyledPanel)
        self.toolbar.setFrameShadow(QFrame.Raised)
        self.toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbarLayout = QHBoxLayout(self.toolbar)
        self.toolbarLayout.setContentsMargins(6, 3, 6, 3)
        self.toolbarLayout.setSpacing(6)

        for label, attr, cmd, tip in _TOOLBAR_BUTTONS:
            btn = QPushButton(label, self.toolbar)
            btn.setObjectName(attr)
            btn.setToolTip(tip)
            btn.setProperty("pdb_command", cmd)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            setattr(self, attr, btn)
            self.toolbarLayout.addWidget(btn)

        self.toolbarLayout.addStretch()
        self.rootLayout.addWidget(self.toolbar, 0)   # no stretch

        # ── Three-column splitter ─────────────────────────────────────
        self.splitter = QSplitter(Qt.Horizontal, Dialog)
        self.splitter.setObjectName("splitter")
        self.splitter.setChildrenCollapsible(False)

        # Column 1 — Frames
        self.groupBox = QGroupBox("Frames", Dialog)
        self.groupBox.setObjectName("groupBox")
        framesLayout = QVBoxLayout(self.groupBox)
        framesLayout.setContentsMargins(4, 10, 4, 4)
        self.lw_frames = QListWidget(self.groupBox)
        self.lw_frames.setObjectName("lw_frames")
        framesLayout.addWidget(self.lw_frames)
        self.splitter.addWidget(self.groupBox)

        # Column 2 — Console
        self.groupBox_3 = QGroupBox("Console", Dialog)
        self.groupBox_3.setObjectName("groupBox_3")
        consoleLayout = QVBoxLayout(self.groupBox_3)
        consoleLayout.setContentsMargins(4, 10, 4, 4)
        self.te_console = QTextEdit(self.groupBox_3)
        self.te_console.setObjectName("te_console")
        consoleLayout.addWidget(self.te_console)
        self.splitter.addWidget(self.groupBox_3)

        # Column 3 — Variables (Locals / Globals tabs)
        self.groupBox_2 = QGroupBox("Variables", Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        varsLayout = QVBoxLayout(self.groupBox_2)
        varsLayout.setContentsMargins(4, 10, 4, 4)
        self.tab_variables = QTabWidget(self.groupBox_2)
        self.tab_variables.setObjectName("tab_variables")
        self.tw_objects = _make_var_tree(self.tab_variables)
        self.tw_globals = _make_var_tree(self.tab_variables)
        self.tab_variables.addTab(self.tw_objects, "Locals")
        self.tab_variables.addTab(self.tw_globals, "Globals")
        varsLayout.addWidget(self.tab_variables)
        self.splitter.addWidget(self.groupBox_2)

        # Column proportions: frames 20 %, console 50 %, variables 30 %
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setStretchFactor(2, 3)
        self.rootLayout.addWidget(self.splitter, 1)   # takes all remaining space

        self.retranslateUi(Dialog)
        QMetaObject.connectSlotsByName(Dialog)

    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Dialog", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", "Frames", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Dialog", "Console", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", "Variables", None))
        for label, attr, _cmd, _tip in _TOOLBAR_BUTTONS:
            getattr(self, attr).setText(QCoreApplication.translate("Dialog", label, None))
        for tree in (self.tw_objects, self.tw_globals):
            item = tree.headerItem()
            item.setText(0, QCoreApplication.translate("Dialog", "Type", None))
            item.setText(1, QCoreApplication.translate("Dialog", "Name", None))
            item.setText(2, QCoreApplication.translate("Dialog", "Value", None))

    # retranslateUi


def _make_var_tree(parent):
    """Create a consistently styled QTreeWidget for variable display."""
    tree = QTreeWidget(parent)
    bold = QFont()
    bold.setBold(True)
    header_item = QTreeWidgetItem(["", "", ""])
    for col in range(3):
        header_item.setFont(col, bold)
    tree.setHeaderItem(header_item)
    tree.setProperty("showDropIndicator", False)
    tree.setAlternatingRowColors(True)
    tree.setSelectionBehavior(QAbstractItemView.SelectItems)
    tree.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    tree.setIndentation(10)
    tree.setUniformRowHeights(True)
    tree.setAnimated(False)
    tree.setAllColumnsShowFocus(False)
    tree.setHeaderHidden(False)
    tree.header().setVisible(True)
    tree.header().setHighlightSections(False)
    return tree
