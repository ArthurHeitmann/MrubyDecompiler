from __future__ import annotations

from .codeGenerator import CodeGen
from .opcodeReader import OpCodeReader
from mrbParser import RiteFile
from .rbExpressions import MainClass


def mrbToRb(riteFile: RiteFile) -> CodeGen:
	codeGen = CodeGen()
	irepConverter = OpCodeReader(riteFile.irepBlock.section, riteFile.lvarBlock.section, None, MainClass(0), codeGen)
	irepConverter.parseOps()
	return codeGen
