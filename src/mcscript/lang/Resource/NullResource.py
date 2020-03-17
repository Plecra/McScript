from typing import Any

from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class NullResource(ValueResource):
    def __init__(self, value: Any = None, isStatic: bool = True):
        """
        parameters are discarded
        :param value: ignored
        :param isStatic: ignored
        """
        super().__init__(None, True)

    def embed(self) -> str:
        return "null"

    def typeCheck(self) -> bool:
        return True

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NULL
