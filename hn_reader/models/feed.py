from enum import Enum


class Feed(Enum):
    TOP = ('top', 'topstories')
    NEW = ('new', 'newstories')
    BEST = ('best', 'beststories')

    def __init__(self, _, endpoint: str) -> None:
        self.endpoint = endpoint

    def __new__(cls, id: str, _):
        obj = object.__new__(cls)
        obj._value_ = id
        return obj
