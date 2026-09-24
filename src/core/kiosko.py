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
"""

import os


def es_kiosko():
    return os.environ.get("LABSIM_KIOSKO", "").strip() == "1"
