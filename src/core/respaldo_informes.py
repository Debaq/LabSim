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
    {appointment_id, tipo, data, huella, guardado, estado, version}
estado: 'pendiente' (no llegó al servidor), 'subido', o 'cerrada' (el
servidor lo rechazó porque la atención ya estaba cerrada: no hay a dónde
subirlo, se guarda igual por si el docente lo pide).
version: la versión del servidor sobre la que se armó este informe (0 si
no se conoce). Viaja con cada subida: si en el servidor hay otra, el
servidor guarda aparte la que pisa (ver report_upload.php).

Lo ya subido también queda: si al retomar no se puede preguntar al
servidor, el módulo vuelve con lo último de este equipo en vez de vacío
(vacío, el autoguardado subía la atención en blanco encima de lo hecho).
"""
import json
import os
import re
import shutil
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

from core import rutas

# guardar() corre en el hilo de la ventana y marcar() en el de la subida:
# leer-modificar-escribir el mismo archivo a la vez revertía lo nuevo.
_lock = threading.RLock()

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
        texto = ruta.read_text("utf-8")
    except OSError:
        return None
    try:
        registro = json.loads(texto)
    except ValueError:
        # Roto (un corte de luz antes de este arreglo, un disco con
        # problemas): se aparta en vez de ignorarlo, para que podar() no lo
        # borre y se pueda rescatar a mano.
        print(f"respaldo: {ruta.name} está dañado, se aparta como .danado")
        try:
            os.replace(ruta, ruta.with_name(ruta.name + ".danado"))
        except OSError:
            pass
        return None
    return registro if isinstance(registro, dict) else None


def _fsync_carpeta(carpeta: Path) -> None:
    if os.name == "nt":
        return   # Windows no abre carpetas; NTFS ya ordena el rename
    try:
        fd = os.open(carpeta, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _escribir(ruta: Path, registro: dict) -> None:
    # Atómico y a disco: un corte de luz deja el archivo anterior o el
    # nuevo, nunca uno vacío (sin fsync el rename podía llegar al disco
    # antes que el contenido). Temporal propio de cada escritura: dos
    # hilos escribiendo el mismo .tmp mezclaban el contenido.
    fd, tmp = tempfile.mkstemp(prefix=ruta.name + ".", suffix=".tmp", dir=ruta.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False, default=str))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, ruta)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    _fsync_carpeta(ruta.parent)


def guardar(usuario, job, huella, imagenes=None, version=None) -> bool:
    """Escribe el informe y copia sus imágenes ({sufijo: ruta}; None = no
    se tocan las que ya había). Nunca lanza: un disco lleno no puede
    frenar la atención. True si quedó.

    `version`: la del servidor sobre la que se armó; None conserva la
    que ya tenía el registro."""
    if not usuario:
        return False
    try:
        with _lock:
            ruta = _ruta(usuario, job["appointment_id"], job["tipo"])
            previo = _leer(ruta) if ruta.exists() else None
            if version is None:
                version = (previo or {}).get("version") or 0
            if imagenes is not None:
                _reemplazar_imagenes(ruta, imagenes)
            _escribir(ruta, {
                "appointment_id": int(job["appointment_id"]),
                "tipo": job["tipo"],
                "data": job["data"],
                "huella": huella,
                "guardado": datetime.now().isoformat(timespec="seconds"),
                "estado": "pendiente",
                "version": int(version or 0),
            })
    except Exception as exc:  # noqa: BLE001
        print(f"respaldo: no se pudo guardar {job.get('tipo')} en el equipo: {exc}")
        return False
    return True


def _reemplazar_imagenes(ruta, imagenes):
    """A una carpeta nueva y después el cambio: las imágenes pueden venir
    de la carpeta misma (una prueba del ABR recuperada de acá que se
    vuelve a respaldar). Las que ya estaban y no vienen se conservan: la
    EOA retomada vuelve con los números pero sin los gráficos, y el
    próximo respaldo borraba los de la vuelta anterior sin subir."""
    destino = _carpeta_imagenes(ruta)
    nueva = destino.with_name(destino.name + ".nueva")
    shutil.rmtree(nueva, ignore_errors=True)
    nueva.mkdir(parents=True, exist_ok=True)
    for sufijo, origen in imagenes.items():
        try:
            shutil.copyfile(origen, nueva / f"{sufijo}.jpg")
        except OSError:
            continue
    if destino.is_dir():
        for vieja in destino.glob("*.jpg"):
            if not (nueva / vieja.name).exists():
                try:
                    shutil.copyfile(vieja, nueva / vieja.name)
                except OSError:
                    continue
    shutil.rmtree(destino, ignore_errors=True)
    os.replace(nueva, destino)


def imagenes(usuario, appointment_id, tipo) -> dict:
    """{sufijo: ruta} de las imágenes respaldadas."""
    if not usuario:
        return {}
    try:
        carpeta = _carpeta_imagenes(_ruta(usuario, appointment_id, tipo))
        if not carpeta.is_dir():
            return {}
        return {p.stem: str(p) for p in carpeta.glob("*.jpg")}
    except OSError as exc:
        print(f"respaldo: no se pudieron leer las imágenes de {tipo}: {exc}")
        return {}


def leer(usuario, appointment_id, tipo):
    """El registro de ese informe en el equipo, o None."""
    if not usuario:
        return None
    try:
        ruta = _ruta(usuario, appointment_id, tipo)
    except OSError:
        return None
    return _leer(ruta) if ruta.exists() else None


def marcar(usuario, appointment_id, tipo, huella, estado, version=None) -> None:
    """El informe con esa huella ya llegó (o no tiene a dónde llegar). Si
    en el medio se respaldó uno más nuevo, ese sigue pendiente, pero igual
    se anota la versión nueva del servidor: es sobre la que va a subir."""
    if not usuario:
        return
    try:
        with _lock:
            ruta = _ruta(usuario, appointment_id, tipo)
            registro = _leer(ruta)
            if registro is None:
                return
            if registro.get("huella") == huella:
                registro["estado"] = estado
            elif version is None:
                return
            if version is not None:
                registro["version"] = int(version)
            _escribir(ruta, registro)
    except Exception as exc:  # noqa: BLE001
        print(f"respaldo: no se pudo marcar {tipo}: {exc}")


def anotar_del_servidor(usuario, appointment_id, informe) -> None:
    """Lo que trajo el servidor al retomar queda también en el equipo,
    como ya subido: sirve de respaldo si más tarde no hay red, y su
    versión es la base de la próxima subida. Un pendiente del equipo no se
    toca (es más nuevo)."""
    tipo = informe.get("tipo")
    if not usuario or not tipo or not isinstance(informe.get("data"), dict):
        return
    try:
        with _lock:
            ruta = _ruta(usuario, appointment_id, tipo)
            previo = _leer(ruta) if ruta.exists() else None
            if previo is not None and previo.get("estado") == "pendiente":
                return
            _escribir(ruta, {
                "appointment_id": int(appointment_id),
                "tipo": tipo,
                "data": informe["data"],
                "huella": None,
                "guardado": datetime.now().isoformat(timespec="seconds"),
                "estado": "subido",
                "version": int(informe.get("version") or 0),
            })
    except Exception as exc:  # noqa: BLE001
        print(f"respaldo: no se pudo anotar {tipo} del servidor: {exc}")


def _registros(usuario):
    if not usuario:
        return []
    carpeta = _base() / usuario
    salida = []
    for ruta in sorted(carpeta.glob("*.json")):
        registro = _leer(ruta)
        if registro is not None:
            salida.append(registro)
    return salida


def pendientes(usuario, appointment_id=None) -> list:
    """Los informes del usuario que no llegaron al servidor."""
    return [r for r in _registros(usuario)
            if r.get("estado") == "pendiente"
            and (appointment_id is None
                 or str(r.get("appointment_id")) == str(appointment_id))]


def mezclar(usuario, appointment_id, del_servidor, tipos=None, servidor_ok=True) -> list:
    """Lo que hay que recuperar de una cita: lo del servidor (el más nuevo
    primero, como lo da my_report.php) con lo pendiente del equipo delante,
    que es más nuevo.

    `servidor_ok=False`: no se pudo preguntar. Entonces vale también lo ya
    subido desde este equipo, que es lo último que se sabe."""
    estados = ("pendiente",) if servidor_ok else ("pendiente", "subido")
    locales = [{"tipo": r["tipo"], "data": r["data"], "origen": "equipo",
                "estado": r.get("estado")}
               for r in _registros(usuario)
               if r.get("estado") in estados
               and str(r.get("appointment_id")) == str(appointment_id)
               and (tipos is None or r.get("tipo") in tipos)]
    # Pendientes primero: son los más nuevos.
    locales.sort(key=lambda r: r["estado"] != "pendiente")
    for r in locales:
        r.pop("estado")
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


# -- Borrador de la evolución ---------------------------------------------------
# La evolución escrita vivía solo en la ventana: reabrirla la borraba, y
# cerrar sesión, una caída o el apagado del kiosko se la llevaban. Es lo
# único que deja el alumno de las pruebas sin informe propio (audiometría,
# logo, impedanciometría), así que se escribe acá mientras la escribe.
# Aparte de los informes: no se sube sola, viaja como nota al cerrar.

def _ruta_borrador(usuario, appointment_id) -> Path:
    carpeta = _base() / usuario
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / f"{int(appointment_id)}.evolucion.txt"


def guardar_borrador(usuario, appointment_id, texto) -> bool:
    if not usuario or appointment_id is None:
        return False
    try:
        with _lock:
            ruta = _ruta_borrador(usuario, appointment_id)
            if not texto.strip():
                ruta.unlink(missing_ok=True)
                return True
            fd, tmp = tempfile.mkstemp(prefix=ruta.name + ".", suffix=".tmp", dir=ruta.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(texto)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, ruta)
            _fsync_carpeta(ruta.parent)
    except Exception as exc:  # noqa: BLE001
        print(f"respaldo: no se pudo guardar el borrador de la evolución: {exc}")
        return False
    return True


def leer_borrador(usuario, appointment_id) -> str:
    if not usuario or appointment_id is None:
        return ""
    try:
        return _ruta_borrador(usuario, appointment_id).read_text("utf-8")
    except (OSError, ValueError):
        return ""


def borrar_borrador(usuario, appointment_id) -> None:
    if not usuario or appointment_id is None:
        return
    try:
        _ruta_borrador(usuario, appointment_id).unlink(missing_ok=True)
    except (OSError, ValueError):
        pass
