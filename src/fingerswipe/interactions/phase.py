from enum import Enum


class GesturePhase(str, Enum):
    BEGIN = "begin"
    UPDATE = "update"
    END = "end"
    CANCEL = "cancel"