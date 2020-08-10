from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.base.ResourceType import ResourceType

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.base.ResourceBase import Resource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class FixedPointFunction(BuiltinFunction):
    """
    parameter => value: Number
    Converts a number to a fixed-point number.
    """

    def name(self) -> str:
        return "fixed"

    def returnType(self) -> ResourceType:
        return ResourceType.FIXED_POINT

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        parameter: IntegerResource
        parameter, = parameters

        if parameter.isStatic:
            return FunctionResult(None, FixedNumberResource.fromNumber(parameter.value))

        return FunctionResult(
            None, parameter.convertToFixedNumber(compileState)
        )
