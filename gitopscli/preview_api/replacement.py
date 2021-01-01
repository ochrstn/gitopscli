from enum import Enum, auto
from dataclasses import dataclass


@dataclass(frozen=True)
class Replacement:
    class Variable(Enum):
        GIT_COMMIT = auto()
        ROUTE_HOST = auto()

    path: str
    variable: Variable

    def __post_init__(self) -> None:
        assert isinstance(self.path, str), "path of wrong type!"
        assert isinstance(self.variable, self.Variable), "variable of wrong type!"
