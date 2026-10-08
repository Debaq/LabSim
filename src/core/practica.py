"""
Práctica deliberada del lado de la app: lo que comparten la agenda (modo
"Práctica libre") y Mis pacientes. La lista y los intentos viven en el
backend (labsim_backend/src/Practica.php); cada intento es una cita propia
del alumno, así que atenderla y cerrarla es el mismo camino de siempre.
"""
import tempfile
from pathlib import Path

import requests
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from core.helpers import ficha_estudio_pdf


def abrir_ficha_estudio(parent, appointment_id):
    """Baja la ficha de estudio (PDF) de un intento cerrado y la abre con el
    visor del sistema. Avisa si no se pudo, sin lanzar."""
    try:
        contenido = ficha_estudio_pdf(int(appointment_id))
    except requests.RequestException as exc:
        QMessageBox.warning(parent, "Ficha de estudio",
                            f"No se pudo traer la ficha de estudio.\n\n{exc}")
        return
    carpeta = Path(tempfile.mkdtemp(prefix="labsim_ficha_"))
    ruta = carpeta / f"ficha_estudio_{int(appointment_id)}.pdf"
    ruta.write_bytes(contenido)
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta))):
        QMessageBox.information(parent, "Ficha de estudio",
                                f"La ficha quedó guardada en:\n{ruta}")
