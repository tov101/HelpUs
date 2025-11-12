# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
    QUrl,
)
from qtpy.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import resource_rc


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(1038, 500)
        icon = QIcon()
        icon.addFile(":/snake.ico", QSize(), QIcon.Normal, QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.gridLayout_3 = QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.splitter_2 = QSplitter(Dialog)
        self.splitter_2.setObjectName("splitter_2")
        self.splitter_2.setOrientation(Qt.Vertical)
        self.splitter_2.setChildrenCollapsible(False)
        self.splitter = QSplitter(self.splitter_2)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.groupBox = QGroupBox(self.splitter)
        self.groupBox.setObjectName("groupBox")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.lw_frames = QListWidget(self.groupBox)
        self.lw_frames.setObjectName("lw_frames")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lw_frames.sizePolicy().hasHeightForWidth())
        self.lw_frames.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.lw_frames, 0, 0, 1, 1)

        self.splitter.addWidget(self.groupBox)
        self.line = QFrame(self.splitter)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.splitter.addWidget(self.line)
        self.groupBox_2 = QGroupBox(self.splitter)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.tw_objects = QTreeWidget(self.groupBox_2)
        font = QFont()
        font.setBold(True)
        font.setItalic(False)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setFont(2, font)
        __qtreewidgetitem.setFont(1, font)
        __qtreewidgetitem.setFont(0, font)
        self.tw_objects.setHeaderItem(__qtreewidgetitem)
        self.tw_objects.setObjectName("tw_objects")
        self.tw_objects.setProperty("showDropIndicator", False)
        self.tw_objects.setAlternatingRowColors(True)
        self.tw_objects.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tw_objects.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tw_objects.setIndentation(10)
        self.tw_objects.setUniformRowHeights(True)
        self.tw_objects.setAnimated(False)
        self.tw_objects.setAllColumnsShowFocus(False)
        self.tw_objects.setHeaderHidden(False)
        self.tw_objects.header().setVisible(True)
        self.tw_objects.header().setHighlightSections(False)

        self.gridLayout_2.addWidget(self.tw_objects, 0, 0, 1, 1)

        self.splitter.addWidget(self.groupBox_2)
        self.splitter_2.addWidget(self.splitter)
        self.line_2 = QFrame(self.splitter_2)
        self.line_2.setObjectName("line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)
        self.splitter_2.addWidget(self.line_2)
        self.groupBox_3 = QGroupBox(self.splitter_2)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout = QHBoxLayout(self.groupBox_3)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.pb_continue = QPushButton(self.groupBox_3)
        self.pb_continue.setObjectName("pb_continue")

        self.verticalLayout.addWidget(self.pb_continue)

        self.pb_next = QPushButton(self.groupBox_3)
        self.pb_next.setObjectName("pb_next")

        self.verticalLayout.addWidget(self.pb_next)

        self.pb_step = QPushButton(self.groupBox_3)
        self.pb_step.setObjectName("pb_step")

        self.verticalLayout.addWidget(self.pb_step)

        self.pb_where = QPushButton(self.groupBox_3)
        self.pb_where.setObjectName("pb_where")

        self.verticalLayout.addWidget(self.pb_where)

        self.pb_up = QPushButton(self.groupBox_3)
        self.pb_up.setObjectName("pb_up")

        self.verticalLayout.addWidget(self.pb_up)

        self.pb_down = QPushButton(self.groupBox_3)
        self.pb_down.setObjectName("pb_down")

        self.verticalLayout.addWidget(self.pb_down)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.te_console = QTextEdit(self.groupBox_3)
        self.te_console.setObjectName("te_console")

        self.horizontalLayout.addWidget(self.te_console)

        self.splitter_2.addWidget(self.groupBox_3)

        self.gridLayout_3.addWidget(self.splitter_2, 0, 0, 1, 1)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)

    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Dialog", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", "Frames", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", "Objects", None))
        ___qtreewidgetitem = self.tw_objects.headerItem()
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("Dialog", "Value", None))
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("Dialog", "Object", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("Dialog", "Type", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Dialog", "Console", None))
        self.pb_continue.setText(QCoreApplication.translate("Dialog", "(c)ontinue", None))
        self.pb_next.setText(QCoreApplication.translate("Dialog", "(n)ext", None))
        self.pb_step.setText(QCoreApplication.translate("Dialog", "(s)tep", None))
        self.pb_where.setText(QCoreApplication.translate("Dialog", "(w)here", None))
        self.pb_up.setText(QCoreApplication.translate("Dialog", "(u)p", None))
        self.pb_down.setText(QCoreApplication.translate("Dialog", "(d)own", None))

    # retranslateUi
