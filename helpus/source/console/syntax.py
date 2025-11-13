# -*- coding: utf-8 -*-
"""
PyCharm-like Python syntax highlighter implemented with qtpy.

- Uses qtpy to support PySide2/PySide6/PyQt5/PyQt6 transparently.
- Highlights Python 3 keywords, operators, braces, builtins, numbers, strings (incl. raw/bytes/f/f-strings),
  decorators, imports, self/cls, type hints, and multi-line triple-quoted strings.
- Includes fixes for consistent string patterns and pre-detection of triple quotes within single-line strings.

Usage:
    document = QtGui.QTextDocument()
    highlighter = SyntaxHighlighter(document)
"""

from qtpy import QtCore, QtGui


def make_format(color: str, style: str = "") -> QtGui.QTextCharFormat:
    """Return a QTextCharFormat with the given attributes."""
    _color = QtGui.QColor()
    _color.setNamedColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if "bold" in style:
        # Qt6 enum lives under QFont.Weight; qtpy maps it but keep try/except for broader compat
        try:
            _format.setFontWeight(QtGui.QFont.Weight.Bold)
        except AttributeError:
            _format.setFontWeight(QtGui.QFont.Bold)
    if "italic" in style:
        _format.setFontItalic(True)

    return _format


STYLES = {
    "dark": {
        # Python core (Adapted for dark background contrast)
        "keyword": make_format(
            "#C46638",
        ),
        "operator": make_format("white"),
        "brace": make_format("lightGray"),
        "defclass": make_format(
            "#56A8F5",
        ),
        "decorator": make_format(
            "yellow",
        ),
        "string": make_format("#66A46F"),
        "fstring_expr": make_format(
            "darkGreen",
        ),
        "string2": make_format("#66A46F"),
        "comment": make_format("gray", "italic"),
        "self": make_format("#D146B7"),
        "numbers": make_format("teal"),
        "builtin": make_format(
            "#4D6DC5",
        ),
        "type_hint": make_format("lightBlue"),
        "import_as": make_format("orange"),
    },
    "light": {
        # Python core
        "keyword": make_format(
            "blue",
        ),
        "operator": make_format("red"),
        "brace": make_format("darkGray"),
        "defclass": make_format(
            "black",
        ),
        "decorator": make_format(
            "darkMagenta",
        ),
        "string": make_format("magenta"),
        "fstring_expr": make_format(
            "darkMagenta",
        ),
        "string2": make_format("darkMagenta"),
        "comment": make_format("forestgreen", "italic"),
        "self": make_format("darkMagenta"),
        "numbers": make_format("brown"),
        "builtin": make_format(
            "darkCyan",
        ),
        "type_hint": make_format("darkCyan"),
        "import_as": make_format("blue"),
    },
}


class PythonSyntax:
    # Python keywords (Py3, including async/await, nonlocal, with, match/case)
    keywords = [
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
        "match",
        "case",
    ]

    # Common builtins as per Py3, highlighted distinctly
    builtins = [
        # Types
        "bool",
        "bytearray",
        "bytes",
        "classmethod",
        "complex",
        "dict",
        "enumerate",
        "filter",
        "float",
        "frozenset",
        "int",
        "list",
        "map",
        "memoryview",
        "object",
        "property",
        "range",
        "reversed",
        "set",
        "slice",
        "staticmethod",
        "str",
        "super",
        "tuple",
        "type",
        "zip",
        # Functions/consts
        "abs",
        "all",
        "any",
        "ascii",
        "bin",
        "breakpoint",
        "callable",
        "chr",
        "compile",
        "delattr",
        "dir",
        "divmod",
        "eval",
        "exec",
        "format",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "locals",
        "max",
        "min",
        "next",
        "oct",
        "open",
        "ord",
        "pow",
        "print",
        "repr",
        "round",
        "setattr",
        "sorted",
        "sum",
        "vars",
        "__import__",
        # Exceptions
        "BaseException",
        "Exception",
        "ArithmeticError",
        "BufferError",
        "LookupError",
        "AssertionError",
        "AttributeError",
        "EOFError",
        "FloatingPointError",
        "GeneratorExit",
        "ImportError",
        "ModuleNotFoundError",
        "IndexError",
        "KeyError",
        "KeyboardInterrupt",
        "MemoryError",
        "NameError",
        "NotImplementedError",
        "OSError",
        "OverflowError",
        "RecursionError",
        "ReferenceError",
        "RuntimeError",
        "StopIteration",
        "StopAsyncIteration",
        "SyntaxError",
        "IndentationError",
        "TabError",
        "SystemError",
        "SystemExit",
        "TypeError",
        "UnboundLocalError",
        "UnicodeError",
        "UnicodeEncodeError",
        "UnicodeDecodeError",
        "UnicodeTranslateError",
        "ValueError",
        "ZeroDivisionError",
        "EnvironmentError",
        "IOError",
        "BlockingIOError",
        "ChildProcessError",
        "ConnectionError",
        "BrokenPipeError",
        "ConnectionAbortedError",
        "ConnectionRefusedError",
        "ConnectionResetError",
        "FileExistsError",
        "FileNotFoundError",
        "InterruptedError",
        "IsADirectoryError",
        "NotADirectoryError",
        "PermissionError",
        "ProcessLookupError",
        "TimeoutError",
        # Sentinels
        "NotImplemented",
        "Ellipsis",
    ]

    # Operators including walrus, matrix mult
    operators = [
        "=",  # assignment
        # Comparison
        "==",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        # Arithmetic
        r"\+",
        "-",
        r"\*",
        "/",
        "//",
        r"\%",
        r"\*\*",
        # Matrix multiplication
        r"@",
        # In-place
        r"\+=",
        "-=",
        r"\*=",
        "/=",
        r"\%=",
        r"\*\*=",
        "//=",
        r"@=",
        r"\|=",
        r"\^=",
        r"\&=",
        r"<<=",
        r">>=",
        # Bitwise
        r"\^",
        r"\|",
        r"\&",
        r"\~",
        ">>",
        "<<",
        # Walrus
        r":=",
    ]

    # Braces and punctuation commonly colored as braces in PyCharm
    braces = [
        r"\{",
        r"\}",
        r"\(",
        r"\)",
        r"\[",
        r"\]",
        r"\:",
        r"\,",
        r"\.",
        r";",
    ]

    # Type hint identifiers (common from typing and typing_extensions)
    type_hint_idents = [
        "Optional",
        "Union",
        "Any",
        "Callable",
        "Iterable",
        "Iterator",
        "Sequence",
        "Mapping",
        "MutableMapping",
        "List",
        "Dict",
        "Tuple",
        "Set",
        "FrozenSet",
        "Type",
        "TypeVar",
        "Generic",
        "Protocol",
        "Literal",
        "Final",
        "ClassVar",
        "NoReturn",
        "Self",
        "Annotated",
        "TypedDict",
    ]

    # String patterns (single-line) kept consistent and correct
    STRING_PATTERNS = (
        # Plain strings
        r'"[^"\\]*(\\.[^"\\]*)*"',
        r"'[^'\\]*(\\.[^'\\]*)*'",
        # Raw strings
        r'r"[^"\\]*(\\.[^"\\]*)*"',
        r"r'[^'\\]*(\\.[^'\\]*)*'",
        # Byte strings
        r'b"[^"\\]*(\\.[^"\\]*)*"',
        r"b'[^'\\]*(\\.[^'\\]*)*'",
        # F-strings
        r'f"[^"\\]*(\\.[^"\\]*)*"',
        r"f'[^'\\]*(\\.[^'\\]*)*'",
    )

    def __init__(self, theme="dark"):
        self._rules = []

        self.set_theme(theme=theme)

    def set_theme(self, theme="dark"):
        # Keywords, operators, braces
        self._rules += [(r"\b%s\b" % w, 0, STYLES[theme]["keyword"]) for w in PythonSyntax.keywords]
        self._rules += [(r"%s" % o, 0, STYLES[theme]["operator"]) for o in PythonSyntax.operators]
        self._rules += [(r"%s" % b, 0, STYLES[theme]["brace"]) for b in PythonSyntax.braces]

        # Builtins
        self._rules += [(r"\b%s\b" % b, 0, STYLES[theme]["builtin"]) for b in PythonSyntax.builtins]

        # Type hints (identifiers often used in annotations)
        self._rules += [(r"\b%s\b" % t, 0, STYLES[theme]["type_hint"]) for t in PythonSyntax.type_hint_idents]

        # Other rules
        self._rules += [
            # self / cls
            (r"\bself\b", 0, STYLES[theme]["self"]),
            (r"\bcls\b", 0, STYLES[theme]["self"]),
            # decorators
            (r"^\s*@[\w\.]+", 0, STYLES[theme]["decorator"]),
            # import and from-import lines
            (r"\bimport\b\s+[\w\.]+(\s+\bas\b\s+\w+)?", 0, STYLES[theme]["import_as"]),
            (r"\bfrom\b\s+[\w\.]+\s+\bimport\b\s+[\w\*,\s]+", 0, STYLES[theme]["import_as"]),
            # def/class identifiers
            (r"\bdef\b\s+([A-Za-z_]\w*)", 1, STYLES[theme]["defclass"]),
            (r"\bclass\b\s+([A-Za-z_]\w*)", 1, STYLES[theme]["defclass"]),
            # Numeric literals (ints, hex, bin, oct, floats, underscores)
            (
                r"\b[+-]?(?:0[bB][01](?:_?[01])*|0[oO][0-7](?:_?[0-7])*|0[xX][0-9A-Fa-f](?:_?[0-9A-Fa-f])*|[0-9](?:_?[0-9])*)\b",
                0,
                STYLES[theme]["numbers"],
            ),
            (r"\b[+-]?(?:\d(?:_?\d)*)?\.(?:\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?\b", 0, STYLES[theme]["numbers"]),
            (r"\b[+-]?\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)\b", 0, STYLES[theme]["numbers"]),
            # From '#' until a newline
            (r"#.*", 0, STYLES[theme]["comment"]),
            # F-string expressions like {expr} inside f-strings (best-effort)
            (r"\{[^{}]*\}", 0, STYLES[theme]["fstring_expr"]),
        ]

        # Single-line string token rules
        self._rules += [(pat, 0, STYLES[theme]["string"]) for pat in PythonSyntax.STRING_PATTERNS]

    def __iter__(self):
        return iter(self._rules)


class SyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for Python language following PyCharm-like rules, using qtpy."""

    SYNTAX_PYTHON = "python"
    SYNTAX_EVALUATE = "evaluate"

    def __init__(self, parent: QtGui.QTextDocument, theme="dark") -> None:
        super().__init__(parent)

        # Multi-line string delimiters (triple single/double quotes), styled as string2
        self.tri_single = (QtCore.QRegularExpression("'''"), 1, STYLES[theme]["string2"])
        self.tri_double = (QtCore.QRegularExpression('"""'), 2, STYLES[theme]["string2"])

        # Compile all rules
        self.rules = [(QtCore.QRegularExpression(pat), index, fmt) for (pat, index, fmt) in PythonSyntax(theme=theme)]

        # Keep the exact set of patterns we treat as single-line strings
        self.single_line_string_patterns = set(PythonSyntax.STRING_PATTERNS)

    def highlightBlock(self, text: str) -> None:
        # Track triple quotes that appear inside a matched single-line string
        self.tripleQuoutesWithinStrings = []

        # Do not highlight responses
        if text.startswith(("-> ", "> ", "(Pdb)   ")):
            return

        # Pre-detect triple quotes inside single-line strings, so we can skip them
        for expression, _, _ in self.rules:
            patt = expression.pattern()
            if patt in self.single_line_string_patterns:
                m = expression.match(text, 0)
                start = m.capturedStart()
                if start >= 0:
                    inner_single = self.tri_single[0].match(text, start + 1).capturedStart()
                    inner_double = self.tri_double[0].match(text, start + 1).capturedStart()
                    innerIndex = inner_single if inner_single != -1 else inner_double
                    if innerIndex != -1:
                        self.tripleQuoutesWithinStrings.extend(range(innerIndex, innerIndex + 3))

        # Apply all single-line rules
        for expression, nth, fmt in self.rules:
            index = expression.match(text, 0).capturedStart()
            while isinstance(index, int) and index >= 0:
                # Skip triple quotes within already-matched strings
                if index in self.tripleQuoutesWithinStrings:
                    index = expression.match(text, index + 1).capturedStart()
                    continue

                m = expression.match(text, index)
                cap_start = m.capturedStart(nth)
                cap_len = m.capturedLength(nth)

                # Guard for -1 returns
                if cap_start < 0 or cap_len < 0:
                    break

                self.setFormat(cap_start, cap_len, fmt)
                next_from = cap_start + max(cap_len, 1)
                index = expression.match(text, next_from).capturedStart()

        self.setCurrentBlockState(0)

        # Multi-line strings
        if not self._match_multiline(text, *self.tri_single):
            self._match_multiline(text, *self.tri_double)

    def _match_multiline(
        self,
        text: str,
        delimiter: QtCore.QRegularExpression,
        in_state: int,
        style: QtGui.QTextCharFormat,
    ) -> bool:
        """Highlight multi-line strings between matching delimiters."""
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            dm = delimiter.match(text)
            start = dm.capturedStart()
            if start in getattr(self, "tripleQuoutesWithinStrings", []):
                return False
            add = dm.capturedLength()

        while start >= 0:
            dm_end = delimiter.match(text, start + add)
            end = dm_end.capturedEnd()
            if end >= add:
                # Found closing delimiter on this line
                length = end - start
                self.setCurrentBlockState(0)
            else:
                # No closing delimiter: continue in this state
                self.setCurrentBlockState(in_state)
                length = len(text) - start
            self.setFormat(start, length, style)
            start = delimiter.match(text, start + length).capturedStart()

        return self.currentBlockState() == in_state
