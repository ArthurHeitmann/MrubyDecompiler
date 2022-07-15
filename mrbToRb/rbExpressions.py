from __future__ import annotations

from typing import Any, List, Dict, Set
import re

OperatorPriority: Dict[str, int] = {
	"!": 0,
	"~": 0,
	"+@": 0,
	"**": 1,
	"-@": 2,
	"*": 3,
	"/": 3,
	"%": 3,
	"+": 4,
	"-": 4,
	"<<": 5,
	">>": 5,
	"&": 6,
	"|": 7,
	"^": 7,
	">": 8,
	">=": 8,
	"<": 8,
	"<=": 8,
	"<=>": 9,
	"==": 9,
	"===": 9,
	"!=": 9,
	"=~": 9,
	"!~": 9,
	"&&": 10,
	"||": 11,
	"..": 12,
	"...": 12,
	"?": 13,
	":": 13,
	# "modifier-rescue": 14,
	"=": 15,
	"+=": 15,
	"-=": 15,
	"*=": 15,
	"/=": 15,
	"%=": 15,
	"&=": 15,
	"|=": 15,
	"^=": 15,
	"<<=": 15,
	">>=": 15,
	"&&=": 15,
	"||=": 15,
	"**=": 15,
}


class Expression:
	"""If true, this expression might be optimized away from the output code."""
	hasUsages: bool
	canBeOptimizedAway: bool
	register: int
	associatedSymbol: Expression|None

	def __init__(self, register: int):
		self.hasUsages = False
		self.canBeOptimizedAway = True
		self.register = register
		self.associatedSymbol = None

	def __str__(self):
		return self._toStr()

	def _toStr(self):
		raise NotImplementedError()

class AnyValueExpression(Expression):
	value: Any

	def __init__(self, register: int, value: Any):
		super().__init__(register)
		self.value = value
		if isinstance(value, Expression):
			value.hasUsages = True
	
	
	def _toStr(self):
		return str(self.value)

class LineCommentEx(AnyValueExpression):
	def _toStr(self):
		return f"#{self.value}"

class LiteralEx(AnyValueExpression):
	def _toStr(self):
		strVal = str(self.value)
		if re.match(r"\d+\.\d+e[+-]\d+", strVal):
			return str(float(strVal))
		else:
			return strVal

class SelfEx(LiteralEx):
	def __init__(self, register: int):
		super().__init__(register, "self")
class NilEx(LiteralEx):
	def __init__(self, register: int):
		super().__init__(register, "nil")
class TrueEx(LiteralEx):
	def __init__(self, register: int):
		super().__init__(register, "true")
class FalseEx(LiteralEx):
	def __init__(self, register: int):
		super().__init__(register, "false")

class SymbolEx(AnyValueExpression):
	...

class SymbolValEx(LiteralEx):
	def _toStr(self):
		return f":{self.value}"

class ClassSymbolEx(SymbolEx):
	...

class TwoExpEx(Expression):
	left: Expression
	right: Expression
	
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register)
		self.left = left
		self.right = right
		left.hasUsages = True
		right.hasUsages = True

class TwoCombinedExpEx(TwoExpEx):
	operator: Expression
	priority: int
	
	def __init__(self, register: int, left: Expression, right: Expression, operator: Expression):
		super().__init__(register, left, right)
		self.operator = operator
		self.priority = OperatorPriority.get(str(operator), 99)
	
	def _toStr(self):
		if isinstance(self.left, TwoCombinedExpEx) and self.left.priority > self.priority:
			left = f"({self.left})"
		else:
			left = self.left
		if isinstance(self.right, TwoCombinedExpEx) and self.right.priority > self.priority:
			right = f"({self.right})"
		else:
			right = self.right
		return f"{left} {self.operator} {right}"

class AssignmentEx(TwoCombinedExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right, LiteralEx(0, "="))

	def _toStr(self):
		return f"{self.left} = {self.right}"

class BlockEx(Expression):
	expressions: List[Expression]
	
	def __init__(self, register: int):
		super().__init__(register)

	def addExpression(self, expression: Expression):
		self.expressions.append(expression)
		expression.hasUsages = True

	def _toStr(self):
		if len(self.expressions) == 0:
			return ""
		elif len(self.expressions) == 1:
			return f" {self.expressions[0]} "
		else:
			result = ""
			for expression in self.expressions:
				result += f"{expression}\n"
			return result

class PassableBlockEx(BlockEx):
	def _toStr(self):
		if len(self.expressions) == 0:
			return "{}"
		elif len(self.expressions) == 1:
			return f"{{ {super()._toStr()} }}"
		else:
			return f"{{\n{super()._toStr()}}}"

AllOperatorsTwoExp: Set[str] = {
	"*", "/", "%", "+", "-", "**",
	"<<", ">>",
	"&", "|", "^",
	">", ">=", "<", "<=", "<=>", "==", "===", "!=", "=~", "!~",
	"&&", "||",
	"..", "...",
	"?", ":",
	"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>=", "&&=", "||=", "**=",
}
AllUnanaryOperators: Set[str] = {
	"+@", "-@", "~", "!",
}

class MethodCallEx(Expression):
	srcObj: Expression
	symbol: SymbolEx
	args: List[Expression]
	isOperatorCall: bool
	operatorPriority: int

	def __init__(self, register: int, srcObj: Expression|None, symbol: SymbolEx, args: List[Expression]):
		super().__init__(register)
		self.srcObj = srcObj
		self.symbol = symbol
		self.args = args
		self.isOperatorCall = str(symbol) in AllOperatorsTwoExp and len(args) == 1 or str(symbol) in AllUnanaryOperators and len(args) == 0
		self.operatorPriority = OperatorPriority.get(str(symbol), 99)
		if srcObj is not None:
			srcObj.hasUsages = True
		symbol.hasUsages = True
		for arg in args:
			arg.hasUsages = True

	def _toStr(self):
		if self.isOperatorCall:
			if str(self.symbol) in AllOperatorsTwoExp:
				if isinstance(self.srcObj, SymbolEx) or isinstance(self.srcObj, LiteralEx):
					left = self.srcObj
				else:
					left = f"({self.srcObj})"
				if isinstance(self.args[0], SymbolEx) or isinstance(self.args[0], LiteralEx):
					right = self.args[0]
				else:
					right = f"({self.args[0]})"
				return f"{left} {self.symbol} {right}"
			else:
				return f"{str(self.symbol).replace('@', '')}{self.srcObj}"
		else:
			result = ""
			if self.srcObj is not None and not isinstance(self.srcObj, MainClass):
				if isinstance(self.srcObj, SymbolEx) or isinstance(self.srcObj, LiteralEx):
					result += f"{self.srcObj}."
				else:
					result += f"({self.srcObj})."
			result += f"{self.symbol}({', '.join(map(str, self.args))})"
			return result

class MethodCallWithBlockEx(MethodCallEx):
	block: BlockEx

	def __init__(self, register: int, srcObj: Expression, symbol: SymbolEx, args: List[Expression], block: BlockEx):
		super().__init__(register, srcObj, symbol, args)
		self.block = block
		block.hasUsages = True

	def _toStr(self):
		return f"{super()._toStr()} {self.block}"

class BoolExpEx(TwoCombinedExpEx):
	...

class ArrayEx(Expression):
	elements: List[Expression]

	def __init__(self, register: int, elements: List[Expression]):
		super().__init__(register)
		self.elements = elements
		for element in elements:
			element.hasUsages = True
	
	def _toStr(self):
		if len(self.elements) == 0:
			return "[]"
		elif len(self.elements) == 1:
			return f"[ {self.elements[0]} ]"
		else:
			elements = list(map(str, self.elements))
			elementsTotalLen = sum(map(len, elements)) + 2 * (len(elements) - 1)
			if elementsTotalLen > 80:
				joiner = ",\n\t"
				return f"[\n\t{joiner.join(map(str, self.elements))}\n]"
			else:
				return f"[ {', '.join(map(str, self.elements))} ]"

class ArrayConcatEx(TwoExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right)

	def _toStr(self):
		return f"{self.left}.push(*{self.right})"

class ArrayPushEx(TwoCombinedExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right, LiteralEx(0, "<<"))

class ArrayRefEx(AnyValueExpression):
	index: int

	def __init__(self, register: int, array: Expression, index: int):
		super().__init__(register, array)
		self.index = index
	
	def _toStr(self):
		return f"{self.value}[{self.index}]"

class ArraySetEx(Expression):
	arrSymbol: SymbolEx
	index: int
	value: Expression
	
	def __init__(self, register: int, arrSymbol: SymbolEx, index: int, value: Expression):
		super().__init__(register)
		self.arrSymbol = arrSymbol
		self.index = index
		self.value = value
		self.value.hasUsages = True
	
	def _toStr(self):
		return f"{self.arrSymbol}[{self.index}] = {self.value}"

class StringEx(AnyValueExpression):
	def _toStr(self):
		return '"' + str(self.value).replace("\\", "\\\\").replace('"', '\\"') + '"'

class StringConcatEx(TwoExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right)

	def _toStr(self):
		if isinstance(self.left, StringEx) and self.left.value == "":
			return f'"{self.right}"'
		parts: List[Expression]
		if isinstance(self.left, StringConcatEx):
			parts = self.flattenConcat()
		else:
			parts = [self.left, self.right]
		partsStr = map(lambda x: x.value if isinstance(x, StringEx) else f"#{{{x}}}", parts)
		return f"\"{''.join(partsStr)}\""

	def flattenConcat(self) -> List[Expression]:
		flat: List[Expression] = []
		if isinstance(self.left, StringConcatEx):
			flat.extend(self.left.flattenConcat())
		else:
			flat.append(self.left)
		if isinstance(self.right, StringConcatEx):
			flat.extend(self.right.flattenConcat())
		else:
			flat.append(self.right)
		return flat

class HashEx(Expression):
	hash: Dict[Expression, Expression]

	def __init__(self, register: int, hashDict: Dict[Expression, Expression]):
		super().__init__(register)
		self.hash = hashDict
		for key, value in hashDict.items():
			key.hasUsages = True
			value.hasUsages = True

	def _toStr(self):
		if len(self.hash) == 0:
			return "{}"
		elif len(self.hash) == 1:
			return f"{{ {list(self.hash.keys())[0]}: {list(self.hash.values())[0]} }}"
		else:
			result = "{\n"
			for key, value in self.hash.items():
				if re.match(r"^\d", str(key)):
					key = f"\"{key}\""
				result += f": {key} => {value},\n"
			result += "}"
			return result

class RangeEx(TwoExpEx):
	min: Expression
	max: Expression
	isMaxExclusive: bool

	def __init__(self, register: int, minVal: Expression, maxVal: Expression, isMaxExclusive: bool):
		super().__init__(register, minVal, maxVal)
		self.min = minVal
		self.max = maxVal
		self.isMaxExclusive = isMaxExclusive

	def _toStr(self):
		if self.isMaxExclusive:
			return f"{self.min}...{self.max}"
		else:
			return f"{self.min}..{self.max}"

class ClassEx(BlockEx):
	className: SymbolEx
	parentClass: Expression|None

	def __init__(self, register: int, className: SymbolEx, parentClass: Expression|None):
		super().__init__(register)
		self.className = className
		self.parentClass = parentClass
		self.canBeOptimizedAway = False

	def _toStr(self):
		if self.parentClass is None or isinstance(self.parentClass, MainClass):
			result = f"class {self.className}\n"
		else:
			result = f"class {self.className} < {self.parentClass}\n"

		result += super()._toStr()
		result += "\nend"
		return result

class MainClass(ClassEx):
	def __init__(self, register: int):
		super().__init__(register, SymbolEx(0, "main"), None)

class SingletonClassEx(BlockEx):
	object: Expression

	def __init__(self, register: int, obj: Expression):
		super().__init__(register)
		self.object = obj
		self.canBeOptimizedAway = False
		self.object.hasUsages = True

	def _toStr(self):
		result = f"class << {self.object}\n"
		result += super()._toStr()
		result += "\nend"
		return result

class Module(BlockEx):
	name: SymbolEx

	def __init__(self, register: int, name: SymbolEx):
		super().__init__(register)
		self.name = name
		self.canBeOptimizedAway = False

	def _toStr(self):
		result = f"module {self.name}\n"
		result += super()._toStr()
		result += "\nend"
		return result

class ExecEx(Expression):
	# TODO

	def _toStr(self):
		pass

