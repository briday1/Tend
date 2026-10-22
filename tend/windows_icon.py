"""Generate a multi-size Windows .ico for Tend without external dependencies.

The packaged favicon is SVG; Windows shortcuts require an ICO file.
"""
from pathlib import Path
import struct
import zlib

def png_chunk(name, data):
    return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xffffffff)

def raster(size):
    pixels = bytearray()
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            u = (x + .5) * 64 / size
            v = (y + .5) * 64 / size
            # Rounded square with a white geometric T, echoing the current mark.
            corner = min(u, 64-u)
            vertical = min(v, 64-v)
            inside = (corner >= 10 or vertical >= 10 or (corner-10)**2+(vertical-10)**2 <= 100)
            if not inside:
                rgba=(0,0,0,0)
            elif (12 <= u <= 52 and 15 <= v <= 22) or (28 <= u <= 36 and 15 <= v <= 49):
                rgba=(250,252,247,255)
            else:
                rgba=(38,61,48,255)
            pixels.extend(rgba)
    raw=zlib.compress(bytes(pixels),9)
    return (b"\x89PNG\r\n\x1a\n"+png_chunk(b"IHDR",struct.pack(">2I5B",size,size,8,6,0,0,0))
            +png_chunk(b"IDAT",raw)+png_chunk(b"IEND",b""))

def create_icon(path):
    sizes=[16,24,32,48,64,128,256]
    images=[raster(n) for n in sizes]
    offset=6+16*len(images)
    entries=[]
    for n,png in zip(sizes,images):
        entries.append(struct.pack("<BBBBHHII",0 if n==256 else n,0 if n==256 else n,0,0,1,32,len(png),offset))
        offset+=len(png)
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(struct.pack("<HHH",0,1,len(images))+b"".join(entries)+b"".join(images))
    return target

if __name__=="__main__":
    import sys
    create_icon(sys.argv[1])
