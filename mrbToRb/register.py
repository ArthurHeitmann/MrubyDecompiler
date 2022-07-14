from __future__ import annotations
from typing import Any, List

from mrbToRb.rbExpressions import Expression, SymbolEx


class Register:
	i: int
	symbol: SymbolEx
	value: Expression
	lvarName: str
	tmpLvarName: str|None

	def __init__(self, i: int, value: Any, lvarName: str = None):
		self.i = i
		self.symbol = SymbolEx(0, f"_r_{i}")
		self.value = value
		self.lvarName = lvarName
		self.tmpLvarName = None

	def moveIn(self, other: Register):
		self.value = other.value
		self.tmpLvarName = other.lvarName or other.tmpLvarName

	def load(self, value: Expression):
		self.value = value
		self.tmpLvarName = None
