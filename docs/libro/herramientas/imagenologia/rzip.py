# Lista o extrae un miembro de un zip remoto usando HTTP Range (sin bajar todo)
import sys, io, zipfile, urllib.request
class RF(io.RawIOBase):
    def __init__(s,url):
        s.url=url; s.pos=0
        r=urllib.request.urlopen(urllib.request.Request(url,headers={"Range":"bytes=0-0"}))
        s.size=int(r.headers["Content-Range"].split("/")[1])
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s,o,w=0):
        s.pos = o if w==0 else (s.pos+o if w==1 else s.size+o); return s.pos
    def read(s,n=-1):
        if n<0: n=s.size-s.pos
        if n==0 or s.pos>=s.size: return b""
        end=min(s.pos+n,s.size)-1
        r=urllib.request.urlopen(urllib.request.Request(s.url,headers={"Range":f"bytes={s.pos}-{end}"}))
        b=r.read(); s.pos+=len(b); return b
    def readinto(s,b):
        d=s.read(len(b)); b[:len(d)]=d; return len(d)
url=sys.argv[1]
z=zipfile.ZipFile(io.BufferedReader(RF(url),buffer_size=1<<20))
if len(sys.argv)==2:
    for i in z.infolist(): print(f"{i.file_size/1e6:10.1f} MB  {i.filename}")
else:
    name,out=sys.argv[2],sys.argv[3]
    with z.open(name) as src, open(out,"wb") as dst:
        while True:
            b=src.read(1<<22)
            if not b: break
            dst.write(b)
    print("ok",out)
