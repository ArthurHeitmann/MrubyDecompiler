from __future__ import annotations
from typing import List, Union

from opcodes import *


class OpCodeFeed:
    opcodes: List[MrbCode]
    pos: int
    fullOpcodes: List[MrbCode]
    offset: int

    def __init__(self, opcodes: List[MrbCode], fullOpcodes: List[MrbCode]|None = None, offset: int = 0):
        self.opcodes = opcodes
        self.pos = 0
        self.fullOpcodes = fullOpcodes or opcodes
        self.offset = offset

    def cur(self) -> Union[MrbCode, MrbCodeABC, MrbCodeABx, MrbCodeAsBx, MrbCodeAx]:
        return self.opcodes[self.pos]

    def jump(self, offset: int):
        self.pos += offset

    def seek(self, pos: int):
        if pos < self.pos:
            raise ValueError("Cannot seek backwards")
        self.pos = pos

    def next(self):
        self.pos += 1

    def stop(self):
        self.pos = len(self.opcodes)

    def hasNext(self):
        return self.pos < len(self.opcodes)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.opcodes[item]
        elif isinstance(item, slice):
            return OpCodeFeed(self.opcodes[item.start:item.stop:item.step], self.fullOpcodes, self.offset + item.start)
        else:
            raise TypeError(f"Invalid slice type {type(item)}")

    def getJumpedOpcodes(self, count: int) -> List[MrbCode]:
        start = self.offset + self.pos
        return self.fullOpcodes[start + 1:start + count]

    def getRel(self, offset: int):
        return self.opcodes[self.pos + offset]

    def __len__(self):
        return len(self.opcodes)
