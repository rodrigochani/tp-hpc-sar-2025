TP Final — HPC con Python en SAR (SAOCOM)

Tema: medir rendimiento de enfoques simples (secuencial y paralelos) sobre una pila de SLC SAOCOM.
Pipeline: módulo → |S|² → multilook 4×4 → recorte 1024×1024 → mean & std.

1) Requisitos
# Ubuntu
sudo apt update
sudo apt install -y gdal-bin libgdal-dev

# Python (VS Code/venv recomendado)
python3 -m venv .venv
source .venv/bin/activate
pip install numpy rasterio matplotlib


(Opcional) Para MPI: sudo apt install -y openmpi-bin libopenmpi-dev mpi-default-bin y pip install mpi4py.

2) Datos (no incluidos)

Usé SLC SAOCOM (coarse coreg) accesibles vía *.slc.vrt (o *.slc.xml de ISCE 2).
Crear carpeta plana con los VRT legibles por GDAL:

SLC_FINE_LOCAL/   # ← todos los .slc.vrt (o links a .slc.xml renombrados a .vrt)


Ejemplo de creación rápida (si tenés subcarpetas por fecha):

FLAT=SLC_FINE_LOCAL
SRC=Coarse
mkdir -p "$FLAT"
find "$SRC" -type f -name "*.slc.vrt" -exec ln -sf {} "$FLAT"/ \;

3) Generar intensidades + recortes (1024×1024, multilook 4×4)
python scripts/make_intensity_and_crop.py SLC_FINE_LOCAL intens_512 "1024,1024,0,0" True 4 True


Salida: intens_512/*_int_crop.tif (float32, sin georreferencia).

Si querés tiles más chicos: "512,512,0,0".

4) Correr backends y medir tiempos

Para evitar sobre-suscripción de BLAS:

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1


Secuencial (baseline):

/usr/bin/time -f "%e" -o benchmarks/sec_time.txt \
  python scripts/run_secuencial.py intens_512 mean.tif std.tif


Multiprocessing v2 (lista particionada, menos IPC):

/usr/bin/time -f "%e" -o benchmarks/mp4_time.txt \
  python scripts/run_mp_v2.py intens_512 mean_mp.tif std_mp.tif 4


Multiprocessing “mem” (I/O secuencial, cálculo en paralelo):

/usr/bin/time -f "%e" -o benchmarks/mp4_mem_time.txt \
  python scripts/run_mp_v3_mem.py intens_512 mean_mp_mem.tif std_mp_mem.tif 4


(Opcional) MPI 4 ranks:

/usr/bin/time -f "%e" -o benchmarks/mpi4_time.txt \
  mpiexec -n 4 python scripts/run_mpi.py intens_512 mean_mpi.tif std_mpi.tif

5) CSV y gráficos
echo -e "backend\ttiempo" > benchmarks/resultados.csv
[ -f benchmarks/sec_time.txt ]     && echo -e "sec\t$(cat benchmarks/sec_time.txt)"         >> benchmarks/resultados.csv
[ -f benchmarks/mp4_time.txt ]     && echo -e "mp4\t$(cat benchmarks/mp4_time.txt)"         >> benchmarks/resultados.csv
[ -f benchmarks/mp4_mem_time.txt ] && echo -e "mp4_mem\t$(cat benchmarks/mp4_mem_time.txt)" >> benchmarks/resultados.csv
[ -f benchmarks/mpi4_time.txt ]    && echo -e "mpi4\t$(cat benchmarks/mpi4_time.txt)"       >> benchmarks/resultados.csv

python scripts/plot_bench.py benchmarks/resultados.csv
# => benchmarks/t_barras.png  y  benchmarks/speedup.png

6) Verificación rápida (igualdad de resultados)
python - << 'PY'
import rasterio as rio, numpy as np
def R(p): 
    with rio.open(p) as s: return s.read(1)
m=R("mean.tif"); s=R("std.tif")
mm=R("mean_mp.tif"); sm=R("std_mp.tif")
print("max|Δ| mean vs mp:", float(np.nanmax(np.abs(m-mm))))
print("max|Δ| std  vs mp:", float(np.nanmax(np.abs(s-sm))))
PY

7) Estructura del repo
.
├─ scripts/
│  ├─ make_intensity_and_crop.py
│  ├─ run_secuencial.py
│  ├─ run_mp_v2.py
│  ├─ run_mp_v3_mem.py
│  ├─ run_mp.py
│  ├─ run_mpi.py
│  └─ plot_bench.py
├─ intens_512/                # salidas TIF generadas (chicos)
├─ benchmarks/
│  ├─ resultados.csv
│  ├─ t_barras.png
│  └─ speedup.png
├─ informe.md                 # conclusiones del trabajo
├─ requirements.txt           
└─ README.md                  # este archivo


No subir SLC/VRT originales. Con los scripts y pasos alcanza para reproducir.

8) Tips / fallos comunes

“Attempt to create 0x0 dataset”: usar recorte desde (0,0) y/o tamaño menor (512x512).

“Writing through VRTSourcedRasterBand is not supported”: al escribir, forzar driver='GTiff' (ya está en make_intensity_and_crop.py).

Resultados más lentos en paralelo: pocas imágenes + kernel liviano ⇒ domina I/O. Probá más fechas, tiles más grandes o run_mp_v3_mem.py.

BLAS peleándose: fijá *_NUM_THREADS=1 como arriba.

GDAL/Rasterio: si hay conflicto de versiones, pip install "rasterio==1.3.*" suele arreglar.

9) Notas

Los GeoTIFF de salida no están georreferenciados (Affine identidad) → suficiente para este TP.

El objetivo es comparar tiempos y entender cuellos (I/O, IPC, etc.), no optimizar al extremo.