"""Tabla de medidas de la electrococleografía.

La tabla del ABR (AbrTable) no sirve para esto: ahí se miden cinco ondas
con sus latencias, sus interpicos y la razón V/I. Acá se miden tres
potenciales y lo que se informa son RAZONES entre dos de ellos.

El alumno arma la medida poniendo cuatro marcas sobre el trazo (barra de
arriba, clic sobre la curva):

    BL   línea de base, en el tramo previo a la respuesta
    PS   hombro del potencial de sumación
    PA   pico del potencial de acción
    FIN  donde el complejo vuelve a la línea de base

Con BL, PS y PA ya hay razón de amplitudes; el área y el ancho del complejo
necesitan además el retorno. Lo que falta se dice en la celda, porque un
número que no aparece sin explicación se lee como "este examen no lo
tiene".

El corrimiento por tasa no es una medida de una curva sola: sale de
comparar la curva más lenta con la más rápida que el alumno haya
registrado en ese oído (ver ecochg.rate_shift).
"""
# pylint: disable=no-name-in-module
from PySide6.QtCore import QCoreApplication, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QToolButton,
                               QVBoxLayout, QWidget)

from abr import ecochg

tr = QCoreApplication.translate


# Fila de la tabla -> (rótulo, clave de la medida, unidad, decimales).
# `None` en la clave = fila calculada desde el corrimiento por tasa.
FILAS = (
    ("Amplitud PS", 'sp_amp', "µV", 2),
    ("Amplitud PA", 'ap_amp', "µV", 2),
    ("Razón PS/PA", 'sp_ap', "", 3),
    ("Razón de áreas", 'area_ratio', "", 2),
    ("Latencia PA", 'ap_lat', "ms", 2),
    ("Ancho PA", 'ancho_pa', "ms", 2),
    ("Duración complejo", 'ancho', "ms", 2),
    ("Δ latencia por tasa", 'd_lat', "ms", 2),
    ("Δ amplitud por tasa", 'd_amp_pct', "%", 0),
)

# Qué marca hace falta para que cada medida exista. Lo que no está acá sale
# con las tres primeras.
REQUIERE = {
    'area_ratio': 'FIN',
    'ancho': 'FIN',
}


class EcochgTable(QWidget):
    """Medidas del ECochG de un oído, con la barra de marcas."""

    # Marca que el alumno dejó armada (o None al desarmarla): el gráfico la
    # pone donde haga clic.
    sig_arm_mark = Signal(int, object)

    OUT_COLOR = QColor(255, 120, 120, 170)

    def __init__(self, side) -> None:
        QWidget.__init__(self)
        self.side = side
        self.side_text = 'OD' if side == 0 else 'OI'
        self.norms = {}
        self.medidas = {}
        self._build()

    # ------------------------------------------------------------ armado

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        cabecera = QHBoxLayout()
        self.label = QLabel(self.side_text)
        cabecera.addWidget(self.label)
        cabecera.addStretch(1)
        # No exclusivo: el mismo botón arma y desarma la marca, y volver a
        # apretarlo tiene que soltarla (con un grupo exclusivo, Qt no deja
        # destildar el que ya está tildado).
        self.botones = QButtonGroup(self)
        self.botones.setExclusive(False)
        for marca in ecochg.MARKS:
            btn = QToolButton(self)
            btn.setText(marca)
            btn.setCheckable(True)
            btn.setToolTip(ecochg.MARK_LABELS[marca])
            self.botones.addButton(btn)
            btn.clicked.connect(lambda _=False, m=marca: self._armar(m))
            cabecera.addWidget(btn)
        layout.addLayout(cabecera)

        self.tabla = QTableWidget(len(FILAS), 1, self)
        self.tabla.setVerticalHeaderLabels([f[0] for f in FILAS])
        self.tabla.setHorizontalHeaderLabels(["Valor"])
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        color = 'rgba(255, 0, 127, 30)' if self.side == 0 else '#9965f4'
        self.tabla.setStyleSheet(
            f"QTableWidget::item{{ background-color:{color}; }}")
        layout.addWidget(self.tabla)
        self.clear_all()

    def _armar(self, marca) -> None:
        """Arma o desarma una marca (el mismo botón hace las dos cosas)."""
        pulsado = None
        for btn in self.botones.buttons():
            if btn.text() == marca:
                pulsado = btn
            else:
                btn.setChecked(False)
        activa = marca if (pulsado is not None and pulsado.isChecked()) else None
        self.sig_arm_mark.emit(self.side, activa)

    def armed(self):
        """Marca armada en este momento, o None."""
        for btn in self.botones.buttons():
            if btn.isChecked():
                return btn.text()
        return None

    def disarm(self) -> None:
        """Suelta la marca armada (después de ponerla o de cambiar de curva)."""
        for btn in self.botones.buttons():
            btn.setChecked(False)

    # ------------------------------------------------------------ valores

    def set_norms(self, norms) -> None:
        self.norms = norms or {}
        self._pintar()

    def set_medidas(self, medidas) -> None:
        """Medidas de la curva seleccionada (ecochg.measure_complex)."""
        self.medidas = dict(medidas or {})
        self._pintar()

    def set_rate_shift(self, shift) -> None:
        """Corrimiento por tasa del oído (ecochg.rate_shift), o None."""
        for clave in ('d_lat', 'd_amp_pct'):
            self.medidas.pop(clave, None)
        if shift:
            self.medidas.update({'d_lat': shift['d_lat'],
                                 'd_amp_pct': shift['d_amp_pct']})
            self.medidas['tasas'] = (shift['rate_lenta'], shift['rate_rapida'])
        self._pintar()

    def clear_all(self) -> None:
        self.medidas = {}
        self._pintar()

    # ------------------------------------------------------------ pintado

    def _pintar(self) -> None:
        faltan = set(self.medidas.get('faltan') or ())
        for fila, (_, clave, unidad, dec) in enumerate(FILAS):
            valor = self.medidas.get(clave)
            item = QTableWidgetItem()
            if valor is None:
                item.setText("")
                falta = REQUIERE.get(clave)
                if clave in ('d_lat', 'd_amp_pct'):
                    item.setToolTip("Necesita dos curvas de este oído a "
                                    "distinta tasa")
                elif falta and (falta in faltan or not self.medidas):
                    item.setToolTip(f"Falta la marca {falta} "
                                    f"({ecochg.MARK_LABELS[falta]})")
                elif faltan:
                    item.setToolTip("Faltan marcas: " + ", ".join(sorted(faltan)))
            else:
                texto = f"{valor:.{dec}f}"
                item.setText(f"{texto} {unidad}".strip())
                self._flag(item, clave, valor)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(fila, 0, item)
        # La fila del corrimiento dice entre qué dos tasas se comparó: sin
        # eso el número no se puede leer (0.3 ms entre 11 y 21/s y entre 11
        # y 91/s no significan lo mismo).
        tasas = self.medidas.get('tasas')
        fila = [f[1] for f in FILAS].index('d_lat')
        rotulo = FILAS[fila][0]
        if tasas:
            rotulo += f" ({tasas[0]:.0f}→{tasas[1]:.0f}/s)"
        self.tabla.setVerticalHeaderItem(fila, QTableWidgetItem(rotulo))

    def _flag(self, item, clave, valor) -> None:
        rango = self.norms.get(clave)
        if not rango:
            return
        lo, hi = rango
        dentro = ((lo is None or valor >= lo) and (hi is None or valor <= hi))
        if dentro:
            return
        if lo is None:
            texto = f"esperado ≤ {hi:.2f}"
        elif hi is None:
            texto = f"esperado ≥ {lo:.2f}"
        else:
            texto = f"esperado {lo:.2f} – {hi:.2f}"
        item.setBackground(self.OUT_COLOR)
        item.setToolTip(f"Fuera de rango: {texto}")
