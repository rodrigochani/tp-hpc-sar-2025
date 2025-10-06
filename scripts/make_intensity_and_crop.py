import os, sys, numpy as np, rasterio as rio
from glob import glob
from rasterio.transform import Affine

def multilook_block_mean(img, bs=4):
    H, W = img.shape
    H2, W2 = (H//bs)*bs, (W//bs)*bs
    return img[:H2, :W2].reshape(H2//bs, bs, W2//bs, bs).mean(axis=(1,3))

def main(in_dir, out_dir, crop="512,512,0,0", do_multilook=False, bs=4, use_abs2=True):
    os.makedirs(out_dir, exist_ok=True)
    r, c, r0, c0 = [int(x) for x in crop.split(",")]
    files = sorted(glob(os.path.join(in_dir, "*.vrt"))) + sorted(glob(os.path.join(in_dir, "*.tif")))
    assert files, "No se encontraron SLC (.vrt/.tif)"
    for f in files:
        with rio.open(f) as src:
            a = src.read(1)  # complejo o real
            if np.iscomplexobj(a):
                a = np.abs(a)
                if use_abs2: a = a*a
            else:
                if use_abs2: a = a*a
            if do_multilook:
                a = multilook_block_mean(a, bs=bs)
            H, W = a.shape
            r1, c1 = min(r0+r, H), min(c0+c, W)
            tile = a[r0:r1, c0:c1].astype(np.float32)

            # Construir un profile NUEVO para GeoTIFF (no heredar VRT)
            profile = {
                "driver": "GTiff",
                "dtype": "float32",
                "count": 1,
                "height": tile.shape[0],
                "width": tile.shape[1],
                "transform": Affine.identity(),  # sin geotransform: identidad
                "compress": "deflate"
            }
        out = os.path.join(out_dir, os.path.basename(f).replace(".vrt","").replace(".tif","") + "_int_crop.tif")
        with rio.open(out, "w", **profile) as dst:
            dst.write(tile, 1)
        print("OK:", out)

if __name__ == "__main__":
    # Uso: python scripts/make_intensity_and_crop.py SLC_FINE_LOCAL intens_512 "512,512,r0,c0" True 4 True
    in_dir, out_dir = sys.argv[1], sys.argv[2]
    crop = sys.argv[3] if len(sys.argv)>3 else "512,512,0,0"
    do_multilook = sys.argv[4].lower()=="true" if len(sys.argv)>4 else False
    bs = int(sys.argv[5]) if len(sys.argv)>5 else 4
    use_abs2 = sys.argv[6].lower()=="true" if len(sys.argv)>6 else True
    main(in_dir, out_dir, crop, do_multilook, bs, use_abs2)
