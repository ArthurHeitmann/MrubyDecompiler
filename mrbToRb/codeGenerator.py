from typing import List

from mrbToRb.rbExpressions import Expression, LineCommentEx


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

	def toStr(self, includeComments: bool, includeRegAssigns: bool) -> str:
		result = ""
		for exp in self.expressions:
			if not includeComments and isinstance(exp, LineCommentEx):
				continue
			# if not includeRegAssigns and isinstance(exp, RegisterAssignmentEx):
			# 	continue
			if exp.canBeOptimizedAway and exp.hasUsages:
				continue
			result += f"{exp}\n"
		return result[:-1]
