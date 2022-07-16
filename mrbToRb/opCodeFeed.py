from __future__ import annotations
from typing import List, Union

from opcodes import *


class OpCodeFeed:
    opcodes: List[MrbCode]
    pos: int

    def __init__(self, opcodes: List[MrbCode]):
        self.opcodes = opcodes
        self.pos = 0

    def cur(self) -> Union[MrbCode, MrbCodeABC, MrbCodeABx, MrbCodeAsBx, MrbCodeAx]:
        return self.opcodes[self.pos]

    def jump(self, offset: int):
        self.pos += offset

    def seek(self, pos: int):
        self.pos = pos

    def next(self):
        self.pos += 1

    def hasNext(self):
        return self.pos < len(self.opcodes)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.opcodes[item]
        elif isinstance(item, slice):
            return OpCodeFeed(self.opcodes[item.start:item.stop:item.step])
        else:
            raise TypeError(f"Invalid slice type {type(item)}")

    def getRel(self, offset: int):
        return self.opcodes[self.pos + offset]

    def __len__(self):
        return len(self.opcodes)
