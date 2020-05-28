from __future__ import annotations

from mcscript.lang.resource.base.ResourceBase import Resource


def compareTypes(a: Resource, b: Resource) -> bool:
    """ compares two resources. """
    from mcscript.lang.resource.StructObjectResource import StructObjectResource
    from mcscript.lang.resource.StructResource import StructResource

    if b == Resource:
        return True
    if isinstance(a, StructObjectResource):
        return (isinstance(b, StructResource) and a.struct == b) or \
               (isinstance(b, StructObjectResource) and a.struct == b.struct)
    return a.type() == b.type()


def isStatic(resource: Resource) -> bool:
    """ Returns whether the resource is static if it is a value resource else False"""
    return getattr(resource, "isStatic", False)
