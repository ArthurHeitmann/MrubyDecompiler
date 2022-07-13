import struct

# Big Endian

def read_int8(file) -> int:
    entry = file.read(1)
    return struct.unpack('>b', entry)[0]

def read_uint8(file) -> int:
    entry = file.read(1)
    return struct.unpack('B', entry)[0]

def read_int16(file) -> int:
    entry = file.read(2)
    return struct.unpack('>h', entry)[0]

def read_uint16(file) -> int:
    entry = file.read(2)
    return struct.unpack('>H', entry)[0]

def read_int32(file) -> int:
    entry = file.read(4)
    return struct.unpack('>i', entry)[0]

def read_uint32(file) -> int:
    entry = file.read(4)
    return struct.unpack('>I', entry)[0]

def read_int64(file) -> int:
    entry = file.read(8)
    return struct.unpack('>q', entry)[0]

def read_uint64(file) -> int:
    entry = file.read(8)
    return struct.unpack('>Q', entry)[0]

def read_string(file, maxLen = -1) -> str:
    binaryString = b""
    while maxLen == -1 or len(binaryString) < maxLen:
        char = file.read(1)
        if char == b'\x00':
            break
        binaryString += char
    return binaryString.decode('utf-8', 'ignore')
