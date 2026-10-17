import sys, glob, os, numpy as np, pydicom, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
src, out, idxs, crop = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
y0,y1,x0,x1 = [int(v) for v in crop.split(",")]
ds=[]
for f in glob.glob(os.path.join(src,"*.dcm")):
    ds.append(pydicom.dcmread(f))
ds.sort(key=lambda d: float(d.ImagePositionPatient[2]))
idx=[int(x) for x in idxs.split(",")]
n=len(idx); cols=min(n,3); rows=(n+cols-1)//cols
fig, ax = plt.subplots(rows, cols, figsize=(6*cols, 4*rows), squeeze=False)
for a,i in zip(ax.flat, idx):
    im=ds[i].pixel_array.astype(float)[y0:y1,x0:x1]; lo,hi=np.percentile(im,[1,99.7])
    a.imshow(im,cmap="gray",vmin=lo,vmax=hi); a.set_title(f"slice {i}"); a.axis("off")
plt.tight_layout(); plt.savefig(out, dpi=80)
