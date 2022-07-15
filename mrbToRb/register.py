from __future__ import annotations
from typing import Any

from mrbToRb.rbExpressions import Expression, SymbolEx, NilEx


class Register:
	i: int
	regSymbol: SymbolEx
	value: Expression
	lvarSymbol: SymbolEx

	def __init__(self, i: int, lvarName: str = None):
		self.i = i
		self.regSymbol = SymbolEx(i, f"_r_{i}")
		if lvarName:
			self.lvarSymbol = SymbolEx(i, lvarName)
		else:
			self.lvarSymbol = None
		self.value = self.lvarSymbol if lvarName else NilEx(0)

	def moveIn(self, other: Register):
		if other.lvarSymbol:
			self.value = other.lvarSymbol
		else:
			self.value = other.value

	def load(self, value: Expression):
		self.value = value
