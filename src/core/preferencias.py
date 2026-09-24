"""Preferencias personales del usuario logueado: atajos de teclado propios
y "mouse para zurdos".

Viven en su cuenta del backend (users.prefs, ver UserPrefs.php), no en el
equipo: llegan con el login y se guardan desde Configuración, así que el
alumno las encuentra en cualquier computador del laboratorio.

Los módulos escuchan `cambiaron` para rearmar sus atajos (audiómetro,
impedanciometría) y core/mouse_zurdo.py para invertir o no los botones.
"""

from PySide6.QtCore import QObject, Signal

from core import atajos


def _normalizar(prefs):
    prefs = prefs if isinstance(prefs, dict) else {}
    propios = prefs.get("atajos") if isinstance(prefs.get("atajos"), dict) else {}
    return {
        "mouse_zurdo": bool(prefs.get("mouse_zurdo")),
        "atajos": {k: v for k, v in propios.items()
                   if k in atajos.IDS and atajos.tecla_valida(v)},
    }


class PreferenciasUsuario(QObject):
    cambiaron = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prefs = _normalizar({})

    def cargar(self, prefs):
        """Las del login (o las que devolvió el servidor al guardar)."""
        self._prefs = _normalizar(prefs)
        self.cambiaron.emit()

    def limpiar(self):
        """Cierre de sesión: el próximo que entre no hereda las del anterior."""
        self.cargar({})

    def atajos(self):
        return dict(self._prefs["atajos"])

    def mouse_zurdo(self):
        return self._prefs["mouse_zurdo"]

    def como_dict(self):
        return {"mouse_zurdo": self.mouse_zurdo(), "atajos": self.atajos()}

    def guardar(self, prefs):
        """Guarda en el servidor y aplica lo que quedó guardado. (ok, mensaje)."""
        from core.helpers import guardar_preferencias
        try:
            guardadas = guardar_preferencias(_normalizar(prefs))
        except Exception as exc:  # noqa: BLE001 -- se informa en el diálogo
            return False, f"No se pudieron guardar en el servidor: {exc}"
        self.cargar(guardadas)
        return True, "Guardado en tu perfil."


_unica = None


def preferencias():
    global _unica
    if _unica is None:
        _unica = PreferenciasUsuario()
    return _unica
