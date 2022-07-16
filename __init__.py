import sys

from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

file = sys.argv[1] if len(sys.argv) >= 2 else "./examples/classes.mrb"
outfile = sys.argv[2] if len(sys.argv) >= 3 else file + ".rb"


with open(file, "rb") as f:
    riteFile = RiteFile(f)
    codesRes = mrbToRb(riteFile)
    # print(codesRes.toStr())
with open(outfile, "wb") as f:
    f.write(codesRes.toStr().encode("utf-8", "ignore"))

