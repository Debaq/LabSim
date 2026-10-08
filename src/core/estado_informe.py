"""Aviso de guardado del informe, igual en todos los módulos de examen.

El informe se sube solo mientras se atiende (ver core/report_autosave.py):
no hay botón "Guardar". Lo que el alumno necesita es saber que quedó
guardado, o por qué no, y verlo en el mismo lugar donde escribe. Cada
módulo pone un EstadoInforme bajo su conclusión y el autoguardado lo
actualiza después de cada subida.
"""
from datetime import datetime

from PySide6.QtWidgets import QLabel


# Rótulo corto por tipo, para el módulo que sube más de uno (ABR + ECochG).
ROTULOS = {"ABR": "ABR", "ELECTROCOCLEO": "ECochG", "AABR": "AABR",
           "EOA": "EOA", "VEMP": "VEMP", "OTOSCOPIA": "Otoscopia"}


class EstadoInforme(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self._estado = {}   # tipo -> (ok, hora, error)
        self.limpiar()

    def limpiar(self):
        """Atención nueva: lo de la anterior no dice nada de esta."""
        self._estado.clear()
        self.setText("El informe se guarda solo mientras atiendes.")
        self.setStyleSheet("color: #666666;")

    def guardado(self, tipo, ok, error=""):
        self._estado[tipo] = (ok, datetime.now().strftime("%H:%M"), error)
        varios = len(self._estado) > 1
        lineas = []
        for t, (bien, hora, err) in self._estado.items():
            prefijo = f"{ROTULOS.get(t, t)}: " if varios else ""
            if bien:
                lineas.append(f"{prefijo}informe guardado a las {hora}.")
            else:
                lineas.append(f"{prefijo}no se pudo guardar a las {hora} "
                              f"({(err or 'sin conexión')[:80]}). Se reintenta solo.")
        self.setText("\n".join(lineas))
        todo_bien = all(bien for bien, _, _ in self._estado.values())
        self.setStyleSheet("color: #27ae60;" if todo_bien else "color: #c0392b;")
