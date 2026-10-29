"""La rinoscopía anterior en LabSim (H25): el paciente, el espéculo y el
informe por fosa, como la otoscopía.

El paciente de frente, como lo ve el examinador (la cabeza de
labyrinthus3d fotografiada reclinándose de 0° a 60° cada 2°:
scripts/nasal/cara_rinoscopia.py). Al lado derecho, "Reclinar": las
flechas, mantenidas apretadas, echan la cabeza hacia atrás o la devuelven,
suave.

El espéculo es el mouse: sobre una narina aparece, y encima de la cara se
abre lo que se ve por él en esa fosa y con la cabeza en esa posición.
Moviéndolo un poco dentro de la narina se recorre la fosa (se inclina el
espéculo). La fosa la elige la narina: la derecha del paciente queda a la
izquierda del examinador.

Lo que se ve lo dibuja nasal/rinoscopia.py desde la nariz del caso (la
misma de la rinomanometría y la rinometría, nasal/sesion.py): si el alumno
puso vasoconstrictor en la RM, el cornete se ve retraído también aquí.
Se calcula cada 10° (recta, 10°, ..., 60°): la cabeza se reclina de a 2° y
el interior muestra el cálculo más cercano.

El módulo anota solo en qué orden miró las fosas y en qué posiciones de la
cabeza (una posición cuenta cuando pasó el espéculo por la narina), que es
lo que pide H25: "primero la fosa derecha", "cabeza recta, 30° y 60°". Va
en el informe para el docente, sin avisarle nada al alumno.

Cada imagen tarda un par de segundos: se calculan fuera de la ventana,
primero la que se pide y después las demás, y quedan guardadas en el equipo
(local_cache/nasal/rinoscopia) para la próxima vez.

Demo interna (docs/roadmap_nasal.md): solo el admin abre el módulo.
Sin `cases.data['NASAL']` no hay nariz que mirar.
"""

import hashlib
import json
import os

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QPlainTextEdit, QPushButton,
                               QScrollArea, QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

from core import hilos, iconos, tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import rinoscopia, sesion
from vemp.widgets.kit import Campos, Tarjeta, etiqueta

LADOS = (('D', 'Fosa derecha', 'FND'), ('I', 'Fosa izquierda', 'FNI'))
POSICIONES = (0, 30, 60)
ANGULOS = tuple(range(0, 61, 10))     # el interior se calcula cada 10°
TAM = 320
CAMPO = 1.15                          # cuánto más que la narina abarca el campo
NEGRO_VISOR = QColor('#0E0A0D')
METAL = '#8E9098'

PASO_RECLINAR = 2                     # grados por paso de las flechas
REPETIR_MS = 70                       # cada cuánto avanza con la flecha apretada
RADIO_NARINA = 13.0                   # px de la foto de 600: dónde "entra" el espéculo
LUPA = 0.27                           # radio del círculo, en fracción del lado de la cara
RECORTE = 0.62                        # qué parte del campo calculado entra en el círculo
BATA = '#A9C4C8'

# Lo que el alumno informa por fosa: (clave, rótulo, opciones (clave, texto)).
CAMPOS_INFORME = [
    ('tabique', 'Tabique', [('', '—'), ('centrado', 'Centrado'), ('desviado', 'Desviado hacia esta fosa'),
                            ('espolon', 'Espolón'), ('no_se_ve', 'No se ve')]),
    ('cornete_inferior', 'Cornete inferior', [('', '—'), ('normal', 'Normal'), ('hipertrofico', 'Hipertrófico'),
                                              ('contacta', 'Contacta el tabique'), ('no_se_ve', 'No se ve')]),
    ('cornete_medio', 'Cornete medio', [('', '—'), ('normal', 'Normal'), ('aumentado', 'Aumentado'),
                                        ('no_se_ve', 'No se ve')]),
    ('meato_medio', 'Meato medio', [('', '—'), ('libre', 'Libre'), ('polipos', 'Pólipos'),
                                    ('secrecion', 'Secreción'), ('no_se_ve', 'No se ve')]),
    ('mucosa', 'Mucosa', [('', '—')] + [(k, v[0]) for k, v in rinoscopia.MUCOSAS.items()]),
    ('secrecion', 'Secreción', [('', '—')] + [(k, v[0]) for k, v in rinoscopia.SECRECIONES.items()]),
]


def _carpeta_cache():
    ruta = context.get_resource('local_cache/nasal/rinoscopia')
    os.makedirs(ruta, exist_ok=True)   # en el build no existe local_cache/*
    return ruta


def _clave(fosa, lado, grados):
    """Identifica una imagen: la misma fosa en la misma posición sale igual."""
    crudo = json.dumps([rinoscopia.VERSION, TAM, CAMPO, lado, grados, round(fosa.vol_ci, 3), fosa.dev,
                        fosa.concavo, fosa.polipos, fosa.perf, fosa.aspecto, round(fosa.r_cm, 3)],
                       sort_keys=True, default=str)
    return hashlib.blake2b(crudo.encode(), digest_size=12).hexdigest()


def _calcular(fosa, lado, grados, ruta):
    """Fuera de la ventana: la imagen, de la caché del equipo o calculada
    (y guardada)."""
    if os.path.exists(ruta):
        img = QImage(ruta)
        if not img.isNull():
            return img
    arr = rinoscopia.render(fosa, grados, TAM, espejo=(lado == 'I'), campo=CAMPO)
    img = QImage(arr.data, TAM, TAM, 3 * TAM, QImage.Format.Format_RGB888).copy()
    try:
        img.save(ruta, 'PNG')
    except Exception as exc:  # noqa: BLE001 -- sin caché igual se ve
        print(f'rinoscopía: no se pudo guardar {ruta}: {exc}')
    return img


_cara = None


def cara():
    """resources/rinoscopia: los cuadros de la cara y dónde caen las narinas."""
    global _cara
    if _cara is None:
        with open(context.get_resource('rinoscopia/cara.json'), encoding='utf-8') as f:
            info = json.load(f)
        with open(context.get_resource('rinoscopia/cara.bin'), 'rb') as f:
            info['bin'] = f.read()
        _cara = info
    return _cara


class Cara(QWidget):
    """El paciente de frente. Con el mouse sobre una narina aparece el
    espéculo y, encima de la cara, lo que se ve por él."""

    miro = Signal(str)          # la fosa ('D' o 'I') por la que pasó el espéculo

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grados = 0
        self.interior = {}      # lado -> QPixmap de lo que se ve, o None si se está calculando
        self.activa = False     # hay paciente con nariz
        self._fotos = {}
        self._mouse = None
        self._fosa = None       # la narina bajo el mouse
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def set_grados(self, grados):
        self.grados = grados
        self.update()

    def set_interior(self, lado, pixmap):
        self.interior[lado] = pixmap
        self.update()

    def _foto(self):
        g = str(self.grados)
        if g not in self._fotos:
            d = cara()
            ini, largo = d['indice'][g]
            self._fotos[g] = QPixmap.fromImage(QImage.fromData(d['bin'][ini:ini + largo], 'WEBP'))
        return self._fotos[g]

    def _marco(self):
        lado = min(self.width(), self.height())
        return QRectF((self.width() - lado) / 2, (self.height() - lado) / 2, lado, lado), lado / cara()['tam']

    def _narinas(self):
        """Dónde cae cada narina en pantalla, en este cuadro."""
        marco, k = self._marco()
        fila = cara()['cuadros'][str(self.grados)]
        return {l: QPointF(marco.x() + fila[l][0] * k, marco.y() + fila[l][1] * k) for l in ('D', 'I')}, k

    def fosa_bajo(self, pos):
        narinas, k = self._narinas()
        lado = min(narinas, key=lambda l: (narinas[l] - pos).manhattanLength())
        d = narinas[lado] - pos
        return lado if (d.x() ** 2 + d.y() ** 2) ** 0.5 <= RADIO_NARINA * k else None

    def mouseMoveEvent(self, evento):
        self._mouse = evento.position()
        self._fosa = self.fosa_bajo(self._mouse) if self.activa else None
        self.setCursor(Qt.CursorShape.BlankCursor if self._fosa else Qt.CursorShape.ArrowCursor)
        if self._fosa:
            self.miro.emit(self._fosa)
        self.update()
        super().mouseMoveEvent(evento)

    def leaveEvent(self, evento):
        self._mouse = self._fosa = None
        self.update()
        super().leaveEvent(evento)

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        marco, k = self._marco()
        p.drawPixmap(marco, self._foto(), QRectF(0, 0, cara()['tam'], cara()['tam']))
        self._pintar_bata(p, marco, k)
        if self._fosa and self._mouse is not None:
            self._pintar_especulo(p, marco, k)
        p.end()

    def _pintar_bata(self, p, marco, k):
        """El modelo termina en el cuello: al reclinar asoma el corte. Los
        hombros con la bata lo tapan, hasta justo debajo del borde."""
        x0, x1, y = cara()['cuadros'][str(self.grados)]['cuello']
        arriba = marco.y() + (y - 8) * k
        if arriba > marco.bottom():
            return
        # Centrada en la cara (el borde del modelo no es simétrico).
        mitad = max(cara()['tam'] / 2 - x0, x1 - cara()['tam'] / 2) + 6
        medio = marco.center().x()
        izq, der = medio - mitad * k, medio + mitad * k
        hombro = arriba + 90 * k
        ancho = self.width()
        bata = QPainterPath()
        bata.moveTo(-2, self.height() + 2)
        bata.lineTo(-2, hombro + 60 * k)
        bata.cubicTo(medio - 300 * k, hombro, izq - 50 * k, hombro, izq, arriba)
        bata.lineTo(der, arriba)
        bata.cubicTo(der + 50 * k, hombro, medio + 300 * k, hombro, ancho + 2, hombro + 60 * k)
        bata.lineTo(ancho + 2, self.height() + 2)
        bata.closeSubpath()
        p.setPen(QPen(QColor('#8FAFB4'), 1.2))
        p.setBrush(QColor(BATA))
        p.drawPath(bata)
        # El escote, una línea un poco más oscura.
        p.setPen(QPen(QColor('#8FAFB4'), 2))
        p.drawLine(QPointF(izq, arriba + 2), QPointF(der, arriba + 2))

    def _pintar_especulo(self, p, marco, k):
        lado = self._fosa
        narinas, _ = self._narinas()
        centro = narinas[lado]
        # El espéculo en la narina (pequeño, plateado) ...
        p.setPen(QPen(QColor(METAL), 2.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(centro, 9 * k, 11 * k)
        # ... y lo que se ve por él, en grande al costado de esa fosa (la
        # derecha del paciente hacia mi izquierda), sin tapar la narina.
        r = marco.width() * LUPA
        hacia = -1 if lado == 'D' else 1
        c = QPointF(centro.x() + hacia * (r + 40 * k), centro.y() - r * 0.15)
        c.setX(max(r + 6, min(self.width() - r - 6, c.x())))
        c.setY(max(r + 6, min(self.height() - r - 6, c.y())))
        p.setPen(QPen(QColor(METAL), 1.6, Qt.PenStyle.DashLine))
        p.drawLine(centro, c + (centro - c) * (r / max(1.0, ((centro - c).x() ** 2 + (centro - c).y() ** 2) ** 0.5)))
        circulo = QPainterPath()
        circulo.addEllipse(c, r, r)
        p.save()
        p.setClipPath(circulo)
        p.fillRect(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), NEGRO_VISOR)
        img = self.interior.get(lado)
        if img is None:
            p.setPen(QColor(tema.TEXTO_TENUE))
            p.drawText(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), Qt.AlignmentFlag.AlignCenter,
                       'Acomodando el espéculo…')
        else:
            # Mover el mouse dentro de la narina inclina el espéculo: se
            # recorre el campo calculado.
            d = self._mouse - centro
            dx = max(-1.0, min(1.0, d.x() / (RADIO_NARINA * k)))
            dy = max(-1.0, min(1.0, d.y() / (RADIO_NARINA * k)))
            w = img.width() * RECORTE
            libre = (img.width() - w) / 2
            fuente = QRectF(libre + dx * libre, libre + dy * libre, w, w)
            p.drawPixmap(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), img, fuente)
            luz = QRadialGradient(c, r)
            luz.setColorAt(0.0, QColor(255, 220, 150, 35))
            luz.setColorAt(0.7, QColor(0, 0, 0, 0))
            luz.setColorAt(1.0, QColor(NEGRO_VISOR.red(), NEGRO_VISOR.green(), NEGRO_VISOR.blue(), 230))
            p.fillRect(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), luz)
        p.restore()
        aro = max(5.0, r * 0.05)
        p.setPen(QPen(QColor(METAL), aro))
        p.drawEllipse(c, r + aro / 2, r + aro / 2)
        p.setPen(QPen(QColor(255, 255, 255, 110), aro * 0.35))
        p.drawArc(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), 40 * 16, 70 * 16)
        p.setPen(QColor(tema.TARJETA))
        p.drawText(QRectF(c.x() - r, c.y() + r * 0.72, 2 * r, r * 0.2), Qt.AlignmentFlag.AlignCenter,
                   'Fosa derecha' if lado == 'D' else 'Fosa izquierda')


class PanelFosa(Tarjeta):
    """Lo que el alumno dice haber visto en una fosa."""

    def __init__(self, lado, titulo):
        super().__init__(titulo)
        self.lado = lado
        campos = Campos()
        self.combos = {}
        for clave, rotulo, opciones in CAMPOS_INFORME:
            combo = QComboBox()
            for valor, texto in opciones:
                combo.addItem(texto, valor)
            self.combos[clave] = campos.agregar(rotulo, combo)
        self.chk_perforacion = campos.agregar_ancho(QCheckBox('Perforación septal'))
        self.agregar(campos)
        self.agregar(etiqueta('Observaciones', rol='campo'))
        self.txt_obs = QPlainTextEdit()
        self.txt_obs.setFixedHeight(70)
        self.agregar(self.txt_obs)

    def limpiar(self):
        for combo in self.combos.values():
            combo.setCurrentIndex(0)
        self.chk_perforacion.setChecked(False)
        self.txt_obs.clear()

    def to_dict(self):
        d = {clave: combo.currentData() for clave, combo in self.combos.items()}
        d['perforacion'] = self.chk_perforacion.isChecked()
        d['observaciones'] = self.txt_obs.toPlainText()
        return d

    def tiene_algo(self):
        d = self.to_dict()
        return any(d[c] for c, _r, _o in CAMPOS_INFORME) or d['perforacion'] or d['observaciones'].strip()

    def from_dict(self, d):
        for clave, combo in self.combos.items():
            i = combo.findData(d.get(clave) or '')
            combo.setCurrentIndex(max(0, i))
        self.chk_perforacion.setChecked(bool(d.get('perforacion')))
        self.txt_obs.setPlainText(d.get('observaciones') or '')


class RinoscopiaWindow(QWidget):
    TIPO = 'RINOSCOPIA'

    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.sesion = None
        self.nasal = None
        self.appointment_id = None
        self.grados = 0
        self.imagenes = {}      # (lado, grados, vc) -> QPixmap
        self.cola = []          # (lado, grados) por calcular, la primera es la que se pide
        self.tarea = None
        self.calculando = None
        self.vistas = []        # (lado, grados) en el orden en que el alumno los miró
        tema.aplicar_estilo(self)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 8, 12, 12)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._pestana_visor(), iconos.icono('nariz', tema.TEXTO_TENUE, 16), 'Rinoscopio')
        self.tabs.addTab(self._pestana_informe(), iconos.icono('evolucion', tema.TEXTO_TENUE, 16), 'Informe')
        raiz.addWidget(self.tabs)
        self.la_super(None)

    # --- UI -----------------------------------------------------------------

    def _pestana_visor(self):
        tab = QWidget()
        fila = QHBoxLayout(tab)
        fila.setContentsMargins(0, 10, 0, 0)
        fila.setSpacing(10)
        self.cara = Cara()
        self.cara.miro.connect(self._miro)
        fila.addWidget(self.cara, 1)

        # Reclinar: mantener apretada una flecha mueve la cabeza de a poco.
        lado = QVBoxLayout()
        lado.setSpacing(6)
        lado.addStretch(1)
        self.btn_atras = QPushButton('▲')
        self.btn_adelante = QPushButton('▼')
        for b, paso, ayuda in ((self.btn_atras, PASO_RECLINAR, 'Echar la cabeza hacia atrás'),
                               (self.btn_adelante, -PASO_RECLINAR, 'Volver la cabeza')):
            b.setToolTip(ayuda)
            b.setFixedSize(54, 54)
            b.setAutoRepeat(True)
            b.setAutoRepeatDelay(250)
            b.setAutoRepeatInterval(REPETIR_MS)
            b.clicked.connect(lambda _c=False, d=paso: self._reclinar(d))
        lado.addWidget(self.btn_atras, 0, Qt.AlignmentFlag.AlignHCenter)
        rotulo = etiqueta('RECLINAR', rol='seccion')
        rotulo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lado.addWidget(rotulo)
        self.lbl_grados = etiqueta('', rol='hint')
        self.lbl_grados.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lado.addWidget(self.lbl_grados)
        lado.addWidget(self.btn_adelante, 0, Qt.AlignmentFlag.AlignHCenter)
        lado.addStretch(1)
        fila.addLayout(lado)
        return tab

    def _pestana_informe(self):
        tab = QWidget()
        col = QVBoxLayout(tab)
        col.setContentsMargins(0, 10, 0, 0)
        col.setSpacing(8)
        fosas = QHBoxLayout()
        fosas.setSpacing(10)
        self.paneles = {lado: PanelFosa(lado, texto) for lado, texto, _s in LADOS}
        for lado in ('D', 'I'):
            fosas.addWidget(self.paneles[lado], 1)
        col.addLayout(fosas)
        caja = Tarjeta('Conclusión')
        self.txt_conclusion = QPlainTextEdit()
        self.txt_conclusion.setFixedHeight(70)
        caja.agregar(self.txt_conclusion)
        self.estado_informe = EstadoInforme()
        caja.agregar(self.estado_informe)
        col.addWidget(caja)
        col.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidgetResizable(True)
        desplazable.setWidget(tab)
        return desplazable

    # --- Ciclo de vida (API que llama main.py) ---------------------------

    def la_super(self, data, appointment_id=None):
        """Entra (o sale) el paciente en atención."""
        self.sesion = sesion.para(data, appointment_id)
        self.nasal = (data or {}).get('NASAL') if isinstance(data, dict) else None
        self.appointment_id = appointment_id
        self.imagenes.clear()
        self.cola.clear()
        self.vistas = []
        for panel in self.paneles.values():
            panel.limpiar()
        self.txt_conclusion.clear()
        self.estado_informe.limpiar()
        hay = self.sesion is not None and self.sesion.hay_paciente
        for b in (self.btn_atras, self.btn_adelante):
            b.setEnabled(hay)
        self.cara.activa = hay
        self.cara.interior.clear()
        self.grados = 0
        self.cara.set_grados(0)
        self.lbl_grados.setText('recta' if hay else '')
        if not hay:
            return
        self._mostrar()
        # Las tres posiciones de las dos fosas primero; después los ángulos
        # intermedios, todo de a poco y fuera de la ventana.
        for g in POSICIONES + tuple(a for a in ANGULOS if a not in POSICIONES):
            for lado in ('D', 'I'):
                self._pedir(lado, g, al_final=True)

    def showEvent(self, evento):
        # El vasoconstrictor pudo ponerse en la RM o la RA: otra imagen.
        if self.sesion is not None and self.sesion.hay_paciente:
            self._mostrar()
        super().showEvent(evento)

    # --- Visor -----------------------------------------------------------

    def angulo(self):
        """El cálculo del interior más cercano a cómo está la cabeza."""
        return min(ANGULOS, key=lambda a: abs(a - self.grados))

    def _reclinar(self, paso):
        if self.sesion is None or not self.sesion.hay_paciente:
            return
        self.grados = max(0, min(ANGULOS[-1], self.grados + paso))
        self.cara.set_grados(self.grados)
        self.lbl_grados.setText('recta' if self.grados == 0 else f'{self.grados}°')
        self._mostrar()

    def _mostrar(self):
        """Pone en la cara el interior de las dos fosas para esta posición
        (o lo pide, si no está)."""
        g = self.angulo()
        for lado in ('D', 'I'):
            img = self.imagenes.get((lado, g, self.sesion.vc))
            self.cara.set_interior(lado, img)
            if img is None:
                self._pedir(lado, g)

    def _miro(self, lado):
        """Pasó el espéculo por la narina: cuenta como mirada de esa fosa en
        esta posición (la del cálculo, de 10 en 10)."""
        vista = (lado, self.angulo())
        if vista not in self.vistas:
            self.vistas.append(vista)

    def _pedir(self, lado, grados, al_final=False):
        clave = (lado, grados)
        if (lado, grados, self.sesion.vc) in self.imagenes or clave == self.calculando:
            return
        if clave in self.cola:
            self.cola.remove(clave)
        if al_final:
            self.cola.append(clave)
        else:
            self.cola.insert(0, clave)
        self._siguiente()

    def _siguiente(self):
        if self.calculando is not None or not self.cola or self.sesion is None:
            return
        lado, grados = self.cola.pop(0)
        vc = self.sesion.vc
        if (lado, grados, vc) in self.imagenes:
            return self._siguiente()
        fosa = rinoscopia.fosa_del_paciente(self.sesion.paciente, self.nasal, lado, self.sesion.estado())
        ruta = os.path.join(_carpeta_cache(), _clave(fosa, lado, grados) + '.png')
        self.calculando = (lado, grados)
        sesion_actual = self.sesion

        def listo(img):
            self.calculando = None
            if self.sesion is not sesion_actual:
                return self._siguiente()
            self.imagenes[(lado, grados, vc)] = QPixmap.fromImage(img)
            if (grados, vc) == (self.angulo(), self.sesion.vc):
                self.cara.set_interior(lado, self.imagenes[(lado, grados, vc)])
            self._siguiente()

        def fallo(exc):
            self.calculando = None
            print(f'rinoscopía: no se pudo dibujar {lado} {grados}°: {exc}')
            self._siguiente()

        self.tarea = hilos.en_fondo(_calcular, fosa, lado, grados, ruta, listo=listo, fallo=fallo,
                                    dueno=self, nombre='rinoscopia')

    # --- Informe (contrato de core/report_autosave.py) -----------------

    def tecnica(self):
        """Cómo miró: qué fosa primero y en qué posiciones de la cabeza."""
        primera = self.vistas[0][0] if self.vistas else None
        posiciones = {lado: sorted({g for l, g in self.vistas if l == lado}) for lado in ('D', 'I')}
        return {'primera_fosa': primera, 'posiciones': posiciones,
                'tres_posiciones': {lado: all(g in posiciones[lado] for g in POSICIONES) for lado in ('D', 'I')}}

    def report_job(self):
        if not self.data_login or self.sesion is None or not self.sesion.hay_paciente:
            return None
        if not (self.vistas or any(p.tiene_algo() for p in self.paneles.values())):
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        data = {lado: self.paneles[lado].to_dict() for lado in ('D', 'I')}
        data.update({'conclusion': self.txt_conclusion.toPlainText(), 'tecnica': self.tecnica(),
                     'vistas': [list(v) for v in self.vistas], 'vasoconstrictor': self.sesion.vc})
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data, 'images': None}

    def restore_report(self, data):
        """Retomar la atención: vuelve lo informado y lo que ya había mirado,
        si en esta vuelta todavía no se hizo nada."""
        if self.sesion is None or not self.sesion.hay_paciente or self.vistas \
                or any(p.tiene_algo() for p in self.paneles.values()):
            return False
        for lado in ('D', 'I'):
            self.paneles[lado].from_dict(data.get(lado) or {})
        self.txt_conclusion.setPlainText(data.get('conclusion') or '')
        self.vistas = [tuple(v) for v in (data.get('vistas') or [])
                       if isinstance(v, (list, tuple)) and len(v) == 2]
        if data.get('vasoconstrictor'):
            self.sesion.aplicar_vasoconstrictor()
        return True
