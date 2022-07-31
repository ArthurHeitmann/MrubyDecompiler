# Mruby Decompiler

This is a decompiler for mruby byte code. It's made for the mruby version from 2015
(rite binary version 0030). It can decompile about 70% of opcodes. The outputs
currently isn't 100% optimal and can still be optimized, but is good enough for now.
The main reason I made this is to decompile mruby scripts for the game Nier:Automata.
So it's mostly focused on the game's script files.

## Usage

`__init__.py` can both compile and decompile ruby/mrb files. This repository comes with precompiled mruby binaries.

#### 1. Without command line

Drag any rb/mrb/bin files you want onto the `__init__.py` file. This will automatically (de-)compile them.

#### 2. With command line

##### 2.1

```bash
python __init__.py <file1> <file2> ...
```

##### 2.2

```bash
python __init__.py --decompileAll <directory>
```

This will decompile all `.mrb` or `_scp.bin` files in the folder. 

## Issues and things to watch out for

- For most function calls inside classes, modules, etc. the decompiler prefixes them with `self.` which can usually be omitted.
- Simple `where` (aka switch) statements work mostly fine, but more complicated ones are a bit buggy.
- Anything in general involving JMP opcodes (if, else, while, where statements) might not be 100% accurate, but good enough for most cases.
- Since JMP opcodes don't have a representation in ruby, when an unhandled JMP opcode is encountered, a warning is printed and instead an exception is thrown in the output code.
- Some patterns (like `exp1 && exp2` and `if exp1 then exp2`) are indistinguishable in the byte code. These kinds of patterns are currently not optimized for.
- Since in ruby everything has a return value and return values in general are a bit funny, you might see some random useless symbols in the output.
