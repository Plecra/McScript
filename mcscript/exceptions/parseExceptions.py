from typing import List

from mcscript.exceptions.McScriptException import McScriptException


class McScriptParseException(McScriptException):
    def __init__(self, line: int, column: int, code: str, expected: List[str], got: str):
        code = code.split("\n")[line - 1]
        message = f"At line {line}, column {column}:\n" \
                  f"{code}\n" \
                  f"{' ' * max(column - 1, 0)}^\n" \
                  f"Got token '{''.join(got.split())}' but expected one of:\n\t- " + \
                  "\n\t- ".join(expected)
        super().__init__(message)
