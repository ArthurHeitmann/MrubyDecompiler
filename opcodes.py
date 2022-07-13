from __future__ import annotations

def getMrbCode(mrbCode) -> MrbCode:
	opcode = mrbCode & 0x7f
	return opcodes[opcode][1](mrbCode)

class MrbCode:
	opcode: int
	fullOpcode: int

	def __init__(self, mrbCode: int) -> None:
		self.opcode = mrbCode & 0x7f
		self.fullOpcode = mrbCode

	def __str__(self) -> str:
		return opcodes[self.opcode][0]

class MrbCodeABC(MrbCode):
	A: int
	B: int
	C: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.B = (mrbCode >> 14) & 0x1ff
		self.C = (mrbCode >> 7) & 0x7f
	
	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]} {self.A:x} {self.B:x} {self.C:x}"

class MrbCodeABx(MrbCode):
	A: int
	Bx: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.Bx = (mrbCode >> 7) & 0xffff

	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]} {self.A:x} {self.Bx:x}"

class MrbCodeAsBx(MrbCode):
	A: int
	sBx: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.sBx = ((mrbCode >> 7) & 0xffff) - (0xffff >> 1)

	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]} {self.A:x} {self.sBx:x}"

class MrbCodeAx(MrbCode):
	Ax: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.Ax = (mrbCode >> 7) & 0x1ffffff
	
	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]} {self.Ax:x}"

class MrbCodeABzCz(MrbCode):
	A: int
	Bz: int
	Cz: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.Bz = (mrbCode >> 9) & 0x3fff
		self.Cz = (mrbCode >> 7) & 0x3
	
	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]} {self.A:x} {self.Bz:x} {self.Cz:x}"

opcodes = [
	["OP_NOP", MrbCode],
	["OP_MOVE", MrbCodeABC],
	["OP_LOADL", MrbCodeABx],
	["OP_LOADI", MrbCodeAsBx],
	["OP_LOADSYM", MrbCodeABx],
	["OP_LOADNIL", MrbCodeABC],
	["OP_LOADSELF", MrbCodeABC],
	["OP_LOADT", MrbCodeABC],
	["OP_LOADF", MrbCodeABC],

	["OP_GETGLOBAL", MrbCodeABx],
	["OP_SETGLOBAL", MrbCodeABx],
	["OP_GETSPECIAL", MrbCodeABx],
	["OP_SETSPECIAL", MrbCodeABx],
	["OP_GETIV", MrbCodeABx],
	["OP_SETIV", MrbCodeABx],
	["OP_GETCV", MrbCodeABx],
	["OP_SETCV", MrbCodeABx],
	["OP_GETCONST", MrbCodeABx],
	["OP_SETCONST", MrbCodeABx],
	["OP_GETMCNST", MrbCodeABx],
	["OP_SETMCNST", MrbCodeABx],
	["OP_GETUPVAR", MrbCodeABC],
	["OP_SETUPVAR", MrbCodeABC],

	["OP_JMP", MrbCodeAsBx],
	["OP_JMPIF", MrbCodeAsBx],
	["OP_JMPNOT", MrbCodeAsBx],
	["OP_ONERR", MrbCodeAsBx],
	["OP_RESCUE", MrbCodeABC],
	["OP_POPERR", MrbCodeABC],
	["OP_RAISE", MrbCodeABC],
	["OP_EPUSH", MrbCodeABx],
	["OP_EPOP", MrbCodeABC],

	["OP_SEND", MrbCodeABC],
	["OP_SENDB", MrbCodeABC],
	["OP_FSEND", MrbCodeABC],
	["OP_CALL", MrbCodeABC],
	["OP_SUPER", MrbCodeABC],
	["OP_ARGARY", MrbCodeABx],
	["OP_ENTER", MrbCodeAx],
	["OP_KARG", MrbCodeABC],
	["OP_KDICT", MrbCodeABC],

	["OP_RETURN", MrbCodeABC],
	["OP_TAILCALL", MrbCodeABC],
	["OP_BLKPUSH", MrbCodeABx],

	["OP_ADD", MrbCodeABC],
	["OP_ADDI", MrbCodeABC],
	["OP_SUB", MrbCodeABC],
	["OP_SUBI", MrbCodeABC],
	["OP_MUL", MrbCodeABC],
	["OP_DIV", MrbCodeABC],
	["OP_EQ", MrbCodeABC],
	["OP_LT", MrbCodeABC],
	["OP_LE", MrbCodeABC],
	["OP_GT", MrbCodeABC],
	["OP_GE", MrbCodeABC],

	["OP_ARRAY", MrbCodeABC],
	["OP_ARYCAT", MrbCodeABC],
	["OP_ARYPUSH", MrbCodeABC],
	["OP_AREF", MrbCodeABC],
	["OP_ASET", MrbCodeABC],
	["OP_APOST", MrbCodeABC],

	["OP_STRING", MrbCodeABx],
	["OP_STRCAT", MrbCodeABC],

	["OP_HASH", MrbCodeABC],
	["OP_LAMBDA", MrbCodeABzCz],
	["OP_RANGE", MrbCodeABC],

	["OP_OCLASS", MrbCodeABC],
	["OP_CLASS", MrbCodeABC],
	["OP_MODULE", MrbCodeABC],
	["OP_EXEC", MrbCodeABx],
	["OP_METHOD", MrbCodeABC],
	["OP_SCLASS", MrbCodeABC],
	["OP_TCLASS", MrbCodeABC],

	["OP_DEBUG", MrbCodeABC],
	["OP_STOP", MrbCodeABC],
	["OP_ERR", MrbCodeABx],
	
	["OP_RSVD1", MrbCode],
	["OP_RSVD2", MrbCode],
	["OP_RSVD3", MrbCode],
	["OP_RSVD4", MrbCode],
	["OP_RSVD5", MrbCode],
	["OP_UNKNOWN", MrbCode],
]