"""Texto centrado sobre un gráfico del impedanciómetro.

Lo usan los avisos que reemplazan a una curva: el oído donde la sonda no va
(impedanciometría no realizable, ver z_generator.oido_no_realizable).
"""
import pyqtgraph as pg


class AvisoGrafico:
    def __init__(self, pw, color='y'):
        self.pw = pw
        self.item = pg.TextItem("", color=color, anchor=(0.5, 0.5))
        self.item.setVisible(False)

    def mostrar(self, texto, grave=False):
        # set_prueba de la ETF limpia el gráfico entero (pw.clear()) y se
        # lleva el texto con lo demás: se vuelve a poner si hace falta.
        if self.item not in self.pw.getPlotItem().items:
            self.pw.addItem(self.item, ignoreBounds=True)
        (x0, x1), (y0, y1) = self.pw.viewRange()
        if grave:
            # Falta grave: en rojo, sobre fondo blanco, que no se confunda
            # con un rótulo del equipo.
            lineas = texto.split("\n")
            cuerpo = "<br>".join(lineas[1:])
            self.item.setHtml(
                '<div style="background:#fff; color:#c00000; padding:6px; text-align:center;">'
                f'<b style="font-size:13pt;">{lineas[0]}</b><br>{cuerpo}</div>')
        else:
            self.item.setText(texto)
        self.item.setPos((x0 + x1) / 2, (y0 + y1) / 2)
        self.item.setVisible(True)

    def ocultar(self):
        self.item.setVisible(False)
