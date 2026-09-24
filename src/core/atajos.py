"""Atajos de teclado del audiómetro y la impedanciometría.

Dos juegos de teclas:
- CONTROLADOR: las que manda el firmware del keyboard LabSim
  (firmware/labsim_keyboard). No se pueden cambiar desde la app: si se
  cambiaran, el controlador dejaría de manejar la acción.
- TECLADO: las del teclado del computador. Tienen un valor por defecto y
  cada alumno las puede cambiar en Configuración; lo suyo se guarda en su
  perfil (ver core/preferencias.py y UserPrefs.php en el backend) y lo
  sigue a cualquier equipo.

La diferencia de fondo entre los dos juegos es el dial: el encoder manda
's' al girar a la derecha (subir) y 'w' a la izquierda (bajar); en un
teclado lo intuitivo es lo contrario, W arriba y S abajo, como WASD.

Mantener los ids iguales a UserPrefs::ACCIONES en el backend.
"""

import re

from PySide6.QtGui import QKeySequence

AUDIOMETRO = "Audiómetro"
IMPEDANCIOMETRIA = "Impedanciometría"

# (id, grupo, descripción, tecla de teclado por defecto, tecla del controlador)
ACCIONES = (
    ("a_ch1_subir", AUDIOMETRO, "Canal 1: subir intensidad", "W", "S"),
    ("a_ch1_bajar", AUDIOMETRO, "Canal 1: bajar intensidad", "S", "W"),
    ("a_ch2_subir", AUDIOMETRO, "Canal 2: subir intensidad", "I", "I"),
    ("a_ch2_bajar", AUDIOMETRO, "Canal 2: bajar intensidad", "K", "K"),
    ("a_estimulo_ch1", AUDIOMETRO, "Canal 1: presentar estímulo (mantener)", "V", "V"),
    ("a_estimulo_ch2", AUDIOMETRO, "Canal 2: presentar estímulo (mantener)", "B", "B"),
    ("a_freq_menos", AUDIOMETRO, "Frecuencia: bajar", "A", "A"),
    ("a_freq_mas", AUDIOMETRO, "Frecuencia: subir", "D", "D"),
    ("a_salida_ch1", AUDIOMETRO, "Canal 1: cambiar salida", "1", "1"),
    ("a_tipo_estimulo_ch1", AUDIOMETRO, "Canal 1: cambiar tipo de estímulo", "2", "2"),
    ("a_transductor_ch1", AUDIOMETRO, "Canal 1: cambiar transductor", "3", "3"),
    ("a_salida_ch2", AUDIOMETRO, "Canal 2: cambiar salida", "8", "8"),
    ("a_tipo_estimulo_ch2", AUDIOMETRO, "Canal 2: cambiar tipo de estímulo", "7", "7"),
    ("a_transductor_ch2", AUDIOMETRO, "Canal 2: cambiar transductor", "6", "6"),
    ("z_subir", IMPEDANCIOMETRIA, "Subir presión (dial)", "W", "S"),
    ("z_bajar", IMPEDANCIOMETRIA, "Bajar presión (dial)", "S", "W"),
    ("z_estimulo", IMPEDANCIOMETRIA, "Presentar estímulo", "V", "V"),
)

IDS = tuple(a[0] for a in ACCIONES)
GRUPO = {a[0]: a[1] for a in ACCIONES}
DESCRIPCION = {a[0]: a[2] for a in ACCIONES}
POR_DEFECTO = {a[0]: a[3] for a in ACCIONES}
CONTROLADOR = {a[0]: a[4] for a in ACCIONES}

# Teclas fijas de cada módulo que no son configurables (botones de la
# interfaz con su propio atajo): no se pueden usar para otra acción.
RESERVADAS = {AUDIOMETRO: {"5", "E"}}

# Mismo criterio que UserPrefs::TECLA en el backend.
_TECLA_VALIDA = re.compile(r"^([A-Z0-9]|F([1-9]|1[0-2])|Up|Down|Left|Right|Space|PgUp|PgDown|Home|End)$")


def tecla_valida(texto):
    return bool(texto) and bool(_TECLA_VALIDA.match(texto))


def teclas(conectado, personalizados=None):
    """{acción: tecla} vigente. Con el controlador conectado mandan las del
    firmware; sin él, las del alumno encima de las por defecto."""
    if conectado:
        return dict(CONTROLADOR)
    mapa = dict(POR_DEFECTO)
    for accion, tecla in (personalizados or {}).items():
        if accion in mapa and tecla_valida(tecla):
            mapa[accion] = tecla
    return mapa


def qt_key(texto):
    """Qt.Key de una tecla escrita como la escribe QKeySequence ("W", "Up")."""
    return QKeySequence(texto)[0].key()


def conflictos(mapa):
    """Mensajes de error si dos acciones del mismo módulo comparten tecla o
    una usa una tecla reservada. Lista vacía = todo bien."""
    errores = []
    por_grupo = {}
    for accion, tecla in mapa.items():
        grupo = GRUPO.get(accion)
        if grupo is None:
            continue
        if not tecla_valida(tecla):
            errores.append(f"{DESCRIPCION[accion]}: la tecla «{tecla}» no se puede usar "
                           "(solo una letra, número, F1-F12, flechas o espacio, sin Ctrl/Alt).")
            continue
        if tecla in RESERVADAS.get(grupo, ()):
            errores.append(f"{DESCRIPCION[accion]}: «{tecla}» ya la usa otro botón del {grupo.lower()}.")
        por_grupo.setdefault((grupo, tecla), []).append(accion)
    for (grupo, tecla), acciones in por_grupo.items():
        if len(acciones) > 1:
            nombres = " y ".join(DESCRIPCION[a].lower() for a in acciones)
            errores.append(f"{grupo}: «{tecla}» está repetida ({nombres}).")
    return errores
