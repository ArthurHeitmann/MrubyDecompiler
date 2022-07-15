from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

file = "./examples/classes.mrb"

with open(file, "rb") as f:
    riteFile = RiteFile(f)
    codesRes = mrbToRb(riteFile)
    print(codesRes.toStr())
