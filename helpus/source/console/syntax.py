# -*- coding: utf-8 -*-
"""
PyCharm-like Python syntax highlighter implemented with qtpy.

- Uses qtpy to support PySide2/PySide6/PyQt5/PyQt6 transparently.
- Highlights Python 3 keywords, operators, braces, builtins, numbers, strings
  (all valid prefix combinations: r/b/f/u/rb/br/rf/fr and their uppercase variants),
  decorators, imports, self/cls, dunder names, type hints, and multi-line
  triple-quoted strings.
- Triple-quote delimiters inside single-line strings or line comments are
  correctly ignored so they never trigger spurious multiline-string state.

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
        try:
            _format.setFontWeight(QtGui.QFont.Weight.Bold)
        except AttributeError:
            _format.setFontWeight(QtGui.QFont.Bold)
    if "italic" in style:
        _format.setFontItalic(True)

    return _format


STYLES = {
    "dark": {
        "keyword": make_format("#C46638"),
        "operator": make_format("white"),
        "brace": make_format("lightGray"),
        "defclass": make_format("#56A8F5"),
        "decorator": make_format("yellow"),
        "string": make_format("#66A46F"),
        "string2": make_format("#66A46F"),
        "comment": make_format("gray", "italic"),
        "self": make_format("#D146B7"),
        "numbers": make_format("teal"),
        "builtin": make_format("#4D6DC5"),
        "type_hint": make_format("lightBlue"),
        "import_as": make_format("orange"),
        "dunder": make_format("#A080D0"),
    },
    "light": {
        "keyword": make_format("blue"),
        "operator": make_format("red"),
        "brace": make_format("darkGray"),
        "defclass": make_format("black"),
        "decorator": make_format("darkMagenta"),
        "string": make_format("magenta"),
        "string2": make_format("darkMagenta"),
        "comment": make_format("forestgreen", "italic"),
        "self": make_format("darkMagenta"),
        "numbers": make_format("brown"),
        "builtin": make_format("darkCyan"),
        "type_hint": make_format("darkCyan"),
        "import_as": make_format("blue"),
        "dunder": make_format("darkBlue"),
    },
}

# ---------------------------------------------------------------------------
# String prefix helpers
# ---------------------------------------------------------------------------

_SQ_BODY = r"[^'\\]*(\\.[^'\\]*)*"
_DQ_BODY = r'[^"\\]*(\\.[^"\\]*)*'

# All valid single-line string prefixes in Python (case-insensitive combinations).
# Covers: plain, u, r, b, f, rb/br (raw-bytes), rf/fr (raw-f-string).
_STRING_PREFIXES = [
    "",
    "u", "U",
    "r", "R",
    "b", "B",
    "f", "F",
    "rb", "rB", "Rb", "RB",
    "br", "bR", "Br", "BR",
    "rf", "rF", "Rf", "RF",
    "fr", "fR", "Fr", "FR",
]


class PythonSyntax:
    # Python keywords (Py3, including async/await, nonlocal, match/case)
    keywords = [
        "False", "None", "True",
        "and", "as", "assert", "async", "await",
        "break", "case", "class", "continue",
        "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global",
        "if", "import", "in", "is",
        "lambda", "match", "nonlocal", "not",
        "or", "pass", "raise", "return",
        "try", "while", "with", "yield",
    ]

    # Common builtins
    builtins = [
        # Types
        "bool", "bytearray", "bytes", "classmethod", "complex", "dict",
        "enumerate", "filter", "float", "frozenset", "int", "list", "map",
        "memoryview", "object", "property", "range", "reversed", "set",
        "slice", "staticmethod", "str", "super", "tuple", "type", "zip",
        # Functions / constants
        "abs", "all", "any", "ascii", "bin", "breakpoint", "callable",
        "chr", "compile", "delattr", "dir", "divmod", "eval", "exec",
        "format", "getattr", "globals", "hasattr", "hash", "help", "hex",
        "id", "input", "isinstance", "issubclass", "iter", "len", "locals",
        "max", "min", "next", "oct", "open", "ord", "pow", "print", "repr",
        "round", "setattr", "sorted", "sum", "vars", "__import__",
        # Exceptions
        "BaseException", "Exception", "ArithmeticError", "BufferError",
        "LookupError", "AssertionError", "AttributeError", "EOFError",
        "FloatingPointError", "GeneratorExit", "ImportError",
        "ModuleNotFoundError", "IndexError", "KeyError", "KeyboardInterrupt",
        "MemoryError", "NameError", "NotImplementedError", "OSError",
        "OverflowError", "RecursionError", "ReferenceError", "RuntimeError",
        "StopIteration", "StopAsyncIteration", "SyntaxError",
        "IndentationError", "TabError", "SystemError", "SystemExit",
        "TypeError", "UnboundLocalError", "UnicodeError",
        "UnicodeEncodeError", "UnicodeDecodeError", "UnicodeTranslateError",
        "ValueError", "ZeroDivisionError", "EnvironmentError", "IOError",
        "BlockingIOError", "ChildProcessError", "ConnectionError",
        "BrokenPipeError", "ConnectionAbortedError", "ConnectionRefusedError",
        "ConnectionResetError", "FileExistsError", "FileNotFoundError",
        "InterruptedError", "IsADirectoryError", "NotADirectoryError",
        "PermissionError", "ProcessLookupError", "TimeoutError",
        # Sentinels
        "NotImplemented", "Ellipsis",
    ]

    # Operators: ordered so that longer / more specific patterns come AFTER
    # shorter ones; since setFormat overwrites previous formatting, the last
    # matching rule wins for any given character position.
    operators = [
        "=",          # assignment (overwritten by compound ops below)
        "==", "!=", "<", "<=", ">", ">=",
        r"\+", "-", r"\*", "/", "//", r"\%", r"\*\*",
        r"@",
        r"\+=", "-=", r"\*=", "/=", r"\%=", r"\*\*=", "//=", r"@=",
        r"\|=", r"\^=", r"\&=", r"<<=", r">>=",
        r"\^", r"\|", r"\&", r"\~", ">>", "<<",
        r":=",
    ]

    # Braces and punctuation
    braces = [r"\{", r"\}", r"\(", r"\)", r"\[", r"\]", r"\:", r"\,", r"\.", r";"]

    # Typing-module identifiers
    type_hint_idents = [
        "Optional", "Union", "Any", "Callable", "Iterable", "Iterator",
        "Sequence", "Mapping", "MutableMapping", "List", "Dict", "Tuple",
        "Set", "FrozenSet", "Type", "TypeVar", "Generic", "Protocol",
        "Literal", "Final", "ClassVar", "NoReturn", "Self", "Annotated",
        "TypedDict",
    ]

    # All valid single-line string patterns, generated from the prefix table.
    STRING_PATTERNS: tuple = tuple(
        [f"{p}'{_SQ_BODY}'" for p in _STRING_PREFIXES]
        + [f'{p}"{_DQ_BODY}"' for p in _STRING_PREFIXES]
    )

    def __init__(self, theme: str = "dark") -> None:
        self._rules: list = []
        self.set_theme(theme=theme)

    def set_theme(self, theme: str = "dark") -> None:
        """Rebuild all highlighting rules for the given theme."""
        self._rules = [(r"\b%s\b" % w, 0, STYLES[theme]["keyword"]) for w in PythonSyntax.keywords]
        self._rules += [(r"%s" % o, 0, STYLES[theme]["operator"]) for o in PythonSyntax.operators]
        self._rules += [(r"%s" % b, 0, STYLES[theme]["brace"]) for b in PythonSyntax.braces]
        self._rules += [(r"\b%s\b" % b, 0, STYLES[theme]["builtin"]) for b in PythonSyntax.builtins]
        self._rules += [(r"\b%s\b" % t, 0, STYLES[theme]["type_hint"]) for t in PythonSyntax.type_hint_idents]

        self._rules += [
            # Dunder names (__foo__) — comes after builtins so dunder color wins
            # for names like __import__, __name__, etc.
            (r"\b__\w+__\b", 0, STYLES[theme]["dunder"]),
            # self / cls
            (r"\bself\b", 0, STYLES[theme]["self"]),
            (r"\bcls\b", 0, STYLES[theme]["self"]),
            # Decorators
            (r"^\s*@[\w\.]+", 0, STYLES[theme]["decorator"]),
            # import / from-import lines
            (r"\bimport\b\s+[\w\.]+(\s+\bas\b\s+\w+)?", 0, STYLES[theme]["import_as"]),
            (r"\bfrom\b\s+[\w\.]+\s+\bimport\b\s+[\w\*,\s]+", 0, STYLES[theme]["import_as"]),
            # def / class names
            (r"\bdef\b\s+([A-Za-z_]\w*)", 1, STYLES[theme]["defclass"]),
            (r"\bclass\b\s+([A-Za-z_]\w*)", 1, STYLES[theme]["defclass"]),
            # ── Numbers ──────────────────────────────────────────────────────
            # Integer literals: decimal, hex, octal, binary (no sign prefix —
            # let the operator rules colour signs independently).
            (
                r"\b(?:0[bB][01](?:_?[01])*"
                r"|0[oO][0-7](?:_?[0-7])*"
                r"|0[xX][0-9A-Fa-f](?:_?[0-9A-Fa-f])*"
                r"|[0-9](?:_?[0-9])*)\b",
                0,
                STYLES[theme]["numbers"],
            ),
            # Float: digit(s) then dot, optional fraction and/or exponent.
            # e.g.  1.  1.0  1.0e5  1_000.5e-3
            # Uses lookahead (?=\W|$) instead of \b because the match may end
            # with '.' which is a non-word character, causing \b to fail.
            (
                r"\b\d(?:_?\d)*\.(?:\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?(?=\W|$)",
                0,
                STYLES[theme]["numbers"],
            ),
            # Float: dot then digit(s), optional exponent.  e.g.  .5  .5e3
            # Uses (?<!\w) to avoid matching attribute-access dots like  obj.5
            (
                r"(?<!\w)\.\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)?\b",
                0,
                STYLES[theme]["numbers"],
            ),
            # Float: pure scientific notation without a decimal point.  e.g.  1e5
            # Ordered AFTER the integer rule so it overwrites the bare-integer
            # colour for the digit prefix.
            (
                r"\b\d(?:_?\d)*[eE][+-]?\d(?:_?\d)*\b",
                0,
                STYLES[theme]["numbers"],
            ),
            # Comments
            (r"#.*", 0, STYLES[theme]["comment"]),
        ]

        # String rules last — they overwrite any keyword/operator colour that
        # falls inside a string literal (e.g. 'if' inside "if you want").
        self._rules += [(pat, 0, STYLES[theme]["string"]) for pat in PythonSyntax.STRING_PATTERNS]

    def __iter__(self):
        return iter(self._rules)


class SyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for Python, using qtpy."""

    def __init__(self, parent: QtGui.QTextDocument, theme: str = "dark") -> None:
        super().__init__(parent)

        # Triple-quote delimiters for multiline strings
        self.tri_single = (QtCore.QRegularExpression("'''"), 1, STYLES[theme]["string2"])
        self.tri_double = (QtCore.QRegularExpression('"""'), 2, STYLES[theme]["string2"])

        # Compiled single-line rules
        self.rules = [
            (QtCore.QRegularExpression(pat), index, fmt)
            for (pat, index, fmt) in PythonSyntax(theme=theme)
        ]
        self.single_line_string_patterns = set(PythonSyntax.STRING_PATTERNS)

        # Compiled comment-start detector (used inside highlightBlock)
        self._hash_re = QtCore.QRegularExpression(r"#")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def highlightBlock(self, text: str) -> None:
        # Skip PDB output / response lines — they should appear unstyled.
        if text.startswith(("-> ", "> ", "(Pdb)   ")):
            self.setCurrentBlockState(self.previousBlockState())
            return

        # Build the set of character positions that belong to a single-line
        # string literal or a line comment.  Triple-quote delimiters at these
        # positions must NOT trigger multiline-string block state.
        self.tripleQuotesWithinStrings: set = self._build_protected_positions(text)

        # Apply all single-line rules.  Rules are ordered so that the last
        # matching rule for any character position wins (setFormat overwrites).
        for expression, nth, fmt in self.rules:
            pos = 0
            while True:
                m = expression.match(text, pos)
                if not m.hasMatch():
                    break
                cap_start = m.capturedStart(nth)
                cap_len = m.capturedLength(nth)
                # Advance past the full match regardless of capture group result
                next_pos = m.capturedEnd()
                if next_pos <= pos:
                    next_pos = pos + 1
                if cap_start >= 0 and cap_len > 0:
                    self.setFormat(cap_start, cap_len, fmt)
                pos = next_pos

        self.setCurrentBlockState(0)

        if not self._match_multiline(text, *self.tri_single):
            self._match_multiline(text, *self.tri_double)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_protected_positions(self, text: str) -> set:
        """
        Return the set of character positions in *text* that lie inside a
        single-line string literal or a line comment.  Triple-quote delimiters
        at these positions should not start (or end) multiline-string state.
        """
        protected: set = set()

        # Collect spans covered by single-line string matches.
        string_spans: list = []
        for expression, _, _ in self.rules:
            if expression.pattern() not in self.single_line_string_patterns:
                continue
            pos = 0
            while True:
                m = expression.match(text, pos)
                if not m.hasMatch():
                    break
                s, e = m.capturedStart(), m.capturedEnd()
                protected.update(range(s, e))
                string_spans.append((s, e))
                pos = e if e > pos else pos + 1

        # Find the first '#' that is not itself inside a string — it starts a
        # line comment; everything from there to end-of-line is protected.
        pos = 0
        while True:
            hm = self._hash_re.match(text, pos)
            if not hm.hasMatch():
                break
            h = hm.capturedStart()
            if not any(s <= h < e for s, e in string_spans):
                protected.update(range(h, len(text)))
                break
            pos = h + 1

        return protected

    def _match_multiline(
        self,
        text: str,
        delimiter: QtCore.QRegularExpression,
        in_state: int,
        style: QtGui.QTextCharFormat,
    ) -> bool:
        """
        Highlight multi-line strings delimited by *delimiter* (''' or \"\"\").

        Returns True if this block ends inside a multiline string of this type.
        """
        ignored: set = getattr(self, "tripleQuotesWithinStrings", set())

        if self.previousBlockState() == in_state:
            # We are already inside a multiline string — the closing delimiter
            # is somewhere on this line (or the string continues further).
            start = 0
            add = 0
        else:
            # Search for the opening delimiter, skipping any that fall inside
            # a single-line string or comment.
            start, add = self._find_delimiter(text, delimiter, 0, ignored)
            if start < 0:
                return False

        while start >= 0:
            dm_end = delimiter.match(text, start + add)
            end = dm_end.capturedEnd()
            if end > start + add:
                # Closing delimiter found on this line.
                length = end - start
                self.setCurrentBlockState(0)
            else:
                # No closing delimiter — this multiline string continues.
                self.setCurrentBlockState(in_state)
                length = len(text) - start

            self.setFormat(start, length, style)

            if self.currentBlockState() == in_state:
                # No closing delimiter was found; nothing more to do.
                break

            # The multiline string closed on this line.  Look for another
            # opening delimiter further along (handles  '''a''' + '''b  ).
            next_start, next_add = self._find_delimiter(
                text, delimiter, start + length, ignored
            )
            start = next_start
            add = next_add

        return self.currentBlockState() == in_state

    @staticmethod
    def _find_delimiter(
        text: str,
        delimiter: QtCore.QRegularExpression,
        from_pos: int,
        ignored: set,
    ) -> tuple:
        """
        Find the first occurrence of *delimiter* in *text* starting at
        *from_pos* that is NOT at a position listed in *ignored*.

        Returns ``(start, length)`` of the found delimiter, or ``(-1, 0)``
        if no valid delimiter exists.
        """
        pos = from_pos
        while True:
            dm = delimiter.match(text, pos)
            if not dm.hasMatch():
                return -1, 0
            s = dm.capturedStart()
            if s not in ignored:
                return s, dm.capturedLength()
            pos = s + 1
