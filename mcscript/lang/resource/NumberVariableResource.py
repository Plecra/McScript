from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.VariableResource import VariableResource

if TYPE_CHECKING:
    from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
    from mcscript.compiler.CompileState import CompileState


class NumberVariableResource(VariableResource):
    """
    Used when a number is stored as a variable
    """

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NUMBER

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        """ An efficient way to convert a storage number to a fixed is to load with a factor of 1000"""
        from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
        if self.isStatic:
            return FixedNumberResource.fromNumber(self.value)
        return FixedNumberResource(self._load(compileState, None, FixedNumberResource.BASE), False)

    def load(self, compileState: CompileState, stack: ValueResource = None) -> NumberResource:
        stack = self._load(compileState, stack)
        return NumberResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        stack = self._copy(compileState, target)
        if not isinstance(stack, NbtAddressResource):
            return stack
        return NumberVariableResource(target, False)
