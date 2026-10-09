#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cliente de la consola remota del backend (api/consola.php).

El token se genera en el panel (Datos e IA -> Consola remota) y vence solo.
Lee LABSIM_CONSOLA_URL y LABSIM_CONSOLA_TOKEN de --env, del entorno o de
~/.config/labsim/consola.env (lo escribe scripts/labsim_token.sh).

    consola.py ping
    consola.py sql "SELECT id, username FROM users WHERE role = ?" -p '["student"]'
    consola.py script cambios.sql          (o "-" para stdin; una transaccion)
    consola.py esquema
    consola.py backup
    consola.py archivos tickets
    consola.py leer tickets/ticket_3.log.gz [-o salida]
    consola.py revocar                     (corta el token y borra el archivo)

Solo stdlib: no depende del entorno de la app.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENV_POR_DEFECTO = Path.home() / ".config" / "labsim" / "consola.env"


def _cargar_env(ruta: str | None) -> tuple[str, str, str | None]:
    valores = dict(os.environ)
    if not ruta and "LABSIM_CONSOLA_TOKEN" not in valores and ENV_POR_DEFECTO.is_file():
        ruta = str(ENV_POR_DEFECTO)
    if ruta:
        for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                valores[k.strip()] = v.strip()
    url = valores.get("LABSIM_CONSOLA_URL", "")
    token = valores.get("LABSIM_CONSOLA_TOKEN", "")
    if not url or not token:
        sys.exit("Sin token: correr scripts/labsim_token.sh <token> (o --env / entorno)")
    return url, token, ruta


def _llamar(url: str, token: str, cuerpo: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=150) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        texto = e.read().decode("utf-8", "replace")
        try:
            texto = json.loads(texto).get("error", texto)
        except ValueError:
            pass
        sys.exit(f"HTTP {e.code}: {texto}")


def _tabla(columnas: list, filas: list, ancho_max: int) -> str:
    def celda(v) -> str:
        s = "NULL" if v is None else str(v)
        s = s.replace("\n", "\\n")
        return s if len(s) <= ancho_max else s[: ancho_max - 1] + "…"

    texto = [[celda(c) for c in columnas]] + [[celda(v) for v in f] for f in filas]
    anchos = [max(len(f[i]) for f in texto) for i in range(len(columnas))]
    lineas = [" | ".join(v.ljust(anchos[i]) for i, v in enumerate(f)) for f in texto]
    lineas.insert(1, "-+-".join("-" * a for a in anchos))
    return "\n".join(lineas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", help="archivo con LABSIM_CONSOLA_URL y LABSIM_CONSOLA_TOKEN")
    ap.add_argument("--json", action="store_true", help="respuesta cruda en JSON")
    ap.add_argument("--ancho", type=int, default=80, help="ancho maximo de celda en la tabla")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sql")
    s.add_argument("sql")
    s.add_argument("-p", "--params", default="[]", help="JSON: lista para ?, objeto para :nombre")
    s = sub.add_parser("script")
    s.add_argument("archivo", help="archivo .sql o - para stdin")
    for nombre in ("ping", "esquema", "backup", "revocar"):
        sub.add_parser(nombre)
    s = sub.add_parser("archivos")
    s.add_argument("ruta", nargs="?", default="")
    s = sub.add_parser("leer")
    s.add_argument("ruta")
    s.add_argument("-o", "--salida", help="guardar en archivo en vez de imprimir")
    a = ap.parse_args()

    url, token, ruta_env = _cargar_env(a.env)
    if a.cmd == "sql":
        cuerpo = {"sql": a.sql, "params": json.loads(a.params)}
    elif a.cmd == "script":
        texto = sys.stdin.read() if a.archivo == "-" else Path(a.archivo).read_text(encoding="utf-8")
        cuerpo = {"script": texto}
    elif a.cmd in ("archivos", "leer"):
        cuerpo = {"accion": a.cmd, "ruta": a.ruta}
    else:
        cuerpo = {"accion": a.cmd}
    r = _llamar(url, token, cuerpo)

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif a.cmd == "sql" and r.get("columnas"):
        print(_tabla(r["columnas"], r["filas"], a.ancho))
        extra = " (truncado)" if r.get("truncado") else ""
        print(f"\n{r['n']} fila(s){extra}, {r['ms']} ms")
    elif a.cmd in ("sql", "script"):
        print(f"{r['cambios']} fila(s) modificada(s), {r['ms']} ms")
    elif a.cmd == "revocar":
        if ruta_env == str(ENV_POR_DEFECTO):
            ENV_POR_DEFECTO.unlink(missing_ok=True)
        print("Token revocado")
    elif a.cmd == "esquema":
        for o in r["objetos"]:
            if o.get("sql"):
                print(o["sql"].strip() + ";\n")
    elif a.cmd == "archivos":
        for e in r["entradas"]:
            tam = "" if e["bytes"] is None else str(e["bytes"])
            print(f"{e['tipo']:7} {tam:>10}  {e['modificado']}  {e['nombre']}")
    elif a.cmd == "leer":
        datos = r["contenido"]
        crudo = base64.b64decode(datos) if r["codificacion"] == "base64" else datos.encode("utf-8")
        if a.salida:
            Path(a.salida).write_bytes(crudo)
            print(f"{len(crudo)} bytes -> {a.salida}")
        elif r["codificacion"] == "base64":
            sys.exit("Archivo binario: usar -o para guardarlo")
        else:
            sys.stdout.write(datos)
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
