import binascii
import struct
import sys

def wrap(input_filename, output_filename):
    with open(input_filename, "rb") as f:
        data = f.read()
    
    length = len(data)
    crc = binascii.crc32(data)
    
    # LiteX BIOS expects: [Length (4 bytes)][CRC32 (4 bytes)][Data...]
    # Using '>' for Big Endian because your SoC reported 'big ordering'
    # header = struct.pack(">II", length, crc)
    header = struct.pack("<II", length, crc)
    
    with open(output_filename, "wb") as f:
        f.write(header + data)
    
    print(f"Wrapped {length} bytes with CRC {hex(crc)}")
    print(f"Created {output_filename}")

if __name__ == "__main__":
    wrap("firmware.bin", "firmware.fbi")