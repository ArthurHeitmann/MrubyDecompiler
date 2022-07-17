from __future__ import annotations

from typing import Any, List, Dict, Set
import re

from utils import prefixLines

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
		return f"# {self.value}"

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
	parent: Expression
	isSingleton: bool

	def __init__(self, register: int, sym: Expression, parent: Expression|None = None, isSingleton: bool = False):
		super().__init__(register, sym)
		self.parent = parent
		self.isSingleton = isSingleton

class ModuleSymbolEx(SymbolEx):
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
	
	def __init__(self, register: int, expressions: List[Expression]):
		super().__init__(register)
		self.expressions = expressions
		for expression in expressions:
			expression.hasUsages = True

	def addExpression(self, expression: Expression):
		self.expressions.append(expression)
		expression.hasUsages = True

	def _toStr(self):
		if len(self.expressions) == 0:
			return ""
		elif len(self.expressions) == 1:
			return str(self.expressions[0])
		else:
			return "\n".join(map(str, self.expressions))

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
AllUnaryOperators: Set[str] = {
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
		self.isOperatorCall = str(symbol) in AllOperatorsTwoExp and len(args) == 1 or str(symbol) in AllUnaryOperators and len(args) == 0
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
				if isinstance(self.srcObj, SymbolEx) or isinstance(self.srcObj, LiteralEx):
					right = self.srcObj
				else:
					right = f"({self.srcObj})"
				return f"{str(self.symbol).replace('@', '')}{right}"
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
	block: LambdaEx

	def __init__(self, register: int, srcObj: Expression, symbol: SymbolEx, args: List[Expression], block: LambdaEx):
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
		array.hasUsages = True
	
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
		arrSymbol.hasUsages = True
		value.hasUsages = True
	
	def _toStr(self):
		return f"{self.arrSymbol}[{self.index}] = {self.value}"

class StringEx(AnyValueExpression):
	def _toStr(self):
		return '"' + str(self.value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

class StringConcatEx(TwoExpEx):
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
			lines = []
			for key, value in self.hash.items():
				if re.match(r"^\d", str(key)):
					key = f"\"{key}\""
				lines.append(f"\t{key} => {value},")
			newLine = "\n"
			return f"{{\n{newLine.join(lines)}\n}}"

class RangeEx(TwoExpEx):
	min: Expression
	max: Expression
	isMaxExclusive: bool

	def __init__(self, register: int, minVal: Expression, maxVal: Expression, isMaxExclusive: bool):
		super().__init__(register, minVal, maxVal)
		self.min = minVal
		self.max = maxVal
		self.isMaxExclusive = isMaxExclusive
		minVal.hasUsages = True
		maxVal.hasUsages = True

	def _toStr(self):
		if self.isMaxExclusive:
			return f"{self.min}...{self.max}"
		else:
			return f"{self.min}..{self.max}"

class MainClass(SymbolEx):
	def __init__(self, register: int):
		super().__init__(register, SymbolEx(0, "main"))

class StatementEx(AnyValueExpression):
	def __init__(self, register: int, value: str):
		super().__init__(register, value)
		self.canBeOptimizedAway = False

class ReturnStatementEx(StatementEx):
	returnValue: Expression|None

	def __init__(self, register: int, returnValue: Expression|None):
		super().__init__(register, "return")
		self.returnValue = returnValue
		if returnValue is not None:
			returnValue.hasUsages = True

	def _toStr(self):
		if self.returnValue is None:
			return "return"
		else:
			return f"return {self.returnValue}"

class BreakStatementEx(StatementEx):
	def __init__(self, register: int):
		super().__init__(register, "break")

class MethodArgumentEx(Expression):
	name: SymbolEx
	prefix: str
	defaultValue: Expression|None

	def __init__(self, register: int, name: SymbolEx, defaultValue: Expression|None = None, prefix: str = ""):
		super().__init__(register)
		self.name = name
		self.prefix = prefix
		self.defaultValue = defaultValue
		self.canBeOptimizedAway = False
		name.hasUsages = True
		if defaultValue is not None:
			defaultValue.hasUsages = True

	def _toStr(self):
		if self.defaultValue is None:
			return f"{self.prefix}{self.name}"
		else:
			return f"{self.prefix}{self.name} = {self.defaultValue}"

class MethodEx(Expression):
	parentObject: Expression|None
	name: SymbolEx
	arguments: List[MethodArgumentEx]
	body: BlockEx

	def __init__(self, register: int, name: SymbolEx, arguments: List[MethodArgumentEx], body: BlockEx, parentObject: Expression|None):
		super().__init__(register)
		self.name = name
		self.arguments = arguments
		self.body = body
		self.parentObject = parentObject
		self.canBeOptimizedAway = False
		name.hasUsages = True
		for arg in arguments:
			arg.hasUsages = True
		body.hasUsages = True
		if parentObject is not None:
			parentObject.hasUsages = True

	def _toStr(self):
		if self.parentObject is None:
			result = f"def {self.name}("
		else:
			result = f"def {self.parentObject}.{self.name}("
		if len(self.arguments) > 0:
			result += ", ".join(map(str, self.arguments))
		result += ")\n"
		result += prefixLines(str(self.body), "\t")
		result += "\nend\n"
		return result

class LambdaEx(Expression):
	arguments: List[MethodArgumentEx]
	body: BlockEx

	def __init__(self, register: int, arguments: List[MethodArgumentEx], body: BlockEx):
		super().__init__(register)
		self.arguments = arguments
		self.body = body
		self.canBeOptimizedAway = True
		for arg in arguments:
			arg.hasUsages = True
		body.hasUsages = True

	def _toStr(self):
		args = ""
		if len(self.arguments) > 0:
			args = f"|{', '.join(map(str, self.arguments))}| "
		if len(self.body.expressions) == 0:
			return f"{{ {args}nil }}"
		elif len(self.body.expressions) == 1:
			return f"{{ {args}{self.body} }}"
		else:
			body = prefixLines(str(self.body), "\t")
			return f"{{ {args}\n{body}\n}}"

class ClassEx(Expression):
	name: Expression
	parentClass: Expression|None
	isSingleton: bool
	body: BlockEx

	def __init__(self, register: int, name: ClassSymbolEx, body: BlockEx, isSingleton: bool = False):
		super().__init__(register)
		self.name = name
		self.body = body
		self.parentClass = name.parent
		self.isSingleton = isSingleton
		self.canBeOptimizedAway = False
		name.hasUsages = True
		if self.parentClass is not None:
			self.parentClass.hasUsages = True

	def _toStr(self):
		if self.isSingleton:
			start = f"class << {self.name}\n"
		elif self.parentClass is not None:
			start = f"class {self.name} < {self.parentClass}\n"
		else:
			start = f"class {self.name}\n"
		body = prefixLines(str(self.body), "\t")
		return f"{start}{body}\nend\n"

class ModuleEx(Expression):
	name: ModuleSymbolEx
	body: BlockEx

	def __init__(self, register: int, name: ModuleSymbolEx, body: BlockEx):
		super().__init__(register)
		self.name = name
		self.body = body
		self.canBeOptimizedAway = False
		name.hasUsages = True

	def _toStr(self):
		start = f"module {self.name}\n"
		body = prefixLines(str(self.body), "\t")
		return f"{start}{body}\nend\n"

class AndEx(TwoCombinedExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right, SymbolEx(0, "&&"))

class OrEx(TwoCombinedExpEx):
	def __init__(self, register: int, left: Expression, right: Expression):
		super().__init__(register, left, right, SymbolEx(0, "||"))

class IfEx(StatementEx):
	condition: Expression
	ifBlock: BlockEx
	elseBlock: BlockEx|None

	def __init__(self, register: int, condition: Expression, ifBlock: BlockEx, elseBlock: BlockEx|None = None):
		super().__init__(register, "if")
		self.condition = condition
		self.ifBlock = ifBlock
		self.elseBlock = elseBlock
		condition.hasUsages = True
		ifBlock.hasUsages = True
		if elseBlock is not None:
			elseBlock.hasUsages = True

	def _toStr(self):
		ifBlock = prefixLines(str(self.ifBlock), "\t")
		if self.elseBlock is None:
			return f"if {self.condition}\n{ifBlock}\nend"
		else:
			elseBlock = prefixLines(str(self.elseBlock), "\t")
			return f"if {self.condition}\n{ifBlock}\nelse\n{elseBlock}\nend"

class MConstSymbolEx(TwoExpEx):
	def _toStr(self):
		return f"{self.left}::{self.right}"

class WhileOrUntilEx(StatementEx):
	condition: Expression
	body: BlockEx

	def __init__(self, register: int, loopType: str, condition: Expression, body: BlockEx):
		super().__init__(register, loopType)
		self.condition = condition
		self.body = body
		condition.hasUsages = True
		body.hasUsages = True

	def _toStr(self):
		body = prefixLines(str(self.body), "\t")
		return f"{self.value} {self.condition}\n{body}\nend"

class CaseWhenEx(StatementEx):
	conditions: List[Expression]
	body: BlockEx

	def __init__(self, conditions: List[Expression], body: BlockEx):
		super().__init__(0, "case")
		self.conditions = conditions[:]
		self.body = body
		for cond in conditions:
			cond.hasUsages = True
		body.hasUsages = True

	def _toStr(self):
		cond = "when " + ", ".join(map(str, self.conditions))
		body = prefixLines(str(self.body), "\t")
		return f"{cond}\n{body}"

class CaseEx(Expression):
	caseExp: Expression|None
	whenBlocks: List[CaseWhenEx]
	elseBlock: BlockEx|None

	def __init__(self, register: int, caseExp: Expression|None, whenBlocks: List[CaseWhenEx], elseBlock: BlockEx|None):
		super().__init__(register)
		self.caseExp = caseExp
		self.whenBlocks = whenBlocks
		self.elseBlock = elseBlock
		for whenBlock in whenBlocks:
			whenBlock.hasUsages = True
		if elseBlock is not None:
			elseBlock.hasUsages = True

	def _toStr(self):
		if self.caseExp is None:
			start = "case"
		else:
			start = f"case {self.caseExp}"
		whenBlocks = "\n".join(map(str, self.whenBlocks))
		if self.elseBlock is None:
			return f"\n{start}\n{whenBlocks}\nend\n"
		else:
			elseBlock = prefixLines(str(self.elseBlock), "\t")
			return f"\n{start}\n{whenBlocks}\nelse\n{elseBlock}\nend\n"
