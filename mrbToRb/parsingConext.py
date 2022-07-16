from __future__ import annotations
from typing import List


class ParsingState:
    NORMAL = 0
    METHOD = 1
    FOR_LOOP = 2
    WHILE_LOOP = 3
    IF = 4

class ParsingContext:
    parentStates: List[ParsingState]

    def __init__(self, state: ParsingState, parent: ParsingContext|None = None):
        if parent:
            self.parentStates = parent.parentStates + parent.parentStates
        else:
            self.parentStates = [state]

    def isIf(self):
        return ParsingState.IF in self.parentStates

    def isMethod(self):
        return ParsingState.METHOD in self.parentStates

    def isForLoop(self):
        for state in reversed(self.parentStates):
            if state == ParsingState.WHILE_LOOP:
                return False
            elif state == ParsingState.METHOD:
                return False
            if state == ParsingState.FOR_LOOP:
                return True
        return False

    def isWhileLoop(self):
        for state in reversed(self.parentStates):
            if state == ParsingState.METHOD:
                return False
            elif state == ParsingState.FOR_LOOP:
                return False
            elif state == ParsingState.WHILE_LOOP:
                return True
        return False

    def pushAndNew(self, state: ParsingState) -> ParsingContext:
        return ParsingContext(state, self)
