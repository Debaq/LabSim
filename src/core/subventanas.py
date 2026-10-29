"""Las subventanas del MDI por nombre (MainWindow.subw), con módulos diferidos.

Armar todos los módulos de examen en el login congelaba la ventana unos
2,6 s (2026-10-28: EOAS 0,8, ABR 0,7, VEMP, audiómetro y Z 0,3 cada uno).
Ahora main deja los pesados como pendientes y los arma de a uno por vuelta
del bucle de eventos, con la agenda ya a la vista (ver
MainWindow._armar_modulos_en_fondo).

Si algo pide uno que todavía no está (un clic en su botón, `subw["ABR"]`),
se arma en ese momento: nadie tiene que saber cuáles faltan. `get()` no
arma: devuelve lo que ya hay (quien pregunta con get solo quiere saber si
está a la vista). `in` cuenta también los pendientes.
"""


class Subventanas(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pendientes = {}   # nombre -> (crear() -> FrameSubMdi, despues(frame) o None)

    def pendiente(self, nombre, crear, despues=None):
        """`despues` corre con el módulo ya guardado: puede pedir `self[nombre]`."""
        self._pendientes[nombre] = (crear, despues)

    def faltan(self) -> list:
        return list(self._pendientes)

    def construir(self, nombre):
        pendiente = self._pendientes.pop(nombre, None)
        if pendiente is not None and not dict.__contains__(self, nombre):
            crear, despues = pendiente
            frame = crear()
            dict.__setitem__(self, nombre, frame)
            if despues is not None:
                despues(frame)
        return dict.get(self, nombre)

    def construir_siguiente(self) -> bool:
        """Arma el próximo pendiente. True si quedan más."""
        if self._pendientes:
            self.construir(next(iter(self._pendientes)))
        return bool(self._pendientes)

    def construir_todo(self):
        while self._pendientes:
            self.construir(next(iter(self._pendientes)))

    def cancelar(self):
        """Se cerró la sesión: lo que faltaba ya no se arma."""
        self._pendientes.clear()

    def __missing__(self, nombre):
        if nombre in self._pendientes:
            return self.construir(nombre)
        raise KeyError(nombre)

    def __contains__(self, nombre):
        return dict.__contains__(self, nombre) or nombre in self._pendientes
