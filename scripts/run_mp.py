import os, sys, time, numpy as np, rasterio as rio
from glob import glob
from multiprocessing import Pool

def load_full(path):
    with rio.open(path) as src:
        return src.read(1).astype(np.float32)

def main(in_dir, out_mean, out_std, procs=4):
    files = sorted(glob(os.path.join(in_dir, "*_int_crop.tif"))); assert files
    with rio.open(files[0]) as ref:
        H, W = ref.height, ref.width; profile = ref.profile
    t0 = time.time()
    sum_img  = np.zeros((H,W), np.float64)
    sum2_img = np.zeros((H,W), np.float64)
    with Pool(processes=procs) as pool:
        for a in pool.imap_unordered(load_full, files):
            sum_img  += a
            sum2_img += a*a
    n = len(files)
    mean = (sum_img/n).astype(np.float32)
    std  = np.sqrt(np.maximum(sum2_img/n - mean*mean, 0)).astype(np.float32)
    profile.update(dtype="float32", count=1, compress="deflate")
    with rio.open(out_mean,"w",**profile) as dst: dst.write(mean,1)
    with rio.open(out_std ,"w",**profile) as dst: dst.write(std,1)
    print("tiempo_total_s", time.time()-t0)

if __name__=="__main__":
    in_dir, out_mean, out_std = sys.argv[1], sys.argv[2], sys.argv[3]
    procs = int(sys.argv[4]) if len(sys.argv)>4 else 4
    main(in_dir, out_mean, out_std, procs)
