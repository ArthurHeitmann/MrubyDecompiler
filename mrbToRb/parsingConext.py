from __future__ import annotations
from typing import List, Callable, Any, Dict


class ParsingState:
    NORMAL = 0
    METHOD = 1
    FOR_LOOP = 2
    WHILE_LOOP = 3
    IF = 4
    WHEN_COND = 5
    CASE_ELSE = 6

class ParsingContext:
    parentStates: List[ParsingState]
    callback: Callable[..., Any]|None
    hasMoreOpcodesOutside: bool
    data: Dict

    def __init__(self, state: ParsingState, parent: ParsingContext|None = None, hasMoreOpcodesOutside: bool = False) -> None:
        if parent:
            self.parentStates = parent.parentStates + [state]
        else:
            self.parentStates = [state]
        self.callback = None
        self.hasMoreOpcodesOutside = hasMoreOpcodesOutside
        self.data = {}

    def isMethod(self):
        return ParsingState.METHOD in self.parentStates

    def isIf(self):
        for state in reversed(self.parentStates):
            if state == ParsingState.METHOD:
                return False
            elif state == ParsingState.IF:
                return True
        return False

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

    def isWhenCond(self):
        return self.parentStates[-1] == ParsingState.WHEN_COND

    def isWhenCondOrElse(self):
        return self.parentStates[-1] == ParsingState.CASE_ELSE

    def updateState(self, state: ParsingState) -> None:
        self.parentStates[-1] = state

    def pushAndNew(self, state: ParsingState, hasMore: bool = False) -> ParsingContext:
        return ParsingContext(state, self, hasMore)
