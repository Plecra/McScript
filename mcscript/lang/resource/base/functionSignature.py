# ToDo: Those classes need refactoring, I dont like them
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from typing import List, Optional, Sequence, TYPE_CHECKING

from mcscript.exceptions.exceptions import McScriptArgumentError
from mcscript.lang.Type import Type
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class FunctionParameterMatch(Enum):
    MATCHES = auto()
    FAIL_MULTIPLE_PARAMETERS = auto()
    FAIL_NOT_ENOUGH_PARAMETERS = auto()
    FAIL_WRONG_TYPE = auto()
    MUST_NOT_BE_STATIC = auto()
    MUST_BE_STATIC = auto()


@dataclass(frozen=True)
class FunctionParameter:
    class ParameterCount(Enum):
        ONCE = auto()
        ARBITRARY = auto()
        ONE_OR_MORE = auto()

    class ResourceMode(Flag):
        STATIC = auto()
        NON_STATIC = auto()

    name: str
    type: Type
    count: FunctionParameter.ParameterCount = ParameterCount.ONCE
    defaultValue: Optional[Resource] = None
    accepts: FunctionParameter.ResourceMode = ResourceMode.STATIC | ResourceMode.NON_STATIC
    documentation: str = field(default="")

    def matchAgainst(self, parameters: Sequence[Resource]) -> FunctionParameterMatch:
        """
        returns True if the list of parameters matches.
        """
        if not parameters and self.count != self.ParameterCount.ARBITRARY:
            return FunctionParameterMatch.FAIL_NOT_ENOUGH_PARAMETERS

        if self.count in (FunctionParameter.ParameterCount.ARBITRARY, FunctionParameter.ParameterCount.ONE_OR_MORE):
            for i in parameters:
                if (result := self._check_parameter(i)) != FunctionParameterMatch.MATCHES:
                    if result == FunctionParameterMatch.FAIL_WRONG_TYPE:
                        return FunctionParameterMatch.FAIL_MULTIPLE_PARAMETERS
                    return result
            return FunctionParameterMatch.MATCHES

        return self._check_parameter(parameters[0])

    def _check_parameter(self, parameter: Resource) -> FunctionParameterMatch:
        if parameter.type().matches(self.type):
            if not isinstance(parameter, ValueResource):
                return FunctionParameterMatch.MATCHES
            if parameter.is_static:
                if self.accepts & self.ResourceMode.STATIC:
                    return FunctionParameterMatch.MATCHES
                return FunctionParameterMatch.MUST_NOT_BE_STATIC
            if self.accepts & self.ResourceMode.NON_STATIC:
                return FunctionParameterMatch.MATCHES
            return FunctionParameterMatch.MUST_BE_STATIC
        return FunctionParameterMatch.FAIL_WRONG_TYPE


@dataclass(unsafe_hash=True)
class FunctionSignature:
    parameters: Sequence[FunctionParameter]
    returnType: Type
    name: str = field(default="<unknown>")
    # if not None the type of the struct of this method, otherwise normal function
    self_type: Optional[Type] = field(default=None)
    documentation: str = field(default="")

    format_string: str = field(init=False, default="For function {function}\n"
                                                   "{signature}\n"
                                                   "called with {{}}\n"
                                                   "{{}}")

    def __post_init__(self):
        if self.is_method:
            self.parameters = [FunctionParameter("self", self.self_type, documentation="The self type")] + \
                              list(self.parameters)

        self.format_string = self.format_string.format(function=self.name, signature=self.signature_string())

    @property
    def is_method(self) -> bool:
        """ Returns whether this is a method (self_type is not None)"""
        return self.self_type is not None

    def signature_string(self) -> str:
        parameters = []
        for parameter in self.parameters:
            # count: * -> arbitrary; * -> one or more
            prefix = "*" if parameter.count == parameter.ParameterCount.ARBITRARY else \
                "+" if parameter.count == parameter.ParameterCount.ONE_OR_MORE else ""

            # exclamation mark if parameter is only static
            suffix = "!" if parameter.accepts == FunctionParameter.ResourceMode.STATIC else ""
            # default value if given
            suffix += f" = {parameter.defaultValue}" if parameter.defaultValue else ""

            parameters.append(f'{prefix}{parameter.name}: {parameter.type.name}{suffix}')

        return f"{'method' if self.is_method else 'fun'} {self.name}" \
               f"({', '.join(parameters)})" \
               f" -> {self.returnType.name}"

    def matchParameters(self, compileState: CompileState, parameters: Sequence[Resource]) -> List[Resource]:
        """
        Verifies that all parameters match the signature and returns the correct parameters (including default values)

        Raises:
            if the signature does not match the parameters

        Returns:
            A List of parameters
        """
        parameters = list(parameters)
        original_parameters = parameters[:]
        returnParameters = []
        usedParameters = []
        iterator = iter(self.parameters)
        for parameter in iterator:
            usedParameters.append(parameter)
            if not parameters and parameter.count != FunctionParameter.ParameterCount.ARBITRARY:
                break
            match = parameter.matchAgainst(parameters)
            if match == FunctionParameterMatch.MATCHES:
                if parameter.count in (parameter.ParameterCount.ARBITRARY, parameter.ParameterCount.ONE_OR_MORE):
                    returnParameters.extend(parameters)
                    parameters = []
                else:
                    returnParameters.append(parameters.pop(0))
            elif match == FunctionParameterMatch.FAIL_WRONG_TYPE:
                raise McScriptArgumentError(self.format_string.format(
                    self.arguments_format(original_parameters),
                    f"Expected type {parameter.type} for parameter '{parameter.name}' but got "
                    f"type {parameters[0].type()}"
                ), compileState)
            elif match == FunctionParameterMatch.FAIL_MULTIPLE_PARAMETERS:
                raise McScriptArgumentError(self.format_string.format(
                    self.arguments_format(original_parameters),
                    f"All parameters for '{parameter.name}' must be of type "
                    f"{parameter.type} but got ({', '.join(str(i.type()) for i in parameters)})"
                ), compileState)
            elif match == FunctionParameterMatch.MUST_BE_STATIC:
                raise McScriptArgumentError(self.format_string.format(
                    self.arguments_format(original_parameters),
                    f"Parameter {parameter.name} must be static but got ({', '.join(str(i) for i in parameters)})"
                ), compileState)
            elif match == FunctionParameterMatch.MUST_NOT_BE_STATIC:
                raise McScriptArgumentError(self.format_string.format(
                    self.arguments_format(original_parameters),
                    f"Parameter {parameter.name} must not be static but "
                    f"got({', '.join(str(i) for i in parameters)})"
                ), compileState)
            else:
                raise McScriptArgumentError("Unknown error.", compileState)
        else:
            if parameters:
                raise McScriptArgumentError(self.format_string.format(
                    self.arguments_format(original_parameters),
                    f"Too many parameters: Expected {len(self.parameters)} at most but got {len(original_parameters)}"
                ), compileState)
            return returnParameters

        # if this code is reached, try to add the defaults of the remaining parameter
        for parameter in itertools.chain((parameter,), iterator):
            if parameter.defaultValue is not None:
                returnParameters.append(parameter.defaultValue)
                usedParameters.append(parameter)
            else:
                if parameter.count == parameter.ParameterCount.ONE_OR_MORE:
                    raise McScriptArgumentError(self.format_string.format(
                        self.arguments_format(original_parameters),
                        f"Expected parameter '{parameter.name}' but got nothing"
                    ), compileState)
                else:
                    raise McScriptArgumentError(self.format_string.format(
                        self.arguments_format(original_parameters),
                        f"Parameter '{parameter.name}' must be specified!"
                    ), compileState)

        return returnParameters

    def arguments_format(self, arguments: List[Resource]):
        return "(" + ", ".join(str(i.type()) for i in arguments) + ")"

    def __str__(self):
        return self.signature_string()
