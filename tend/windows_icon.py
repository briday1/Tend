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
            # Horizon: transparent pixels outside a circular landscape mark.
            import math
            dx=u-32;dy=v-32
            distance=math.hypot(dx,dy)
            alpha=max(0,min(255,round((30.2-distance)*255)))
            wave1=31+4*math.sin((u-10)/10)
            wave2=39+4*math.sin((u-7)/9)
            wave3=48+4*math.sin((u-12)/8)
            if v>=wave3:rgb=(40,77,62)
            elif v>=wave2:rgb=(93,134,108)
            elif v>=wave1:rgb=(140,171,150)
            else:rgb=(201,217,198)
            rgba=(*rgb,alpha)
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
