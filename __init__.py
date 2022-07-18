from __future__ import annotations
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

def decompileFile(file: str, outFile: str|None = None):
    with open(file, "rb") as f:
        riteFile = RiteFile(f)
        codesRes = mrbToRb(riteFile)
        # print(codesRes.toStr())
    with open(outFile or "{file}.rb", "wb") as f:
        f.write(codesRes.toStr().encode("utf-8", "ignore"))

def compileFile(file: str, outFile: str|None = None):
    outFile = outFile or file + ".mrb"
    if os.name == "nt":
        os.system(f"bins\\windows\\mrbc.exe -o \"{outFile}\" \"{file}\"")
    elif os.name == "posix":
        os.system(f"./bins/linux/mrbc.exe -o \"{outFile}\" {file}\"")
    else:
        print(f"Unknown OS '{os.name}'")

if __name__ == "__main__":
    mrbFiles = file = sys.argv[1:]
    # file = sys.argv[1] if len(sys.argv) >= 2 else "./examples/case.mrb"
    t1 = time.time()

    for file in mrbFiles:
        if file.endswith(".mrb") or file.endswith("_scp.bin"):
            print(f"Decompiling {file}")
            decompileFile(file)
        elif file.endswith(".rb"):
            print(f"Compiling {file}")
            compileFile(file)
        else:
            print(f"Unknown file type: {file}")

    t2 = time.time()
    print(f"Time: {((t2 - t1)*1000):.1f}ms")
