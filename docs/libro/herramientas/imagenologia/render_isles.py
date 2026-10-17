import sys, numpy as np, nibabel as nib, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
d,case,out=sys.argv[1],sys.argv[2],sys.argv[3]
L=lambda p: np.asarray(nib.as_closest_canonical(nib.load(p)).dataobj).astype(np.float32)
dwi=L(f"{d}/img/sub-strokecase{case}_ses-0001_dwi.nii.gz"); adc=L(f"{d}/img/sub-strokecase{case}_ses-0001_adc.nii.gz")
m=L(f"{d}/msk/sub-strokecase{case}_ses-0001_msk.nii.gz")>0
zs=np.where(m.any((0,1)))[0]; zc=[zs[len(zs)//4], zs[len(zs)//2], zs[3*len(zs)//4]]
fig,ax=plt.subplots(3,3,figsize=(12,12))
for r,z in enumerate(zc):
    for c,(v,t) in enumerate([(dwi,"DWI"),(adc,"ADC"),(dwi,"DWI+mask")]):
        sl=v[:,:,z].T; lo,hi=np.percentile(v[v>0],[1,99.5])
        ax[r,c].imshow(sl,cmap="gray",vmin=lo,vmax=hi,origin="lower")
        if c==2: ax[r,c].contour(m[:,:,z].T,[0.5],colors="r",linewidths=0.8,origin="lower")
        ax[r,c].set_title(f"{t} z{z}"); ax[r,c].axis("off")
plt.tight_layout(); plt.savefig(out,dpi=60)
