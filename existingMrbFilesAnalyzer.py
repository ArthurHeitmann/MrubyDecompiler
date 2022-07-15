from typing import List
from mrbParser import RiteFile, RiteIrepSection
import os
from opcodes import opcodes

searchPath = "D:\\delete\\mods\\na\\blender\\extracted\\"
mrbFile = "D:\\delete\\mods\\na\\blender\\extracted\\data002.cpk_unpacked\\ph1\\nier2blender_extracted\\p100.dat\\p100_56f39801_scp.bin"
fileExt = "_scp.bin"

allOpCodes: List[List] = []
for i in range(len(opcodes)):
	allOpCodes.append([0, []])

def searchForOpcodes(irepSection: RiteIrepSection, file: str):
	for opCode in irepSection.mrbCodes:
		allOpCodes[opCode.opcode][0] += 1
		if len(allOpCodes[opCode.opcode][1]) < 5 and file not in allOpCodes[opCode.opcode][1]:
			allOpCodes[opCode.opcode][1].append(file)
	for child in irepSection.childIreps:
		searchForOpcodes(child, file)

def main():
	for root, dirs, files in os.walk(searchPath):
		for file in files:
			if not file.endswith(fileExt):
				continue
			try:
				with open(os.path.join(root, file), "rb") as f:
					riteFile = RiteFile(f)
				searchForOpcodes(riteFile.irepBlock.section, file)
			except Exception as e:
				print(e)
				continue
	
	for i, opCode in enumerate(allOpCodes):
		print(f"{opcodes[i][0]}:\t{opCode[0]}" + ("\t\t" + ", ".join(opCode[1][:5])))
	
main()
