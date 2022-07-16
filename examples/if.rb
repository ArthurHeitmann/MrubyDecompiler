v1 = someRand
v2 = someRand

x = []

# "OP_JMPNOT: A: 0x1,	 B: 0x100,	 C: 0x3,	 Bx: 0x8003,	 sBx: 4,	 Ax: 0x18003,	 Bz: 2000,	 Cz: 3"
if v1
    # "OP_LOADSELF: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0"
    # "OP_LOADI: A: 0x5,	 B: 0x100,	 C: 0x0,	 Bx: 0x8000,	 sBx: 1,	 Ax: 0x58000,	 Bz: 2000,	 Cz: 0"
    # "OP_SEND: A: 0x4,	 B: 0x1,	 C: 0x1,	 Bx: 0x81,	 sBx: -32638,	 Ax: 0x40081,	 Bz: 20,	 Cz: 1"
    puts 1
end
# ...

x = []

# "OP_JMPNOT: A: 0x1,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x18004,	 Bz: 2001,	 Cz: 0"
if v1
    # "OP_LOADSELF: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0"
    # "OP_LOADI: A: 0x5,	 B: 0x100,	 C: 0x1,	 Bx: 0x8001,	 sBx: 2,	 Ax: 0x58001,	 Bz: 2000,	 Cz: 1"
    # "OP_SEND: A: 0x4,	 B: 0x1,	 C: 0x1,	 Bx: 0x81,	 sBx: -32638,	 Ax: 0x40081,	 Bz: 20,	 Cz: 1"
    puts 2
    # "OP_JMP: A: 0x0,	 B: 0x100,	 C: 0x3,	 Bx: 0x8003,	 sBx: 4,	 Ax: 0x8003,	 Bz: 2000,	 Cz: 3"
else
    # "OP_LOADSELF: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0"
    # "OP_LOADI: A: 0x5,	 B: 0x100,	 C: 0x2,	 Bx: 0x8002,	 sBx: 3,	 Ax: 0x58002,	 Bz: 2000,	 Cz: 2"
    # "OP_SEND: A: 0x4,	 B: 0x1,	 C: 0x1,	 Bx: 0x81,	 sBx: -32638,	 Ax: 0x40081,	 Bz: 20,	 Cz: 1"
    puts 3
end
# ...

x = []


# "OP_JMPNOT: A: 0x1,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x18004,	 Bz: 2001,	 Cz: 0"
if v1
    # "OP_LOADSELF: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0"
    # "OP_LOADI: A: 0x5,	 B: 0x100,	 C: 0x3,	 Bx: 0x8003,	 sBx: 4,	 Ax: 0x58003,	 Bz: 2000,	 Cz: 3"
    # "OP_SEND: A: 0x4,	 B: 0x1,	 C: 0x1,	 Bx: 0x81,	 sBx: -32638,	 Ax: 0x40081,	 Bz: 20,	 Cz: 1"
    puts 4
    # "OP_JMP: A: 0x0,	 B: 0x100,	 C: 0x8,	 Bx: 0x8008,	 sBx: 9,	 Ax: 0x8008,	 Bz: 2002,	 Cz: 0"
# "OP_JMPNOT: A: 0x2,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x28004,	 Bz: 2001,	 Cz: 0"
elsif v2
    # "OP_LOADSELF: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0"
    # "OP_LOADI: A: 0x5,	 B: 0x100,	 C: 0x4,	 Bx: 0x8004,	 sBx: 5,	 Ax: 0x58004,	 Bz: 2001,	 Cz: 0"
    puts 5
    # "OP_JMP: A: 0x0,	 B: 0x100,	 C: 0x3,	 Bx: 0x8003,	 sBx: 4,	 Ax: 0x8003,	 Bz: 2000,	 Cz: 3"
else
    # "OP_LOADSELF: A: 0x4,	 B: 0x0,	 C: 0x0,	 Bx: 0x0,	 sBx: -32767,	 Ax: 0x40000,	 Bz: 0,	 Cz: 0"
    # "OP_LOADI: A: 0x5,	 B: 0x100,	 C: 0x5,	 Bx: 0x8005,	 sBx: 6,	 Ax: 0x58005,	 Bz: 2001,	 Cz: 1"
    # "OP_SEND: A: 0x4,	 B: 0x1,	 C: 0x1,	 Bx: 0x81,	 sBx: -32638,	 Ax: 0x40081,	 Bz: 20,	 Cz: 1"
    puts 6
end
# ...