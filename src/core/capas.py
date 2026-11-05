"""Ítems de pyqtgraph reutilizables entre redibujos (ver Capas)."""
import numpy as np
import pyqtgraph as pg


class Capas:
    """Los ítems de un gráfico, creados una sola vez y reutilizados.

    Para gráficos que se redibujan seguido (cada tick de un registro): en
    vez de `PlotItem.clear()` y volver a crear textos, líneas y puntos, cada
    redibujo pide los ítems por su papel (`tomar`), se les cambian los datos
    y el estilo, y lo que no se usó en esa pasada queda escondido. Ningún
    ítem se borra mientras viva el gráfico.

    Por qué: borrar y crear objetos de Qt con envoltura de PySide en cada
    tick es donde cayeron los tickets 35 y 43 (2026-11-05, ASSR), en
    `BindingManager::unregisterWrapper` al borrar un QGraphicsItem. Lo usan
    abr/AssrPanel.py y el módulo nasal (CPAP, rinomanometría).

    Uso: `empezar()`, `tomar(...)` las veces que haga falta, `terminar()`.
    """

    def __init__(self, plot):
        self.plot = plot
        self._items = {}    # papel -> [ítems, en orden de creación]
        self._usados = {}   # papel -> cuántos se usaron en esta pasada
        self._orden = 0

    def empezar(self):
        self._usados = {}
        self._orden = 0

    def tomar(self, papel, crear):
        lista = self._items.setdefault(papel, [])
        i = self._usados.get(papel, 0)
        if i == len(lista):
            item = crear()
            self.plot.addItem(item)
            lista.append(item)
        item = lista[i]
        self._usados[papel] = i + 1
        # Lo tomado después queda encima, como cuando se creaba todo en
        # cada pasada: sin esto mandaba el orden de creación (el OD tapaba
        # al OI si su línea había nacido después).
        self._orden += 1
        item.setZValue(self._orden)
        item.setVisible(True)
        return item

    def terminar(self):
        for papel, lista in self._items.items():
            for item in lista[self._usados.get(papel, 0):]:
                item.setVisible(False)

    def vaciar(self):
        self.empezar()
        self.terminar()

    # --- atajos por tipo de ítem ---------------------------------------
    def curva(self, papel, x, y, **estilo):
        """PlotDataItem con datos y estilo nuevos. Lo que no se pasa vuelve
        a su valor por defecto (relleno y símbolo apagados)."""
        item = self.tomar(papel, pg.PlotDataItem)
        opciones = dict(fillLevel=None, brush=None, symbol=None)
        opciones.update(estilo)
        item.setData(np.asarray(x, dtype=float), np.asarray(y, dtype=float),
                     **opciones)
        return item

    def puntos(self, papel, x, y, **estilo):
        item = self.tomar(papel, pg.ScatterPlotItem)
        item.setData(x=list(x), y=list(y), **estilo)
        return item

    def linea(self, papel, pos, angle, pen):
        item = self.tomar(papel, lambda: pg.InfiniteLine(angle=angle, movable=False))
        item.setAngle(angle)
        item.setPos(pos)
        item.setPen(pen)
        return item

    def texto(self, papel, texto, pos, color, anchor, font):
        """TextItem: el ancla y la letra (None = la de pyqtgraph) se fijan
        al crearlo, así que cada papel debe usar siempre las mismas."""
        def crear():
            item = pg.TextItem("", anchor=anchor)
            if font is not None:
                item.setFont(font)
            return item
        item = self.tomar(papel, crear)
        item.setText(texto, color=color)
        item.setPos(*pos)
        return item
