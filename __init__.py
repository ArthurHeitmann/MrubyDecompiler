from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

file = "./examples/methods.mrb"

with open(file, "rb") as f:
    riteFile = RiteFile(f)
    codesRes = mrbToRb(riteFile)
    print(codesRes.toStr())
