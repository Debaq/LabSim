import sys, numpy as np, nrrd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
f,out=sys.argv[1],sys.argv[2]; idx=[int(x) for x in sys.argv[3].split(",")]
v,h=nrrd.read(f)
bone=v[::4,::4,::4]; lo,hi=np.percentile(bone,[50,99.9])
fig,ax=plt.subplots(2,3,figsize=(15,10))
for a,i in zip(ax.flat,idx):
    sl=v[150:520,130:470,i].astype(np.float32).T
    a.imshow(sl,cmap="gray",vmin=lo,vmax=hi,origin="lower"); a.set_title(f"z {i}"); a.axis("off")
plt.tight_layout(); plt.savefig(out,dpi=70)
print(lo,hi)
