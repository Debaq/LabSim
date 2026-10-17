import sys, glob, os, numpy as np, pydicom, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
src, out = sys.argv[1], sys.argv[2]
idx = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
ds = []
for f in glob.glob(os.path.join(src, "*")):
    try:
        d = pydicom.dcmread(f)
        if hasattr(d, "pixel_array"): ds.append(d)
    except Exception as e:
        print("skip", f, e)
ds.sort(key=lambda d: float(d.ImagePositionPatient[2]))
vol = np.stack([d.pixel_array.astype(float) for d in ds])
d0 = ds[0]
print("n", len(ds), "shape", vol.shape, "px", d0.PixelSpacing, "thk", d0.get("SliceThickness"), "desc", d0.get("SeriesDescription"))
print("age", d0.get("PatientAge"), "sex", d0.get("PatientSex"), "deid", d0.get("PatientIdentityRemoved"), d0.get("DeidentificationMethod"))
idx = idx or list(np.linspace(len(ds)*0.2, len(ds)*0.8, 6).astype(int))
fig, ax = plt.subplots(2, 3, figsize=(15, 10))
for a, i in zip(ax.flat, idx):
    im = vol[i]; lo, hi = np.percentile(im, [1, 99.5])
    a.imshow(im, cmap="gray", vmin=lo, vmax=hi); a.set_title(f"slice {i}"); a.axis("off")
plt.tight_layout(); plt.savefig(out, dpi=70)
