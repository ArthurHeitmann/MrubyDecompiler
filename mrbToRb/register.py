from __future__ import annotations
from typing import Any

from mrbToRb.rbExpressions import Expression, SymbolEx


class Register:
	i: int
	regSymbol: SymbolEx
	value: Expression
	lvarName: str

	def __init__(self, i: int, value: Any, lvarName: str = None):
		self.i = i
		self.regSymbol = SymbolEx(i, f"_r_{i}")
		self.value = value
		self.lvarName = lvarName

	def moveIn(self, other: Register):
		if other.lvarName:
			self.value = SymbolEx(self.i, other.lvarName)
		else:
			self.value = other.value

	def load(self, value: Expression):
		self.value = value
