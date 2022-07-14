from typing import List

from mrbToRb.rbExpressions import Expression


class CodeGen:
	expressions: List[Expression]

	def __init__(self) -> None:
		self.expressions = []
	
	def pushExp(self, expression: Expression) -> None:
		self.expressions.append(expression)

	def popExps(self, exps: List[Expression]) -> None:
		for exp in exps:
			self.expressions.remove(exp)
