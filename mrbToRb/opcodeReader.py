from __future__ import annotations

import copy
from typing import cast, Tuple, Type

from mrbParser import RiteLvarRecord, RiteIrepSection
from mrbToRb.codeGenerator import CodeGen
from mrbToRb.opCodeFeed import OpCodeFeed
from mrbToRb.parsingConext import ParsingContext, ParsingState
from mrbToRb.register import Register
from mrbToRb.rbExpressions import *
from opcodes import *
from utils import ENCODING


class OpCodeReader:
    registers: List[Register]
    currentClass: SymbolEx
    parent: OpCodeReader
    context: ParsingContext
    opcodes: OpCodeFeed
    pool: List[str]
    symbols: List[SymbolEx]
    irep: RiteIrepSection
    lvars: RiteLvarRecord
    childIreps: List[RiteIrepSection]
    childLvars: List[RiteLvarRecord]
    localVarsMap: Dict[int, SymbolEx]
    codeGen: CodeGen

    def __init__(self, irep: RiteIrepSection, lvars: RiteLvarRecord, parent: OpCodeReader | None, curClass: SymbolEx,
                 codeGen: CodeGen, context: ParsingContext):
        self.parent = parent
        self.pool = list(map(lambda b: b.decode(ENCODING, "ignore"), irep.pools))
        self.symbols = list(map(lambda s: SymbolEx(0, s), irep.symbols))
        self.localVarsMap = {}
        for lvar in lvars.lvarRecords:
            self.localVarsMap[lvar.symbolRegister] = SymbolEx(lvar.symbolRegister, lvar.symbol)
        self.registers = []
        for i in range(irep.numRegisterVariables + 1):
            self.registers.append(Register(i, self.localVarsMap.get(i, None)))
        self.currentClass = curClass
        self.opcodes = OpCodeFeed(irep.mrbCodes)
        self.irep = irep
        self.lvars = lvars
        self.childIreps = irep.childIreps
        self.childLvars = lvars.childLvars
        self.codeGen = codeGen
        self.context = context

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
            pass
        elif opcode.opcode == AllOpCodes.OP_MOVE:
            val = self.registers[opcode.B].valueOrSymbol
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
            exp = MConstSymbolEx(opcode.A, self.registers[opcode.A].value, self.symbols[opcode.Bx])
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_SETMCNST:
            mConstExp = MConstSymbolEx(opcode.A, self.registers[opcode.A + 1].value, self.symbols[opcode.Bx])
            exp = AssignmentEx(opcode.A + 1, mConstExp, self.registers[opcode.A].value)
            self.codeGen.pushExp(exp)
        elif opcode.opcode == AllOpCodes.OP_GETUPVAR:
            upVar, _ = self.findUpVar(opcode.B)
            self.registers[opcode.A].moveIn(upVar)
            pushExpToCodeGen(opcode.A, upVar.value)
        elif opcode.opcode == AllOpCodes.OP_SETUPVAR:
            upVarReg, context = self.findUpVar(opcode.B)
            upVarReg.moveIn(self.registers[opcode.A])
            pushExpToCodeGen(opcode.B, upVarReg.value, context.localVarsMap)

        elif opcode.opcode == AllOpCodes.OP_JMP:
            if self.context.isWhenCond():
                if self.opcodes.pos + 1 == len(self.opcodes):
                    pass
                else:
                    raise Exception("Unexpected jump in when condition")
            elif opcode.sBx < 0:
                self.codeGen.pushExp(StatementEx(0, "next"))
            elif self.opcodes.pos + opcode.sBx >= len(self.opcodes):
                if not self.context.isWhileLoop():
                    raise Exception("Jump out of range")
                self.codeGen.pushExp(StatementEx(0, "break"))
            else:
                self.parseWhile()
        elif opcode.opcode == AllOpCodes.OP_JMPIF:
            self.parseJMPIF()
        elif opcode.opcode == AllOpCodes.OP_JMPNOT:
            self.parseJMPNOT()
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
        elif opcode.opcode == AllOpCodes.OP_SENDB:
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
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_KARG:
        #     unhandledOpCode()
        # elif opcode.opcode == AllOpCodes.OP_KDICT:
        #     unhandledOpCode()

        elif opcode.opcode == AllOpCodes.OP_RETURN:
            retStatement: StatementEx
            if opcode.B == 0 and self.context.isForLoop() and self.context.hasMoreOpcodesOutside:
                retStatement = StatementEx(0, "next")
                self.codeGen.pushExp(retStatement)
            elif opcode.B == 0 or opcode.B == 2:
                if opcode.A in self.localVarsMap or self.opcodes.pos + 1 < len(self.opcodes) or self.context.hasMoreOpcodesOutside:
                    retValue = self.registers[opcode.A].value
                    if isinstance(retValue, NilEx):
                        retValue.hasUsages = True
                        retValue = None
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
            innerContext = self.context.pushAndNew(ParsingState.NORMAL)
            opcodeReader = OpCodeReader(self.childIreps[opcode.Bx], self.childLvars[opcode.Bx], self, target, codeGen, innerContext)
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
        innerState = ParsingState.METHOD

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
                    opcodeReader = OpCodeReader(tmpIrep, lvars, self, parentClass, CodeGen(), self.context.pushAndNew(ParsingState.METHOD))
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
                innerState = ParsingState.FOR_LOOP
                methodStartPointer = 1
                argI = 0
                if irep.mrbCodes[1].opcode == AllOpCodes.OP_AREF:
                    while irep.mrbCodes[argI*2 + 1].opcode == AllOpCodes.OP_AREF:
                        setUpVar = cast(MrbCodeABC, irep.mrbCodes[argI*2 + 2])
                        upVarReg, _ = self.findUpVar(setUpVar.B, True)
                        argReg = upVarReg.i
                        argSym = cast(SymbolEx, upVarReg.value)
                        args.append(MethodArgumentEx(argReg, argSym))

                        argI += 1
                        methodStartPointer += 2
                elif irep.mrbCodes[1].opcode == AllOpCodes.OP_SETUPVAR:
                    while irep.mrbCodes[argI + 1].opcode == AllOpCodes.OP_SETUPVAR:
                        setUpVar = cast(MrbCodeABC, irep.mrbCodes[argI + 1])
                        upVarReg, _ = self.findUpVar(setUpVar.B, True)
                        argReg = upVarReg.i
                        argSym = cast(SymbolEx, upVarReg.value)
                        args.append(MethodArgumentEx(argReg, argSym))

                        argI += 1
                        methodStartPointer += 1
                else:
                    raise Exception("Invalid for loop args")

        # body
        irep.mrbCodes = irep.mrbCodes[methodStartPointer:]
        codeGen = CodeGen()
        opcodeReader = OpCodeReader(irep, lvars, self, parentClass, codeGen, self.context.pushAndNew(innerState))
        opcodeReader.parseOps()
        body = codeGen.getExpressions()

        return args, body

    def parseSection(self, start: int, end: int, newContext: ParsingContext|None = None, copyRegister = True) -> CodeGen:
        tmpIrep = copy.copy(self.irep)
        tmpIrep.mrbCodes = tmpIrep.mrbCodes[start : end]
        codeGen = CodeGen()
        opcodeReader = OpCodeReader(tmpIrep, self.lvars, self.parent, self.currentClass, codeGen, newContext or self.context)
        if copyRegister:
            for i in range(len(self.registers)):
                opcodeReader.registers[i] = copy.copy(self.registers[i])
        opcodeReader.parseOps()
        return codeGen

    def parseAndOrOr(self, jmpCode: MrbCodeAsBx, expClass: Type[AndEx|OrEx]):
        left = self.registers[jmpCode.A].valueOrSymbol
        rightStart = self.opcodes.pos + 1
        rightEnd =  self.opcodes.pos + jmpCode.sBx
        innerContext = self.context.pushAndNew(ParsingState.IF, True)
        body = self.parseSection(rightStart, rightEnd, innerContext, False).getExpressions()
        if len(body) > 1 and expClass == AndEx:
            # is actually and If block
            self.pushIf(left, BlockEx(0, body))
            self.opcodes.seek(rightEnd - 1)
            return
        if len(body) != 1:
            raise Exception("Invalid OR/AND body length")

        reg = jmpCode.A
        right = body[0]
        exp = expClass(reg, left, right)

        self.registers[exp.register].load(exp)
        if reg in self.localVarsMap:
            self.codeGen.pushExp(AssignmentEx(reg, self.localVarsMap[reg], exp))
        else:
            self.codeGen.pushExp(exp)

        self.opcodes.seek(rightEnd - 1)

    def parseJMPIF(self):
        jmpCode = cast(MrbCodeAsBx, self.opcodes.cur())
        orEnd = self.opcodes.pos + jmpCode.sBx
        caseEndCode = self.opcodes[orEnd - 1]
        if caseEndCode.opcode == AllOpCodes.OP_JMP and caseEndCode.sBx > 0:
            if self.context.isWhenCond() and orEnd == len(self.opcodes):
                self.reportBackWhenCond(jmpCode)
            else:
                self.parseCase(jmpCode)
        else:
            self.parseAndOrOr(jmpCode, OrEx)

    def parseJMPNOT(self):
        jmpCode = cast(MrbCodeAsBx, self.opcodes.cur())
        andEnd = self.opcodes.pos + jmpCode.sBx
        ifEndCode = self.opcodes[andEnd - 1]
        if ifEndCode.opcode == AllOpCodes.OP_JMP and ifEndCode.sBx > 0 and andEnd + ifEndCode.sBx - 1 <= len(self.opcodes):
            self.parseIfElse(jmpCode, andEnd + ifEndCode.sBx - 1)
        else:
            self.parseAndOrOr(jmpCode, AndEx)

    def parseIfElse(self, jmpCode: MrbCodeAsBx, elseEnd: int):
        ifStart = self.opcodes.pos + 1
        ifEnd = self.opcodes.pos + jmpCode.sBx - 1
        elseStart = self.opcodes.pos + jmpCode.sBx

        condition = self.registers[jmpCode.A].valueOrSymbol
        innerContext = self.context.pushAndNew(ParsingState.IF, True)
        ifBody = self.parseSection(ifStart, ifEnd, innerContext).getExpressions()
        elseBody = self.parseSection(elseStart, elseEnd, innerContext).getExpressions()

        self.pushIf(condition, BlockEx(0, ifBody), BlockEx(0, elseBody))
        self.opcodes.seek(elseEnd - 1)

    def pushIf(self, condition: Expression, ifBlock: BlockEx, elseBlock: BlockEx|None = None):
        exp = IfEx(0, condition, ifBlock, elseBlock)
        self.codeGen.pushExp(exp)

    def parseWhile(self):
        jmpToCondCode = cast(MrbCodeAsBx, self.opcodes.cur())
        condStart = self.opcodes.pos + jmpToCondCode.sBx
        condEnd = condStart + 1
        condEndJmp = cast(MrbCodeAsBx, self.opcodes[condEnd])
        while not (condEndJmp.opcode == AllOpCodes.OP_JMPIF and condEndJmp.sBx < 0):
            condEnd += 1
            condEndJmp = self.opcodes[condEnd]

        conditionBody = self.parseSection(condStart, condEnd).getExpressions()
        if len(conditionBody) != 1:
            raise Exception("Invalid while condition body length")
        condition = conditionBody[0]

        bodyStart = self.opcodes.pos + 1
        bodyEnd = condStart
        innerContext = self.context.pushAndNew(ParsingState.WHILE_LOOP, True)
        body = self.parseSection(bodyStart, bodyEnd, innerContext).getExpressions()
        exp = WhileEx(0, condition, BlockEx(0, body))

        self.codeGen.pushExp(exp)
        self.opcodes.seek(condEnd)

    def reportBackWhenCond(self, jmpCode: MrbCodeAsBx):
        self.context.callback(self.registers[jmpCode.A].valueOrSymbol)

    def parseCaseWhenCond(self, start: int, end: int) -> List[Expression]:
        if start >= end or start + 1 == end and self.opcodes[start].opcode == AllOpCodes.OP_JMP:
            return []
        conditions: List[Expression] = []
        subContext = self.context.pushAndNew(ParsingState.WHEN_COND)
        subContext.callback = lambda exp: conditions.append(exp)
        self.parseSection(start, end, subContext)
        return conditions

    def parseCaseElse(self, start: int, end: int) -> List[Expression]:
        return self.parseSection(start, end).getExpressions()

    def parseCase(self, jmpCode: MrbCodeAsBx):
        whenBlocks: List[CaseWhenEx] = []
        elseBlock: BlockEx|None = None

        condStart = self.opcodes.pos + 1
        condEnd = self.opcodes.pos + jmpCode.sBx
        curWhenConditions: List[Expression] = [self.registers[jmpCode.A].valueOrSymbol]
        caseEnd = -1

        while condStart < condEnd:
            curWhenConditions.extend(self.parseCaseWhenCond(condStart, condEnd))
            if len(curWhenConditions) == 0:
                # ending else
                elseExp = self.parseCaseElse(condStart, condEnd - 1)
                elseBlock = BlockEx(0, elseExp)
                caseEnd = condEnd
                break

            elseJMP = self.opcodes[condEnd - 1]
            whenBodyStart = condEnd
            whenBodyEnd = condEnd + elseJMP.sBx - 2
            whenBody = self.parseSection(whenBodyStart, whenBodyEnd).getExpressions()
            whenBlocks.append(CaseWhenEx(curWhenConditions, BlockEx(0, whenBody)))

            curWhenConditions.clear()
            lastJMP = self.opcodes[whenBodyEnd]
            caseEnd = whenBodyEnd + lastJMP.sBx
            condStart = whenBodyEnd + 1
            condEnd = condStart + 1
            while self.opcodes[condEnd].opcode != AllOpCodes.OP_JMP and condEnd < caseEnd:
                condEnd += 1
            condEnd += 1
            if condEnd > caseEnd:
                # last when
                break

        # check if all when conditions are like EXP(variable) === EXP(same)
        caseVar: Expression|None = None
        if len(whenBlocks) > 1:
            firstCaseExp = whenBlocks[0].conditions[0]
            if isinstance(firstCaseExp, MethodCallEx) and firstCaseExp.symbol.value == "===":
                caseVar = firstCaseExp.args[0]
                isValid = True
                for whenCond in whenBlocks:
                    if not isValid:
                        break
                    for cond in whenCond.conditions:
                        if not isinstance(cond, MethodCallEx) or cond.symbol.value != "===":
                            isValid = False
                            break
                        if cond.args[0] != caseVar:
                            isValid = False
                            break

                if isValid:
                    for whenCond in whenBlocks:
                        cond: MethodCallEx
                        for i, cond in enumerate(whenCond.conditions):
                            whenCond.conditions[i] = cond.srcObj


        exp = CaseEx(0, caseVar, whenBlocks, elseBlock)    # TODO case as assignment
        self.codeGen.pushExp(exp)
        self.opcodes.seek(caseEnd - 1)



