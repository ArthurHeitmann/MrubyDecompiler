from __future__ import annotations
from typing import Union

from mrbParser import RiteLvarRecord, RiteIrepSection
from mrbToRb.codeGenerator import CodeGen
from mrbToRb.opCodeFeed import OpCodeFeed
from mrbToRb.register import Register
from mrbToRb.rbExpressions import *
from opcodes import *
from consts import ENCODING


class OpCodeReader:
    registers: List[Register]
    currentClass: Any
    parent: OpCodeReader
    opcodes: OpCodeFeed
    pool: List[bytes]
    symbols: List[str]
    childIreps: List[RiteIrepSection]
    localVarsMap: Dict[int, str]
    codeGen: CodeGen

    def __init__(self, irep: RiteIrepSection, lvars: RiteLvarRecord, parent: OpCodeReader, curClass, codeGen: CodeGen):
        self.parent = parent
        self.localVarsMap = {}
        for lvar in lvars.lvarRecords:
            self.localVarsMap[lvar.symbolRegister] = lvar.symbol
        self.registers = []
        for i in range(irep.numRegisterVariables):
            self.registers.append(Register(i, None, self.localVarsMap.get(i, None)))
        self.currentClass = curClass
        self.opcodes = OpCodeFeed(irep.mrbCodes)
        self.childIreps = irep.childIreps
        self.codeGen = codeGen

    def step(self):
        opcode: Union[MrbCode, MrbCodeABC, MrbCodeABx, MrbCodeAsBx, MrbCodeAx]
        opcode = self.opcodes.cur()
        self.codeGen.pushExp(LineCommentEx(str(opcode)))

        if opcode == AllOpCodes.OP_NOP:
            return
        elif opcode == AllOpCodes.OP_MOVE:
            self.registers[opcode.A].moveIn(self.registers[opcode.B])
        elif opcode == AllOpCodes.OP_LOADL:
            self.registers[opcode.A].load(StringEx(self.pool[opcode.Bx].decode(ENCODING)))
        elif opcode == AllOpCodes.OP_LOADI:
            self.registers[opcode.A].load(LiteralEx(opcode.sBx))
        elif opcode == AllOpCodes.OP_LOADSYM:
            self.registers[opcode.A].load(SymbolEx(self.symbols[opcode.Bx]))
        elif opcode == AllOpCodes.OP_LOADNIL:
            self.registers[opcode.A].load(LiteralEx("nil"))
        elif opcode == AllOpCodes.OP_LOADSELF:
            self.registers[opcode.A].load(LiteralEx("self"))
        elif opcode == AllOpCodes.OP_LOADT:
            self.registers[opcode.A].load(LiteralEx("true"))
        elif opcode == AllOpCodes.OP_LOADF:
            self.registers[opcode.A].load(LiteralEx("false"))

        elif opcode == AllOpCodes.OP_GETGLOBAL:
            self.registers[opcode.A].load(GlobalSymbolEx(self.symbols[opcode.Bx]))
        elif opcode == AllOpCodes.OP_SETGLOBAL:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_GETSPECIAL:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_SETSPECIAL:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_GETIV:
            self.registers[opcode.A].load(InstanceSymbolEx(self.symbols[opcode.Bx]))
        elif opcode == AllOpCodes.OP_SETIV:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_GETCV:
            self.registers[opcode.A].load(ClassSymbolEx(self.symbols[opcode.Bx]))
        elif opcode == AllOpCodes.OP_SETCV:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_GETCONST:
            self.registers[opcode.A].load(SymbolEx(self.symbols[opcode.Bx]))
        elif opcode == AllOpCodes.OP_SETCONST:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_GETMCNST:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_SETMCNST:
            # TODO
            pass
        elif opcode == AllOpCodes.OP_GETUPVAR:
            # TODO check
            self.registers[opcode.A].load(SymbolEx(self.findUpVar(opcode.B)))
        elif opcode == AllOpCodes.OP_SETUPVAR:
            # TODO
            pass

        elif opcode == AllOpCodes.OP_JMP:  # end of if
            pass
        elif opcode == AllOpCodes.OP_JMPIF:  # start of if or while
            pass
        elif opcode == AllOpCodes.OP_JMPNOT:
            pass
        elif opcode == AllOpCodes.OP_ONERR:
            pass
        elif opcode == AllOpCodes.OP_RESCUE:
            pass
        elif opcode == AllOpCodes.OP_POPERR:
            pass
        elif opcode == AllOpCodes.OP_RAISE:
            pass
        elif opcode == AllOpCodes.OP_EPUSH:
            pass
        elif opcode == AllOpCodes.OP_EPOP:
            pass

        elif opcode == AllOpCodes.OP_SEND:
            pass
        elif opcode == AllOpCodes.OP_SENDB:
            pass
        elif opcode == AllOpCodes.OP_FSEND:
            pass
        elif opcode == AllOpCodes.OP_CALL:
            pass
        elif opcode == AllOpCodes.OP_SUPER:
            pass
        elif opcode == AllOpCodes.OP_ARGARY:
            pass
        elif opcode == AllOpCodes.OP_ENTER:
            pass
        elif opcode == AllOpCodes.OP_KARG:
            pass
        elif opcode == AllOpCodes.OP_KDICT:
            pass

        elif opcode == AllOpCodes.OP_RETURN:
            pass
        elif opcode == AllOpCodes.OP_TAILCALL:
            pass
        elif opcode == AllOpCodes.OP_BLKPUSH:
            pass

        elif opcode == AllOpCodes.OP_ADD:
            pass
        elif opcode == AllOpCodes.OP_ADDI:
            pass
        elif opcode == AllOpCodes.OP_SUB:
            pass
        elif opcode == AllOpCodes.OP_SUBI:
            pass
        elif opcode == AllOpCodes.OP_MUL:
            pass
        elif opcode == AllOpCodes.OP_DIV:
            pass
        elif opcode == AllOpCodes.OP_EQ:
            pass
        elif opcode == AllOpCodes.OP_LT:
            pass
        elif opcode == AllOpCodes.OP_LE:
            pass
        elif opcode == AllOpCodes.OP_GT:
            pass
        elif opcode == AllOpCodes.OP_GE:
            pass

        elif opcode == AllOpCodes.OP_ARRAY:
            pass
        elif opcode == AllOpCodes.OP_ARYCAT:
            pass
        elif opcode == AllOpCodes.OP_ARYPUSH:
            pass
        elif opcode == AllOpCodes.OP_AREF:
            pass
        elif opcode == AllOpCodes.OP_ASET:
            pass
        elif opcode == AllOpCodes.OP_APOST:
            pass

        elif opcode == AllOpCodes.OP_STRING:
            pass
        elif opcode == AllOpCodes.OP_STRCAT:
            pass

        elif opcode == AllOpCodes.OP_HASH:
            pass
        elif opcode == AllOpCodes.OP_LAMBDA:
            pass
        elif opcode == AllOpCodes.OP_RANGE:
            pass

        elif opcode == AllOpCodes.OP_OCLASS:
            pass
        elif opcode == AllOpCodes.OP_CLASS:
            pass
        elif opcode == AllOpCodes.OP_MODULE:
            pass
        elif opcode == AllOpCodes.OP_EXEC:
            pass
        elif opcode == AllOpCodes.OP_METHOD:
            pass
        elif opcode == AllOpCodes.OP_SCLASS:
            pass
        elif opcode == AllOpCodes.OP_TCLASS:
            pass

        elif opcode == AllOpCodes.OP_DEBUG:
            pass
        elif opcode == AllOpCodes.OP_STOP:
            pass
        elif opcode == AllOpCodes.OP_ERR:
            pass

        elif opcode == AllOpCodes.OP_RSVD1:
            pass
        elif opcode == AllOpCodes.OP_RSVD2:
            pass
        elif opcode == AllOpCodes.OP_RSVD3:
            pass
        elif opcode == AllOpCodes.OP_RSVD4:
            pass
        elif opcode == AllOpCodes.OP_RSVD5:
            pass
        elif opcode == AllOpCodes.OP_UNKNOWN:
            pass

    def parseOps(self):
        for i in range(len(self.opcodes)):
            self.step()

    def findUpVar(self, register: int) -> str:
        for regI, symb in self.localVarsMap:
            if regI == register:
                return symb
        if self.parent is not None:
            return self.parent.findUpVar(register)
        raise Exception("Could not find upvar for register " + str(register))