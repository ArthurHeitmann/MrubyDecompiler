from __future__ import annotations
from typing import Union, cast

from mrbParser import RiteLvarRecord, RiteIrepSection
from mrbToRb.codeGenerator import CodeGen
from mrbToRb.opCodeFeed import OpCodeFeed
from mrbToRb.register import Register
from mrbToRb.rbExpressions import *
from opcodes import *
from consts import ENCODING


class OpCodeReader:
    registers: List[Register]
    currentClass: SymbolEx
    parent: OpCodeReader
    opcodes: OpCodeFeed
    pool: List[str]
    symbols: List[SymbolEx]
    childIreps: List[RiteIrepSection]
    localVarsMap: Dict[int, SymbolEx]
    codeGen: CodeGen

    def __init__(self, irep: RiteIrepSection, lvars: RiteLvarRecord, parent: OpCodeReader|None, curClass: SymbolEx, codeGen: CodeGen):
        self.parent = parent
        self.pool = list(map(lambda b: b.decode(ENCODING, "ignore"), irep.pools))
        self.symbols = list(map(lambda s: SymbolEx(0, s), irep.symbols))
        self.localVarsMap = {}
        for lvar in lvars.lvarRecords:
            self.localVarsMap[lvar.symbolRegister] = SymbolEx(lvar.symbolRegister, lvar.symbol)
        self.registers = []
        for i in range(irep.numRegisterVariables):
            self.registers.append(Register(i, NilEx(0), self.localVarsMap.get(i, None)))
        self.currentClass = curClass
        self.opcodes = OpCodeFeed(irep.mrbCodes)
        self.childIreps = irep.childIreps
        self.codeGen = codeGen

    def step(self):
        opcode: Union[MrbCode, MrbCodeABC, MrbCodeABx, MrbCodeAsBx, MrbCodeAx]
        opcode = self.opcodes.cur()
        # self.codeGen.pushExp(LineCommentEx(0, str(opcode)))

        def pushExpToCodeGen(regI: int, expression: Expression):
            if regI in self.localVarsMap:
                self.codeGen.pushExp(AssignmentEx(regI, self.localVarsMap[regI], expression))
            else:
                self.codeGen.pushExp(expression)

        def unhandledOpCode():
            raise Exception("Unhandled opcode: " + str(opcode))

        if opcode.opcode == AllOpCodes.OP_NOP:
            return
        elif opcode.opcode == AllOpCodes.OP_MOVE:
            self.registers[opcode.A].moveIn(self.registers[opcode.B])
            pushExpToCodeGen(opcode.A, self.registers[opcode.B].value)
        elif AllOpCodes.OP_LOADL <= opcode.opcode <= AllOpCodes.OP_LOADF:
            value: Expression
            if opcode.opcode == AllOpCodes.OP_LOADL:
                value = LiteralEx(opcode.A, self.pool[opcode.Bx])
            elif opcode.opcode == AllOpCodes.OP_LOADI:
                value = LiteralEx(opcode.A, opcode.sBx)
            elif opcode.opcode == AllOpCodes.OP_LOADSYM:
                value = SymbolValEx(opcode.A, self.symbols[opcode.Bx])
            elif opcode.opcode == AllOpCodes.OP_LOADNIL:
                value = NilEx(opcode.A)
            elif opcode.opcode == AllOpCodes.OP_LOADSELF:
                value = SelfEx(opcode.A)
            elif opcode.opcode == AllOpCodes.OP_LOADT:
                value = TrueEx(opcode.A)
            elif opcode.opcode == AllOpCodes.OP_LOADF:
                value = FalseEx(opcode.A)
            else:
                raise Exception("Unknown load opcode " + str(opcode))
            self.registers[opcode.A].load(value)
            pushExpToCodeGen(opcode.A, value)

        elif opcode.opcode in { AllOpCodes.OP_GETGLOBAL, AllOpCodes.OP_GETSPECIAL, AllOpCodes.OP_GETIV, AllOpCodes.OP_GETCV, AllOpCodes.OP_GETCONST }:
            exp = SymbolEx(opcode.A, self.symbols[opcode.Bx])
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode in { AllOpCodes.OP_SETGLOBAL , AllOpCodes.OP_SETSPECIAL, AllOpCodes.OP_SETIV, AllOpCodes.OP_SETCV, AllOpCodes.OP_SETCONST }:
            exp = AssignmentEx(opcode.A, SymbolEx(opcode.A, self.symbols[opcode.Bx]), self.registers[opcode.A].value)
            self.codeGen.pushExp(exp)
        elif opcode.opcode == AllOpCodes.OP_GETMCNST:
            unhandledOpCode()
        elif opcode.opcode == AllOpCodes.OP_SETMCNST:
            unhandledOpCode()
        elif opcode.opcode == AllOpCodes.OP_GETUPVAR:
            upVar = self.findUpVar(opcode.B)        # TODO check
            self.registers[opcode.A].moveIn(upVar)
            pushExpToCodeGen(opcode.A, upVar.value)
        elif opcode.opcode == AllOpCodes.OP_SETUPVAR:
            unhandledOpCode()   # TODO

        # elif opcode.opcode == AllOpCodes.OP_JMP:  # end of if
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_JMPIF:  # start of if or while
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_JMPNOT:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_ONERR:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_RESCUE:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_POPERR:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_RAISE:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_EPUSH:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_EPOP:
        #     unhandledOpCode()

        elif opcode.opcode == AllOpCodes.OP_SEND:
            args = [reg.value for reg in self.registers[opcode.A + 1: opcode.A + 1 + opcode.C]]
            srcObj: SymbolEx|None = self.registers[opcode.A].value
            if isinstance(srcObj, SelfEx) and isinstance(self.currentClass, MainClass):
                srcObj.hasUsages = True
                srcObj = None
            exp = MethodCallEx(opcode.A, srcObj, self.symbols[opcode.B], args)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_SENDB:      # TODO check
            args = [reg.value for reg in self.registers[opcode.A + 1: opcode.A + 1 + opcode.C]]
            block = self.registers[opcode.A + opcode.C + 1].value
            exp = MethodCallWithBlockEx(opcode.A, self.registers[opcode.A].value, self.symbols[opcode.B], args, cast(BlockEx, block))
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        # elif opcode.opcode == AllOpCodes.OP_FSEND:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_CALL:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_SUPER:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_ARGARY:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_ENTER:
        #     # TODO
        #     pass
        # elif opcode.opcode == AllOpCodes.OP_KARG:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_KDICT:
        #     unhandledOpCode()

        elif opcode.opcode == AllOpCodes.OP_RETURN:
            # TODO
            pass
        # elif opcode.opcode == AllOpCodes.OP_TAILCALL:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_BLKPUSH:
        #     unhandledOpCode()

        elif AllOpCodes.OP_ADD <= opcode.opcode <= AllOpCodes.OP_DIV:
            if opcode.opcode in { AllOpCodes.OP_ADD, AllOpCodes.OP_SUB, AllOpCodes.OP_MUL, AllOpCodes.OP_DIV }:
                exp = TwoCombinedExpEx(opcode.A, self.registers[opcode.A].value, self.registers[opcode.A + 1].value, self.symbols[opcode.B])
            elif opcode.opcode in { AllOpCodes.OP_ADDI, AllOpCodes.OP_SUBI }:
                exp = TwoCombinedExpEx(opcode.A, self.registers[opcode.A].value, LiteralEx(0, opcode.C), self.symbols[opcode.B])
            else:
                raise Exception("Unknown arithmetic opcode " + str(opcode))
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif AllOpCodes.OP_EQ <= opcode.opcode <= AllOpCodes.OP_GE:
            exp = BoolExpEx(opcode.A, self.registers[opcode.A].value, self.registers[opcode.A + 1].value, self.symbols[opcode.B])
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)

        elif opcode.opcode == AllOpCodes.OP_ARRAY:
            elements = [reg.value for reg in self.registers[opcode.B : opcode.B + opcode.C]]
            exp = ArrayEx(opcode.A, elements)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_ARYCAT:
            exp = ArrayConcatEx(opcode.A, self.registers[opcode.A].value, self.registers[opcode.B].value)
            self.codeGen.pushExp(exp)
        elif opcode.opcode == AllOpCodes.OP_ARYPUSH:
            exp = ArrayPushEx(opcode.A, self.registers[opcode.A].value, self.registers[opcode.B].value)
            self.codeGen.pushExp(exp)
        # elif opcode.opcode == AllOpCodes.OP_AREF:
        #     exp = ArrayRefEx(opcode.A, self.registers[opcode.B].value, opcode.C)
        #     self.registers[opcode.A].load(exp)
        #     pushExpToCodeGen(opcode.A, exp)
        # elif opcode.opcode == AllOpCodes.OP_ASET:
        #     exp = ArraySetEx(opcode.A, cast(SymbolEx, self.registers[opcode.B].value), opcode.C, self.registers[opcode.A].value)
        #     self.codeGen.pushExp(exp)
        # elif opcode.opcode == AllOpCodes.OP_APOST:
        #     unhandledOpCode()

        elif opcode.opcode == AllOpCodes.OP_STRING:
            exp = StringEx(opcode.A, self.pool[opcode.Bx])
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_STRCAT:
            exp = StringConcatEx(opcode.A, self.registers[opcode.A].value, self.registers[opcode.B].value)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)

        elif opcode.opcode == AllOpCodes.OP_HASH:
            keys = self.registers[opcode.B : opcode.B + opcode.C*2 : 2]
            keys = [reg.value for reg in keys]
            values = self.registers[opcode.B + 1 : opcode.B + 1 + opcode.C*2 : 2]
            values = [reg.value for reg in values]
            combinedDict = dict(zip(keys, values))
            exp = HashEx(opcode.A, combinedDict)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_LAMBDA:
            unhandledOpCode()   # TODO
        elif opcode.opcode == AllOpCodes.OP_RANGE:
            exp = RangeEx(opcode.A, self.registers[opcode.B].value, self.registers[opcode.B + 1].value, bool(opcode.C))
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)

        # elif opcode.opcode == AllOpCodes.OP_OCLASS:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_CLASS:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_MODULE:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_EXEC:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_METHOD:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_SCLASS:
        #     unhandledOpCode()
        elif opcode.opcode == AllOpCodes.OP_TCLASS:
            pass    # TODO check

        # elif opcode.opcode == AllOpCodes.OP_DEBUG:
        #     unhandledOpCode()
        elif opcode.opcode == AllOpCodes.OP_STOP:
            self.codeGen.pushExp(LineCommentEx(0, "STOP"))
        # elif opcode.opcode == AllOpCodes.OP_ERR:
        #     unhandledOpCode()

        # elif opcode.opcode == AllOpCodes.OP_RSVD1:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_RSVD2:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_RSVD3:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_RSVD4:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_RSVD5:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_UNKNOWN:
        #     unhandledOpCode()
        else:
            unhandledOpCode()

        self.opcodes.next()

    def parseOps(self):
        for i in range(len(self.opcodes)):
            self.step()

    def findUpVar(self, register: int) -> Register:
        for regI in self.localVarsMap.keys():
            if regI == register:
                return self.registers[regI]
        if self.parent is not None:
            return self.parent.findUpVar(register)
        raise Exception("Could not find upvar for register " + str(register))