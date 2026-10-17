import sys, io, zipfile, struct, subprocess, zlib, urllib.request
url, name, out = sys.argv[1:4]
def rng(a,b):
    return subprocess.run(["curl","-sL","--retry","5","-r",f"{a}-{b}",url],capture_output=True,check=True).stdout
size=int(urllib.request.urlopen(urllib.request.Request(url,headers={"Range":"bytes=0-0"})).headers["Content-Range"].split("/")[1])
tail=rng(size-(1<<20), size-1)
class F(io.RawIOBase):
    # solo el final del archivo esta en memoria; suficiente para el directorio central
    def __init__(s): s.pos=0
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s,o,w=0):
        s.pos = o if w==0 else (s.pos+o if w==1 else size+o); return s.pos
    def readinto(s,b):
        base=size-len(tail)
        if s.pos>=base:
            d=tail[s.pos-base:s.pos-base+len(b)]
        else:
            d=rng(s.pos, min(s.pos+len(b),size)-1)
        b[:len(d)]=d; s.pos+=len(d); return len(d)
z=zipfile.ZipFile(F())
i=z.getinfo(name)
h=rng(i.header_offset, i.header_offset+29)
n,e=struct.unpack("<HH",h[26:30])
start=i.header_offset+30+n+e
print("member",name,"comp",i.compress_size,"type",i.compress_type,"start",start)
subprocess.run(["curl","-sL","--retry","5","-r",f"{start}-{start+i.compress_size-1}","-o",out+".raw",url],check=True)
raw=open(out+".raw","rb").read(); assert len(raw)==i.compress_size, len(raw)
data = raw if i.compress_type==0 else zlib.decompress(raw,-15)
assert zlib.crc32(data)==i.CRC
open(out,"wb").write(data); print("ok",len(data))
import os; os.remove(out+".raw")
