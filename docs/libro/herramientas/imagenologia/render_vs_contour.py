import sys,json,glob,numpy as np,pydicom,matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
ser,cj,out=sys.argv[1:4]
ds=sorted([pydicom.dcmread(f) for f in glob.glob(ser+"/*.dcm")],key=lambda d: float(d.ImagePositionPatient[2]))
z=np.array([float(d.ImagePositionPatient[2]) for d in ds]); o=np.array(ds[0].ImagePositionPatient,float); ps=float(ds[0].PixelSpacing[0])
polys=[np.array(p) for s in json.load(open(cj)) if s['structure_name'].lower()=='tv' for p in s['LPS_contour_points']]
allp=np.vstack(polys); c=allp.mean(0); print("centro LPS",c.round(1))
cx,cy=(c[0]-o[0])/ps,(c[1]-o[1])/ps
zi=sorted(set(int(np.argmin(abs(z-p[:,2].mean()))) for p in polys)); print("slices",zi)
mid=zi[len(zi)//2]; sel=[mid-6,mid-3,mid,mid+2,mid+4,mid+8]
fig,ax=plt.subplots(2,3,figsize=(15,9))
for a,i in zip(ax.flat,sel):
    im=ds[i].pixel_array.astype(float); h=110
    y0,y1,x0,x1=int(cy-h*0.7),int(cy+h*0.7),int(min(cx,448-cx)-60),int(max(cx,448-cx)+60)
    x0=max(0,x0);x1=min(448,x1)
    sub=im[y0:y1,x0:x1]; lo,hi=np.percentile(sub,[1,99.7])
    a.imshow(sub,cmap="gray",vmin=lo,vmax=hi)
    for p in polys:
        if int(np.argmin(abs(z-p[:,2].mean())))==i:
            a.plot((p[:,0]-o[0])/ps-x0,(p[:,1]-o[1])/ps-y0,'r-',lw=0.7)
    a.set_title(f"slice {i}"); a.axis("off")
plt.tight_layout(); plt.savefig(out,dpi=70)
