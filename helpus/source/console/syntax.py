from PySide6 import (
    QtCore,
    QtGui
)


def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QtGui.QColor()
    _color.setNamedColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QtGui.QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    # Python Keywords
    'keyword':            format('blue', 'bold'),
    'operator':           format('red'),
    'brace':              format('darkGray'),
    'defclass':           format('black', 'bold'),
    'string':             format('magenta'),
    'string2':            format('darkMagenta'),
    'comment':            format('green', 'italic'),
    'self':               format('darkMagenta'),
    'numbers':            format('brown'),
    # Evaluate Keywords
    'conditions':         format('magenta'),
    'triggers':           format('blue', 'bold'),
    'evaluators':         format('blue', 'bold'),
    'functions':          format('magenta', 'bold'),
    'hardcoded_triggers': format('darkGray', 'italic'),
    'e_operator':         format('blue')
}


class PythonSyntax:
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False', 'as',
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self):
        self._rules = []

        # Keyword, operator, and brace rules
        self._rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                        for w in PythonSyntax.keywords]
        self._rules += [(r'%s' % o, 0, STYLES['operator'])
                        for o in PythonSyntax.operators]
        self._rules += [(r'%s' % b, 0, STYLES['brace'])
                        for b in PythonSyntax.braces]

        # All other rules
        self._rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),
        ]

    def __iter__(self):
        return iter(self._rules)


class SyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    SYNTAX_PYTHON = 'python'
    SYNTAX_EVALUATE = 'evaluate'

    def __init__(self, parent: QtGui.QTextDocument) -> None:
        super().__init__(parent)

        # Multi-line strings (expression, flag, style)
        self.tri_single = (QtCore.QRegularExpression("'''"), 1, STYLES['string2'])
        self.tri_double = (QtCore.QRegularExpression('"""'), 2, STYLES['string2'])

        # All other rules
        self.rules = [(QtCore.QRegularExpression(pat), index, fmt)
                      for (pat, index, fmt) in PythonSyntax()]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        self.tripleQuoutesWithinStrings = []
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.match(text, 0).capturedStart()
            if index >= 0:
                # if there is a string we check
                # if there are some triple quotes within the string
                # they will be ignored if they are matched again
                if expression.pattern() in [r'"[^"\\]*(\\.[^"\\]*)*"', r"'[^'\\]*(\\.[^'\\]*)*'"]:
                    innerIndex = self.tri_single[0].match(text, index + 1).capturedStart()
                    if innerIndex == -1:
                        innerIndex = self.tri_double[0].match(text, index + 1).capturedStart()

                    if innerIndex != -1:
                        tripleQuoteIndexes = range(innerIndex, innerIndex + 3)
                        self.tripleQuoutesWithinStrings.extend(tripleQuoteIndexes)

            while isinstance(index, int) and index >= 0:
                # skipping triple quotes within strings
                if index in self.tripleQuoutesWithinStrings:
                    index += 1
                    expression.match(text, index).capturedStart()
                    continue

                # We actually want the index of the nth match
                expression_match = expression.match(text, index)
                index = expression_match.capturedStart(nth)
                length = expression_match.capturedLength(nth)
                self.setFormat(index, length, format)
                index = expression.match(text, index + length).capturedStart()

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegularExpressionMatch`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            delimiter_match = delimiter.match(text)
            start = delimiter_match.capturedStart()
            # skipping triple quotes within strings
            if start in self.tripleQuoutesWithinStrings:
                return False
            # Move past this match
            add = delimiter_match.capturedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            delimiter_match = delimiter.match(text, start + add)
            end = delimiter_match.capturedEnd()
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter_match.capturedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.match(text, start + length).capturedStart()

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        return False
