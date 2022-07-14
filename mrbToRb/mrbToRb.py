from __future__ import annotations

from .codeGenerator import CodeGen
from .opcodeReader import OpCodeReader
from ..mrbParser import RiteFile


def mrbToRb(riteFile: RiteFile) -> CodeGen:
	codeGen = CodeGen()
	irepConverter = OpCodeReader()
	irepConverter.parseOps()
	return codeGen
