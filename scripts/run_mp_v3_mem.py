import os, sys, time, numpy as np, rasterio as rio
from glob import glob
from multiprocessing import Pool, get_context

def load_all(paths):
    arrs = []
    for p in paths:
        with rio.open(p) as src:
            arrs.append(src.read(1).astype(np.float32))
    return arrs

def worker(a):
    # trabajo por imagen (aquí es liviano: sumas). Si querés, podés agregar
    # algo de cómputo (e.g., (a**0.5 + a).sum()) para ver más speedup.
    return a, a*a

def main(in_dir, out_mean, out_std, procs=4):
    files = sorted(glob(os.path.join(in_dir, "*_int_crop.tif")))
    assert files, "No hay recortes en la carpeta"
    with rio.open(files[0]) as ref:
        H, W = ref.height, ref.width; profile = ref.profile

    t0 = time.time()
    # 1) I/O secuencial (evita pelear por disco)
    arrs = load_all(files)

    # 2) Cálculo en paralelo sobre arrays en RAM
    with get_context("fork").Pool(processes=procs) as pool:
        parts = pool.map(worker, arrs, chunksize=max(1, len(arrs)//(2*procs) or 1))

    sum_img  = np.zeros((H,W), np.float64)
    sum2_img = np.zeros((H,W), np.float64)
    for s, s2 in parts:
        sum_img  += s
        sum2_img += s2
    n = len(arrs)
    mean = (sum_img/n).astype(np.float32)
    std  = np.sqrt(np.maximum(sum2_img/n - mean*mean, 0)).astype(np.float32)
    profile.update(dtype="float32", count=1, compress="deflate")
    with rio.open(out_mean, "w", **profile) as dst: dst.write(mean, 1)
    with rio.open(out_std,  "w", **profile) as dst: dst.write(std, 1)
    print("tiempo_total_s", time.time()-t0)

if __name__=="__main__":
    in_dir, out_mean, out_std = sys.argv[1], sys.argv[2], sys.argv[3]
    procs = int(sys.argv[4]) if len(sys.argv)>4 else 4
    main(in_dir, out_mean, out_std, procs)
