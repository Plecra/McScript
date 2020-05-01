from time import perf_counter
from typing import Any, Callable

import lark
from lark import Tree

from mcscript import Compiler, Grammar, Logger
from mcscript.Exceptions.compileExceptions import McScriptError
from mcscript.Exceptions.parseExceptions import McScriptParseException
from mcscript.analyzer.Analyzer import Analyzer
from mcscript.data.Config import Config
from mcscript.data.defaultCode import addDefaults
from mcscript.utils.Datapack import Datapack
from mcscript.utils.utils import debug_log_text

eventCallback = Callable[[str, float, Any], Any]


def compileMcScript(text: str, callback: eventCallback, config: Config) -> Datapack:
    """
    compiles a mcscript string and returns the generated datapack.

    Args:
        text: the script
        callback: a callback function that accepts the current state, the progress and the temporary object
        config: the config

    Returns:
        A datapack
    """
    steps = (
        (lambda string: _parseCode(string), "Parsing"),
        (lambda tree: Analyzer().analyze(tree), "Analyzing context"),
        (lambda tree: Compiler.compile(tree[0], tree[1], text, config), "Compiling"),
        (lambda datapack: addDefaults(datapack), "post processing")
    )

    debug_log_text(text, "[Compile] parsing the following code: ")

    arg = text
    for index, step in enumerate(steps):
        callback(step[1], index / len(steps), arg)
        start_time = perf_counter()
        try:
            arg = step[0](arg)
        except Exception as e:
            if not isinstance(e, McScriptError):
                Logger.critical(f"Exception occurred: {repr(e)}")
            raise e
        Logger.debug(f"{step[1]} finished in {perf_counter() - start_time:.4f} seconds")
        if isinstance(arg, Tree):
            _debug_log_tree(arg)

    callback("Done", 1, arg)
    # noinspection PyTypeChecker
    return arg


def _parseCode(code: str) -> Tree:
    try:
        # keeping tabs can produce error messages that are offset
        return Grammar.parse(code.replace("\t", "  "))
    except lark.exceptions.UnexpectedToken as e:
        raise McScriptParseException(e.line, e.column, code, e.expected, e.token) from None


def _debug_log_tree(tree: Tree):
    debug_log_text(tree.pretty(), "[Compile] Intermediate Tree:")
