import sys
import time

from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

file = sys.argv[1] if len(sys.argv) >= 2 else "./examples/if.mrb"
outfile = sys.argv[2] if len(sys.argv) >= 3 else file + ".rb"

t1 = time.time()

with open(file, "rb") as f:
    riteFile = RiteFile(f)
    codesRes = mrbToRb(riteFile)
    print(codesRes.toStr())
# with open(outfile, "wb") as f:
#     f.write(codesRes.toStr().encode("utf-8", "ignore"))

t2 = time.time()
print(f"\nTime: {((t2 - t1)*1000):.1f}ms")
