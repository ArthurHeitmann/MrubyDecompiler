from __future__ import annotations

import copy
from typing import cast, Tuple

from mrbParser import RiteLvarRecord, RiteIrepSection
from mrbToRb.codeGenerator import CodeGen
from mrbToRb.opCodeFeed import OpCodeFeed
from mrbToRb.register import Register
from mrbToRb.rbExpressions import *
from opcodes import *
from utils import ENCODING


class OpCodeReader:
    registers: List[Register]
    currentClass: SymbolEx
    parent: OpCodeReader
    opcodes: OpCodeFeed
    pool: List[str]
    symbols: List[SymbolEx]
    childIreps: List[RiteIrepSection]
    childLvars: List[RiteLvarRecord]
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
            self.registers.append(Register(i, self.localVarsMap.get(i, None)))
        self.currentClass = curClass
        self.opcodes = OpCodeFeed(irep.mrbCodes)
        self.childIreps = irep.childIreps
        self.childLvars = lvars.childLvars
        self.codeGen = codeGen

    def step(self):
        opcode = self.opcodes.cur()
        # self.codeGen.pushExp(LineCommentEx(0, str(opcode)))

        def pushExpToCodeGen(regI: int, expression: Expression, localVarsMap: Dict = None):
            if not localVarsMap:
                localVarsMap = self.localVarsMap
            if regI in localVarsMap:
                self.codeGen.pushExp(AssignmentEx(regI, localVarsMap[regI], expression))
            else:
                self.codeGen.pushExp(expression)

        def unhandledOpCode():
            raise Exception("Unhandled opcode: " + str(opcode))

        if opcode.opcode == AllOpCodes.OP_NOP:
            return
        elif opcode.opcode == AllOpCodes.OP_MOVE:
            val = self.registers[opcode.B].value
            self.registers[opcode.A].moveIn(self.registers[opcode.B])
            pushExpToCodeGen(opcode.A, val)
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
            upVar, _ = self.findUpVar(opcode.B)
            self.registers[opcode.A].moveIn(upVar)
            pushExpToCodeGen(opcode.A, upVar.value)
        elif opcode.opcode == AllOpCodes.OP_SETUPVAR:
            upVarReg, context = self.findUpVar(opcode.B)
            upVarReg.moveIn(self.registers[opcode.A])
            pushExpToCodeGen(opcode.B, upVarReg.value, context.localVarsMap)

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
            srcObj: Expression|None = self.registers[opcode.A].value
            if isinstance(srcObj, SelfEx) and isinstance(self.currentClass, MainClass):
                srcObj.hasUsages = True
                srcObj = None
            exp = MethodCallEx(opcode.A, srcObj, self.symbols[opcode.B], args)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_SENDB:      # TODO check
            args = [reg.value for reg in self.registers[opcode.A + 1: opcode.A + 1 + opcode.C]]
            block = cast(LambdaEx, self.registers[opcode.A + opcode.C + 1].value)
            exp = MethodCallWithBlockEx(opcode.A, self.registers[opcode.A].value, self.symbols[opcode.B], args, block)
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
            retStatement: StatementEx
            if opcode.B == 0:
                if opcode.A in self.localVarsMap:
                    retValue = self.registers[opcode.A].value
                    retStatement = ReturnStatementEx(opcode.A, retValue)
                    self.codeGen.pushExp(retStatement)
            elif opcode.B == 1:
                retStatement = BreakStatementEx(opcode.A)
                self.codeGen.pushExp(retStatement)
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
            args, body = self.parseLambda(self.currentClass)
            nextOpcode = self.opcodes.getRel(1)
            if nextOpcode.opcode == AllOpCodes.OP_METHOD:
                self.opcodes.next()
                srcObj = self.registers[nextOpcode.A].value
                if srcObj is self.currentClass:
                    srcObj.hasUsages = True
                    srcObj = None
                elif isinstance(srcObj, SelfEx) and isinstance(self.currentClass, MainClass):
                    srcObj = self.currentClass
                exp = MethodEx(0, self.symbols[nextOpcode.B], args,
                               BlockEx(opcode.A, body), srcObj)
                self.codeGen.pushExp(exp)
            else:
                exp = LambdaEx(opcode.A, args, BlockEx(0, body))
                self.registers[opcode.A].load(exp)
                pushExpToCodeGen(opcode.A, exp)


        elif opcode.opcode == AllOpCodes.OP_RANGE:
            exp = RangeEx(opcode.A, self.registers[opcode.B].value, self.registers[opcode.B + 1].value, bool(opcode.C))
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)

        elif opcode.opcode == AllOpCodes.OP_OCLASS:
            exp = ClassSymbolEx(opcode.A, StringEx(0, "Object"))
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_CLASS:
            parentClass = self.registers[opcode.A + 1].value
            if isinstance(parentClass, NilEx):
                parentClass = None
            exp = ClassSymbolEx(opcode.A, self.symbols[opcode.B], parentClass)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_MODULE:
            exp = ModuleSymbolEx(opcode.A, self.symbols[opcode.B])
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_EXEC:
            target = self.registers[opcode.A].value
            if not isinstance(target, ClassSymbolEx) and not isinstance(target, ModuleSymbolEx):
                unhandledOpCode()
            codeGen = CodeGen()
            opcodeReader = OpCodeReader(self.childIreps[opcode.Bx], self.childLvars[opcode.Bx], self, target, codeGen)
            opcodeReader.parseOps()
            body = BlockEx(0, codeGen.getExpressions())
            if isinstance(target, ClassSymbolEx):
                exp = ClassEx(opcode.A, target, body, target.isSingleton)
            else:
                exp = ModuleEx(opcode.A, target, body)
            self.codeGen.pushExp(exp)
        elif opcode.opcode == AllOpCodes.OP_METHOD:
            if self.opcodes.getRel(-2).opcode != AllOpCodes.OP_SCLASS and self.opcodes.getRel(-1) != AllOpCodes.OP_LAMBDA:
                unhandledOpCode()
            name = SymbolEx(0, f"{self.registers[opcode.A].value}.{self.symbols[opcode.B]}")
            lambdaExp = cast(LambdaEx, self.registers[opcode.A + 1].value)
            exp = MethodEx(opcode.A, name, lambdaExp.arguments, lambdaExp.body, self.registers[opcode.A].value)
            self.codeGen.pushExp(exp)

        elif opcode.opcode == AllOpCodes.OP_SCLASS:
            exp = ClassSymbolEx(opcode.A, self.registers[opcode.B].value, None, True)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)

        elif opcode.opcode == AllOpCodes.OP_TCLASS:
            classSym = self.currentClass
            self.registers[opcode.A].load(classSym)
            pushExpToCodeGen(opcode.A, classSym)

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
        while self.opcodes.hasNext():
            self.step()

    def findUpVar(self, register: int, _checkSelf = False) -> Tuple[Register, OpCodeReader]:
        if _checkSelf:
            for regI in self.localVarsMap.keys():
                if regI == register:
                    return self.registers[regI], self
        if self.parent is not None:
            return self.parent.findUpVar(register, True)
        raise Exception("Could not find upvar for register " + str(register))

    def parseLambda(self, parentClass: SymbolEx) -> Tuple[List[MethodArgumentEx], List[Expression]]:
        args: List[MethodArgumentEx] = []
        body: List[Expression]
        opcode = cast(MrbCodeABzCz, self.opcodes.cur())
        irep = self.childIreps[opcode.Bz]
        lvars = self.childLvars[opcode.Bz]
        methodStartPointer = 0

        # args
        lvarIndex = 0
        enterOpcode = cast(MrbCodeAspec, irep.mrbCodes[0])
        # has args?
        if enterOpcode.opcode == AllOpCodes.OP_ENTER:
            # not a for loop?
            if not (enterOpcode.Ax == 0x40000 and len(lvars.lvarRecords) == 0):
                methodStartPointer = 1
                for i in range(enterOpcode.req):
                    argReg = lvars.lvarRecords[lvarIndex].symbolRegister
                    argSym = SymbolEx(0, lvars.lvarRecords[lvarIndex].symbol)
                    args.append(MethodArgumentEx(argReg, argSym))
                    lvarIndex += 1
                instructionsPointer = 1
                for i in range(enterOpcode.opt):
                    argReg = lvars.lvarRecords[lvarIndex].symbolRegister
                    argSym = SymbolEx(0, lvars.lvarRecords[lvarIndex].symbol)

                    jmpStartInstruction = cast(MrbCodeAsBx, irep.mrbCodes[i + 1])
                    jmpEndInstruction = cast(MrbCodeAsBx, irep.mrbCodes[i + 2])
                    methodStartPointer = instructionsPointer + jmpEndInstruction.sBx + 1
                    startPointer = instructionsPointer + jmpStartInstruction.sBx
                    endPointer = instructionsPointer + jmpEndInstruction.sBx + 1
                    tmpIrep = copy.deepcopy(irep)
                    tmpIrep.mrbCodes = tmpIrep.mrbCodes[startPointer : endPointer]
                    opcodeReader = OpCodeReader(tmpIrep, lvars, self, parentClass, CodeGen())
                    opcodeReader.parseOps()
                    argVal = opcodeReader.registers[lvars.lvarRecords[lvarIndex].symbolRegister].value

                    args.append(MethodArgumentEx(argReg, argSym, argVal))

                    instructionsPointer += 1
                    lvarIndex += 1
                if enterOpcode.rest:
                    argReg = lvars.lvarRecords[lvarIndex].symbolRegister
                    argSym = SymbolEx(0, lvars.lvarRecords[lvarIndex].symbol)
                    args.append(MethodArgumentEx(argReg, argSym, None, "*"))
                    lvarIndex += 1
                if enterOpcode.block:
                    argReg = lvars.lvarRecords[lvarIndex].symbolRegister
                    argSym = SymbolEx(0, lvars.lvarRecords[lvarIndex].symbol)
                    args.append(MethodArgumentEx(argReg, argSym, None, "&"))
                    lvarIndex += 1
            else:
                # for loop
                methodStartPointer = 1
                if irep.mrbCodes[1].opcode != AllOpCodes.OP_AREF:
                    raise Exception("Invalid for loop args")
                argI = 0
                while irep.mrbCodes[argI*2 + 1].opcode == AllOpCodes.OP_AREF:
                    setUpVar = cast(MrbCodeABC, irep.mrbCodes[argI*2 + 2])
                    upVarReg, _ = self.findUpVar(setUpVar.B, True)
                    argReg = upVarReg.i
                    argSym = cast(SymbolEx, upVarReg.value)
                    args.append(MethodArgumentEx(argReg, argSym))

                    argI += 1
                    methodStartPointer += 2

        # body
        irep.mrbCodes = irep.mrbCodes[methodStartPointer:]
        codeGen = CodeGen()
        opcodeReader = OpCodeReader(irep, lvars, self, parentClass, codeGen)
        opcodeReader.parseOps()
        body = codeGen.getExpressions()

        return args, body
