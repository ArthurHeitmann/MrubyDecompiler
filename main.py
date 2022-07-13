from mrbParser import RiteFile


mrbFile = "D:\\delete\\mods\\na\\blender\\extracted\\data002.cpk_unpacked\\ph1\\nier2blender_extracted\\p100.dat\\p100_56f39801_scp.bin"

def main():
	with open(mrbFile, "rb") as f:
		riteFile = RiteFile(f)

main()
