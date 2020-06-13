from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from mcscript.analyzer.VariableContext import VariableContext
from mcscript.compiler.ContextType import ContextType
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.utils.Address import Address
from mcscript.utils.NbtAddress import NbtAddress


class Context:
    """
    Manages a single context. A context is unique to each block that is entered, which includes ia. functions.

    A `Context` keeps track of:
        * The previous `Context`
        * The numerical id of this `Context`
        * The variables unique to this context
        * The type of context, ia. if it can be evaluated at compile time (not influenced by inner non-static contexts)
        * A template string for context specific variable names
        * A template string for nbt variable names
        * An optional resource which is the resource that is returned from this stack.
    """

    @dataclass()
    class Variable:
        """
        The value class of the namespace of the context
        """
        resource: Resource = field()
        context: Optional[VariableContext] = field(default=None)

    def __init__(
            self,
            index: int,
            ctx_type: ContextType,
            variable_context: List[VariableContext],
            predecessor: Context = None
    ):
        self.index = index
        self.context_type = ctx_type
        self.predecessor = predecessor

        # make a simple lookup table name -> ctx
        self.variable_context = {i.identifier: i for i in variable_context}

        # the namespace of variables unique to this context
        self.namespace: Dict[str, Context.Variable] = {}

        # formats variables to ".exp<x>_<varId>"
        self.format_string = Address(f".exp{self.index}_{{}}")
        # for nbt names
        self.nbt_format = NbtAddress(f"{self.index}_{{}}" if self.index != 0 else "{}")

        # A resource which is returned when this context is popped
        self.return_resource: Optional[Resource] = None

    def find_var(self, name: str) -> Optional[Context.Variable]:
        """
        Recursively looks for a variable with key `name`.

        Args:
            name: The name of the variable

        Returns:
            The variable or None if not found
        """
        if name in self.namespace:
            return self.namespace[name]

        if self.predecessor is not None:
            return self.predecessor.find_var(name)

        return None

    def find_resource(self, name: str) -> Optional[Resource]:
        """
        Like `find_var` but returns just the resource.

        Args:
            name: The name of the variable

        Returns:
            The resource or None if not found
        """
        return None if (var := self.find_var(name)) is None else var.resource

    def add_var(self, name: str, value: Resource):
        """
        Adds a variable to this context and assigns it the correct variable context.
        Note that there must be a valid variable context!
        Fails if the variable does already exist.

        Args:
            name: the name of the variable
            value: the resource

        Returns:
            None

        Raises:
            ValueError: If the resource does already exist
        """
        if name in self.namespace:
            raise ValueError(f"Variable {name} does already exist!")

        variable_context = self.variable_context[name] if self.variable_context else None
        self.namespace[name] = self.Variable(value, variable_context)

    def set_var(self, name: str, value: Resource):
        """
        Overwrites the value of an existing resource.
        If the variable is not in this namespace, the next lower namespace will be used.
        Raises if the resource does not exist in this or any lower namespace.

        Args:
            name: The name of the variable
            value: The resource

        Returns:
            None

        Raises:
            KeyError: If the variable does not exist
        """

        if name in self.namespace:
            self.namespace[name].resource = value
        elif self.predecessor is not None:
            self.predecessor.set_var(name, value)
        else:
            raise KeyError(f"Variable '{name}' does not exist!")

    def as_dict(self) -> Dict[str, Context.Variable]:
        """
        Creates a dictionary containing all variable names from this and earlier contexts.
        If a variable shares the same name on multiple contexts, the variable in the highest context will be kept.

        Returns:
            A Dict containing all variables from this and previous contexts
        """
        if self.predecessor is not None:
            data = self.predecessor.as_dict()
        else:
            data = {}

        data.update(self.namespace)
        return data

    def search_non_static_until(self, other: Context) -> Optional[Context]:
        """
        Searches down until a context is not static or ´other´ is found.

        Args:
            other: Another context

        Returns:
            The first found non-static found context or None if none was found
        """

        ctx = self
        while ctx != other and ctx is not None:
            if not ctx.context_type.hasStaticContext:
                return ctx
            ctx = ctx.predecessor

        return None

    def __contains__(self, item) -> bool:
        """
        Tests recursively if the item is in this contexts namespace or below
        """
        if item in self.namespace:
            return True

        if self.predecessor:
            return item in self.predecessor

        return False