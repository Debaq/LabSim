"""Modo laboratorio (kiosko): computadores compartidos del laboratorio.

Se activa con la variable de entorno LABSIM_KIOSKO=1, que define quien
administra el equipo (no la app). Es el único lugar donde se lee.

Qué cambia en un kiosko:
- El "mouse para zurdos" del perfil del alumno se aplica dentro de LabSim
  (core/mouse_zurdo.py). En un computador personal no: ahí el alumno lo
  configura en el sistema, y si LabSim lo invirtiera otra vez quedaría al
  derecho.
- Las actualizaciones se aplican sin preguntar (main._auto_update_forzado):
  el alumno podía decir "No" siempre y las máquinas quedaban viejas.
- Al apagar el equipo (SIGTERM) la app cierra en orden y guarda lo abierto
  (atender_apagado), aunque el alumno no pueda cerrarla.
"""

import os
import signal
import sys
import threading

from PySide6.QtCore import QTimer


# apagar.sh espera 15 s a que LabSim salga; systemd, después, lo mata con
# SIGKILL. Pasado este plazo se sale igual, con lo que se haya alcanzado a
# subir (los logs pendientes siguen en la cola local para la próxima vez).
PLAZO_APAGADO_S = 12


def es_kiosko():
    return os.environ.get("LABSIM_KIOSKO", "").strip() == "1"


def atender_apagado(cerrar):
    """SIGTERM (apagar.sh, systemd al apagar) llama a `cerrar` en el hilo
    de Qt en vez de matar la app al instante, que perdía el informe en
    curso. Solo en el laboratorio, que es Linux: en Windows no hay kiosko
    ni SIGTERM al apagar.

    Devuelve el temporizador "despertador" (o None): hay que guardarlo, si
    se recolecta deja de andar. Python atiende las señales solo cuando corre
    código Python, y con la app quieta el que corre es el bucle de Qt (C++):
    sin este tic la señal esperaría hasta el próximo clic.
    """
    if sys.platform == "win32" or not es_kiosko():
        return None
    recibida = []

    def al_recibir(_signum, _frame):
        # apagar.sh y después systemd pueden mandar una cada uno.
        if recibida:
            return
        recibida.append(True)
        # Si el cierre se traba (red colgada, un hilo que no para), se sale
        # igual antes del SIGKILL.
        guardia = threading.Timer(PLAZO_APAGADO_S, os._exit, args=(0,))
        guardia.daemon = True
        guardia.start()
        # El trabajo, fuera del manejador: apenas Qt pueda.
        QTimer.singleShot(0, cerrar)

    signal.signal(signal.SIGTERM, al_recibir)
    despertador = QTimer()
    despertador.timeout.connect(lambda: None)
    despertador.start(500)
    return despertador
