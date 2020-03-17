from __future__ import annotations

from typing import Union, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptTypeError
from src.mcscript.data.Commands import Command, Struct, Operator, multiple_commands
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.Protocols import ExplicitNumberProtocol
from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript.lang.Resource.NumberResource import NumberResource
    from src.mcscript import CompileState
    from src.mcscript.lang.Resource.FixedNumberVariableResource import FixedNumberVariableResource


class FixedNumberResource(ValueResource, ExplicitNumberProtocol):
    """
    A Fixed number: used for calculations with rational numbers.
    The current precision is not great (1/1024) and the number should be kept as small as possible
    Edit: maybe the lower precision of 1 / 1000 is better, since the amount values that can be expressed exactly
    is usually better.
    Behavior:
        - if both numbers are static, do the entire operation statically
        - if one of the numbers is static, do the entire operation as no number was static
        - operations with other fixed numbers will produce fixed numbers
        - operations with other values will call toFixed of that resource and then do the operation
    """
    BASE = 1000

    def embed(self) -> str:
        return str("{:.8f}".format(self.value / self.BASE) if self.isStatic else self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, int)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FIXED_POINT

    @classmethod
    def fromNumber(cls, number: Union[int, float]) -> FixedNumberResource:
        return FixedNumberResource(int(round(number * cls.BASE)), True)

    def convertToNumber(self, compileState: CompileState) -> NumberResource:
        from src.mcscript.lang.Resource.NumberResource import NumberResource
        if self.isStatic:
            return NumberResource(self.value // self.BASE, True)

        tmpStack = compileState.expressionStack.next()
        compileState.writeline(Command.SET_VALUE(stack=tmpStack, value=self.BASE))
        compileState.writeline(Command.OPERATION(
            stack=self.value,
            operator=Operator.DIVIDE.value,
            stack2=tmpStack
        ))
        compileState.expressionStack.previous()
        return NumberResource(self.value, False)

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        return self

    def storeToNbt(self, stack: AddressResource, compileState: CompileState) -> FixedNumberVariableResource:
        from src.mcscript.lang.Resource.FixedNumberVariableResource import FixedNumberVariableResource

        if self.isStatic:
            compileState.writeline(Command.SET_VARIABLE(struct=Struct.VAR(
                var=stack,
                value=self.value
            )))
        else:
            compileState.writeline(
                Command.SET_VARIABLE_FROM(var=stack, command=Command.GET_SCOREBOARD_VALUE(stack=self.value))
            )
        return FixedNumberVariableResource(stack, False)

    def operation_plus(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.value + other.value, True)

        a, b = self, other
        if a.isStatic:
            a, b = b, a

        # if one of the values is static, just do scoreboard players add
        if b.isStatic:
            command = Command.ADD_SCORE if b.value >= 0 else Command.REMOVE_SCORE
            compileState.writeline(command(stack=a.value, value=abs(b.value)))
            return a

        # else do a normal operation
        compileState.writeline(Command.OPERATION(
            stack=a.value,
            operator=Operator.PLUS.value,
            stack2=b.value
        ))
        return a

    def operation_minus(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.value - other.value, True)
        a, b = self, other
        if a.isStatic:
            a, b = b, a

        # if one of the values is static, just do scoreboard players add
        if b.isStatic:
            command = Command.ADD_SCORE if b.value <= 0 else Command.REMOVE_SCORE
            compileState.writeline(command(stack=a.value, value=abs(b.value)))
            return a

        # else do a normal operation
        compileState.writeline(Command.OPERATION(
            stack=a.value,
            operator=Operator.MINUS.value,
            stack2=b.value
        ))
        return a

    def operation_times(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.value * other.value // self.BASE, True)

        # 1. a *= b
        # 2. a += base // 2 (for correct rounding, round(a) = int(a+0.5)), rounding not implemented for now
        # 3. c = base, ToDo only set base once globally
        # 4. a /= c

        a = self.toScoreboard(compileState)
        b = other.toScoreboard(compileState)

        tmpStack = compileState.expressionStack.next()
        compileState.writeline(multiple_commands(
            Command.OPERATION(
                stack=a.value,
                operator=Operator.TIMES.value,
                stack2=b.value
            ),
            # Command.ADD_SCORE(
            #     stack=a.value,
            #     value=self.BASE // 2
            # ),
            Command.SET_VALUE(
                stack=tmpStack,
                value=FixedNumberResource.BASE
            ),
            Command.OPERATION(
                stack=a.value,
                operator=Operator.DIVIDE.value,
                stack2=tmpStack
            )
        ))
        compileState.expressionStack.previous()
        return a

    def operation_divide(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.value * self.BASE // other.value, True)

        a = self.toScoreboard(compileState)
        b = other.toScoreboard(compileState)

        tmpStack = compileState.expressionStack.next()
        compileState.writeline(multiple_commands(
            Command.SET_VALUE(
                stack=tmpStack,
                value=FixedNumberResource.BASE
            ),
            Command.OPERATION(
                stack=a.value,
                operator=Operator.TIMES.value,
                stack2=tmpStack
            ),
            Command.OPERATION(
                stack=a.value,
                operator=Operator.DIVIDE.value,
                stack2=b.value
            )
        ))
        compileState.expressionStack.previous()
        return a

    def operation_modulo(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.value % other.value, True)

        a = self.toScoreboard(compileState)
        b = other.toScoreboard(compileState)

        compileState.writeline(Command.OPERATION(
            stack=a,
            operator=Operator.MODULO.value,
            stack2=b
        ))
        return a

    def toScoreboard(self, compileState) -> FixedNumberResource:
        if not self.isStatic:
            return self

        stack = compileState.expressionStack.next()
        compileState.writeline(Command.SET_VALUE(stack=stack, value=self.value))
        return FixedNumberResource(stack, False)

    def toNumber(self) -> int:
        # is this really what should happen?
        # update comparisons for custom implementations
        if self.isStatic:
            return self.value
        raise TypeError

    def _checkOther(self, other: ValueResource, compileState: CompileState) -> FixedNumberResource:
        if hasattr(other, "convertToFixedNumber"):
            return other.convertToFixedNumber(compileState)

        raise McScriptTypeError(f"Expected a type that can be converted to a fixed point number but got {repr(other)}")
