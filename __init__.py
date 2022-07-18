import os
import sys
import time

from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

mrbFiles = file = sys.argv[1:]
# file = sys.argv[1] if len(sys.argv) >= 2 else "./examples/case.mrb"

def decompileFile(file: str):
    with open(file, "rb") as f:
        riteFile = RiteFile(f)
        codesRes = mrbToRb(riteFile)
        # print(codesRes.toStr())
    with open(f"{file}.rb", "wb") as f:
        f.write(codesRes.toStr().encode("utf-8", "ignore"))

def compileFile(file: str):
    if os.name == "nt":
        os.system(f"bins\\windows\\mrbc.exe {file}")
    elif os.name == "posix":
        os.system(f"./bins/linux/mrbc.exe {file}")
    else:
        print(f"Unknown OS '{os.name}'")

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
