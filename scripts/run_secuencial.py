import os, sys, time, numpy as np, rasterio as rio
from glob import glob

def main(in_dir, out_mean, out_std, tau=0.3, sigma=0.1):
    files = sorted(glob(os.path.join(in_dir, "*_int_crop.tif")))
    assert files, "No hay recortes en la carpeta"
    with rio.open(files[0]) as ref:
        H, W = ref.height, ref.width; profile = ref.profile
    sum_ = np.zeros((H,W), np.float64); sum2 = np.zeros((H,W), np.float64); n = 0
    t0 = time.time()
    for f in files:
        with rio.open(f) as src: a = src.read(1).astype(np.float32)
        sum_ += a; sum2 += a*a; n += 1
        print("leido", os.path.basename(f))
    mean = (sum_/n).astype(np.float32)
    std  = np.sqrt(np.maximum(sum2/n - mean*mean, 0)).astype(np.float32)
    profile.update(dtype="float32", count=1, compress="deflate")
    with rio.open(out_mean,"w",**profile) as dst: dst.write(mean,1)
    with rio.open(out_std ,"w",**profile) as dst: dst.write(std,1)
    mask = ((mean>tau)&(std<sigma)).astype("uint8")
    profile.update(dtype="uint8")
    with rio.open(out_mean.replace(".tif","_mask.tif"),"w",**profile) as dst:
        dst.write(mask,1)
    print("tiempo_total_s", time.time()-t0)

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
