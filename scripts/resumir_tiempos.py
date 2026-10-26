#!/usr/bin/env python3
"""Lee los tiempos recogidos en los equipos (core/tiempos.py) y los resume.

Uso: scripts/resumir_tiempos.py CARPETA_O_ARCHIVO [...]

En cada equipo están en ~/.local/share/LabSim/tiempos/ (Linux) o
%LOCALAPPDATA%\\LabSim\\tiempos\\ (Windows). Se pueden juntar los de varios
equipos en una sola carpeta: se agrupa por equipo y versión.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def leer(rutas):
    archivos = []
    for r in map(Path, rutas):
        archivos += sorted(r.rglob("tiempos-*.jsonl")) if r.is_dir() else [r]
    for a in archivos:
        sesion = []
        for linea in a.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                sesion.append(json.loads(linea))
            except ValueError:
                pass  # última línea cortada por un cierre brusco
        if sesion:
            yield a, sesion


def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(len(v) * p))] if v else 0


def main(rutas):
    sesiones = list(leer(rutas))
    if not sesiones:
        sys.exit("no hay archivos tiempos-*.jsonl")

    bloqueos, metricas, ui_http, procesos = [], defaultdict(list), [], defaultdict(list)
    hitos = defaultdict(list)
    print(f"{len(sesiones)} arranques\n")
    for a, ev in sesiones:
        sis = next((e for e in ev if e["tipo"] == "sistema"), {})
        equipo = f'{sis.get("host", "?")} {sis.get("version", "?")}'
        fin = next((e for e in ev if e["tipo"] == "fin"), None)
        print(f'- {equipo} · {sis.get("so")} · {sis.get("cpu")} · {sis.get("nucleos")} núcleos · '
              f'{sis.get("ram_mb")} MB · {"cerró bien, " + str(fin["segundos"]) + " s" if fin else "SIN cierre limpio"}')
        for e in ev:
            t = e["tipo"]
            if t == "bloqueo":
                bloqueos.append((equipo, e))
            elif t == "hito":
                hitos[e["nombre"]].append(e["t"])
            elif t == "lento" and e.get("hilo") == "ui":
                ui_http.append((equipo, e))
            elif t == "resumen":
                for nombre, m in e["metricas"].items():
                    metricas[nombre].append(m)
                p = e["proceso"]
                if p.get("rss_mb") is not None:
                    procesos["rss"].append(p["rss_mb"])
                procesos["cpu"].append(p["cpu_pct"])

    print("\n== Arranque (ms desde que parte el proceso)")
    for nombre, v in hitos.items():
        print(f"  {nombre:32} mediana {pct(v, .5):8.0f}   peor {max(v):8.0f}")

    print("\n== Bloqueos del hilo de la ventana")
    total = sum(e["ms"] for _, e in bloqueos)
    print(f"  {len(bloqueos)} bloqueos, {total / 1000:.1f} s en total; "
          f"p50 {pct([e['ms'] for _, e in bloqueos], .5):.0f} ms, p95 {pct([e['ms'] for _, e in bloqueos], .95):.0f} ms, "
          f"máx {max([e['ms'] for _, e in bloqueos], default=0)} ms")
    por_pila = defaultdict(lambda: [0, 0, set()])
    for equipo, e in bloqueos:
        pila = e["pilas"][0]["pila"] if e["pilas"] else "(sin muestras: ráfaga corta)"
        g = por_pila[pila]
        g[0] += 1
        g[1] += e["ms"]
        g[2].add(e.get("tras", "-"))
    print("  Pilas que más tiempo se llevan (la primera es lo más interno):")
    for pila, (n, ms, tras) in sorted(por_pila.items(), key=lambda kv: -kv[1][1])[:10]:
        print(f"   {ms / 1000:6.1f} s · {n:3} veces · tras: {', '.join(sorted(tras))[:60]}\n      {pila[:230]}")
    print("  Los 8 más largos:")
    for equipo, e in sorted(bloqueos, key=lambda x: -x[1]["ms"])[:8]:
        print(f'   {e["ms"]:6} ms · {equipo} · {e["ts"]} · tras: {e.get("tras", "-")}')

    print("\n== Red hecha desde el hilo de la ventana (congela la pantalla mientras espera)")
    por_ruta = defaultdict(list)
    for _, e in ui_http:
        por_ruta[e["nombre"]].append(e["ms"])
    for nombre, v in sorted(por_ruta.items(), key=lambda kv: -sum(kv[1]))[:10]:
        print(f"  {nombre:46} {len(v):4} veces · {sum(v) / 1000:6.1f} s · máx {max(v):.0f} ms")
    if not por_ruta:
        print("  ninguna")

    print("\n== Por nombre (suma de todos los resúmenes de minuto)")
    print(f"  {'nombre':44} {'n':>7} {'total s':>8} {'p95 ms':>8} {'máx ms':>8}")
    filas = []
    for nombre, ms in metricas.items():
        filas.append((sum(m["tot"] for m in ms), nombre, sum(m["n"] for m in ms),
                      max(m["p95"] for m in ms), max(m["max"] for m in ms)))
    for tot, nombre, n, p95, mx in sorted(filas, reverse=True)[:25]:
        print(f"  {nombre[:44]:44} {n:7} {tot / 1000:8.1f} {p95:8.1f} {mx:8.1f}")

    print("\n== Proceso")
    if procesos["rss"]:
        print(f"  memoria: mediana {pct(procesos['rss'], .5):.0f} MB, máx {max(procesos['rss']):.0f} MB")
    print(f"  CPU: mediana {pct(procesos['cpu'], .5):.1f} %, p95 {pct(procesos['cpu'], .95):.1f} %")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
