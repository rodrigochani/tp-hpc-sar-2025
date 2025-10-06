Informe (TP Final – HPC con Python en SAR)
Metodología

Trabajé con SLC SAOCOM (previamente con corregistro grueso de ISCE 2: coarse coreg). Pipeline simple: módulo → |S|² → multilook 4×4 → recorte 1024×1024 (sin georref).

Implementé tres formas de calcular promedio y desvío sobre la pila:

Secuencial (baseline).

Multiprocessing (dos variantes; la v2 reduce tráfico entre procesos).

Multiprocessing “mem”: leo todo a RAM y paralelizo solo el cálculo para evitar pelear por disco.
(Dejé preparado MPI, pero en esta compu no lo corrí).

Resultados (5 recortes de 1024×1024)

Tiempos con /usr/bin/time %e:

sec ≈ 1.06 s

mp4 (v2) ≈ 1.58 s → más lento que secuencial

mp4_mem ≈ 1.00 s → speedup ~1.06×

Los tres dan lo mismo numéricamente (diff máx. = 0.0 en mean/std).

Resultados

El “kernel” es liviano (sumas y cuadrados). Con pocas imágenes, manda el I/O y el overhead de crear procesos → por eso mp4 perdió.

Funcionó mejor cuando:

Partí la lista y acumulé local en cada proceso (menos IPC).

Leí a RAM y paralelicé solo el cálculo (mp4_mem) → ahí apareció un speedup chico, pero real.

El N° de procesos importa: con poca carga, 2 o 4 van parecido; 8 ya me empeoró.

Limitaciones

Dataset chico (5 fechas) y recortes de 1024×1024: poco trabajo para lucir el paralelismo.

Sin GPU: para este caso tan simple, el I/O probablemente tape cualquier ganancia.

Coarse coreg: usé (r0,c0)=(0,0) y multilook 4×4 para no salirme de rango. Solución práctica.

Próximos pasos (ideas cortas)

Más fechas (12–24) o recortes más grandes (p. ej. 2048×2044) para subir el cómputo útil.

Probar MPI repartiendo por fechas y compararlo contra multiprocessing.

GPU (Numba/CuPy/PyCUDA) pero con kernels más pesados (p. ej. filtros de speckle o convoluciones).

Usar NVMe/ramdisk o memoria mapeada para bajar la presión de I/O.

Reproducible en 3 líneas

Scripts: make_intensity_and_crop.py, run_secuencial.py, run_mp_v2.py, run_mp_v3_mem.py, plot_bench.py.

Medición: /usr/bin/time -f "%e" -o benchmarks/<backend>_time.txt ...

CSV → benchmarks/resultados.csv → gráficos t_barras.png y speedup.png.
(Fijé *_NUM_THREADS=1 para no sobre-suscribir hilos de BLAS.)

Cierre. Con pocos datos y un kernel simple, el paralelismo “a lo bruto” no alcanza por I/O + overhead. Ajustando el diseño (menos IPC, I/O secuencial) conseguí un speedup modesto. Para mejorar en serio necesito más carga o kernels más intensivos; ahí MPI/GPU tienen más sentido. Me queda claro el balance datos vs. cómputo y que el diseño del pipeline es clave.
