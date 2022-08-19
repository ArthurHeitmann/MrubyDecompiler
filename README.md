# MRuby Decompiler

This is a decompiler for MRuby byte code. It's made for the MRuby version from 2015
(Rite binary version 0030). It can decompile about 70% of opcodes. The outputs
currently are not 100% optimal and can still be optimized, but good enough for now.
The main reason I made this is to decompile MRuby scripts for the game NieR:Automata.
So it's mostly focused on the game's script files.

If you need auto recompiling for NieR Modding, check out [NierAutoRebuild](https://github.com/ArthurHeitmann/NierAutoRebuild).

## Usage

`__init__.py` can both compile and decompile Ruby/MRB files. This repository comes with precompiled mruby binaries.

#### 1. Without command line

Drag any RB/MRB/BIN files or folder you want onto the `__init__.py` file. This will automatically (de-)compile them.  
If it's a folder, it will decompile all files in the folder.

#### 2. With command line

```bash
python __init__.py <file1> <file2> <folderX> ...
```

#### 3. Compile tool to frozen executable (binary)

You can compile the main script to an executable, if you want to be python independent.

*Currently supports Windows and Linux*
*"python" is your Python 3 interpreter*

In order to use, first install required dependencies... (feel free to make a "virtual environment")
```bash
python -m pip install -r requirements.txt
```

Next, run the build script.
```bash
python build_release.py
```

Once this is done, you can find your executable (or binary) in the `dist` folder.
If you are on Linux, feel free to use `chmod` to give it the permissions it deserves :) 

## Issues and things to watch out for

- For most function calls inside classes, modules, etc. the decompiler prefixes them with `self.` which can usually be omitted.
- Simple `where` (aka switch) statements work mostly fine, but more complicated ones are a bit buggy.
- Anything in general involving `JMP` opcodes (if, else, while, where statements) might not be 100% accurate, but good enough for most cases.
- Since `JMP` opcodes don't have a representation in Ruby, when an unhandled `JMP` opcode is encountered, a warning is printed and instead an exception is thrown in the output code.
- Some patterns (like `exp1 && exp2` and `if exp1 then exp2`) are indistinguishable in the byte code. These kinds of patterns are currently not optimized for.
- Since in Ruby everything has a return value and return values in general are a bit funny, you might see some random useless symbols in the output.
