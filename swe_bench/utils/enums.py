from enum import Enum, auto


class FileChangeMode(Enum):
    create = auto()
    delete = auto()
    change = auto()


class LineChangeType(Enum):
    addition = auto()
    deletion = auto()
