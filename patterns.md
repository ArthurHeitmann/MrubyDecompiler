variable assignments

function calls (with src object, with args, with block)

if
elsif
else

for

case

(do)
while

class
    method
    self.method

blocks

function declaration & call
```ruby
def function_name(arg1, arg2)
    # code
end

function_name(1, 3)
```

for
```ruby
# "OP_LOADI: A: 0x4,	 B: 0xff,	 C: 0x7f,	 Bx: 0x7fff,	 sBx: 0,	 Ax: 0x47fff,	 Bz: 1fff,	 Cz: 3"
# "OP_LOADI: A: 0x5,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x58004,	 Bz: 2001,	 Cz: 0"
# "OP_RANGE: A: 0x4,	 B: 0x4,	 C: 0x0,	 Bx: 0x200,	 sBx: -32255,	 Ax: 0x40200,	 Bz: 80,	 Cz: 0"
# "OP_LAMBDA: A: 0x5,	 B: 0x0,	 C: 0x2,	 Bx: 0x2,	 sBx: -32765,	 Ax: 0x50002,	 Bz: 0,	 Cz: 2"
#  R(A) = lambda(irep[Bz], Cz?)
# "OP_SENDB: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0"
#  R(A) = Range       R(B) = Sym(each)    R(A+C+1) = Lambda
for i in 0..5:
    # "OP_ENTER: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0" 
    # "OP_SETUPVAR: A: 0x1,	 B: 0x2,	 C: 0x0,	 Bx: 0x100,	 sBx: -32511,	 Ax: 0x10100,	 Bz: 40,	 Cz: 0"
    #                        R(B) = Sym(i)
    ...
    # "OP_RETURN: A: 0x2,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x20000,	 Bz: 0,	 Cz: 0"
end
```

while

START ON: JMP
BODY: JMP + 1 : JMP.sBx
COND: JMP.sBx : (... code == OP_JMPIF && code.sBx < 0)

```ruby
# "OP_LOADI: A: 0x1,	 B: 0xff,	 C: 0x7f,	 Bx: 0x7fff,	 sBx: 0,	 Ax: 0x17fff,	 Bz: 1fff,	 Cz: 3"
index = 0
# Basically a do while with a jump to the end as the first instruction

# "OP_JMP: A: 0x0,	 B: 0x100,	 C: 0x6,	 Bx: 0x8006,	 sBx: 7,	 Ax: 0x8006,	 Bz: 2001,	 Cz: 2" #     >---|
# [AT END OF LOOP]                                                                                                    |
# "OP_MOVE: A: 0x2,	 B: 0x1,	 C: 0x0,	 Bx: 0x80,	 sBx: -32639,	 Ax: 0x20080,	 Bz: 20,	 Cz: 0"       <---|
# "OP_LOADI: A: 0x3,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x38004,	 Bz: 2001,	 Cz: 0"
# "OP_LT: A: 0x2,	 B: 0x2,	 C: 0x1,	 Bx: 0x101,	 sBx: -32510,	 Ax: 0x20101,	 Bz: 40,	 Cz: 1"
# "OP_JMPIF: A: 0x2,	 B: 0xff,	 C: 0x76,	 Bx: 0x7ff6,	 sBx: -9,	 Ax: 0x27ff6,	 Bz: 1ffd,	 Cz: 2"   >---|
while index < 5             #                                                                                         |
    # "OP_LOADSELF: A: 0x2,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x20000,	 Bz: 0,	 Cz: 0"   <---|
    # "OP_MOVE: A: 0x3,	 B: 0x1,	 C: 0x0,	 Bx: 0x80,	 sBx: -32639,	 Ax: 0x30080,	 Bz: 20,	 Cz: 0"
    # "OP_SEND: A: 0x2,	 B: 0x0,	 C: 0x1,	 Bx: 0x1,	 sBx: -32766,	 Ax: 0x20001,	 Bz: 0,	 Cz: 1"
	puts index
    # "OP_MOVE: A: 0x2,	 B: 0x1,	 C: 0x0,	 Bx: 0x80,	 sBx: -32639,	 Ax: 0x20080,	 Bz: 20,	 Cz: 0"
    # "OP_ADDI: A: 0x2,	 B: 0x1,	 C: 0x1,	 Bx: 0x81,	 sBx: -32638,	 Ax: 0x20081,	 Bz: 20,	 Cz: 1"
    # "OP_MOVE: A: 0x1,	 B: 0x2,	 C: 0x0,	 Bx: 0x100,	 sBx: -32511,	 Ax: 0x10100,	 Bz: 40,	 Cz: 0"
	index += 1
end
# "OP_LOADNIL: A: 0x2,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x20000,	 Bz: 0,	 Cz: 0"
```

if

START ON: AndEx && AndEx.hasUsages == false && AndEx.right.mrbCodes[-1] != OP_JMP
COND AndEx.left
BODY AndEx.right

if-else

START ON: AndEx && AndEx.right.mrbCodes[-1] == OP_JMP
COND: AndEx.left
IF BODY: AndEx.right[:-1]
ELSE BODY: AndEx.left[-1].sBx : AndEx.right[-1].sBx

```ruby
# "OP_LOADI: A: 0x1,	 B: 0x100,	 C: 0x3b,	 Bx: 0x803b,	 sBx: 60,	 Ax: 0x1803b,	 Bz: 200e,	 Cz: 3"
# "OP_LOADI: A: 0x2,	 B: 0x100,	 C: 0x31,	 Bx: 0x8031,	 sBx: 50,	 Ax: 0x28031,	 Bz: 200c,	 Cz: 1"
# "OP_GT: A: 0x1,	 B: 0x0,	 C: 0x1,	 Bx: 0x1,	 sBx: -32766,	 Ax: 0x10001,	 Bz: 0,	 Cz: 1"
# "OP_JMPIF: A: 0x1,	 B: 0x100,	 C: 0x3,	 Bx: 0x8003,	 sBx: 4,	 Ax: 0x18003,	 Bz: 2000,	 Cz: 3"    >---------|
# "OP_LOADI: A: 0x1,	 B: 0x100,	 C: 0x3b,	 Bx: 0x803b,	 sBx: 60,	 Ax: 0x1803b,	 Bz: 200e,	 Cz: 3"              |
# "OP_LOADI: A: 0x2,	 B: 0x100,	 C: 0x63,	 Bx: 0x8063,	 sBx: 100,	 Ax: 0x28063,	 Bz: 2018,	 Cz: 3"              |
# "OP_LT: A: 0x1,	 B: 0x1,	 C: 0x1,	 Bx: 0x81,	 sBx: -32638,	 Ax: 0x10081,	 Bz: 20,	 Cz: 1"                  |
# "OP_JMPNOT: A: 0x1,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x18004,	 Bz: 2001,	 Cz: 0"     >--|     |
if 60 > 50 || 60 < 100  #                                                                                              |     |
    # "OP_LOADSELF: A: 0x1,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x10000,	 Bz: 0,	 Cz: 0"        |  <--|
    # "OP_STRING: A: 0x2,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x20000,	 Bz: 0,	 Cz: 0"        |
    # "OP_SEND: A: 0x1,	 B: 0x2,	 C: 0x1,	 Bx: 0x101,	 sBx: -32510,	 Ax: 0x10101,	 Bz: 40,	 Cz: 1"        |
	puts("biiig")    #                                                                                                 |
    # "OP_JMP: A: 0x0,	 B: 0x100,	 C: 0x9,	 Bx: 0x8009,	 sBx: 10,	 Ax: 0x8009,	 Bz: 2002,	 Cz: 1"    >---|--------|
# "OP_LOADI: A: 0x1,	 B: 0x100,	 C: 0x3b,	 Bx: 0x803b,	 sBx: 60,	 Ax: 0x1803b,	 Bz: 200e,	 Cz: 3"    <---|        |
# "OP_LOADI: A: 0x2,	 B: 0x100,	 C: 0x3b,	 Bx: 0x803b,	 sBx: 60,	 Ax: 0x2803b,	 Bz: 200e,	 Cz: 3"                 |
# "OP_SEND: A: 0x1,	 B: 0x3,	 C: 0x1,	 Bx: 0x181,	 sBx: -32382,	 Ax: 0x10181,	 Bz: 60,	 Cz: 1"                     |
# "OP_JMPNOT: A: 0x1,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x18004,	 Bz: 2001,	 Cz: 0"    >-------|    |
elsif 60 != 60           #                                                                                                 |    |
    # "OP_LOADSELF: A: 0x1,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x10000,	 Bz: 0,	 Cz: 0"            |    |
    # "OP_STRING: A: 0x2,	 B: 0x0,	 C: 0x1,	 Bx: 0x1,	 sBx: -32766,	 Ax: 0x20001,	 Bz: 0,	 Cz: 1"            |    |
    # "OP_SEND: A: 0x1,	 B: 0x2,	 C: 0x1,	 Bx: 0x101,	 sBx: -32510,	 Ax: 0x10101,	 Bz: 40,	 Cz: 1"            |    |
	puts("smol")    #                                                                                                      |    |
	# "OP_JMP: A: 0x0,	 B: 0x100,	 C: 0x1,	 Bx: 0x8001,	 sBx: 2,	 Ax: 0x8001,	 Bz: 2000,	 Cz: 1"    >--|    |    |
# "OP_LOADNIL: A: 0x1,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x10000,	 Bz: 0,	 Cz: 0"      <----|----|    |
end                       #                                                                                           |         |
# NEXT                                                                                                             <------------|
```
