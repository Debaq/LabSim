"""La rinoscopía anterior en LabSim (H25): el visor por el espéculo y el
informe por fosa, como la otoscopía.

Lo que se ve lo dibuja nasal/rinoscopia.py desde la nariz del caso (la
misma de la rinomanometría y la rinometría, nasal/sesion.py): si el alumno
puso vasoconstrictor en la RM, el cornete se ve retraído también aquí.

El alumno elige la fosa y la posición de la cabeza (recta, 30°, 60°). El
módulo anota solo en qué orden miró las fosas y en qué posiciones, que es
lo que H25 pide ("primero la fosa derecha", "cabeza recta, 30° y 60°"): va
en el informe para el docente, sin avisarle nada al alumno.

Cada imagen tarda un par de segundos: se calculan fuera de la ventana,
primero la que se pide y después las tres posiciones de cada fosa, y quedan
guardadas en el equipo (local_cache/nasal/rinoscopia) para la próxima vez.

Demo interna (docs/roadmap_nasal.md): solo el admin abre el módulo.
Sin `cases.data['NASAL']` no hay nariz que mirar.
"""

import hashlib
import json
import os

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel,
                               QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSlider,
                               QTabWidget, QVBoxLayout, QWidget)

from core import hilos, iconos, tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import rinoscopia, sesion
from vemp.widgets.kit import Campos, Tarjeta, etiqueta

LADOS = (('D', 'Fosa derecha', 'FND'), ('I', 'Fosa izquierda', 'FNI'))
POSICIONES = (0, 30, 60)
ANGULOS = tuple(range(0, 61, 10))     # lo que se calcula (el control va de 10 en 10)
TAM = 260
PERMISOS_DOCENTE = (555, 777)
NEGRO_VISOR = QColor('#0E0A0D')
METAL = '#8E9098'

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
TEXTO_OPCION = {campo: dict(opciones) for campo, _r, opciones in CAMPOS_INFORME}


def _carpeta_cache():
    ruta = context.get_resource('local_cache/nasal/rinoscopia')
    os.makedirs(ruta, exist_ok=True)   # en el build no existe local_cache/*
    return ruta


def _clave(fosa, lado, grados):
    """Identifica una imagen: la misma fosa en la misma posición sale igual."""
    crudo = json.dumps([rinoscopia.VERSION, TAM, lado, grados, round(fosa.vol_ci, 3), fosa.dev,
                        fosa.polipos, fosa.perf, fosa.aspecto, round(fosa.r_cm, 3)],
                       sort_keys=True, default=str)
    return hashlib.blake2b(crudo.encode(), digest_size=12).hexdigest()


def _calcular(fosa, lado, grados, ruta):
    """Fuera de la ventana: la imagen, de la caché del equipo o calculada
    (y guardada)."""
    if os.path.exists(ruta):
        img = QImage(ruta)
        if not img.isNull():
            return img
    arr = rinoscopia.render(fosa, grados, TAM, espejo=(lado == 'I'))
    img = QImage(arr.data, TAM, TAM, 3 * TAM, QImage.Format.Format_RGB888).copy()
    try:
        img.save(ruta, 'PNG')
    except Exception as exc:  # noqa: BLE001 -- sin caché igual se ve
        print(f'rinoscopía: no se pudo guardar {ruta}: {exc}')
    return img


class Visor(QWidget):
    """Lo que se ve por el espéculo: la imagen centrada sobre negro."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._texto = 'Sin atención abierta'
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def mostrar(self, pixmap):
        self._pixmap, self._texto = pixmap, None
        self.update()

    def aviso(self, texto):
        self._pixmap, self._texto = None, texto
        self.update()

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        borde = QPainterPath()
        borde.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
        p.setClipPath(borde)
        p.fillRect(self.rect(), NEGRO_VISOR)
        if self._pixmap is not None:
            lado = min(self.width(), self.height()) - 24
            destino = QRectF((self.width() - lado) / 2, (self.height() - lado) / 2, lado, lado)
            # Solo la abertura del espéculo, y su aro de metal encima.
            circulo = QPainterPath()
            circulo.addEllipse(destino)
            p.save()
            p.setClipPath(circulo)
            p.drawPixmap(destino, self._pixmap, QRectF(self._pixmap.rect()))
            p.restore()
            aro = max(6.0, lado * 0.025)
            p.setPen(QPen(QColor(METAL), aro))
            p.drawEllipse(destino.adjusted(aro / 2, aro / 2, -aro / 2, -aro / 2))
        else:
            p.setPen(QColor(tema.TEXTO_TENUE))
            p.drawText(self.rect().adjusted(16, 0, -16, 0),
                       Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self._texto or '')
        p.setClipping(False)
        p.setPen(QPen(QColor(tema.BORDE), 1))
        p.drawPath(borde)
        p.end()


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
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self.sesion = None
        self.nasal = None
        self.appointment_id = None
        self.lado = 'D'
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
        self.lbl_verdad = None
        if self.es_docente:
            self.lbl_verdad = etiqueta('', rol='hint')
            self.lbl_verdad.setTextFormat(Qt.TextFormat.RichText)
            self.lbl_verdad.setWordWrap(True)
            self.lbl_verdad.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            caja = QScrollArea()
            caja.setWidgetResizable(True)
            caja.setWidget(self.lbl_verdad)
            self.tabs.addTab(caja, 'Lo que hay')
        raiz.addWidget(self.tabs)
        self.la_super(None)

    # --- UI -----------------------------------------------------------------

    def _pestana_visor(self):
        tab = QWidget()
        col = QVBoxLayout(tab)
        col.setContentsMargins(0, 10, 0, 0)
        col.setSpacing(8)
        fila = QHBoxLayout()
        self.grupo_lado = QButtonGroup(self)
        self.btn_lado = {}
        for lado, texto, sigla in LADOS:
            b = QPushButton(texto)
            b.setCheckable(True)
            b.clicked.connect(lambda _c=False, l=lado: self._elegir(lado=l))
            self.grupo_lado.addButton(b)
            self.btn_lado[lado] = b
            fila.addWidget(b)
        fila.addSpacing(16)
        fila.addWidget(etiqueta('CABEZA', rol='seccion'))
        self.grupo_pos = QButtonGroup(self)
        self.btn_pos = {}
        for g in POSICIONES:
            b = QPushButton('Recta' if g == 0 else f'{g}°')
            b.setCheckable(True)
            b.clicked.connect(lambda _c=False, gg=g: self._elegir(grados=gg))
            self.grupo_pos.addButton(b)
            self.btn_pos[g] = b
            fila.addWidget(b)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, len(ANGULOS) - 1)
        self.slider.setPageStep(1)
        self.slider.setFixedWidth(160)
        self.slider.valueChanged.connect(lambda i: self._elegir(grados=ANGULOS[i]))
        fila.addWidget(self.slider)
        self.lbl_grados = etiqueta('0°', rol='hint')
        fila.addWidget(self.lbl_grados)
        fila.addStretch(1)
        col.addLayout(fila)
        self.visor = Visor()
        col.addWidget(self.visor, 1)
        self.lbl_pista = etiqueta('', rol='hint')
        self.lbl_pista.setWordWrap(True)
        col.addWidget(self.lbl_pista)
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
        for b in (*self.btn_lado.values(), *self.btn_pos.values(), self.slider):
            b.setEnabled(hay)
        if not hay:
            self.visor.aviso('Este paciente no tiene la nariz cargada en el caso.' if data is not None
                             else 'Sin atención abierta')
            self.lbl_pista.setText('')
            self._dibujar_verdad()
            return
        self.lado, self.grados = 'D', 0
        self.lbl_pista.setText('Elige la fosa y la posición de la cabeza del paciente.')
        self._elegir(lado='D', grados=0, mirar=False)
        # Las tres posiciones de las dos fosas, de a poco y fuera de la
        # ventana; los ángulos intermedios, recién cuando se piden.
        for lado in ('D', 'I'):
            for g in POSICIONES:
                self._pedir(lado, g, al_final=True)
        self._dibujar_verdad()

    def showEvent(self, evento):
        # El vasoconstrictor pudo ponerse en la RM o la RA: otra imagen.
        if self.sesion is not None and self.sesion.hay_paciente:
            self._elegir(mirar=False)
        super().showEvent(evento)

    # --- Visor -----------------------------------------------------------

    def _elegir(self, lado=None, grados=None, mirar=True):
        if self.sesion is None or not self.sesion.hay_paciente:
            return
        self.lado = lado or self.lado
        self.grados = self.grados if grados is None else grados
        for l, b in self.btn_lado.items():
            b.setChecked(l == self.lado)
        for g, b in self.btn_pos.items():
            b.setChecked(g == self.grados)
        self.slider.blockSignals(True)
        self.slider.setValue(ANGULOS.index(self.grados))
        self.slider.blockSignals(False)
        self.lbl_grados.setText(f'{self.grados}°')
        if mirar and (self.lado, self.grados) not in self.vistas:
            self.vistas.append((self.lado, self.grados))
        img = self.imagenes.get((self.lado, self.grados, self.sesion.vc))
        if img is not None:
            self.visor.mostrar(img)
        else:
            self.visor.aviso('Acomodando el espéculo…')
            self._pedir(self.lado, self.grados)
        self._dibujar_verdad()

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
            if (lado, grados, vc) == (self.lado, self.grados, self.sesion.vc):
                self.visor.mostrar(self.imagenes[(lado, grados, vc)])
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
        self._dibujar_verdad()
        return True

    # --- Lo que hay (docente) ----------------------------------------------

    def _dibujar_verdad(self):
        if self.lbl_verdad is None:
            return
        if self.sesion is None or not self.sesion.hay_paciente:
            self.lbl_verdad.setText('')
            return
        estado = self.sesion.estado()
        filas = []
        for clave, rotulo in (('tabique', 'Tabique'), ('cornete_inferior', 'Cornete inferior'),
                              ('mucosa', 'Mucosa'), ('secrecion', 'Secreción')):
            celdas = [TEXTO_OPCION[clave].get(rinoscopia.hallazgos(self.sesion.paciente, self.nasal, l, estado)[clave], '—')
                      for l in ('D', 'I')]
            filas.append(f'<tr><td>{rotulo}</td><td>{celdas[0]}</td><td>{celdas[1]}</td></tr>')
        for clave, rotulo in (('perforacion', 'Perforación septal'), ('polipos', 'Pólipos en el meato medio')):
            celdas = ['sí' if rinoscopia.hallazgos(self.sesion.paciente, self.nasal, l, estado)[clave] else 'no'
                      for l in ('D', 'I')]
            filas.append(f'<tr><td>{rotulo}</td><td>{celdas[0]}</td><td>{celdas[1]}</td></tr>')
        t = self.tecnica()
        primera = {'D': 'la derecha', 'I': 'la izquierda', None: '—'}[t['primera_fosa']]
        pos = '; '.join(f"{s}: {', '.join(f'{g}°' for g in t['posiciones'][l]) or 'ninguna'}"
                        for l, _t, s in LADOS)
        self.lbl_verdad.setText(
            '<p>Leído de la nariz del caso, con los umbrales del simulador '
            f'({"con" if self.sesion.vc else "sin"} vasoconstrictor).</p>'
            '<table cellpadding="4"><tr><th></th><th>FND</th><th>FNI</th></tr>' + ''.join(filas) + '</table>'
            f'<p><b>Cómo miró el alumno.</b> Primero {primera}. Posiciones: {pos}.</p>')
