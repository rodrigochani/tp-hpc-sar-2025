import sys, csv, math, re
import matplotlib.pyplot as plt

def parse_time(s):
    s = s.strip()
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts)==2: m,sec = parts; return float(m)*60 + float(sec)
            if len(parts)==3: h,m,sec = parts; return float(h)*3600 + float(m)*60 + float(sec)
        except ValueError:
            pass
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    if not m: raise ValueError(s)
    return float(m.group(1))

def main(path):
    rows=[]
    with open(path, newline="") as f:
        for i,row in enumerate(csv.reader(f, delimiter="\t")):
            if i==0 or not row or len(row)<2: continue
            try: t=parse_time(row[1])
            except: continue
            rows.append((row[0].strip(), t))
    if not rows:
        print("No hay datos válidos en", path); return

    order=["sec","mp2","mp4","mp8","mp4_mem","mpi2","mpi4","mpi8"]
    rows.sort(key=lambda kv: (order.index(kv[0]) if kv[0] in order else 999, kv[0]))
    base=dict(rows).get("sec", None)

    # barras de tiempo
    labels=[k for k,_ in rows]; vals=[v for _,v in rows]
    plt.figure(figsize=(6,4)); plt.bar(labels, vals); plt.ylabel("Tiempo (s)")
    plt.title("Tiempo por backend"); plt.tight_layout()
    plt.savefig("benchmarks/t_barras.png", dpi=150); plt.close()

    # speedup
    if base is not None:
        sp=[base/v if v>0 else math.nan for v in vals]
        plt.figure(figsize=(6,4)); plt.bar(labels, sp); plt.ylabel("Speedup (T_sec/T_backend)")
        plt.title("Speedup vs. secuencial"); plt.tight_layout()
        plt.savefig("benchmarks/speedup.png", dpi=150); plt.close()

    print("\n== Resultados ==")
    print("{:<10s} {:>10s} {:>10s}".format("backend","t(s)","speedup"))
    for k,v in rows:
        sp = (base/v) if (base and v>0) else float("nan")
        print("{:<10s} {:>10.4f} {:>10}".format(k,v, f"{sp:.3f}" if base else "-"))

if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else "benchmarks/resultados.csv")
