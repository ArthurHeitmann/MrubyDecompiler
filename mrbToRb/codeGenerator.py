from typing import List

from mrbToRb.rbExpressions import Expression, LineCommentEx


class CodeGen:
	expressions: List[Expression]
	includeComments: bool

	def __init__(self, includeComments: bool = True):
		self.expressions = []
		self.includeComments = includeComments

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

	def toStr(self) -> str:
		result = ""
		for exp in self.expressions:
			if exp.canBeOptimizedAway and exp.hasUsages:
				continue
			if not self.includeComments and isinstance(exp, LineCommentEx):
				continue
			result += f"{exp}\n"
		return result[:-1]

	def getExpressions(self) -> List[Expression]:
		exps: List[Expression] = []
		for exp in self.expressions:
			if exp.canBeOptimizedAway and exp.hasUsages:
				continue
			if not self.includeComments and isinstance(exp, LineCommentEx):
				continue
			exps.append(exp)
		return exps
