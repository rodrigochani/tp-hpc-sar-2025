from mpi4py import MPI
import os, sys, time, numpy as np, rasterio as rio
from glob import glob
comm = MPI.COMM_WORLD; rank = comm.Get_rank(); size = comm.Get_size()

def main(in_dir, out_mean, out_std):
    files_all = sorted(glob(os.path.join(in_dir, "*_int_crop.tif"))); assert files_all
    with rio.open(files_all[0]) as ref:
        H,W = ref.height, ref.width; profile = ref.profile
    files = files_all[rank::size]
    t0 = time.time()
    sum_local  = np.zeros((H,W), np.float64)
    sum2_local = np.zeros((H,W), np.float64)
    for f in files:
        with rio.open(f) as src:
            a = src.read(1).astype(np.float32)
        sum_local += a; sum2_local += a*a
    sum_total  = np.zeros_like(sum_local);  comm.Allreduce(sum_local,  sum_total,  op=MPI.SUM)
    sum2_total = np.zeros_like(sum2_local); comm.Allreduce(sum2_local, sum2_total, op=MPI.SUM)
    n_total = comm.allreduce(len(files), op=MPI.SUM)
    if rank==0:
        mean = (sum_total/n_total).astype(np.float32)
        std  = np.sqrt(np.maximum(sum2_total/n_total - mean*mean, 0)).astype(np.float32)
        profile.update(dtype="float32", count=1, compress="deflate")
        with rio.open(out_mean,"w",**profile) as dst: dst.write(mean,1)
        with rio.open(out_std ,"w",**profile) as dst: dst.write(std,1)
        print("tiempo_total_s", time.time()-t0)

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
