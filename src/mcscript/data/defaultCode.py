from src.mcscript.data.Commands import Config
from src.mcscript.utils.Datapack import Datapack


def addDefaults(datapack: Datapack) -> Datapack:
    addDynamicDefaults(datapack)
    return datapack


def addDynamicDefaults(datapack: Datapack) -> Datapack:
    # adds functions
    files = datapack.getMainDirectory().getPath("functions").fileStructure
    for default in DEFAULTS:
        files.pushFile(f"{default}.mcfunction")
        try:
            text = DEFAULTS[default](files.pois)
        except KeyError:
            # script does not have to contain every "magic" function
            continue
        files.get().write(text)
    return datapack


MAGIC_FUNCTIONS = {
    "onTick": 0
}

DEFAULTS = {
    "tick": lambda pois: "function {NAME}:{block}".format(NAME=Config.currentConfig.NAME, block=pois["onTick"][1])
}
