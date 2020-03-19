from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.mcscript.data.builtins.builtins import BuiltinFunction, FunctionResult
from src.mcscript.lang.Resource.NullResource import NullResource
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.utils import PrintCommand, TextFormatter

if TYPE_CHECKING:
    from src.mcscript import CompileState


class TextFunction(BuiltinFunction, ABC):
    @abstractmethod
    def getCommand(self) -> PrintCommand:
        pass

    def returnType(self) -> ResourceType:
        return ResourceType.NULL

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        return FunctionResult(
            TextFormatter(compileState).createCommandFromResources(self.getCommand(), *parameters),
            resource=NullResource(),
            inline=True
        )


class PrintFunction(TextFunction):
    """
    Print Function.
    Arguments:
        *values: Strings or integers that will be printed.
    Example:
        aValue = 10
        print("Hello world! ", "The result is: ", aValue)
    """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.TELLRAW

    def name(self) -> str:
        return "print"


class TitleFunction(TextFunction):
    def getCommand(self) -> PrintCommand:
        return PrintCommand.TITLE

    def name(self) -> str:
        return "title"


class SubTitleFunction(TextFunction):
    def getCommand(self) -> PrintCommand:
        return PrintCommand.SUBTITLE

    def name(self) -> str:
        return "subtitle"


class ActionBarFunction(TextFunction):
    def getCommand(self) -> PrintCommand:
        return PrintCommand.ACTIONBAR

    def name(self) -> str:
        return "actionbar"