import os, sys, time, numpy as np, rasterio as rio
from glob import glob
from multiprocessing import Pool, get_context

def chunk(lst, n):
    k = len(lst)
    if k == 0: return []
    m = (k + n - 1)//n
    return [lst[i*m:(i+1)*m] for i in range(n) if lst[i*m:(i+1)*m]]

def worker(paths):
    import numpy as np, rasterio as rio
    sum_img = None; sum2_img = None; n_local = 0
    for p in paths:
        with rio.open(p) as src:
            a = src.read(1).astype(np.float32)
        if sum_img is None:
            H, W = a.shape
            sum_img  = np.zeros((H,W), np.float64)
            sum2_img = np.zeros((H,W), np.float64)
        sum_img  += a
        sum2_img += a*a
        n_local  += 1
    return sum_img, sum2_img, n_local

def main(in_dir, out_mean, out_std, procs=4):
    files = sorted(glob(os.path.join(in_dir, "*_int_crop.tif")))
    assert files, "No hay recortes en la carpeta"
    with rio.open(files[0]) as ref:
        H, W = ref.height, ref.width
        profile = ref.profile
    groups = chunk(files, procs)
    t0 = time.time()
    sum_tot  = np.zeros((H,W), np.float64)
    sum2_tot = np.zeros((H,W), np.float64)
    n_tot = 0
    # usar 'spawn' para evitar sobrecarga rara en algunas MKL/BLAS
    with get_context("spawn").Pool(processes=len(groups)) as pool:
        for s, s2, n in pool.imap_unordered(worker, groups, chunksize=1):
            sum_tot  += s
            sum2_tot += s2
            n_tot    += n
    mean = (sum_tot/n_tot).astype(np.float32)
    std  = np.sqrt(np.maximum(sum2_tot/n_tot - mean*mean, 0)).astype(np.float32)
    profile.update(dtype="float32", count=1, compress="deflate")
    with rio.open(out_mean, "w", **profile) as dst: dst.write(mean, 1)
    with rio.open(out_std,  "w", **profile) as dst: dst.write(std, 1)
    print("tiempo_total_s", time.time()-t0)

if __name__=="__main__":
    in_dir, out_mean, out_std = sys.argv[1], sys.argv[2], sys.argv[3]
    procs = int(sys.argv[4]) if len(sys.argv)>4 else 4
    main(in_dir, out_mean, out_std, procs)
