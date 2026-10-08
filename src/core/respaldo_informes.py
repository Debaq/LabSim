"""Respaldo en el equipo de los informes de examen.

El autoguardado (core/report_autosave.py) sube cada informe al servidor.
Sin red la subida falla, y lo único que quedaba era la memoria: si la app se
cerraba (o se caía) el alumno volvía a abrir el ABR y no tenía nada. Ahora
cada vez que el informe cambia se escribe primero acá, en el disco, y
después se intenta subir.

Al retomar la atención se mezcla con lo que tiene el servidor (`mezclar`):
lo que quedó en el equipo sin subir es más nuevo que lo del servidor, así
que gana. Lo que ya se subió no aporta nada y el servidor manda.

Un archivo por (usuario, cita, tipo): en el laboratorio los equipos son
compartidos y una cita de "todo el curso" es la misma para todos los
alumnos. Va en la carpeta de datos (core/rutas.py), que no se borra al
actualizar.

Formato de cada .json:
    {appointment_id, tipo, data, huella, guardado, estado}
estado: 'pendiente' (no llegó al servidor), 'subido', o 'cerrada' (el
servidor lo rechazó porque la atención ya estaba cerrada: no hay a dónde
subirlo, se guarda igual por si el docente lo pide).
"""
import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from core import rutas

# Lo que no está pendiente se borra pasado este tiempo.
OLVIDAR_DIAS = 30


def _base() -> Path:
    return rutas.carpeta("informes")


def usuario_de(client) -> str:
    """Carpeta del usuario logueado en `client` ('' si no hay sesión)."""
    user = getattr(client, "user", None) or {}
    valor = str(user.get("id") or user.get("username") or "")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", valor)


def _ruta(usuario, appointment_id, tipo) -> Path:
    tipo = re.sub(r"[^A-Za-z0-9_]", "_", str(tipo))
    carpeta = _base() / usuario
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / f"{int(appointment_id)}_{tipo}.json"


def _carpeta_imagenes(ruta: Path) -> Path:
    return ruta.with_suffix("")


def _leer(ruta: Path):
    try:
        registro = json.loads(ruta.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    return registro if isinstance(registro, dict) else None


def _escribir(ruta: Path, registro: dict) -> None:
    # Atómico: un corte a mitad de la escritura deja el archivo anterior,
    # no uno roto.
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_text(json.dumps(registro, ensure_ascii=False, default=str), "utf-8")
    os.replace(tmp, ruta)


def guardar(usuario, job, huella, imagenes=None) -> bool:
    """Escribe el informe y copia sus imágenes ({sufijo: ruta}). Nunca
    lanza: un disco lleno no puede frenar la atención. True si quedó."""
    if not usuario:
        return False
    try:
        ruta = _ruta(usuario, job["appointment_id"], job["tipo"])
        if imagenes is not None:
            # A una carpeta nueva y después el cambio: las imágenes pueden
            # venir de la carpeta misma (una prueba del ABR recuperada de
            # acá que se vuelve a respaldar).
            destino = _carpeta_imagenes(ruta)
            nueva = destino.with_name(destino.name + ".nueva")
            shutil.rmtree(nueva, ignore_errors=True)
            nueva.mkdir(parents=True, exist_ok=True)
            for sufijo, origen in imagenes.items():
                try:
                    shutil.copyfile(origen, nueva / f"{sufijo}.jpg")
                except OSError:
                    continue
            shutil.rmtree(destino, ignore_errors=True)
            os.replace(nueva, destino)
        _escribir(ruta, {
            "appointment_id": int(job["appointment_id"]),
            "tipo": job["tipo"],
            "data": job["data"],
            "huella": huella,
            "guardado": datetime.now().isoformat(timespec="seconds"),
            "estado": "pendiente",
        })
    except Exception as exc:  # noqa: BLE001
        print(f"respaldo: no se pudo guardar {job.get('tipo')} en el equipo: {exc}")
        return False
    return True


def imagenes(usuario, appointment_id, tipo) -> dict:
    """{sufijo: ruta} de las imágenes respaldadas."""
    if not usuario:
        return {}
    carpeta = _carpeta_imagenes(_ruta(usuario, appointment_id, tipo))
    if not carpeta.is_dir():
        return {}
    return {p.stem: str(p) for p in carpeta.glob("*.jpg")}


def marcar(usuario, appointment_id, tipo, huella, estado) -> None:
    """El informe con esa huella ya llegó (o no tiene a dónde llegar). Si
    en el medio se respaldó uno más nuevo, ese sigue pendiente."""
    if not usuario:
        return
    try:
        ruta = _ruta(usuario, appointment_id, tipo)
        registro = _leer(ruta)
        if registro is None or registro.get("huella") != huella:
            return
        registro["estado"] = estado
        _escribir(ruta, registro)
    except Exception as exc:  # noqa: BLE001
        print(f"respaldo: no se pudo marcar {tipo}: {exc}")


def pendientes(usuario, appointment_id=None) -> list:
    """Los informes del usuario que no llegaron al servidor."""
    if not usuario:
        return []
    carpeta = _base() / usuario
    salida = []
    for ruta in sorted(carpeta.glob("*.json")):
        registro = _leer(ruta)
        if registro is None or registro.get("estado") != "pendiente":
            continue
        if appointment_id is not None and str(registro.get("appointment_id")) != str(appointment_id):
            continue
        salida.append(registro)
    return salida


def mezclar(usuario, appointment_id, del_servidor, tipos=None) -> list:
    """Lo que hay que recuperar de una cita: lo del servidor (el más nuevo
    primero, como lo da my_report.php) con lo pendiente del equipo delante,
    que es más nuevo."""
    locales = [{"tipo": r["tipo"], "data": r["data"], "origen": "equipo"}
               for r in pendientes(usuario, appointment_id)
               if tipos is None or r.get("tipo") in tipos]
    return locales + list(del_servidor or [])


def podar(dias=OLVIDAR_DIAS) -> None:
    """Borra lo ya subido (o sin destino) más viejo que `dias`. Lo
    pendiente no se toca nunca."""
    limite = time.time() - dias * 86400
    try:
        for ruta in _base().glob("*/*.json"):
            registro = _leer(ruta)
            if registro is not None and registro.get("estado") == "pendiente":
                continue
            try:
                if ruta.stat().st_mtime > limite:
                    continue
                ruta.unlink()
            except OSError:
                continue
            shutil.rmtree(_carpeta_imagenes(ruta), ignore_errors=True)
    except OSError:
        pass
