from __future__ import annotations

from mrbToRb.rbExpressions import Expression, SymbolEx, NilEx


class Register:
	i: int
	regSymbol: SymbolEx
	_value: Expression
	lvarSymbol: SymbolEx|None
	tmpLvarSymbol: SymbolEx|None

	def __init__(self, i: int, lvarName: str = None):
		self.i = i
		self.regSymbol = SymbolEx(i, f"_r_{i}")
		if lvarName:
			self.lvarSymbol = SymbolEx(i, lvarName)
		else:
			self.lvarSymbol = None
		self.tmpLvarSymbol = None
		self._value = self.lvarSymbol if lvarName else NilEx(0)

	def moveIn(self, other: Register):
		if other.lvarSymbol:
			self._value = other.lvarSymbol
		else:
			self._value = other._value
		if self.lvarSymbol:
			other.tmpLvarSymbol = self.lvarSymbol
		else:
			self.tmpLvarSymbol = other.lvarSymbol or other.tmpLvarSymbol

	def load(self, _value: Expression):
		self._value = _value
		self.tmpLvarSymbol = None

	@property
	def value(self) -> Expression:
		if self.tmpLvarSymbol:
			return self.tmpLvarSymbol
		return self._value
