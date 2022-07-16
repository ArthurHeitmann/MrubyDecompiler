from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

file = "./examples/methods.mrb"
# file = "D:\\delete\\mods\\na\\blender\\extracted\\data002.cpk_unpacked\\ph1\\nier2blender_extracted\\p100.dat\\p100_56f39801_scp.bin"


with open(file, "rb") as f:
    riteFile = RiteFile(f)
    codesRes = mrbToRb(riteFile)
    print(codesRes.toStr())
