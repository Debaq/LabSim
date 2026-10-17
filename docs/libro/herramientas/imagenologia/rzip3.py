# Extrae miembros que matchean un regex de un zip remoto (HTTP Range); uso: url regex outdir
import sys, io, zipfile, struct, subprocess, zlib, urllib.request, re, os
url, pat, outdir = sys.argv[1:4]
def rng(a,b):
    return subprocess.run(["curl","-sL","--retry","5","-r",f"{a}-{b}",url],capture_output=True,check=True).stdout
size=int(urllib.request.urlopen(urllib.request.Request(url,headers={"Range":"bytes=0-0"})).headers["Content-Range"].split("/")[1])
tail=rng(max(0,size-(4<<20)), size-1)
class F(io.RawIOBase):
    def __init__(s): s.pos=0
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s,o,w=0):
        s.pos = o if w==0 else (s.pos+o if w==1 else size+o); return s.pos
    def readinto(s,b):
        base=size-len(tail)
        d=tail[s.pos-base:s.pos-base+len(b)] if s.pos>=base else rng(s.pos, min(s.pos+len(b),size)-1)
        b[:len(d)]=d; s.pos+=len(d); return len(d)
z=zipfile.ZipFile(F())
for i in z.infolist():
    if i.is_dir() or not re.search(pat,i.filename): continue
    out=os.path.join(outdir, os.path.basename(i.filename))
    if os.path.exists(out): continue
    blk=rng(i.header_offset, i.header_offset+29+65536+i.compress_size) if i.compress_size<(2<<20) else None
    if blk is None:
        h=rng(i.header_offset,i.header_offset+29); n,e=struct.unpack("<HH",h[26:30]); st=i.header_offset+30+n+e
        raw=rng(st, st+i.compress_size-1)
    else:
        n,e=struct.unpack("<HH",blk[26:30]); raw=blk[30+n+e:30+n+e+i.compress_size]
    data= raw if i.compress_type==0 else zlib.decompress(raw,-15)
    assert zlib.crc32(data)==i.CRC, i.filename
    open(out,"wb").write(data)
print("done")
