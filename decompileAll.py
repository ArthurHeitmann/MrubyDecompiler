import os
import traceback

from mrbParser import RiteFile
from mrbToRb.mrbToRb import mrbToRb

def decompileAll(searchDir: str):
    filesFound = 0
    filesDecompiled = 0
    for root, dirs, files in os.walk(searchDir):
        for file in files:
            if not (file.endswith("_scp.bin") or file.endswith(".mrb")):
                continue
            filesFound += 1
            filePath = os.path.join(root, file)
            try:
                with open(filePath, "rb") as f:
                    riteFile = RiteFile(f)
                    codesRes = mrbToRb(riteFile)
                with open(f"{filePath}.rb", "wb") as f:
                    f.write(codesRes.toStr().encode("utf-8", "ignore"))
                filesDecompiled += 1
            except:
                print(f"Error decompiling {filePath}")
                traceback.print_exc()
                continue

    print(f"\nDecompiled {filesDecompiled}/{filesFound} files")
