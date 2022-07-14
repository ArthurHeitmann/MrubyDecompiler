from typing import Any, List, Dict, Optional
import re


class Expression:
	"""If true, this expression might be optimized away from the output code."""
	hasUsages: bool
	canBeOptimizedAway: bool
	register: int
	
	def __init__(self, register: int):
		self.hasUsages = False
		self.canBeOptimizedAway = True
		self.register = register

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
	...
SELF = LiteralEx(0, "self")
NIL = LiteralEx(1, "nil")
TRUE = LiteralEx(2, "true")
FALSE = LiteralEx(3, "false")

class SymbolEx(AnyValueExpression):
	...

class ClassSymbolEx(SymbolEx):
	...
MAIN_CLASS = ClassSymbolEx(0, "main")

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
	
	def __init__(self, register: int, left: Expression, right: Expression, operator: Expression):
		super().__init__(register, left, right)
		self.operator = operator
	
	def _toStr(self):
		return f"{self.left} {self.operator} {self.right}"

class AssignmentEx(TwoCombinedExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right, LiteralEx(0, "="))

	def _toStr(self):
		return f"{self.left} = {self.right}"

class RegistryAssignmentEx(AssignmentEx):
	def _toStr(self):
		return f"_r_{self.left} = {self.right}"

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

class MethodCallEx(Expression):
	srcObj: Expression
	symbol: SymbolEx
	args: List[Expression]

	def __init__(self, register: int, srcObj: Expression, symbol: SymbolEx, args: List[Expression]):
		super().__init__(register)
		self.srcObj = srcObj
		self.symbol = symbol
		self.args = args
		srcObj.hasUsages = True
		symbol.hasUsages = True

	def _toStr(self):
		result = ""
		if self.srcObj is not None and self.srcObj != MAIN_CLASS:
			result += f"{self.srcObj}."
		if len(self.args) == 0:
			result += f"{self.symbol}"
		else:
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

class BoolEx(TwoCombinedExpEx):
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
			newLine = "\n"
			return f"[ {(',' + newLine).join(map(str, self.elements))} ]"

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
		return f'"{self.value}"'

class StringConcatEx(TwoExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right)

	def _toStr(self):
		if isinstance(self.left, StringEx) and self.left.value == "":
			return f'"{self.right}"'
		elif isinstance(self.left, StringConcatEx):
			flatExps = self.flattenConcat()
			return "\"" + ("".join(map(lambda ex: f"#{{{ex}}}", flatExps))) + "\""
		else:
			return f"\"#{{{self.left}}}#{{{self.right}}}\""

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
	parentClass: Optional[Expression]

	def __init__(self, register: int, className: SymbolEx, parentClass: Expression = NIL):
		super().__init__(register)
		self.className = className
		self.parentClass = parentClass
		self.canBeOptimizedAway = False

	def _toStr(self):
		if self.parentClass is NIL:
			result = f"class {self.className}\n"
		else:
			result = f"class {self.className} < {self.parentClass}\n"

		result += super()._toStr()
		result += "\nend"
		return result

OBJECT_CLASS = ClassEx(0, SymbolEx(0, "Object"))

class SingletonClassEx(BlockEx):
	object: Expression

	def __init__(self, register: int, obj: Expression):
		super().__init__(register)
		self.object = obj
		self.canBeOptimizedAway = False
		self.object.hasUsages = True

	def __str__(self):
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

