import sys, numpy as np, nrrd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
f,out=sys.argv[1],sys.argv[2]
v,h=nrrd.read(f); v=v.astype(np.float32); sp=np.abs(np.diag(np.array(h["space directions"],dtype=float)))
W=[(-1000+2000)/2, 2000]  # ventana senos: L 0? usamos L=400 W=2000 aprox hueso/aire
lo,hi=-1000,1500
fig,ax=plt.subplots(2,3,figsize=(15,10))
nz=v.shape[2]
for a,k in zip(ax[0],[nz//4,nz//2,3*nz//4]):
    a.imshow(v[:,:,k].T,cmap="gray",vmin=lo,vmax=hi,aspect=sp[1]/sp[0]); a.set_title(f"axial {k}"); a.axis("off")
ny=v.shape[1]
for a,k in zip(ax[1],[ny//3,ny//2,2*ny//3]):
    a.imshow(v[:,k,:].T[::-1],cmap="gray",vmin=lo,vmax=hi,aspect=sp[2]/sp[0]); a.set_title(f"coronal {k}"); a.axis("off")
plt.tight_layout(); plt.savefig(out,dpi=60)
