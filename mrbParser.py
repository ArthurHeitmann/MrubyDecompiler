from __future__ import annotations
from typing import BinaryIO, List
from ioUtils import *
from opcodes import MrbCode, getMrbCode

class RiteBinaryHeader:
	"""
	struct RiteBinaryHeader {
		char binaryIdentifier[4];
		char binaryFormatMajorVersion[2];
		char binaryFormatMinorVersion[2];
		ubyte crc[2];
		uint32 binarySize;
		char compilerName[4];
		char compilerVersion[4];
	} riteHeader;
	"""
	binaryIdentifier: str
	binaryFormatMajorVersion: str
	binaryFormatMinorVersion: str
	crc: int
	binarySize: int
	compilerName: str
	compilerVersion: str

	def __init__(self, file: BinaryIO) -> None:
		self.binaryIdentifier = read_string(file, 4)
		self.binaryFormatMajorVersion = read_string(file, 2)
		self.binaryFormatMinorVersion = read_string(file, 2)
		self.crc = read_uint16(file)
		self.binarySize = read_uint32(file)
		self.compilerName = read_string(file, 4)
		self.compilerVersion = read_string(file, 4)

class RiteSectionHeader:
	"""
	struct RiteSectionHeader
	{
		char sectionIdentifier[4];
		uint32 sectionSize;
	};
	"""
	sectionIdentifier: str
	sectionSize: int

	def __init__(self, file: BinaryIO) -> None:
		self.sectionIdentifier = read_string(file, 4)
		self.sectionSize = read_uint32(file)

class RiteIrepSectionHeader(RiteSectionHeader):
	"""
	struct RiteIrepSectionHeader
	{
		char sectionIdentifier[4];
		uint32 sectionSize;
		char version[4];
	};
	"""
	version: str

	def __init__(self, file: BinaryIO) -> None:
		super().__init__(file)
		self.version = read_string(file, 4)

class RiteIrepSection:
	"""
	struct IrepSection {
		uint32 recordSize;
		uint16 numLocalVariables;
		uint16 numRegisterVariables;
		uint16 numChildIreps;
		
		uint32 iLen;
		byte padding[-FTell() & 3];
		if (iLen > 0) {
			uint32 iSeqMrbCodes[iLen] <read=stringifyMrbCode>;
		}

		uint32 poolLen;
		if (poolLen > 0) {
			struct {
				ubyte tt;
				uint16 poolDataLen;
				char poolData[poolDataLen];
			} pools[poolLen] <optimize = false, read=this.poolData>;
		}

		uint32 symbolsLen;
		if (symbolsLen > 0) {
			struct {
				uint16 symbolNameLength;
				byte symbol[symbolNameLength + 1];
			} symbols[symbolsLen] <optimize = false, read=this.symbol>;
		}

		if (numChildIreps > 0) {
			IrepSection childIreps[numChildIreps] <optimize = false>;
		}
	};
	"""
	recordSize: int
	numLocalVariables: int
	numRegisterVariables: int
	numChildIreps: int

	iLen: int
	mrbCodes: List[MrbCode]

	poolLen: int
	pools: List[bytes]

	symbolsLen: int
	symbols: List[str]

	childIreps: List[RiteIrepSection]

	def __init__(self, file: BinaryIO) -> None:
		self.recordSize = read_uint32(file)
		self.numLocalVariables = read_uint16(file)
		self.numRegisterVariables = read_uint16(file)
		self.numChildIreps = read_uint16(file)
		
		self.iLen = read_uint32(file)
		# align to 4 bytes
		file.read((4 - (file.tell() & 3)) & 3)
		self.mrbCodes = []
		for i in range(self.iLen):
			self.mrbCodes.append(getMrbCode(read_uint32(file)))
		
		self.poolLen = read_uint32(file)
		self.pools = []
		for i in range(self.poolLen):
			read_uint8(file)	# tt
			poolDataLen = read_uint16(file)
			self.pools.append(file.read(poolDataLen))
		
		self.symbolsLen = read_uint32(file)
		self.symbols = []
		for i in range(self.symbolsLen):
			symbolNameLength = read_uint16(file)
			self.symbols.append(read_string(file, symbolNameLength + 1) if symbolNameLength != 0xffff else "")
		
		self.childIreps = []
		for i in range(self.numChildIreps):
			self.childIreps.append(RiteIrepSection(file))

class RiteLvar:
	"""
	struct Lvar {
		uint16 symbolIndex;
		uint16 symbolRegister;
	};
	"""
	symbol: str|None
	symbolRegister: int

	def __init__(self, file: BinaryIO, symbols: List[str]) -> None:
		symbolIndex = read_uint16(file)
		if symbolIndex != 0xffff:
			self.symbol = symbols[symbolIndex]
		else:
			self.symbol = None
		self.symbolRegister = read_uint16(file)

class RiteLvarRecord:
	"""
	struct LvarRecord(const IrepSection& irepSection) {
		Lvar lvars[irepSection.numLocalVariables - 1];

		local int i;
		for (i = 0; i < irepSection.numChildIreps; i++) {
			LvarRecord childRecord(irepSection.childIreps[i]) <optimize = false>;
		}
	};
	"""
	symbols: List[str]
	lvarRecords: List[RiteLvar]
	childLvars: List[RiteLvarRecord]

	def __init__(self, file: BinaryIO|None, irepSection: RiteIrepSection, symbols: List[str]) -> None:
		self.lvarRecords = []
		self.childLvars = []
		if file is not None:
			for i in range(irepSection.numLocalVariables - 1):
				self.lvarRecords.append(RiteLvar(file, symbols))

			for i in range(irepSection.numChildIreps):
				self.childLvars.append(RiteLvarRecord(file, irepSection.childIreps[i], symbols))

class RiteIrepBlock:
	"""
	struct RiteIrepBlock
	{
		RiteIrepSectionHeader header
		RiteIrepSection section
	};
	"""
	header: RiteIrepSectionHeader
	section: RiteIrepSection
	
	def __init__(self, file: BinaryIO) -> None:
		self.header = RiteIrepSectionHeader(file)
		self.section = RiteIrepSection(file)

class RiteLvarBlock:
	"""
	struct Sym {
		uint16 strLen;
		char str[strLen];
	};

	struct LvarRecord;
	struct LvarSection (uint32 sectionSize, const IrepSection& irepSection) {
		uint32 symbolsLen;
		Sym symbols[symbolsLen] <optimize = false, read=this.str>;
		LvarRecord record(irepSection);
	};
	"""
	header: RiteSectionHeader|None
	section: RiteLvarRecord
	
	def __init__(self, file: BinaryIO|None, irepSection: RiteIrepSection) -> None:
		if file is not None:
			self.header = RiteSectionHeader(file)
			symbolsLen = read_uint32(file)
			symbols = []
			for i in range(symbolsLen):
				strLen = read_uint16(file)
				symbols.append(read_string(file, strLen))
			self.section = RiteLvarRecord(file, irepSection, symbols)
		else:
			self.header = None
			self.section = RiteLvarRecord(None, irepSection, [])

class RiteFooter:
	"""
	struct RiteFooter
	{
		char binaryEOFIdentifier[4];
		uint32 binaryEOFSize;
	};
	"""
	binaryEOFIdentifier: str
	binaryEOFSize: int

	def __init__(self, file: BinaryIO) -> None:
		self.binaryEOFIdentifier = read_string(file, 4)
		self.binaryEOFSize = read_uint32(file)

class RiteFile:
	header: RiteBinaryHeader
	irepBlock: RiteIrepBlock
	lvarBlock: RiteLvarBlock
	footer: RiteFooter

	def __init__(self, file: BinaryIO) -> None:
		self.header = RiteBinaryHeader(file)
		remainingSize = self.header.binarySize - 0x16
		size1 = file.tell()
		self.irepBlock = RiteIrepBlock(file)
		remainingSize -= file.tell() - size1
		if remainingSize > 0x8:
			self.lvarBlock = RiteLvarBlock(file, self.irepBlock.section)
		else:
			self.lvarBlock = RiteLvarBlock(None, self.irepBlock.section)
		self.footer = RiteFooter(file)
