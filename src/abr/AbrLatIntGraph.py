
import os
import pyqtgraph as pg
from pyqtgraph import exporters
from core.base import context


class GraphLatInt(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super(GraphLatInt, self).__init__(parent)

        self.configure_pyqtgraph()
        self.setup_ui_elements()
        self.filled_area()

    def configure_pyqtgraph(self):
        color_background = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        self.setBackground(color_background)
    
    def setup_ui_elements(self):
        """Set up UI elements for the graph"""
        self.pw = self.addPlot(row=1,col=0)

        self.pw.setRange(yRange=(0, 12), xRange=(0, 100), disableAutoRange=True)
        self.pw.setLabels(left='ms', bottom='dBnHL')
        grid = pg.GridItem(pen=self.color_pen, textPen=self.color_pen)
        self.pw.addItem(grid)
        grid.setTickSpacing(x=[10], y=[1.0])

        self.pw.setMouseEnabled(x=False, y=False)
        self.pw.setMenuEnabled(False)
        self.pw.hideButtons()
        ay = self.pw.getAxis('left')
        ay.setStyle(showValues=False)
        # Inicializar la leyenda (solo I, III, V -- ver plot_data)
        self.legend = self.pw.addLegend()
        # Nota de color por oido: la leyenda muestra simbolo neutro por onda,
        # el color real (rojo/azul) va en los puntos graficados.
        note = pg.TextItem(
            html='<span style="color:#c0392b;">&#9679;</span> OD &nbsp; '
                 '<span style="color:#2980b9;">&#9679;</span> OI',
            anchor=(1, 1),
        )
        note.setPos(100, 0)
        self.pw.addItem(note)
    
    def filled_area(self):
        """Banda normativa de la onda V. Arranca vacia y la llena set_band().

        Los valores estaban escritos a mano (adulto): con la poblacion
        normativa siguiendo la edad del paciente, un neonato --cuya onda V
        corre casi 1 ms mas tarde-- quedaba SIEMPRE fuera de norma y el
        grafico dejaba de decir nada. Ahora la banda sale del mismo modelo
        que dibuja la curva (ABR_generator.latency_intensity_band).
        """
        self.curve_top = self.pw.plot([], [])
        self.curve_bottom = self.pw.plot([], [])
        # Marcadas para que remove_points() no las borre junto con los
        # puntos de captura -- son la banda normativa, no un dato.
        self.curve_top.is_band = True
        self.curve_bottom.is_band = True
        self.fill_between = pg.FillBetweenItem(self.curve_top, self.curve_bottom)
        self.fill_between.setBrush(pg.mkColor(100, 100, 250, 80))
        self.pw.addItem(self.fill_between)
        self.lbl_band = pg.TextItem(text='', color=(70, 70, 160), anchor=(0, 0))
        self.lbl_band.setPos(2, 11.6)
        self.pw.addItem(self.lbl_band)

    def set_band(self, x_vals, y_bottom_vals, y_top_vals, etiqueta=''):
        """Banda normativa de la poblacion del paciente en atencion."""
        self.curve_bottom.setData(list(x_vals), list(y_bottom_vals))
        self.curve_top.setData(list(x_vals), list(y_top_vals))
        self.fill_between.setCurves(self.curve_top, self.curve_bottom)
        self.lbl_band.setText(etiqueta)

    def plot_data(self, data_dict):
        # Solo I, III y V: son las ondas que realmente se comparan en la
        # funcion latencia-intensidad clinica (II y IV no se grafican aqui
        # aunque el alumno las haya marcado en la tabla).
        symbols = {
            'I': 'o',
            'III': 't1',
            'V': 't3',
        }
        colors = {
            'OD': (192, 57, 43),   # Rojo
            'OI': (41, 128, 185),  # Azul
        }

        # Puntos agrupados por onda: un solo PlotDataItem por onda (no uno
        # por punto) para que la leyenda tenga exactamente 3 entradas.
        points = {wave: {'x': [], 'y': [], 'brush': []} for wave in symbols}
        plotted_points = set()

        for curve_data in data_dict.values():
            side = curve_data.get('side')
            intensity = curve_data.get('int')
            if side not in colors or intensity is None:
                continue
            # Evita graficar dos veces la misma intensidad/oido (repeticion
            # de la captura a la misma intensidad).
            if (side, intensity) in plotted_points:
                continue

            lat_amp_dict = curve_data.get('LatAmp') or {}
            added_any = False
            for wave in symbols:
                lat_amp = lat_amp_dict.get(wave)
                if not lat_amp or lat_amp[0] is None:
                    continue
                points[wave]['x'].append(intensity)
                points[wave]['y'].append(lat_amp[0])
                points[wave]['brush'].append(colors[side])
                added_any = True

            if added_any:
                plotted_points.add((side, intensity))

        for wave, symbol in symbols.items():
            data = points[wave]
            if not data['x']:
                continue
            # Puntos reales, coloreados por oido, sin entrada propia en la
            # leyenda (el color va en el punto, no en el texto).
            self.pw.plot(
                data['x'], data['y'],
                symbol=symbol,
                pen=None,
                symbolBrush=data['brush'],
                symbolPen=None,
                symbolSize=9,
            )
            # Item "proxy" invisible en datos, solo para que la leyenda
            # muestre el simbolo de la onda una unica vez.
            self.pw.plot(
                [], [],
                symbol=symbol,
                pen=None,
                symbolBrush=(120, 120, 120),
                symbolPen=None,
                symbolSize=9,
                name=wave,
            )

    def clear_graph(self):
        self.legend.clear()
        self.remove_points()

    def remove_points(self):
        # Itera sobre los elementos del gráfico
        for item in list(self.pw.items):
            # Verifica si el elemento es una instancia de PlotDataItem
            if isinstance(item, pg.PlotDataItem) and not getattr(item, 'is_band', False):
                # Remueve solo los elementos que corresponden a los puntos
                self.pw.removeItem(item)
    
    def export_(self):
        import os
        width = self.pw.size().width()
        height = self.pw.size().height()
        export = exporters.ImageExporter(self.pw)

        temp_dir = context.get_resource("local_cache/abr/temp")
        output_file = os.path.join(temp_dir, 'LatInt.png')
        export.export(output_file)

    def export_jpg(self, path: str) -> None:
        """Como export_(), pero a JPEG (para subir el informe al backend --
        ver ReportFile.php, que solo acepta JPEG para no depender de GD)."""
        export = exporters.ImageExporter(self.pw)
        export.export(path)

if __name__ == '__main__':
    import pyqtgraph.examples
    pyqtgraph.examples.run()