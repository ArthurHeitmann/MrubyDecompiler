from typing import List

from mrbToRb.rbExpressions import Expression


class CodeGen:
	expressions: List[Expression]

	def __init__(self) -> None:
		self.expressions = []
	
	def pushExp(self, expression: Expression) -> None:
		self.expressions.append(expression)

	def popExps(self, exps: List[Expression], replacement: Expression = None) -> None:
		for exp in exps[:-1]:
			self.expressions.remove(exp)
		lastIndex = self.expressions.index(exps[-1])
		if replacement is not None:
			self.expressions[lastIndex] = replacement
		else:
			self.expressions.pop(lastIndex)
