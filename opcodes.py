from __future__ import annotations
import ctypes

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
	# A:B:C:OP = 9:9:7:7
	A: int
	B: int
	C: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.B = (mrbCode >> 14) & 0x1ff
		self.C = (mrbCode >> 7) & 0x7f
	
	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]}:  A: 0x{self.A:x} B: 0x{self.B:x} C: 0x{self.C:x}"

class MrbCodeABx(MrbCode):
	# A:Bx:OP = 9:16:7
	A: int
	Bx: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.Bx = (mrbCode >> 7) & 0xffff

	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]}:  A: 0x{self.A:x} Bx: 0x{self.Bx:x}"

class MrbCodeAsBx(MrbCode):
	# A:sBx:OP = 9:16:7		(sBx is signed)
	A: int
	sBx: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.sBx = ctypes.c_int32(((mrbCode >> 7) & 0xffff) - (0xffff >> 1)).value

	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]}:  A: 0x{self.A:x} sBx: 0x{self.sBx:x}"

class MrbCodeAx(MrbCode):
	# Ax:OP = 25:7
	Ax: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.Ax = (mrbCode >> 7) & 0x1ffffff

	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]}:  Ax: 0x{self.Ax:x}"

class MrbCodeABzCz(MrbCode):
	# A:Bz:Cz:OP = 9:14:2:7
	A: int
	Bz: int
	Cz: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.A = (mrbCode >> 23) & 0x1ff
		self.Bz = (mrbCode >> 9) & 0x3fff
		self.Cz = (mrbCode >> 7) & 0x3

	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]}:  A: 0x{self.A:x} Bz: 0x{self.Bz:x} Cz: 0x{self.Cz:x}"

class MrbCodeAspec(MrbCode):
	# Aw:Bw:Cw:Dw:Ew:Fw:Gw:OP = 2:5:5:1:5:5:1:1:7
	Ax: int
	req: int
	opt: int
	rest: int
	post: int
	key: int
	kdict: int
	block: int

	def __init__(self, mrbCode: int) -> None:
		super().__init__(mrbCode)
		self.Ax = (mrbCode >> 7) & 0x1ffffff
		self.req = (self.Ax >> 18) & 0x1f
		self.opt = (self.Ax >> 13) & 0x1f
		self.rest = (self.Ax >> 12) & 0x1
		self.post = (self.Ax >> 7) & 0x1f
		self.key = (self.Ax >> 2) & 0x1f
		self.kdict = (self.Ax >> 1) & 0x1
		self.block = self.Ax & 0x1

	def __str__(self) -> str:
		return f"{opcodes[self.opcode][0]}:  req: {self.req} opt: {self.opt} rest: {self.rest} post: {self.post} key: {self.key} kdict: {self.kdict} block: {self.block}"

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
	["OP_ENTER", MrbCodeAspec],
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

class AllOpCodes:
	OP_NOP = 0
	OP_MOVE = 1
	OP_LOADL = 2
	OP_LOADI = 3
	OP_LOADSYM = 4
	OP_LOADNIL = 5
	OP_LOADSELF = 6
	OP_LOADT = 7
	OP_LOADF = 8
	OP_GETGLOBAL = 9
	OP_SETGLOBAL = 10
	OP_GETSPECIAL = 11
	OP_SETSPECIAL = 12
	OP_GETIV = 13
	OP_SETIV = 14
	OP_GETCV = 15
	OP_SETCV = 16
	OP_GETCONST = 17
	OP_SETCONST = 18
	OP_GETMCNST = 19
	OP_SETMCNST = 20
	OP_GETUPVAR = 21
	OP_SETUPVAR = 22
	OP_JMP = 23
	OP_JMPIF = 24
	OP_JMPNOT = 25
	OP_ONERR = 26
	OP_RESCUE = 27
	OP_POPERR = 28
	OP_RAISE = 29
	OP_EPUSH = 30
	OP_EPOP = 31
	OP_SEND = 32
	OP_SENDB = 33
	OP_FSEND = 34
	OP_CALL = 35
	OP_SUPER = 36
	OP_ARGARY = 37
	OP_ENTER = 38
	OP_KARG = 39
	OP_KDICT = 40
	OP_RETURN = 41
	OP_TAILCALL = 42
	OP_BLKPUSH = 43
	OP_ADD = 44
	OP_ADDI = 45
	OP_SUB = 46
	OP_SUBI = 47
	OP_MUL = 48
	OP_DIV = 49
	OP_EQ = 50
	OP_LT = 51
	OP_LE = 52
	OP_GT = 53
	OP_GE = 54
	OP_ARRAY = 55
	OP_ARYCAT = 56
	OP_ARYPUSH = 57
	OP_AREF = 58
	OP_ASET = 59
	OP_APOST = 60
	OP_STRING = 61
	OP_STRCAT = 62
	OP_HASH = 63
	OP_LAMBDA = 64
	OP_RANGE = 65
	OP_OCLASS = 66
	OP_CLASS = 67
	OP_MODULE = 68
	OP_EXEC = 69
	OP_METHOD = 70
	OP_SCLASS = 71
	OP_TCLASS = 72
	OP_DEBUG = 73
	OP_STOP = 74
	OP_ERR = 75
	OP_RSVD1 = 76
	OP_RSVD2 = 77
	OP_RSVD3 = 78
	OP_RSVD4 = 79
	OP_RSVD5 = 80
	OP_UNKNOWN = 81
