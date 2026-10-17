import sys, numpy as np, nibabel as nib, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
f,out,axis = sys.argv[1], sys.argv[2], int(sys.argv[3])
idx=[int(x) for x in sys.argv[4].split(",")] if len(sys.argv)>4 and sys.argv[4] else None
pct=(1,99.8) if len(sys.argv)<6 else tuple(float(x) for x in sys.argv[5].split(","))
im=nib.as_closest_canonical(nib.load(f)); v=np.asarray(im.dataobj).astype(np.float32)
if v.ndim==4: v=v[...,0]
z=im.header.get_zooms()
n=v.shape[axis]; idx=idx or list(np.linspace(n*0.15,n*0.85,6).astype(int))
lo,hi=np.percentile(v,pct)
fig,ax=plt.subplots(2,3,figsize=(15,10),squeeze=False)
asp={2:z[1]/z[0],1:z[2]/z[0],0:z[2]/z[1]}[axis]
for a,i in zip(ax.flat,idx):
    sl=np.take(v,i,axis=axis).T
    a.imshow(sl,cmap="gray",vmin=lo,vmax=hi,origin="lower",aspect=asp); a.set_title(f"ax{axis} {i}"); a.axis("off")
plt.tight_layout(); plt.savefig(out,dpi=60); print(v.shape, z)
