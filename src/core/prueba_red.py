"""Prueba de red contra el servidor, para los tickets que manda el usuario.

Nace del 2026-11-06: en pleno práctico un equipo no lograba abrir la
atención, HostArmada contestó que su servidor estaba bien y que era
problema del proveedor, y no había datos del equipo afectado para
discutirlo. Ahora cada ticket manual lleva lo que vio ese equipo en ese
momento: cuánto tarda en resolver el nombre, en conectar y en el handshake
TLS con conexiones nuevas, cuánto con la conexión que ya está abierta, y la
pérdida de paquetes del ping del sistema.

Sin Qt: corre en el hilo del envío (hilos.en_fondo). Todo con límite de
tiempo; lo que falle queda anotado como falla, no corta el ticket. El
detalle completo va al registro de la app (que viaja con el ticket) y un
resumen corto a las claves red_* del detalle (Tickets::normalizarDetalle
guarda solo valores simples de hasta 200 caracteres).
"""
import platform
import re
import socket
import ssl
import subprocess
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

CONEXIONES_NUEVAS = 5
PEDIDOS_REUTILIZADOS = 3
PING_PAQUETES = 10
LIMITE_S = 15


def _ms(segundos):
    return int(round(segundos * 1000))


def _resumen_tiempos(valores):
    if not valores:
        return "-"
    valores = sorted(valores)
    return f"mín {valores[0]} / med {valores[len(valores) // 2]} / máx {valores[-1]} ms"


def _conexion_nueva(host, ip, puerto, ruta):
    """Una conexión desde cero: TCP, TLS y un HEAD. Tiempos en ms."""
    paso = "tcp"
    t0 = time.monotonic()
    try:
        crudo = socket.create_connection((ip, puerto), timeout=LIMITE_S)
        tcp = time.monotonic()
        paso = "tls"
        contexto = ssl.create_default_context()
        with contexto.wrap_socket(crudo, server_hostname=host) as tls:
            tls_fin = time.monotonic()
            paso = "http"
            tls.sendall(f"HEAD {ruta} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n"
                        "User-Agent: LabSim-prueba-red\r\n\r\n".encode("ascii"))
            linea = tls.recv(64).split(b"\r\n", 1)[0].decode("ascii", "replace")
            fin = time.monotonic()
        return {"tcp_ms": _ms(tcp - t0), "tls_ms": _ms(tls_fin - tcp), "total_ms": _ms(fin - t0),
                "http": linea[9:12] if linea.startswith("HTTP/") else linea[:20]}
    except (OSError, ssl.SSLError) as exc:
        return {"error": f"{paso}: {type(exc).__name__}", "tras_ms": _ms(time.monotonic() - t0)}


def _ping(host):
    """Pérdida y tiempo del ping del sistema. None si no hay ping (o no
    deja: en algunos equipos necesita permisos)."""
    if platform.system() == "Windows":
        cmd = ["ping", "-n", str(PING_PAQUETES), "-w", "2000", host]
    else:
        cmd = ["ping", "-c", str(PING_PAQUETES), "-i", "0.3", "-W", "2", host]
    try:
        salida = subprocess.run(cmd, capture_output=True, text=True, timeout=40,
                                errors="replace").stdout
    except (OSError, subprocess.SubprocessError):
        return None
    perdida = re.search(r"(\d+(?:[.,]\d+)?)\s*%", salida)
    rtt = re.search(r"=\s*[\d.,]+/([\d.,]+)/", salida) or re.search(r"(?:Media|Average)\s*=\s*(\d+)", salida)
    if perdida is None:
        return None
    return {"perdida_pct": perdida.group(1).replace(",", "."),
            "rtt_ms": rtt.group(1).replace(",", ".") if rtt else "-"}


def medir(base_url, sesion=None, ruta_estatica="/css/base.css"):
    """Mide la red hacia el servidor de base_url. Devuelve (claves red_*
    para el detalle del ticket, texto largo para el registro)."""
    partes = urlsplit(base_url)
    host = partes.hostname or ""
    puerto = partes.port or (443 if partes.scheme == "https" else 80)
    ruta = (partes.path.rstrip("/") + ruta_estatica) or "/"
    lineas = [f"Prueba de red hacia {host} ({datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC)"]
    claves = {}

    t0 = time.monotonic()
    try:
        ips = sorted({info[4][0] for info in socket.getaddrinfo(host, puerto, type=socket.SOCK_STREAM)})
        dns_ms = _ms(time.monotonic() - t0)
        claves["red_dns"] = f"{dns_ms} ms → {', '.join(ips)}"
        lineas.append(f"DNS: {claves['red_dns']}")
    except OSError as exc:
        claves["red_dns"] = f"falla: {exc}"
        claves["red_resumen"] = "No se pudo resolver el nombre del servidor (sin DNS o sin internet)."
        lineas.append(f"DNS: {claves['red_dns']}")
        return claves, "\n".join(lineas)
    ip = ips[0]

    nuevas = [_conexion_nueva(host, ip, puerto, ruta) for _ in range(CONEXIONES_NUEVAS)]
    for i, r in enumerate(nuevas, 1):
        lineas.append(f"Conexión nueva {i}: {r}")
    buenas = [r for r in nuevas if "error" not in r]
    fallas = len(nuevas) - len(buenas)
    claves["red_conexiones_nuevas"] = (
        f"{len(buenas)}/{len(nuevas)} ok · TCP {_resumen_tiempos([r['tcp_ms'] for r in buenas])}"
        f" · TLS {_resumen_tiempos([r['tls_ms'] for r in buenas])}")
    if fallas:
        claves["red_fallas"] = "; ".join(r["error"] for r in nuevas if "error" in r)[:200]

    if sesion is not None:
        tiempos, errores = [], []
        url = base_url.rstrip("/") + ruta_estatica
        for _ in range(PEDIDOS_REUTILIZADOS):
            t = time.monotonic()
            try:
                sesion.head(url, timeout=(LIMITE_S, LIMITE_S))
                tiempos.append(_ms(time.monotonic() - t))
            except Exception as exc:  # noqa: BLE001 -- se anota
                errores.append(type(exc).__name__)
        claves["red_conexion_abierta"] = (f"{len(tiempos)}/{PEDIDOS_REUTILIZADOS} ok · "
                                          f"{_resumen_tiempos(tiempos)}"
                                          + (f" · fallas: {', '.join(errores)}" if errores else ""))
        lineas.append(f"Conexión ya abierta: {claves['red_conexion_abierta']}")

    ping = _ping(ip)
    claves["red_ping"] = (f"{ping['perdida_pct']} % perdidos de {PING_PAQUETES}, promedio {ping['rtt_ms']} ms"
                          if ping else "no disponible en este equipo")
    lineas.append(f"Ping: {claves['red_ping']}")

    lento = [r for r in buenas if r["tls_ms"] > 2000 or r["tcp_ms"] > 1500]
    if fallas or lento or (ping and float(ping["perdida_pct"]) >= 10):
        claves["red_resumen"] = (f"Red con problemas: {fallas} de {len(nuevas)} conexiones fallaron, "
                                 f"{len(lento)} lentas"
                                 + (f", {ping['perdida_pct']} % de paquetes perdidos" if ping else "") + ".")
    else:
        claves["red_resumen"] = "Red normal hacia el servidor."
    lineas.append(claves["red_resumen"])
    return claves, "\n".join(lineas)


def estado(claves):
    """'sin_dns' | 'sin_respuesta' | 'problemas' | 'normal', leído de lo que
    devolvió medir()."""
    if str(claves.get("red_dns", "")).startswith("falla"):
        return "sin_dns"
    if str(claves.get("red_conexiones_nuevas", "")).startswith("0/"):
        return "sin_respuesta"
    if str(claves.get("red_resumen", "")).startswith("Red con problemas"):
        return "problemas"
    return "normal"


# Lo que se le dice al docente en la sala: qué revisar, no la técnica.
CONSEJOS = {
    "sin_dns": ("Este equipo no tiene internet",
                "No encuentra el servidor de LabSim. Revisa el cable de red o el wifi de este "
                "equipo. Si los otros equipos sí entran, el problema es de este."),
    "sin_respuesta": ("El servidor no responde desde este equipo",
                      "Hay internet, pero el servidor de LabSim no contesta. Si los otros equipos "
                      "tampoco entran, es el servidor o la red de la institución: espera unos "
                      "minutos y prueba de nuevo. Envía el reporte: si no sale ahora, queda "
                      "guardado y se envía solo después."),
    "problemas": ("La conexión está lenta o se corta",
                  "El servidor contesta, pero con cortes. LabSim reintenta solo: puede tardar más "
                  "en entrar o en abrir una atención. Si no logra entrar, espera un momento y "
                  "prueba de nuevo, y envía el reporte."),
    "normal": ("La conexión con el servidor está bien",
               "Si no se puede ingresar, revisa el usuario y la contraseña (o pide un código "
               "nuevo en la actividad del curso)."),
}
