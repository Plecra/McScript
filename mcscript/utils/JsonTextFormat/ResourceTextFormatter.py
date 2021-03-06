from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING, Union

from mcscript.exceptions.exceptions import McScriptUnexpectedTypeError
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ResourceTextFormatter:
    def __init__(self, compileState: CompileState):
        self.compileState = compileState

    def createFromResources(self, *resources: Union[str, Resource]) -> List:
        # compact strings
        if len(resources) > 1:
            new_resources = [resources[0]]
            for resource in resources[1:]:
                if isinstance(new_resources[-1], str) and isinstance(resource, str):
                    new_resources[-1] += resource
                else:
                    new_resources.append(resource)
            resources = new_resources

        data = []
        for resource in resources:
            data.append(self.createFromResource(resource))

        return data

    def createFromResource(self, resource: Union[Resource, str]) -> Dict:
        if isinstance(resource, str):
            resource = StringResource(resource)

        try:
            return resource.to_json_text(self.compileState, self)
        except TypeError:
            raise McScriptUnexpectedTypeError("String formatter", resource, "json convertible", self.compileState)

    def _getFormattedString(self, handler, resource) -> Dict:
        return handler(resource)
