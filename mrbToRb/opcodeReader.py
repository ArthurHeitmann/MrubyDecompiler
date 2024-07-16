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
    parent: OpCodeReader|None
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
                 codeGen: CodeGen, context: ParsingContext, fullIrepCodes: List[MrbCode]|None = None, originalIrepOffset: int = 0):
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
        self.opcodes = OpCodeFeed(irep.mrbCodes, fullIrepCodes, originalIrepOffset)
        self.irep = irep
        self.lvars = lvars
        self.childIreps = irep.childIreps
        self.childLvars = lvars.childLvars
        self.codeGen = codeGen
        self.context = context

    def step(self):
        opcode = self.opcodes.cur()
        # self.codeGen.pushExp(LineCommentEx(0, str(opcode)))

        def pushExpToCodeGen(regI: int, expression: Expression, localVarsMap: Dict|None = None):
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
            val = SymbolEx(upVar.lvarSymbol.register, upVar.lvarSymbol.value)
            self.registers[opcode.A].load(val)
            pushExpToCodeGen(opcode.A, val)
        elif opcode.opcode == AllOpCodes.OP_SETUPVAR:
            upVarReg, context = self.findUpVar(opcode.B)
            upVarReg.moveIn(self.registers[opcode.A])
            pushExpToCodeGen(opcode.B, upVarReg.value, context.localVarsMap)

        elif opcode.opcode == AllOpCodes.OP_JMP:
            if opcode.sBx < 0:
                self.codeGen.pushExp(StatementEx(0, "next"))
            elif self.opcodes.pos + opcode.sBx >= len(self.opcodes):
                if self.context.isWhileLoop():
                    self.codeGen.pushExp(StatementEx(0, "break"))
                else:
                    jumpedOpcodes = self.opcodes.getJumpedOpcodes(opcode.sBx)
                    if len(jumpedOpcodes) == 0 or len(jumpedOpcodes) <= 2 and all(not code.stats.isReachable for code in jumpedOpcodes):
                        self.opcodes.jump(opcode.sBx)
                    else:
                        self.codeGen.pushExp(RaiseEx(0, StringEx(0, f"ERROR: Unexpected JMP {'+' if opcode.sBx > 0 else ''}{opcode.sBx}! (continuing anyways)")))
                        for jmpOp in jumpedOpcodes:
                            self.codeGen.pushExp(LineCommentEx(0, str(jmpOp)))
                        print(f"ERROR: Unexpected JMP {'+' if opcode.sBx > 0 else ''}{opcode.sBx} ({len(jumpedOpcodes)})! (continuing anyways)")
            else:
                self.parseWhileOrUntil()
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
            methodSymbol = self.symbols[opcode.B]
            if isinstance(srcObj, SelfEx) and isinstance(self.currentClass, MainClass):
                srcObj.hasUsages = True
                srcObj = None
            elif isinstance(srcObj, BlkPushEx) and srcObj.register == opcode.A:
                srcObj = None
                methodSymbol = SymbolEx(opcode.A, "yield")
            exp = MethodCallEx(opcode.A, srcObj, methodSymbol, args)
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
        elif opcode.opcode == AllOpCodes.OP_SUPER:
            if opcode.C != 0x7f:
                args = [reg.value for reg in self.registers[opcode.A + 1: opcode.A + 1 + opcode.C]]
            else:
                args = []
            exp = MethodCallEx(opcode.A, None, SymbolEx(0, "super"), args)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
        elif opcode.opcode == AllOpCodes.OP_ARGARY:
            exp = RaiseEx(0, StringEx(0, "ERROR: OP_ARGARY should not be visible!"))
            self.registers[opcode.A].load(exp)
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
        elif opcode.opcode == AllOpCodes.OP_BLKPUSH:
            exp = BlkPushEx(opcode.A)
            self.registers[opcode.A].load(exp)

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
        elif opcode.opcode == AllOpCodes.OP_AREF:
            exp = ArrayRefEx(opcode.A, self.registers[opcode.B].value, opcode.C)
            self.registers[opcode.A].load(exp)
            pushExpToCodeGen(opcode.A, exp)
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
        if _checkSelf and register in self.localVarsMap:
            return self.registers[register], self
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
        if start > end:
            raise Exception("Invalid section")
        tmpIrep = copy.copy(self.irep)
        tmpIrep.mrbCodes = tmpIrep.mrbCodes[start : end]
        codeGen = CodeGen()
        opcodeReader = OpCodeReader(tmpIrep, self.lvars, self.parent, self.currentClass, codeGen, newContext or self.context, self.opcodes.fullOpcodes, self.opcodes.offset + start)
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
        caseEndCode = self.opcodes[orEnd - 1] if orEnd < len(self.opcodes) else None
        if self.context.isWhenCond() and self.isOpcodeWhenConditionLite(jmpCode, self.context.data["condRegister"]):
            self.reportBackWhenCond(jmpCode)
        elif caseEndCode and caseEndCode.opcode == AllOpCodes.OP_JMP and caseEndCode.sBx > 0 and jmpCode.sBx > 0:
            self.parseCase(jmpCode)
        else:
            self.parseAndOrOr(jmpCode, OrEx)

    def parseJMPNOT(self):
        jmpCode = cast(MrbCodeAsBx, self.opcodes.cur())
        andEnd = self.opcodes.pos + jmpCode.sBx
        ifEndCode = self.opcodes[andEnd - 1]
        if ifEndCode.opcode == AllOpCodes.OP_JMP and ifEndCode.sBx > 0 and ((andEnd + ifEndCode.sBx - 1) <= len(self.opcodes)):
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

    def parseWhileOrUntil(self):
        jmpToCondCode = cast(MrbCodeAsBx, self.opcodes.cur())
        condStart = self.opcodes.pos + jmpToCondCode.sBx
        condEnd = condStart + 1
        condEndJmp = cast(MrbCodeAsBx, self.opcodes[condEnd])
        while not (condEndJmp.opcode in { AllOpCodes.OP_JMPIF, AllOpCodes.OP_JMPNOT } and condEndJmp.sBx < 0):
            condEnd += 1
            if condEnd >= len(self.opcodes):
                self.JMPFallback(jmpToCondCode)
                return
            condEndJmp = self.opcodes[condEnd]
        loopType = "while" if condEndJmp.opcode == AllOpCodes.OP_JMPIF else "until"

        conditionBody = self.parseSection(condStart, condEnd).getExpressions()
        if len(conditionBody) != 1:
            raise Exception("Invalid while condition body length")
        condition = conditionBody[0]

        bodyStart = self.opcodes.pos + 1
        bodyEnd = condStart
        innerContext = self.context.pushAndNew(ParsingState.WHILE_LOOP, True)
        body = self.parseSection(bodyStart, bodyEnd, innerContext).getExpressions()
        exp = WhileOrUntilEx(0, loopType, condition, BlockEx(0, body))

        self.codeGen.pushExp(exp)
        self.opcodes.seek(condEnd)

    def reportBackWhenCond(self, jmpCode: MrbCodeAsBx):
        self.context.callback(self.registers[jmpCode.A].valueOrSymbol)

    def parseCaseWhenCond(self, start: int, end: int, condRegister: int, caseEnd: int) -> List[Expression]:
        if start >= end or start + 1 == end and self.opcodes[start].opcode == AllOpCodes.OP_JMP:
            return []
        conditions: List[Expression] = []
        subContext = self.context.pushAndNew(ParsingState.WHEN_COND)
        subContext.data["condRegister"] = condRegister
        subContext.data["caseEnd"] = caseEnd
        subContext.callback = lambda exp: conditions.append(exp)
        self.parseSection(start, end, subContext)
        return conditions

    def parseCase(self, jmpCode: MrbCodeAsBx):
        whenBlocks: List[CaseWhenEx] = []
        elseBlock: BlockEx|None = None
        condRegister = jmpCode.A

        condStart = self.opcodes.pos
        condEnd = self.opcodes.pos + jmpCode.sBx
        curWhenConditions: List[Expression] = []

        condEndJmpPos = condEnd - 1
        elseJMP = self.opcodes[condEndJmpPos]
        caseEndJmpPos = condEndJmpPos + elseJMP.sBx - 1
        caseEndJMP = self.opcodes[caseEndJmpPos]
        caseEnd = caseEndJmpPos + caseEndJMP.sBx

        while condStart + 1 < caseEnd:
            # blockType = "COND"
            # elseData: List[Expression]|None = None
            # def blockCallback(blType: str, blData: List[Expression]):
            #     nonlocal blockType, elseData
            #     blockType = blType
            #     if blType == "COND":
            #         curWhenConditions.append(blData)
            #     else:
            #         elseData = blData
            # subContext = self.context.pushAndNew(ParsingState.WHEN_COND_OR_ELSE)
            # subContext.callback = blockCallback
            # self.parseSection(condStart, condEnd, subContext)
            # if blockType == "ELSE":
            #     elseBlock = BlockEx(0, elseData)
            #     break
            # elif blockType == "COND" and len(curWhenConditions) == 0:
            #     break
            foundConditions = 0
            isLastWhenBlock: bool|None = None
            pos = condStart
            while pos < caseEnd and self.opcodes[pos].opcode != AllOpCodes.OP_JMP:
                isWhenCondition, _isLastWhenBlock = self.isOpcodeWhenConditionFull(self.opcodes[pos], pos, condRegister, caseEnd)
                if isWhenCondition:
                    foundConditions += 1
                    isLastWhenBlock = _isLastWhenBlock
                pos += 1
            if foundConditions == 0:
                elseBody = self.parseSection(condStart, caseEnd - 1).getExpressions()
                elseBlock = BlockEx(0, elseBody)
                break

            condEnd = pos
            curWhenConditions.extend(self.parseCaseWhenCond(condStart, condEnd, condRegister, caseEnd - condStart))

            elseJMP = self.opcodes[condEnd]
            whenBodyStart = condEnd + 1
            whenBodyEnd = condEnd + elseJMP.sBx - 1
            whenBody = self.parseSection(whenBodyStart, whenBodyEnd).getExpressions()
            whenBlocks.append(CaseWhenEx(curWhenConditions, BlockEx(0, whenBody)))

            curWhenConditions.clear()
            condStart = whenBodyEnd + 1
            if isLastWhenBlock:
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

    def JMPFallback(self, jmpCode: MrbCodeAsBx):
        if jmpCode.sBx >= 0:
            print(f"Warning: JMP outside of known control flow: {jmpCode}")
            self.codeGen.pushExp(LineCommentEx(0, jmpCode))
            for mrbCode in self.opcodes[self.opcodes.pos : self.opcodes.pos + jmpCode.sBx]:
                self.codeGen.pushExp(LineCommentEx(0, mrbCode))
            self.opcodes.seek(self.opcodes.pos + jmpCode.sBx)
        else:
            raise Exception("Negative unhandled JMP")

    def isOpcodeWhenConditionFull(self, jmpIf: MrbCodeAsBx, curPos: int, condRegister: int, caseEnd: int) -> Tuple[bool, bool]:
        """returns: isWhenCondition, isLastWhenBlock"""
        # last, jmp to condEnd - 1
        # non-last when, else jmp to condEnd
        # valid condition if:
        # --> opcodes[pos] == JMPIF
        # --> JMPIF.sBx > 0
        # --> JMPIF.A == condRegister
        # --> JMPIF.target - 1 == JMP (elseJMP)
        # --> elseJMP.sBx > 0 && elseJMP.target < caseEnd
        # --> elseJMP.target - 1 == JMP (whenEndJMP)
        # --> whenEndJMP.target == caseEnd || whenEndJMP.target == caseEnd - 1
        nope = False, False
        if jmpIf.opcode != AllOpCodes.OP_JMPIF:
            return nope
        if jmpIf.sBx < 0:
            return nope
        if jmpIf.A != condRegister:
            return nope
        elseJmpPos = curPos + jmpIf.sBx - 1
        if elseJmpPos > caseEnd:
            return nope
        elseJmp = cast(MrbCodeAsBx, self.opcodes[elseJmpPos])
        if elseJmp.opcode != AllOpCodes.OP_JMP:
            return nope
        whenEndJmpPos = elseJmpPos + elseJmp.sBx - 1
        if elseJmp.sBx < 0 or whenEndJmpPos > caseEnd:
            return nope
        whenEndJmp = cast(MrbCodeAsBx, self.opcodes[whenEndJmpPos])
        if whenEndJmp.opcode != AllOpCodes.OP_JMP or whenEndJmp.sBx < 0:
            return nope
        whenEndJmpTarget = whenEndJmpPos + whenEndJmp.sBx
        if whenEndJmpTarget == caseEnd:
            return True, False
        if whenEndJmpTarget == caseEnd - 1:
            return True, True
        return nope

    def isOpcodeWhenConditionLite(self, jmpIf: MrbCodeAsBx, condRegister: int) -> bool:
        """returns: isWhenCondition, isLastWhenBlock"""
        # --> whenEndJMP.target == caseEnd || whenEndJMP.target == caseEnd - 1
        if jmpIf.opcode != AllOpCodes.OP_JMPIF:
            return False
        if jmpIf.sBx < 0:
            return False
        if jmpIf.A != condRegister:
            return False
        return True

