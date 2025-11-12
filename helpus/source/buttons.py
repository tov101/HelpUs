from qtpy import QtCore


class Buttons(QtCore.QObject):
    CONTINUE = "continue"
    NEXT = "next"
    STEP = "step"
    WHERE = "where"
    UP = "up"
    DOWN = "down"
    _BUTTONS = (CONTINUE, NEXT, STEP, WHERE, UP, DOWN)

    execute = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect Buttons
        for button_text in self._BUTTONS:
            # Create Button Name
            _button = getattr(self.parent(), f"pb_{button_text}")
            _button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            _button.clicked.connect(self.__request)

    def __contains__(self, item):
        return item in self._BUTTONS

    def __iter__(self):
        return (getattr(self.parent(), f"pb_{button_text}") for button_text in self._BUTTONS)

    def __request(self):
        button_scope = self.sender().text()
        button_scope = button_scope.replace("(", "")
        button_scope = button_scope.replace(")", "")
        self.execute.emit(button_scope)
