from __future__ import annotations

from typing import Any, TYPE_CHECKING, Union

from mcscript.data.commands import Command, ExecuteCommand, multiple_commands
from mcscript.data.predicates.WeatherPredicate import WeatherPredicate
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.BooleanResource import BooleanResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class IsThundering(BuiltinFunction):
    """
    returns whether it is currently thundering
    """

    def __init__(self):
        super().__init__()
        self.thunderingPredicate = None

    def name(self) -> str:
        return "isThundering"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        stack = compileState.expressionStack.next()
        return FunctionResult(
            multiple_commands(
                Command.SET_VALUE(
                    stack=stack,
                    value=0
                ),
                Command.EXECUTE(
                    sub=ExecuteCommand.IF_PREDICATE(
                        predicate=self.thunderingPredicate
                    ),
                    command=Command.SET_VALUE(
                        stack=stack,
                        value=1
                    )
                )
            ), BooleanResource(stack, False)
        )

    def include(self, compileState: CompileState) -> Any:
        compileState.datapack.getUtilsDirectory().addWeatherPredicate()
        raining, thundering = WeatherPredicate().keys
        self.thunderingPredicate: str = thundering
