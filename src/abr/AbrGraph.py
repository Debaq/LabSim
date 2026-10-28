

import os
import numpy as np
import pyqtgraph as pg
from abr.smooth import smooth_curve_gaussian
from abr.WidgetsMods import (GraphicsLayoutWidgetMod, InfiniteLineMod,
                             TextItemMod)
from core import tema
from core.base import context
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import QGraphicsRectItem


# Como se abrevia cada parametro cuando hay que ponerlo en la etiqueta de
# una curva. Solo entran los que distinguen una curva de las otras del
# mismo grafico (ver curve_tokens): si toda la pila es click alternado a
# la misma tasa, la etiqueta dice solo la intensidad, que es lo que se lee
# en un ABR de rutina.
STIM_SHORT = {
    "Click": "click",
    "CE-Chirp": "chirp",
    "CE-Chirp LS": "chirp LS",
    "NB CE-Chirp LS 500 Hz": "chirp 500",
    "NB CE-Chirp LS 1 kHz": "chirp 1k",
    "NB CE-Chirp LS 2 kHz": "chirp 2k",
    "NB CE-Chirp LS 4 kHz": "chirp 4k",
    "Burst 500 Hz": "burst 500",
    "Burst 1 kHz": "burst 1k",
    "Burst 2 kHz": "burst 2k",
    "Burst 4 kHz": "burst 4k",
}

POL_SHORT = {
    "Alternada": "alt.",
    "Condensación": "cond.",
    "Rarefacción": "rar.",
}


class AbrGraph(GraphicsLayoutWidgetMod):
    sig_data_info = Signal(dict)
    sig_del_curve = Signal(str)
    sig_change_value_mark = Signal(dict)
    sig_curve_selected = Signal(str)

    # Verde para el subpromedio A y cafe para el B, iguales en los dos
    # oidos: no son senial del canal, son la replicabilidad.
    COLOR_SUB_A = (0, 140, 70)
    COLOR_SUB_B = (140, 90, 40)
    # Trazos superpuestos del oddball (ver abr/cortical.build_traces).
    OVERLAY_STYLE = {
        'frecuente': ((120, 120, 120), Qt.PenStyle.SolidLine),
        'raro': ((40, 40, 40), Qt.PenStyle.DashLine),
    }

    def __init__(self, side):
        super().__init__()
        self.side = side
        # Ventana de registro en ms. La fija el protocolo/Parametros
        # Avanzados (ver set_windows): el eje X, los cursores A/B y las
        # etiquetas de curva la siguen, si no un ECochG de 5 ms o un
        # registro de 20 ms quedaban dibujados sobre una regla de 12.
        self.window_ms = 12.0
        self.act_curve = None
        self.marks = {}
        # Como se llaman las marcas de la prueba activa: cambia el menu
        # contextual de "Eliminar marcas". Las del ABR son las ondas; las
        # del ECochG son los cuatro puntos que definen las dos razones.
        self.mark_labels = ('I', 'II', 'III', 'IV', 'V')
        # Marcas que se pegan al extremo del trazo en vez de caer donde
        # cayo el clic. El PA es un pico y marcarlo es decir donde esta, no
        # acertarle al punto; el hombro del PS y la linea de base NO se
        # pegan a nada, que es justamente la parte que el alumno decide.
        self.snap_marks = ()
        # Hacia donde se pega cada marca (-1 minimo, +1 maximo) y cuanto
        # busca. El PA del ECochG va al minimo con 0.4 ms; la Pa del MLR es
        # un maximo y la P300 tiene decenas de ms de ancho.
        self.snap_sign = {}
        self.snap_ms = self.SNAP_MS
        # Si una marca recien puesta avisa. En el ABR NO: ahi la marca la
        # pone measure_action DESPUES de escribir la tabla con los valores
        # de los cursores (latencia A, amplitud pico-pico A-B), y avisar
        # aca pisaria esos valores con la coordenada cruda del trazo. En el
        # ECochG la marca ES el dato, asi que tiene que avisar.
        self.notify_create = False
        self.data = {}
        self.curve_int = {}
        # Con que quedo registrada cada curva (estimulo, polaridad, tasa y
        # si fue por via osea). No es para el detalle -- eso ya lo lleva la
        # ventana -- sino para la etiqueta: decide que parametro merece
        # escribirse al lado de la intensidad.
        self.curve_cfg = {}
        self.current_lat = 0
        # Trazos por curva: promedio, canal contralateral y los dos
        # subpromedios A/B. Antes habia un solo PlotDataItem por curva y se
        # lo buscaba por item.name(); con cuatro trazos por curva eso ya no
        # alcanza (y el contra ni siquiera se dibujaba).
        self.traces = {}
        # Los dos subpromedios y el contra se pueden ocultar desde la barra
        # del grafico: con cuatro trazos por curva y ocho curvas apiladas,
        # buscar la onda V en el promedio se hace ilegible.
        # Arrancan ocultos (pedido del docente): el que los quiere mirar los
        # prende con los botones AB y C de la barra.
        self.show_sub = False
        self.show_contra = False
        # Escala vertical del grafico, en uV de alto de ventana. Antes el
        # yRange estaba clavado en (-3, 3) y el apilado en 1.8 uV fijos:
        # todas las curvas nacian en la MISMA altura (se pisaban hasta que
        # el alumno las arrastraba a mano) y el gap no seguia a la escala.
        self.scale_uv = 6.0
        # Los botones +/- recorren una escalera de dobles/mitades de la
        # escala base de la prueba (la que fija set_scale). Antes se
        # multiplicaba o dividia la escala actual y se recortaba en 1 y
        # 200 uV: el recorte rompia la escalera (192 -> 200 -> 100 -> ...
        # -> 6.25) y ya no se volvia nunca a la escala de la prueba.
        self.scale_base = self.scale_uv
        self.scale_step = 0
        # En una sesion anterior las curvas son lo que se registro ese dia:
        # se marcan, no se borran (ver AbrMainWindow.select_session).
        self.curves_locked = False
        # Sesion de una atencion ya cerrada: solo se mira. Ni marcas nuevas
        # ni borrar las que tiene (ver AbrMainWindow.set_view_mode).
        self.read_only = False
        # Separacion entre curvas como fraccion de la escala. 0.35 deja el
        # ruido del arranque (hasta ~1.2 uV RMS) sin invadir la curva de
        # arriba a escala normal.
        self.gap_ratio = 0.35
        # Eje Y invertido (boton de la barra). Hay quien lee el ABR con el
        # vertex positivo hacia abajo y el ECochG con el PA hacia arriba:
        # es convencion del equipo, no del examen.
        self.y_inverted = False
        # Linea de base del ECochG por curva: de la marca BL a la FIN (o al
        # borde de la ventana mientras no haya FIN). Sin ella la marca BL
        # era una flechita pegada al eje y parecia que no se habia puesto.
        self.base_lines = {}
        # Achurado de las dos areas del ECochG por curva: {curva: (zonas,
        # [items])}. Las zonas vienen de ecochg.area_shading, o sea de las
        # mismas cuentas que el numero de la tabla.
        self.area_fills = {}
        # Puntos de las marcas BL/INI/FIN: {(curva, marca): ScatterPlotItem}.
        self.dot_items = {}
        # Guias de latencia normal sobre la curva activa (como las cajas de
        # Interacoustics): {marca: (desde, hasta)} en ms y el signo de cada
        # marca (+1 pico, -1 valle). No son ayuda: dicen donde se espera
        # cada componente para ESTE paciente, no donde esta.
        self.norm_lat = {}
        self.norm_signs = {}
        self.show_norms = True
        # Las cajas y rotulos se crean una vez por marca y se reusan
        # (ocultos cuando no van): crearlos y borrarlos en cada cambio de
        # curva dejaba textos de Qt destruidos que el redimensionado de la
        # vista todavia tocaba. norm_items son los que estan a la vista.
        self.norm_pool = {}
        self.norm_items = []
        # callable(intensidad, cfg) -> texto del nivel en la unidad del
        # equipo (lo pone la ventana; ver AbrMainWindow.level_text).
        self.level_text = None
        self.configure_pyqtgraph()
        self.setup_ui_elements()
        self.colors_side()
        self.inifine_ab()

    def configure_pyqtgraph(self):
        self.color_background = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(tema.GRILLA_FUERTE)
        self.color_texto = pg.mkColor(tema.TEXTO_TENUE)
        self.setBackground(self.color_background)
    
    def setup_ui_elements(self):
        """Set up UI elements for the graph"""
        self.pw = self.addPlot(row=0,col=1)
        self.pw.setRange(yRange=(-self.scale_uv / 2, self.scale_uv / 2),
                         xRange=(0, self.window_ms + 1),
                         disableAutoRange=True)
        self.grid = pg.GridItem(pen=self.color_pen, textPen=self.color_texto)
        self.pw.addItem(self.grid)
        self.grid.setTickSpacing(x=[1.0], y=[1.0])
        self.pw.setMouseEnabled(x=False, y=True)
       
        self.pw.setMenuEnabled(False)
        self.pw.hideButtons()
        ay = self.pw.getAxis('left')
        ay.setStyle(showValues=False)
        view_box = self.pw.getViewBox()
        view_box.setMouseMode(pg.ViewBox.PanMode)
        # La rueda y el arrastre con boton derecho hacian zoom por su
        # cuenta, sin pasar por la escala: el rotulo seguia diciendo lo
        # mismo y el siguiente +/- reencuadraba de golpe (las curvas
        # "saltaban" en vez de agrandarse). El zoom es solo de los botones;
        # el arrastre con boton izquierdo sigue desplazando en vertical.
        view_box.wheelEvent = lambda ev, axis=None: ev.ignore()
        arrastre = view_box.mouseDragEvent

        def solo_desplazar(ev, axis=None):
            if ev.button() == Qt.MouseButton.RightButton:
                ev.ignore()
                return
            arrastre(ev, axis)
        view_box.mouseDragEvent = solo_desplazar

    def pen_for(self, clave, activa=True):
        """Pen de un trazo segun su tipo y si la curva esta seleccionada.

        Los subpromedios llevan color propio (verde A, cafe B) y no el del
        canal: con cuatro trazos del mismo tono no se distinguia cual era
        el promedio y cuales el respaldo. La seleccion en ellos se marca
        con opacidad, no con color.
        """
        if clave in ('sub_a', 'sub_b'):
            color = pg.mkColor(self.COLOR_SUB_A if clave == 'sub_a'
                               else self.COLOR_SUB_B)
            color.setAlpha(255 if activa else 110)
            return pg.mkPen(color, width=1)
        if clave.startswith('ov_'):
            # Trazo superpuesto del oddball (frecuente, raro): gris, para
            # que el de la prueba --el raro en la P300, la diferencia en la
            # MMN-- sea el que se lee y se marca.
            gris, estilo = self.OVERLAY_STYLE.get(
                clave[3:], ((120, 120, 120), Qt.PenStyle.SolidLine))
            color = pg.mkColor(*gris)
            color.setAlpha(255 if activa else 120)
            return pg.mkPen(color, width=1, style=estilo)
        base = self.active_color if activa else self.inactive_color
        if clave == 'contra':
            return pg.mkPen(base, width=1, style=Qt.PenStyle.DotLine)
        return pg.mkPen(base)

    def set_sub_visible(self, visible):
        """Muestra u oculta los subpromedios A/B de todas las curvas."""
        self.show_sub = bool(visible)
        self._apply_visibility()

    def set_contra_visible(self, visible):
        """Muestra u oculta el trazo contralateral de todas las curvas."""
        self.show_contra = bool(visible)
        self._apply_visibility()

    def _apply_visibility(self):
        for trazos in self.traces.values():
            for clave, item in trazos.items():
                if clave in ('sub_a', 'sub_b'):
                    item.setVisible(self.show_sub)
                elif clave == 'contra':
                    item.setVisible(self.show_contra)

    def colors_side(self):
        # Etiqueta de nivel: la curva activa en el color de su oído, lleno y
        # con letra blanca; las demás en el tono suave del mismo oído.
        if self.side == 0:
            self.active_color = pg.mkColor(tema.OD)
            self.active_fill_color = tema.OD
            self.inactive_color = pg.mkColor(tema.OD_INACTIVO)
            self.inactive_fill_color = tema.OD_SUAVE
        else:
            self.active_color = pg.mkColor(tema.OI)
            self.active_fill_color = tema.OI
            self.inactive_color = pg.mkColor(tema.OI_INACTIVO)
            self.inactive_fill_color = tema.OI_SUAVE
    
    def inifine_ab(self, pos_A = 0, pos_B = None):
        pos_B = self.window_ms if pos_B is None else pos_B
        #Variables internas
        pen1 = pg.mkPen(tema.ACENTO, width=1, style=Qt.PenStyle.DashLine)
        opst = {'position':0.9, 'color': (255,255,255), 'fill': pg.mkColor(tema.ACENTO), 'movable': True}
        name_a = f"A{self.side}"
        name_b = f"B{self.side}"
        # Lineas infinitas. La bandera dice su latencia ({value} lo
        # rellena pyqtgraph al moverla): antes decia solo "A" y no habia en
        # ninguna parte de la pantalla en que latencia estaba.
        self.inf_a = InfiniteLineMod(lbl='A {value:.2f} ms', pos=pos_A, movable=True, angle=90, pen=pen1, labelOpts=opst, name=name_a)
        self.inf_b = InfiniteLineMod(lbl="A' {value:.2f} ms", pos=pos_B, movable=True, angle=90, pen=pen1, labelOpts=opst, name=name_b)
        #Posición en X de las lineas infinitas
        self.inf_a.sigPositionChanged.connect(self.get_amplitude)
        self.inf_b.sigPositionChanged.connect(self.get_amplitude)
        #Se agregan lineas infinitas a la grafica
        self.pw.addItem(self.inf_a)
        self.pw.addItem(self.inf_b)

    def next_gap(self):
        """Altura de la proxima curva: una ranura por DEBAJO de la ultima.

        Hacia abajo y no hacia arriba porque asi se lee un ABR: la
        intensidad mas alta arriba y las siguientes descendiendo, que es el
        orden en que se captura y en que se busca el umbral.

        El paso sigue a la escala (gap_ratio de la ventana), asi que al
        cambiar de escala las curvas se separan o se juntan con ella en vez
        de quedar clavadas en 1.8 uV.
        """
        paso = self.scale_uv * self.gap_ratio
        if not self.data:
            return 0.0
        return min(v.get('gap', 0.0) for v in self.data.values()) - paso

    def apply_view(self):
        """Rango vertical: una ventana de escala completa mas el apilado."""
        gaps = [v.get('gap', 0.0) for v in self.data.values()]
        piso = min(gaps, default=0.0)
        # Tambien hacia arriba: una curva arrastrada por encima de la
        # primera quedaba fuera de la ventana al cambiar de escala.
        techo = max(max(gaps, default=0.0), 0.0)
        self.pw.setYRange(piso - self.scale_uv / 2, techo + self.scale_uv / 2,
                          padding=0)

    def create_line(self, data, intencity, setting=None):
        for name, values in data.items():
            if name in self.data: #si la curva ya existe solo se actualiza el grafico correspondiente
                self.update_data(name, values)
                self.update_graph(name,values)

            else: #si la curva no existe se crea en self.data y se crea el label que lo acompaña
                self.act_curve = name
                values['gap'] = self.next_gap()
                self.data[name] = values
                self.marks[name] = {}
                self.curve_int[name] = intencity
                self.curve_cfg[name] = self.read_config(setting)
                # Canal de registro (C3, Cz...): lo trae cada curva de los
                # potenciales multicanal y va en su etiqueta.
                self.curve_cfg[name]['canal'] = values.get('canal')
                self.traces[name] = self.create_traces(name, values)
                label = self.create_label(name, values['gap'])
                self.pw.addItem(label)
                # La curva nueva puede estrenar un parametro distinto: ahi
                # las que ya estaban tambien tienen que decir el suyo.
                self.refresh_labels()
                self.refresh_norm_guides()
                self.apply_view()

    def load_curve(self, name, values, intencity, setting, gap, marks=None):
        """Redibuja una curva guardada donde estaba, con sus marcas."""
        self.create_line({name: values}, intencity, setting)
        self.data[name]['gap'] = float(gap)
        self.redraw(name)
        self.move_label(name)
        if name == self.act_curve:
            self.refresh_norm_guides()
        for etiqueta, xy in (marks or {}).items():
            self.recreate_mark(name, etiqueta, list(xy))
        self.apply_view()

    def create_traces(self, name, values):
        """Los cuatro trazos de una curva: A/B, contra y promedio.

        Orden de dibujo a proposito: los subpromedios abajo (son el
        respaldo), el contralateral punteado y el promedio arriba de todo,
        que es el que el alumno marca.
        """
        gap = values['gap']
        trazos = {}
        # Subpromedios A/B (barridos pares e impares). Finos y claros: son
        # la replicabilidad en vivo, no la curva que se informa.
        for clave in ('sub_a', 'sub_b'):
            xy = values.get(clave)
            trazos[clave] = self.pw.plot(
                x=xy[0] if xy else [], y=(np.asarray(xy[1]) + gap) if xy else [],
                pen=self.pen_for(clave), name=f'{name}#{clave}')
            trazos[clave].setVisible(self.show_sub)
        # Canal contralateral (punteado): existe solo si el electrodo del
        # otro mastoides esta puesto -- si no, el generador manda None.
        xy = values.get('contra_xy')
        trazos['contra'] = self.pw.plot(
            x=xy[0] if xy else [], y=(np.asarray(xy[1]) + gap) if xy else [],
            pen=self.pen_for('contra'), name=f'{name}#contra')
        trazos['contra'].setVisible(self.show_contra)
        # Superpuestos del oddball, debajo del promedio que se marca.
        for nombre_ov, xy in (values.get('overlays') or {}).items():
            clave = f'ov_{nombre_ov}'
            trazos[clave] = self.pw.plot(
                x=xy[0], y=np.asarray(xy[1]) + gap, pen=self.pen_for(clave),
                name=f'{name}#{clave}')
        trazos['main'] = self.pw.plot(
            x=values['ipsi_xy'][0], y=np.asarray(values['ipsi_xy'][1]) + gap,
            pen=self.pen_for('main'), name=name)
        # Clic sobre el trazo: esa curva pasa a ser la activa y la bandera A
        # va adonde se hizo clic. Con tres canales por captura la activa era
        # la ultima creada (Pz) y el alumno marcaba en Cz sin saber que la
        # marca caia en otra curva; y la bandera, una linea de un pixel, se
        # escapaba y el arrastre desplazaba el grafico.
        trazos['main'].setCurveClickable(True, width=12)
        trazos['main'].sigClicked.connect(
            lambda _item, ev, curva=name: self.click_curve(curva, ev))
        return trazos

    def click_curve(self, curve, ev):
        if curve not in self.data or ev.button() != Qt.MouseButton.LeftButton:
            return
        ev.accept()
        if curve != self.act_curve:
            self.active_curve(curve)
        x = self.pw.vb.mapSceneToView(ev.scenePos()).x()
        self.inf_a.setPos((max(0.0, min(self.window_ms, x)), 0))

    def update_graph(self, graph_name, data):
        trazos = self.traces.get(graph_name)
        if not trazos:
            return
        gap = self.data[graph_name]['gap']
        fuentes = {'main': data.get('ipsi_xy'), 'contra': data.get('contra_xy'),
                   'sub_a': data.get('sub_a'), 'sub_b': data.get('sub_b')}
        for nombre_ov, xy in (data.get('overlays') or {}).items():
            fuentes[f'ov_{nombre_ov}'] = xy
        for clave, xy in fuentes.items():
            item = trazos.get(clave)
            if item is None:
                continue
            if xy is None:
                if clave == 'main':
                    continue
                item.setData(x=[], y=[])
                continue
            item.setData(x=xy[0], y=np.asarray(xy[1]) + gap)
        self.get_amplitude()

    def update_data(self,name ,values):
        for key, val in values.items():
            if key == 'gap':
                if 'gap' in self.data[name]:
                    continue
            self.data[name][key] = val

    def redraw(self, curve):
        """Redibuja los cuatro trazos de la curva desde self.data."""
        d = self.data[curve]
        self.update_graph(curve, {
            'ipsi_xy': d['ipsi_xy'], 'contra_xy': d.get('contra_xy'),
            'sub_a': d.get('sub_a'), 'sub_b': d.get('sub_b'),
            'overlays': d.get('overlays')})

    def drag_curve(self, value):
        gap_y = value['pos'][1]
        curve = value['name']
        if curve not in self.data:
            # Etiqueta de una curva que ya no esta (se borro o se limpio el
            # grafico con el arrastre en curso): Qt le sigue mandando el
            # arrastre y cada movimiento era un KeyError en la consola. Se
            # quita la etiqueta huerfana y no se hace nada mas.
            for item in self.pw.items[:]:
                if (isinstance(item, TextItemMod) and item.tipo == 'label'
                        and item.name == curve):
                    self.pw.removeItem(item)
            return
        self.data[curve]['gap'] = gap_y
        self.redraw(curve)
        self.move_marks(curve)

    def read_config(self, setting) -> dict:
        """Lo que de la captura puede terminar en la etiqueta.

        La via sale del transductor y no del combo de estimulos (el mismo
        click se presenta por insercion o por vibrador), asi que se guarda
        ya resuelta.
        """
        setting = setting or {}
        return {'stim': setting.get('stim'), 'pol': setting.get('pol'),
                'rate': setting.get('rate'),
                'transducer': setting.get('transducer'),
                'bone': setting.get('transducer') == 'bone_vibrator'}

    def mixed_param(self, clave: str) -> bool:
        """Si ese parametro NO es el mismo en todas las curvas del grafico."""
        valores = {cfg.get(clave) for cfg in self.curve_cfg.values()
                   if cfg and cfg.get(clave) is not None}
        return len(valores) > 1

    def curve_tokens(self, key) -> list:
        """Parametros que hay que escribir al lado de la intensidad.

        Un ABR de rutina es toda la pila con el mismo estimulo, la misma
        polaridad y la misma tasa: repetirlo curva por curva es ruido. Solo
        se escribe el parametro que cambia dentro del grafico, y ahi se
        escribe en TODAS (si una es condensacion y el resto alternada, la
        comparacion se lee sola: 'cond.' contra 'alt.').

        La via osea es la excepcion: se rotula solo la curva osea. La aerea
        es el registro por defecto y no se anuncia.
        """
        cfg = self.curve_cfg.get(key) or {}
        tokens = []
        if self.mixed_param('stim'):
            tokens.append(STIM_SHORT.get(cfg.get('stim'), cfg.get('stim')))
        if self.mixed_param('pol'):
            tokens.append(POL_SHORT.get(cfg.get('pol'), cfg.get('pol')))
        if self.mixed_param('rate'):
            tasa = cfg.get('rate')
            tokens.append(f'{float(tasa):g}/s' if tasa is not None else None)
        if cfg.get('bone'):
            tokens.append('ósea')
        return [t for t in tokens if t]

    def label_html(self, key, fill: str) -> str:
        intensidad = self.curve_int.get(key, '')
        # La unidad la decide el equipo (Parametros avanzados); sin quien la
        # resuelva, nHL como siempre.
        if self.level_text is not None:
            nivel = self.level_text(intensidad, self.curve_cfg.get(key) or {})
        else:
            nivel = f"{intensidad} dB nHL"
        canal = (self.curve_cfg.get(key) or {}).get('canal')
        if canal:
            # En dos lineas: en una ("Cz · 70 dB nHL") no cabia en el
            # margen derecho y se cortaba en "Cz · 70 d".
            nivel = f"<b>{canal}</b><br>{nivel}"
        tokens = self.curve_tokens(key)
        letra = 'white' if fill == self.active_fill_color else tema.color_lado(self.side)
        extra = ''
        if tokens:
            extra = (f"<br><span style='color: {letra}; font-size: 6pt;'>"
                     f"{' · '.join(tokens)}</span>")
        return f"""
                <div style='text-align: center; background-color: {fill};'>
                <span style='color: {letra}; font-size: 7pt;'>
                {nivel}
                </span>{extra}
                </div>
                """

    def refresh_labels(self) -> None:
        """Reescribe todas las etiquetas: lo que se muestra es relativo."""
        for item in self.pw.items:
            if isinstance(item, TextItemMod) and item.tipo == 'label':
                fill = (self.active_fill_color if item.name == self.act_curve
                        else self.inactive_fill_color)
                item.setHtml(self.label_html(item.name, fill))
    def smooth(self, ev):
        curve = self.act_curve
        d = self.data[curve]
        sigma = float(ev)
        # Se suaviza lo que se ve, incluidos los subpromedios y el contra:
        # si no, el promedio quedaba liso y A/B con todo el ruido, y la
        # comparacion visual dejaba de significar nada.
        datos = {'ipsi_xy': [d['ipsi_xy'][0],
                             smooth_curve_gaussian(d['ipsi_xy'][1], sigma=sigma)]}
        for clave in ('contra_xy', 'sub_a', 'sub_b'):
            xy = d.get(clave)
            if xy:
                datos[clave] = [xy[0], smooth_curve_gaussian(xy[1], sigma=sigma)]
        self.update_graph(curve, datos)
        self.move_marks(curve)


    def create_label(self, key, h):
        fill = self.active_fill_color
        lbl = self.label_html(key, fill)
        text = TextItemMod(name=key, tipo='label', curve_parent= key, html=lbl, border="w")
        text.sigDragged.connect(self.drag_curve)
        text.sigPositionChangeStarted.connect(self.active_curve)
        text.setPos(self.window_ms, h)
        return text

    def delete_curve(self):
        if self.curves_locked or self.read_only:
            return
        delete = False
        for item in self.traces.pop(self.act_curve, {}).values():
            self.pw.removeItem(item)
            delete = True

        for item in self.pw.items[:]:
            if isinstance(item, TextItemMod) and item.curve_parent == self.act_curve:
                self.pw.removeItem(item)
                delete = True

        if delete:
            for curva, marca in [k for k in self.dot_items
                                 if k[0] == self.act_curve]:
                self.remove_dot(curva, marca)
            self.remove_base_line(self.act_curve)
            self.set_area_shading(self.act_curve, None)
            self.data.pop(self.act_curve, None)
            self.marks.pop(self.act_curve, None)
            self.curve_int.pop(self.act_curve, None)
            self.curve_cfg.pop(self.act_curve, None)
            # Si la que se fue era la unica distinta, las demas vuelven a
            # mostrar solo la intensidad.
            self.refresh_labels()
            self.sig_del_curve.emit(self.act_curve)
            self.act_curve = None
            self.refresh_norm_guides()
            self.apply_view()

        
    def get_active(self):
        return self.act_curve

    def active_curve(self, sender):
        self.act_curve = sender
        #se selecciona la curva (y con ella sus subpromedios y su contra)
        for nombre, trazos in self.traces.items():
            activa = nombre == self.act_curve
            for clave, item in trazos.items():
                item.setPen(self.pen_for(clave, activa))
        #se selecciona el label de la curva
        self.refresh_labels()
        self.refresh_norm_guides()
        self.sig_curve_selected.emit(self.act_curve)
        #se actualizan los datos de las marcas
        #print(self.marks[self.act_curve])

    def get_amplitude(self):
        # Obtener posiciones actuales de las líneas
        lat_a = self.inf_a.getXPos()
        lat_b = self.inf_b.getXPos()

        # Asegurarse de que las líneas no se salgan de la ventana
        lat_a = max(0, min(self.window_ms, lat_a))
        lat_b = max(0, min(self.window_ms, lat_b))

        # Establecer las posiciones corregidas
        self.inf_a.setPos((lat_a, 0))
        self.inf_b.setPos((lat_b, 0))
        if self.act_curve in self.data:
            x = self.data[self.act_curve]['ipsi_xy'][0]
            y = self.data[self.act_curve]['ipsi_xy'][1]

            # Encontrar los valores de amplitud más cercanos a las posiciones lat_a y lat_b
            amp_a = self.find_nearest(x, lat_a, y)
            amp_b = self.find_nearest(x, lat_b, y)

            # Ordenar las amplitudes y latencias
            order_amp = np.sort([amp_a, amp_b])
            order_lat = np.sort([lat_a, lat_b])

            # Calcular la diferencia de amplitud y latencia
            dif_amp = order_amp[1] - order_amp[0]
            dif_lat = order_lat[1] - order_lat[0]

            # La bandera A' dice la distancia a A: es lo que se mide con las
            # dos banderas y antes solo llegaba al panel de datos.
            self.inf_b.label.setFormat(
                f"A' {{value:.2f}} ms   Δ {dif_lat:.2f} ms · {dif_amp:.2f} µV")

            # Preparar la respuesta
            response = {
                'curve': self.act_curve,
                'data': {
                    "side": self.side,
                    "lat_A": lat_a,
                    "lat_B": lat_b,
                    "amp_AB": dif_amp,
                    "lat_AB": dif_lat
                }
            }

            # Emitir la información calculada
            self.sig_data_info.emit(response)
            # Actualizar la latencia actual
            self.current_lat = lat_a

    def set_marks_mode(self, labels, snap=(), notify=False, signs=None,
                       snap_ms=None):
        """Que marcas tiene esta prueba, cuales se pegan y si avisan.

        `signs` dice hacia donde se pega cada marca (-1 al minimo, +1 al
        maximo; por defecto al minimo, que es el PA del ECochG) y `snap_ms`
        cuanto busca alrededor de la bandera.
        """
        self.mark_labels = tuple(labels)
        self.snap_marks = tuple(snap)
        self.notify_create = bool(notify)
        self.snap_sign = dict(signs or {})
        # Un numero para todas, o {marca: ms} (los corticales).
        if isinstance(snap_ms, dict):
            self.snap_ms = {m: float(v) for m, v in snap_ms.items()}
        else:
            self.snap_ms = float(snap_ms) if snap_ms else self.SNAP_MS

    def snap_to_peak(self, x, mark=None, curve=None):
        """Extremo del trazo cerca de x: el minimo o el maximo segun la marca.

        En el ECochG el PA es una deflexion NEGATIVA (el electrodo activo
        es el del oido, no el vertex), asi que el pico es un minimo. En los
        corticales la Pa, la P1 o la P3 son maximos.
        """
        datos = self.data.get(curve or self.act_curve)
        if not datos:
            return x
        xs, ys = datos['ipsi_xy']
        radio = (self.snap_ms.get(mark, self.SNAP_MS)
                 if isinstance(self.snap_ms, dict) else self.snap_ms)
        cerca = np.where(np.abs(xs - x) <= radio)[0]
        if not len(cerca):
            return x
        valores = np.asarray(ys)[cerca]
        if self.snap_sign.get(mark, -1) > 0:
            return float(xs[cerca[int(np.argmax(valores))]])
        return float(xs[cerca[int(np.argmin(valores))]])

    def mark_at_cursor(self, mark):
        """Pone `mark` en la curva activa, en la latencia de la bandera A.

        Es como se marca en el ABR: se lleva la bandera a la onda y se
        aprieta el boton. Devuelve None si la puso, o el motivo si no.
        """
        if self.read_only:
            return "Sesión de solo lectura: no se puede marcar"
        if self.act_curve is None or self.act_curve not in self.data:
            return ("No hay curva seleccionada en este oído: haga clic en "
                    "la etiqueta de la curva y vuelva a marcar")
        x = float(self.inf_a.getXPos())
        if mark in self.snap_marks:
            x = self.snap_to_peak(x, mark)
        self.current_lat = x
        self.create_marks(mark)
        return None

    def drag_mark(self, curve, lbl_mark, x, final):
        """Corre una marca ya puesta arrastrando su flecha.

        La flecha sigue al mouse pegada al trazo (a su pico si la marca se
        pega); la tabla y la memoria se enteran al soltar, igual que cuando
        se marca con el boton. La curva dueña pasa a ser la activa y la
        bandera A acompaña a la marca, como al hacer clic en el trazo.
        """
        if (self.read_only or curve not in self.data
                or lbl_mark not in self.marks.get(curve, {})):
            return
        if curve != self.act_curve:
            self.active_curve(curve)
        if lbl_mark in self.snap_marks:
            x = self.snap_to_peak(x, lbl_mark, curve)
        xs, ys = self.data[curve]['ipsi_xy']
        i = self.find_idx(xs, x)
        self.marks[curve][lbl_mark] = [xs[i], ys[i]]
        self.place_mark(curve, lbl_mark)
        self.current_lat = xs[i]
        self.inf_a.setPos((max(0.0, min(self.window_ms, float(xs[i]))), 0))
        if final:
            self.update_value_mark(lbl_mark, curve=curve)

    # Cuanto se puede correr una marca que se pega al trazo, en ms.
    SNAP_MS = 0.4

    def create_marks(self, lbl_mark):
        """Pone (o corre) la marca `lbl_mark` de la curva activa en
        current_lat y avisa el valor nuevo."""
        name_curve = self.act_curve
        if self.read_only or name_curve not in self.data:
            return
        xs, ys = self.data[name_curve]['ipsi_xy']
        id_x = self.find_idx(xs, self.current_lat)
        marcas = self.marks.setdefault(name_curve, {})
        nueva = lbl_mark not in marcas
        marcas[lbl_mark] = [xs[id_x], ys[id_x]]
        self.place_mark(name_curve, lbl_mark)
        if not nueva or self.notify_create:
            self.update_value_mark(lbl_mark, curve=name_curve)

    def recreate_mark(self, curve_name, lbl_mark, mark_data):
        """Recrea una marca guardada en el gráfico (sin avisar: el valor ya
        está en la memoria de la sesión)."""
        self.marks.setdefault(curve_name, {})[lbl_mark] = list(mark_data)
        self.place_mark(curve_name, lbl_mark)

    def mark_item(self, curve_name, lbl_mark):
        name = f'{curve_name}_{lbl_mark}'
        for item in self.pw.items:
            if isinstance(item, TextItemMod) and item.tipo == 'mark' and item.name == name:
                return item
        return None

    def place_mark(self, curve_name, lbl_mark):
        """Dibuja la marca donde dice self.marks, sobre la altura actual de
        su curva. Si el dibujo no existe se crea: antes solo se corria el
        que habia, y una marca que se habia quedado sin dibujo (ver
        delete_all_marks) no volvia a aparecer nunca, aunque la latencia
        siguiera en la tabla."""
        x, y = self.marks[curve_name][lbl_mark]
        if lbl_mark in self.DOT_MARKS:
            self.place_dot(curve_name, lbl_mark, x,
                           y + self.data[curve_name].get('gap', 0.0))
            if lbl_mark in ('BL', 'FIN'):
                self.refresh_base_line(curve_name)
            return
        # La flecha va POR ENCIMA del trazo en pantalla: con el eje
        # invertido, "encima" es restar.
        # El despegue sigue a la escala: 0.1 uV a los 6 del ABR, y a los
        # 40 de la P300 una flecha a 0.1 uV quedaba encima del trazo.
        despegue = self.scale_uv / 60.0
        y = y + self.data[curve_name].get('gap', 0.0) + (
            -despegue if self.y_inverted else despegue)
        item = self.mark_item(curve_name, lbl_mark)
        if item is None:
            html = f"<span style='color: #000; font-size: 7pt;'><h3>&darr;<sup>{lbl_mark}</sup></h3></span>"
            item = TextItemMod(name=f'{curve_name}_{lbl_mark}', tipo='mark', curve_parent=curve_name,
                               html=html, anchor=(0.34, 0.6), color=(0, 0, 0, 255))
            font = QFont()
            font.setPixelSize(13)
            item.setFont(font)
            item.mark_label = lbl_mark
            item.sigMarkDragged.connect(self.drag_mark)
            self.pw.addItem(item)
        item.setPos(x, y)
        if lbl_mark in ('BL', 'FIN'):
            self.refresh_base_line(curve_name)

    # Marcas que son un punto de color sobre el trazo y no una flecha: no
    # senialan un pico sino un nivel (BL) o un limite del area (INI, FIN).
    # Con flecha tapaban el trazo justo donde se mira el despegue. El color
    # es el mismo del boton de la tabla.
    DOT_MARKS = {
        'BL': (110, 110, 110),
        'INI': (0, 150, 70),
        'FIN': (210, 40, 40),
    }

    def place_dot(self, curve_name, lbl_mark, x, y):
        clave = (curve_name, lbl_mark)
        punto = self.dot_items.get(clave)
        if punto is None:
            punto = pg.ScatterPlotItem(
                size=9, pen=pg.mkPen('w', width=1),
                brush=pg.mkBrush(*self.DOT_MARKS[lbl_mark]))
            punto.setZValue(10)
            self.pw.addItem(punto)
            self.dot_items[clave] = punto
        punto.setData([float(x)], [float(y)])

    def remove_dot(self, curve_name, lbl_mark):
        punto = self.dot_items.pop((curve_name, lbl_mark), None)
        if punto is not None:
            self.pw.removeItem(punto)

    def refresh_base_line(self, curve_name):
        """Linea horizontal de la base del ECochG: de BL a FIN.

        Va a la altura que marco BL (que es la base de las medidas, ver
        ecochg.measure_complex), sobre la altura actual de la curva. Sin
        FIN llega hasta el borde de la ventana.
        """
        marcas = self.marks.get(curve_name, {})
        if 'BL' not in marcas or curve_name not in self.data:
            self.remove_base_line(curve_name)
            return
        x0, y0 = marcas['BL']
        x1 = marcas['FIN'][0] if 'FIN' in marcas else self.window_ms
        y = float(y0) + self.data[curve_name].get('gap', 0.0)
        linea = self.base_lines.get(curve_name)
        if linea is None:
            linea = pg.PlotDataItem(pen=pg.mkPen((0, 0, 0, 200), width=1,
                                                 style=Qt.PenStyle.DashLine))
            self.pw.addItem(linea)
            self.base_lines[curve_name] = linea
        linea.setData([float(x0), float(x1)], [y, y])

    # Relleno de cada area, color de fondo y no achurado (con dos achurados
    # cruzados no se distinguia cual era cual): el PS celeste claro y el PA
    # naranja mas firme encima, porque el area del PA esta DENTRO de la del
    # PS (metodo publicado: el PS es el complejo entero).
    AREA_STYLE = {
        'ps': ((60, 150, 230, 70), Qt.BrushStyle.SolidPattern),
        'pa': ((245, 140, 20, 150), Qt.BrushStyle.SolidPattern),
    }

    def set_area_shading(self, curve_name, zonas):
        """Achura (o borra, con None) las areas integradas de la curva."""
        _, viejos = self.area_fills.pop(curve_name, (None, []))
        for item in viejos:
            self.pw.removeItem(item)
        if not zonas or curve_name not in self.data:
            return
        gap = self.data[curve_name].get('gap', 0.0)
        items = []
        for clave, (x, arriba, abajo) in zonas.items():
            if len(x) < 2:
                continue
            color, patron = self.AREA_STYLE[clave]
            c1 = pg.PlotCurveItem(x, arriba + gap, pen=None)
            c2 = pg.PlotCurveItem(x, abajo + gap, pen=None)
            relleno = pg.FillBetweenItem(c1, c2,
                                         brush=QBrush(QColor(*color), patron))
            relleno.setZValue(-5 if clave == 'ps' else -4)
            self.pw.addItem(relleno)
            items += [relleno]
            # Las curvas guia no se dibujan, pero tienen que vivir mientras
            # viva el relleno.
            relleno._guias = (c1, c2)
        self.area_fills[curve_name] = (zonas, items)

    def set_norm_guides(self, lat, signs=None):
        """Rangos normales de latencia por marca ({} las saca)."""
        self.norm_lat = dict(lat or {})
        self.norm_signs = dict(signs or {})
        self.refresh_norm_guides()

    def set_norms_visible(self, visible):
        self.show_norms = bool(visible)
        self.refresh_norm_guides()

    # Color de las cajas: gris azulado translucido, que no compita con el
    # trazo ni con los subpromedios.
    NORM_COLOR = (70, 110, 170)

    def refresh_norm_guides(self):
        """Una caja por marca sobre la curva activa: a lo ancho, el rango
        normal de latencia; arriba de la linea de base si la marca es un
        pico, abajo si es un valle. Solo en la activa: con seis curvas
        apiladas, cajas en todas tapaban los trazos."""
        for item in self.norm_items:
            item.hide()
        self.norm_items = []
        curva = self.act_curve
        if (not self.show_norms or not self.norm_lat
                or curva not in self.data):
            return
        gap = self.data[curva].get('gap', 0.0)
        alto = self.scale_uv * 0.12
        for marca, (desde, hasta) in self.norm_lat.items():
            if desde is None or hasta is None:
                continue
            caja, rotulo = self.norm_pair(marca)
            signo = self.norm_signs.get(marca, 1)
            y0 = gap if signo > 0 else gap - alto
            caja.setRect(float(desde), y0, float(hasta) - float(desde), alto)
            # El rotulo por fuera de la caja: arriba de un pico, abajo de
            # un valle (en pantalla, con el eje como este).
            afuera = (signo > 0) != self.y_inverted
            rotulo.setAnchor((0.5, 1.0 if afuera else 0.0))
            rotulo.setPos((float(desde) + float(hasta)) / 2,
                          y0 + alto if signo > 0 else y0)
            for item in (caja, rotulo):
                item.show()
                self.norm_items.append(item)

    def norm_pair(self, marca):
        par = self.norm_pool.get(marca)
        if par is None:
            borde = pg.mkPen((*self.NORM_COLOR, 160), width=1)
            borde.setCosmetic(True)
            caja = QGraphicsRectItem(0, 0, 1, 1)
            caja.setPen(borde)
            caja.setBrush(QBrush(QColor(*self.NORM_COLOR, 45)))
            caja.setZValue(-6)
            rotulo = pg.TextItem(marca, color=(*self.NORM_COLOR, 230))
            rotulo.setZValue(-6)
            for item in (caja, rotulo):
                self.pw.addItem(item)
            par = self.norm_pool[marca] = (caja, rotulo)
        return par

    def remove_base_line(self, curve_name):
        linea = self.base_lines.pop(curve_name, None)
        if linea is not None:
            self.pw.removeItem(linea)

    def move_marks(self, name_curve):
        """Acompaña la curva cuando cambia su altura (escala, arrastre).

        Solo reubica: la latencia y la amplitud no cambian, asi que no se
        avisa nada. Antes avisaba con la curva ACTIVA en vez de la dueña de
        la marca y, si la activa no tenia esa onda, reventaba con KeyError a
        mitad del cambio de escala: las demas curvas quedaban sin reescalar
        (se iban de la ventana) y el otro oido ni se enteraba."""
        for mark in self.marks.get(name_curve, {}):
            self.place_mark(name_curve, mark)
        self.refresh_base_line(name_curve)
        if name_curve == self.act_curve:
            self.refresh_norm_guides()
        if name_curve in self.area_fills:
            self.set_area_shading(name_curve, self.area_fills[name_curve][0])

    def delete_mark(self, mark):
        curve = self.act_curve
        if self.read_only or mark not in self.marks.get(curve, {}):
            return
        item = self.mark_item(curve, mark)
        if item is not None:
            self.pw.removeItem(item)
        self.remove_dot(curve, mark)
        self.update_value_mark(mark, True, curve=curve)
        if mark in ('BL', 'FIN'):
            self.refresh_base_line(curve)

    def delete_all_marks(self):
        """"Eliminar todas" del menú: todas las de la curva activa, igual
        que las opciones de al lado. Antes sacaba el dibujo de las marcas de
        TODAS las curvas pero solo borraba el registro de la activa: las
        otras seguían con su latencia en la tabla y sin flecha, para siempre."""
        for mark in list(self.marks.get(self.act_curve, {})):
            self.delete_mark(mark)

    def update_value_mark(self, mark, delete=False, curve=None):
        curve = self.act_curve if curve is None else curve
        if not delete:
            x = self.marks[curve][mark]
        else:
            self.marks.get(curve, {}).pop(mark, None)
            x = None
        result = {curve:{mark:x}}
        self.sig_change_value_mark.emit(result)



    ###############HELPERS
    def set_scale(self, uv: float) -> None:
        """Alto de la ventana en uV. Lo fija la prueba, no el widget.

        El ABR se dibuja en 6 uV porque sus ondas son de medio uV; un
        ECochG timpanico tiene el PA en 3.5 uV y con esa escala se sale
        por abajo y se pisa con la curva de al lado. El apilado sigue a la
        escala (gap_ratio), asi que las curvas se separan con ella.
        """
        uv = float(uv)
        if uv <= 0:
            return
        self.scale_base = uv
        self.scale_step = 0
        self.apply_scale(uv)

    def apply_scale(self, uv: float) -> None:
        """Lleva la ventana a `uv` y reescala el apilado en la misma proporcion.

        El gap de cada curva se reescala tambien (incluidas las que el
        alumno movio a mano): esta expresado en uV, no en ranuras, y si no
        acompaña a la escala las curvas se juntan al abrirla y se van de
        pantalla al cerrarla.
        """
        if abs(uv - self.scale_uv) < 1e-9:
            return
        proporcion = uv / self.scale_uv
        self.scale_uv = uv
        self.apply_grid()
        for nombre, datos in self.data.items():
            datos['gap'] = datos.get('gap', 0.0) * proporcion
            self.redraw(nombre)
            self.move_label(nombre)
            self.move_marks(nombre)
        self.apply_view()

    LABEL_MARGIN = 0.13
    FLAG_MARGIN = 0.02

    def set_windows(self, ms: float) -> None:
        """Ajusta el eje a la ventana de registro configurada en el equipo.

        setXRange quiere (min, max); con un solo argumento no hacia nada,
        y de hecho nadie llamaba a este helper.
        """
        anterior = self.window_ms
        self.window_ms = float(ms)
        # El margen derecho es de las etiquetas de las curvas: con 8 % se
        # cortaban ("70 dB n"). El izquierdo, para la bandera A: en 0 ms
        # quedaba pegada al borde del eje y no habia de donde agarrarla.
        self.pw.setXRange(-self.window_ms * self.FLAG_MARGIN,
                          self.window_ms * (1 + self.LABEL_MARGIN),
                          padding=0)
        self.apply_grid()
        # Una base sin FIN llega al borde: si el borde se movio, ella tambien.
        for nombre in list(self.base_lines):
            self.refresh_base_line(nombre)
        # Las banderas guardan su lugar en proporcion a la ventana. Antes
        # solo se recortaban al borde: del ABR (12 ms) al CAEP (500 ms)
        # quedaban A en 0 y A' en 12, una encima de la otra contra el eje.
        proporcion = self.window_ms / anterior if anterior > 0 else 1.0
        for item in (getattr(self, 'inf_a', None),
                     getattr(self, 'inf_b', None)):
            if item is not None:
                x = item.getXPos() * proporcion
                item.setPos((max(0.0, min(self.window_ms, x)), 0))

    # Divisiones de la grilla por ventana de escala: 6 da la grilla de
    # 1 uV del ABR a 6 uV.
    GRID_DIVISIONS = 6

    def apply_grid(self):
        """La grilla sigue a la escala. Fija en 1 uV, a 48 uV eran ~70
        lineas y a 192 uV mas de 300: una mancha gris que tapaba las
        curvas, que ademas a esa escala ya eran casi planas."""
        self.grid.setTickSpacing(x=[self.x_tick()], y=[self.y_tick()])

    def y_tick(self):
        """Paso de la grilla en uV: la escala en seis. Si eso no da un
        numero limpio (los 40 uV de la P300 daban 6.66667 y la grilla lo
        escribia asi) se toma el paso redondo mas cercano."""
        paso = self.scale_uv / self.GRID_DIVISIONS
        if abs(paso * 8 - round(paso * 8)) < 1e-6:
            return paso
        magnitud = 10 ** np.floor(np.log10(paso))
        redondos = np.array([1.0, 2.0, 2.5, 5.0, 10.0]) * magnitud
        return float(redondos[np.argmin(np.abs(redondos - paso))])

    def x_tick(self):
        """Paso de la grilla en ms: 1 ms en el ABR, 10 en el MLR y 50 en
        los tardios. Con 1 ms fijo, una ventana de 800 ms eran 800 lineas."""
        if self.window_ms <= 30:
            return 1.0
        if self.window_ms <= 200:
            return 10.0
        return 50.0

    # Hasta cuantas mitades y dobles (en uV) de la escala base se llega.
    # Con los 6 uV del ABR: de 0.75 a 48 uV.
    SCALE_STEPS = (-3, 3)

    def scale(self, direction):
        """Un paso de la escalera de escalas: el doble o la mitad.

        '+' agranda las curvas (la mitad de uV en la ventana) y '-' las
        achica. Al reves, '+' las aplastaba hasta que parecian desaparecer.

        En el tope no hace nada, ni un recorte: asi cada paso es siempre
        x2 o /2 y volver sobre los pasos devuelve exactamente la escala de
        la prueba.
        """
        paso = self.scale_step + {'plus': -1, 'minus': 1}.get(direction, 0)
        lo, hi = self.SCALE_STEPS
        if lo <= paso <= hi and paso != self.scale_step:
            self.scale_step = paso
            self.apply_scale(self.scale_base * 2 ** paso)
        return self.get_scale()

    def set_y_inverted(self, inverted: bool) -> None:
        """Da vuelta el eje Y. Solo el dibujo: las amplitudes y las marcas
        guardadas no cambian de signo."""
        self.y_inverted = bool(inverted)
        self.pw.invertY(self.y_inverted)
        # La grilla escribe sus numeros con la transformacion de la vista:
        # invertida, salen espejados. Se apagan; la escala sigue en el
        # rotulo de la barra.
        self.grid.setTextPen(None if self.y_inverted else self.color_texto)
        for nombre in self.data:
            self.move_marks(nombre)

    def move_label(self, curve):
        """Deja la etiqueta de intensidad a la altura de su curva."""
        for item in self.pw.items:
            if (isinstance(item, TextItemMod) and item.tipo == 'label'
                    and item.curve_parent == curve):
                item.setPos(self.window_ms, self.data[curve]['gap'])

    def get_scale(self):
        return self.scale_uv
        
    def find_nearest(self, array_in, value, array_out):
        array = np.asarray(array_in)
        idx = (np.abs(array - value)).argmin()
        return array_out[idx]

    def find_idx(self, array_in, value):
        array = np.asarray(array_in)
        return (np.abs(array - value)).argmin()
    
    def get_data(self, intencity):
        #
        #if name in self.data:
        #    return self.data[name]
        #else:
        #print(self.data)
        value = None
        for i in self.data:
            if self.data[i]["done"] == True:
                if self.data[i]["intencity"] == intencity:
                    value = self.data[i]["repro"]
        return value

    def limpiar_todo(self):
        """Limpia completamente el gráfico: todas las curvas, labels y marcas"""
        # Eliminar todos los PlotDataItems (curvas)
        for item in self.pw.listDataItems()[:]:
            self.pw.removeItem(item)

        # Eliminar todos los TextItemMod (labels y marcas)
        for item in self.pw.items[:]:
            if isinstance(item, TextItemMod):
                self.pw.removeItem(item)

        # Las lineas de base son PlotDataItem y ya salieron arriba.
        self.base_lines = {}
        for clave in list(self.dot_items):
            self.remove_dot(*clave)
        for nombre in list(self.area_fills):
            self.set_area_shading(nombre, None)
        # Limpiar diccionarios internos
        self.data = {}
        self.marks = {}
        self.curve_int = {}
        self.curve_cfg = {}
        self.traces = {}
        self.act_curve = None
        self.refresh_norm_guides()
        self.apply_view()

    def export_(self):
        import os
        self.inf_a.hide()
        self.inf_b.hide()
        width = self.pw.size().width()
        height = self.pw.size().height()
        options = {'width':width, 'height':height, 'background': self.color_background}
        #export = generateSvg(self.pw, options=options)
        export = pg.exporters.ImageExporter(self.pw)

        temp_dir = context.get_resource("local_cache/abr/temp")
        os.makedirs(temp_dir, exist_ok=True)
        output_file = os.path.join(temp_dir, f'{self.side}.png')
        export.export(output_file)

    def export_jpg(self, path: str) -> None:
        """Como export_(), pero a JPEG (para subir el informe al backend --
        ver ReportFile.php, que solo acepta JPEG para no depender de GD).

        Las guias normativas no van al informe: son de la pantalla."""
        for item in self.norm_items:
            item.hide()
        try:
            export = pg.exporters.ImageExporter(self.pw)
            export.export(path)
        finally:
            for item in self.norm_items:
                item.show()

        self.inf_a.show()
        self.inf_b.show()


