import sys, numpy as np, nrrd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
f,out,axis = sys.argv[1], sys.argv[2], int(sys.argv[3])
idx=[int(x) for x in sys.argv[4].split(",")] if len(sys.argv)>4 else None
v,h=nrrd.read(f); v=v.astype(np.float32)
n=v.shape[axis]; idx = idx or list(np.linspace(n*0.15,n*0.85,9).astype(int))
lo,hi=np.percentile(v[::4,::4,::4],[1,99.8])
cols=3; rows=(len(idx)+2)//3
fig,ax=plt.subplots(rows,cols,figsize=(5*cols,5*rows),squeeze=False)
for a,i in zip(ax.flat,idx):
    sl=np.take(v,i,axis=axis).T
    a.imshow(sl,cmap="gray",vmin=lo,vmax=hi,origin="lower"); a.set_title(f"ax{axis} {i}"); a.axis("off")
plt.tight_layout(); plt.savefig(out,dpi=60)
