from __future__ import annotations
from typing import List

from opcodes import MrbCode


class OpCodeFeed:
    opcodes: List[MrbCode]
    pos: int

    def __init__(self, opcodes: List[MrbCode]):
        self.opcodes = opcodes
        self.pos = 0

    def cur(self) -> MrbCode:
        return self.opcodes[self.pos]

    def jump(self, offset: int):
        self.pos += offset

    def next(self):
        self.pos += 1

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.opcodes[item]
        elif isinstance(item, slice):
            return OpCodeFeed(self.opcodes[item.start:item.stop:item.step])
        else:
            raise TypeError(f"Invalid slice type {type(item)}")

    def __len__(self):
        return len(self.opcodes)
