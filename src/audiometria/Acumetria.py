# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.3 - Acumetria                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
"""Diapasones sobre la cabeza del paciente (2026-11-06).

Va en la ventana de otoscopía y diapasones (ventana_ot_ac.py), que tiene
la cabeza (cabeza_examen.py: se gira y se le apoya el diapasón donde uno
quiera) y las frases al paciente. Este módulo pone sus secciones en el
panel (el diapasón: 512 o 1024 Hz, golpearlo, cuánto vibra todavía), la
conversación y lo que contesta el paciente.

No hay botones de "Rinne" ni de "Weber": la prueba la hace el alumno con
dónde pone el diapasón y lo que le dice al paciente.

- Mastoides: vía ósea de ese lado (responde la mejor cóclea).
- Frente a la oreja: vía aérea de ese oído.
- Línea media (frente, vértex): el Weber.
- Golpeado: suena y se apaga solo, con la misma caída que la barra de
  vibración (audio_synth.diapason_file); sin golpear no suena.

El paciente contesta lo que le instruyeron o le preguntaron, con lo que
dice el caso (diapasones.py: los tiempos salen del audiograma y mandan el
Rinne y el Weber que marcó el docente). Sin instrucción, al sentir el
diapasón no sabe qué hacer. ("Avíseme cuando deje de escucharlo", el Rinne
por tiempo, salió el 2026-11-13: nadie lo usaba.) Con "Compare dónde suena más
fuerte" (Rinne) y "Dígame dónde lo escucha" (Weber) no habla al apoyarle el
diapasón: contesta lo que se le pregunta ("¿Lo escucha?" en cada posición,
"¿Dónde lo escuchó más fuerte?" al final). Sin Rinne/Weber en el caso, el
diapasón suena con armónicos y no sirve.

Todo va a action_logs con prefijo ac_ y la verdad del caso en el payload.
"""
import html
import time

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QStackedLayout, QTextEdit, QVBoxLayout, QWidget,
)

from audiometria import audio_synth
from audiometria import diapasones as dp
from audiometria import no_realizable
from audiometria.cabeza_examen import zona
from audiometria.comandos_voz import SILENCIO
from backend.log_queue import get_log_queue
from core import iconos, tema
from core.base import context

EXTRA_QSS = f"""
QTextEdit[conversacion="true"] {{ border: none; background: {tema.TARJETA}; font-size: 10pt; }}
QProgressBar#vibracion {{ border: 1px solid {tema.BORDE}; border-radius: 5px; background: {tema.TARJETA_ALT};
                          max-height: 10px; text-align: center; }}
QProgressBar#vibracion::chunk {{ background: {tema.ACENTO}; border-radius: 4px; }}
QLabel#armonicos {{ color: {tema.ALERTA}; font-weight: 600; }}
QPushButton[segmento="true"] {{ padding: 4px 0px; }}
QPushButton[herramienta="true"] {{ padding: 5px 0px; font-weight: 600; }}
QPushButton[herramienta="true"]:checked {{ background: {tema.ACENTO}; border-color: {tema.ACENTO}; color: white; }}
"""

# Lo que el evaluador le dice al paciente (audiometria/frases_habladas.py).
# Las claves son también el nombre del audio (resources/audio/comandos_ac/,
# scripts/voces_comandos.py --ac): no se cambian aunque cambie el rótulo.
GRUPOS = (
    ("PREPARAR", (
        ("Explicar los diapasones", "explicar_diapasones"),
    )),
    ("INSTRUCCIONES", (
        ("Avíseme si lo escucha", "avise_si_escucha"),
        ("Compare dónde suena más fuerte", "compare_sonidos"),
        ("Dígame dónde lo escucha", "diga_donde"),
    )),
    ("PREGUNTAS", (
        ("¿Lo escucha?", "lo_escucha"),
        ("¿Lo sigue escuchando?", "sigue_escuchando"),
        ("¿Lo escucha o lo siente vibrar?", "escucha_o_vibra"),
        ("¿Dónde lo escuchó más fuerte?", "donde_mas_fuerte"),
        ("¿Igual en los dos oídos?", "igual_ambos"),
    )),
)
PRUEBA = {"compare_sonidos": "Rinne", "diga_donde": "Weber", "igual_ambos": "Weber"}
INSTRUCCIONES = {"avise_si_escucha", "compare_sonidos", "diga_donde"}
NO_SABE = "¿Y qué tengo que hacer?"
DONDE_WEBER = {"od": "En el oído derecho.", "oi": "En el oído izquierdo.",
               "centrado": "Al medio, en toda la cabeza."}
ARMONICOS = "Diapasón sonando con armónicos"
LADO = {"od": "derecho", "oi": "izquierdo"}
DONDE_TEXTO = {"mastoides": "en la mastoides", "pabellon": "frente al pabellón",
               "linea_media": "en la línea media", "fuera_de_linea": "en la frente, a un lado de la línea media",
               "otro": "en la cabeza"}
TICK_MS = 200
# Recién golpeado suena como una frase del talkback, no como una alarma.
VOLUMEN_DIAPASON = 0.6


class Acumetria(QWidget):

    def __init__(self, thr=None):
        super().__init__()
        self.data = None
        self.appointment_id = None
        self.modelo = dp.ModeloDiapasones({})
        self.log_queue = get_log_queue()
        self._instruccion = None    # la instrucción vigente (INSTRUCCIONES)
        self._golpe = None          # time.monotonic() del último golpe
        self._apoyo = None          # dónde está el diapasón ahora (dict) o None
        self._rinne = None          # {'oido', 'hz', 'golpe', 'vistos': set()} para comparar
        self._ultimo = None         # lo último que sintió (el apoyo ya retirado y si lo oía)
        self._reloj = time.monotonic

        self.cabeza = None            # la de la ventana (conectar)
        self.pedir_herramienta = None # la ventana elige la herramienta Diapasón al golpear

        tema.aplicar_estilo(self, EXTRA_QSS)
        # Las secciones del panel (diapasón y vibración); la conversación va
        # aparte para que la ventana la ponga abajo del panel
        self.equipo = self._secciones()
        self.conversacion = self._conversacion()
        self.aviso_bebe = no_realizable.AvisoNoRealizable("Acumetría no realizable")
        self.pila = QStackedLayout(self)
        self.pila.addWidget(self.equipo)
        self.pila.addWidget(self.aviso_bebe)

        self._tick = QTimer(self)
        self._tick.setInterval(TICK_MS)
        self._tick.timeout.connect(self._mostrar_vibracion)
        # El sonido del diapasón golpeado (lo oye el alumno, no el paciente)
        self._salida = QAudioOutput(self)
        self._salida.setVolume(VOLUMEN_DIAPASON)
        self._sonido = QMediaPlayer(self)
        self._sonido.setAudioOutput(self._salida)
        self.la_super(thr)

    def conectar(self, cabeza):
        """La cabeza de la ventana de otoscopía y diapasones."""
        self.cabeza = cabeza
        cabeza.apoyado.connect(self._apoyar_si_diapason)

    def _sacar_de_la_cabeza(self):
        if self.cabeza is not None:
            self.cabeza.poner_diapason(None)

    def _apoyar_si_diapason(self, punto, normal):
        if self.cabeza is not None and self.cabeza.herramienta == "diapason":
            self._apoyar(punto, normal)

    # ------------------------------------------------------------ armado
    @staticmethod
    def _seccion(texto):
        lbl = QLabel(texto)
        lbl.setProperty("role", "seccion")
        return lbl

    def _secciones(self):
        caja = QWidget()
        pcol = QVBoxLayout(caja)
        pcol.setContentsMargins(0, 0, 0, 0)
        pcol.setSpacing(6)
        pcol.addWidget(self._seccion("DIAPASÓN"))
        fila = QHBoxLayout()
        fila.setSpacing(4)
        self.grupo_hz = QButtonGroup(self)
        self.botones_hz = {}
        for hz, texto in dp.DIAPASONES:
            b = QPushButton(texto)
            b.setCheckable(True)
            b.setProperty("segmento", "true")
            self.grupo_hz.addButton(b)
            self.botones_hz[hz] = b
            fila.addWidget(b, 1)
        # Marcado antes de conectar: el cambio de diapasón necesita la barra
        self.botones_hz["500"].setChecked(True)
        for hz, b in self.botones_hz.items():
            b.toggled.connect(lambda marcado, h=hz: marcado and self._cambiar_diapason(h))
        pcol.addLayout(fila)
        self.btn_golpear = QPushButton(" Golpear el diapasón")
        self.btn_golpear.setIcon(iconos.icono_boton("diapason", tema.TEXTO_SUAVE, tam=16))
        self.btn_golpear.clicked.connect(self._golpear)
        pcol.addWidget(self.btn_golpear)
        self.barra = QProgressBar()
        self.barra.setObjectName("vibracion")
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        pcol.addWidget(self.barra)
        self.lbl_estado = QLabel("Quieto, sin golpear.")
        self.lbl_estado.setProperty("role", "hint")
        pcol.addWidget(self.lbl_estado)
        self.lbl_armonicos = QLabel(ARMONICOS)
        self.lbl_armonicos.setObjectName("armonicos")
        self.lbl_armonicos.setWordWrap(True)
        self.lbl_armonicos.hide()
        pcol.addWidget(self.lbl_armonicos)
        self.btn_retirar = QPushButton(" Retirar el diapasón")
        self.btn_retirar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_SUAVE, tam=14))
        self.btn_retirar.clicked.connect(self._retirar)
        pcol.addWidget(self.btn_retirar)
        return caja

    def _conversacion(self):
        caja = QWidget()
        col = QVBoxLayout(caja)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(6)
        col.addWidget(self._seccion("CONVERSACIÓN"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setProperty("conversacion", "true")
        self.log.setPlaceholderText("Lo que le digas al paciente y lo que él conteste.")
        tema.aplicar_estilo(caja, EXTRA_QSS)
        col.addWidget(self.log, 1)
        return caja

    # ------------------------------------------------------------ caso
    def la_super(self, data, appointment_id=None):
        """Hidrata (o deshidrata, data=None) el módulo con el caso actual --
        llamado por MainWindow._hydrate_modules() cada vez que cambia el
        caso activo. Paciente nuevo: no le han dicho nada todavía."""
        self.data = data
        self.appointment_id = appointment_id
        self.modelo = dp.ModeloDiapasones(data)
        self._instruccion = None
        self._golpe = None
        self._apoyo = None
        self._rinne = None
        self._ultimo = None
        self._sonido.stop()
        self.log.clear()
        if self.cabeza is not None:
            self.cabeza.poner_diapason(None)
        sirve = not data or self.modelo.disponible()
        self.lbl_armonicos.setVisible(not sirve)
        self.btn_golpear.setEnabled(sirve)
        self._mostrar_vibracion()
        motivo = no_realizable.motivo(data, "acumetría")
        if motivo:
            self.aviso_bebe.texto.setText(motivo)
        self.pila.setCurrentWidget(self.aviso_bebe if motivo else self.equipo)

    def _log(self, action, **payload):
        """Encola una acción del alumno con los diapasones (prefijo ac_, ver
        backend/log_queue.py), con la verdad del caso en el payload."""
        case_id = self.data.get("id") if self.data else None
        if case_id is not None:
            payload.setdefault("case_id", case_id)
        payload.setdefault("appointment_id", self.appointment_id)
        payload.setdefault("con_paciente", case_id is not None)
        self.log_queue.push(action, payload)

    def _decir(self, texto):
        """Una línea de la conversación: "Tú:" y "Paciente:" con su color."""
        quien, sep, resto = texto.partition(": ")
        if sep and quien in ("Tú", "Paciente"):
            color = tema.ACENTO if quien == "Tú" else tema.TEXTO_SUAVE
            self.log.append(f'<p style="margin:0 0 6px 0"><b style="color:{color}">{quien}</b> '
                            f'<span style="color:{tema.TEXTO}">{html.escape(resto)}</span></p>')
        else:
            self.log.append(html.escape(texto))

    # ------------------------------------------------------------ diapasón
    def hz(self):
        return next(h for h, b in self.botones_hz.items() if b.isChecked())

    def _desde_golpe(self):
        return None if self._golpe is None else self._reloj() - self._golpe

    def _vibra(self):
        t = self._desde_golpe()
        return t is not None and dp.vibracion(t) > 0

    def _cambiar_diapason(self, hz):
        """Tomar el otro diapasón: está quieto, y el que estaba apoyado se va."""
        if self._golpe is not None or self._apoyo is not None:
            self._log("ac_cambiar_diapason", hz=hz)
        self._golpe = None
        self._apoyo = None
        self._rinne = None
        self._ultimo = None
        self._sonido.stop()
        self._sacar_de_la_cabeza()
        self._mostrar_vibracion()

    def _sonar(self):
        """Desde el principio: golpearlo de nuevo lo vuelve a subir entero."""
        ruta = audio_synth.diapason_file(dp.HZ_REAL[self.hz()], dp.duracion_vibracion(),
                                         dp.CAIDA_DB_S, context.get_resource("audio"))
        self._sonido.stop()
        if ruta is None:
            return
        self._sonido.setSource(QUrl.fromLocalFile(ruta))
        self._sonido.play()

    def _golpear(self):
        if not self.modelo.disponible():
            return
        self._golpe = self._reloj()
        self._apoyo = None
        self._rinne = None
        self._ultimo = None
        self._sacar_de_la_cabeza()
        self._log("ac_golpe", hz=self.hz())
        if self.pedir_herramienta is not None:
            self.pedir_herramienta("diapason")
        self._decir(f"Tú: golpeas el diapasón de {dict(dp.DIAPASONES)[self.hz()]}.")
        self._sonar()
        self._tick.start()
        self._mostrar_vibracion()

    def _retirar(self):
        if self._apoyo is None:
            return
        self._log("ac_retirar", hz=self.hz(), zona=self._apoyo["zona"])
        # Lo que sintió queda: se le puede preguntar después de sacarlo
        self._ultimo = dict(self._apoyo, oia=self._oye_ahora(self._apoyo))
        self._apoyo = None
        self._sacar_de_la_cabeza()
        self._decir("Tú: retiras el diapasón.")
        self.btn_retirar.setEnabled(False)

    def _mostrar_vibracion(self):
        t = self._desde_golpe()
        nivel = dp.vibracion(t) if t is not None else 0.0
        self.barra.setValue(int(nivel * 100))
        if t is None:
            self.lbl_estado.setText("Quieto, sin golpear.")
        elif nivel > 0:
            self.lbl_estado.setText(f"Vibrando · {dp.redondear(t)} s desde el golpe")
        else:
            self.lbl_estado.setText("Ya no vibra: hay que golpearlo de nuevo.")
            self._tick.stop()
            self._sonido.stop()
        self.btn_retirar.setEnabled(self._apoyo is not None)

    def _dura(self, apoyo):
        """Cuánto lo oye en esa posición, desde el golpe (segundos)."""
        hz = self.hz()
        if apoyo["zona"] == "pabellon":
            return self.modelo.tiempos(hz, apoyo["oido"])[0]
        if apoyo["zona"] == "mastoides":
            return self.modelo.tiempos(hz, apoyo["oido"])[1]
        return self.modelo.tiempo_weber(hz)

    def _oye_ahora(self, apoyo):
        t = self._desde_golpe()
        return t is not None and dp.oye(self._dura(apoyo), t)

    def _apoyar(self, punto, normal):
        if not self.data:
            self._decir("Paciente: (no hay un caso cargado)")
            return
        if not self.modelo.disponible():
            self._decir(f"({ARMONICOS}: no sirve para examinar.)")
            return
        donde, oido, sitio, dist = zona(punto)
        apoyo = {"zona": donde, "oido": oido, "sitio": sitio}
        self._apoyo = apoyo
        self._ultimo = None
        if self.cabeza is not None:
            self.cabeza.poner_diapason(punto, normal)
        self.btn_retirar.setEnabled(True)
        hz = self.hz()
        t = self._desde_golpe()
        oye = self._oye_ahora(apoyo)
        verdad = {}
        if donde in ("pabellon", "mastoides"):
            t_aire, t_hueso = self.modelo.tiempos(hz, oido)
            verdad = {"rinne": self.modelo.rinne(hz, oido), "t_aire": t_aire, "t_hueso": t_hueso}
        elif donde in ("linea_media", "fuera_de_linea"):
            verdad = {"weber": self.modelo.weber(hz), "t_weber": self.modelo.tiempo_weber(hz)}
        self._log("ac_apoyo", hz=hz, zona=donde, oido=oido, sitio=sitio, distancia_mm=round(dist * 1000),
                  desde_golpe_s=None if t is None else round(t, 1), vibrando=self._vibra(),
                  oye=oye, instruccion=self._instruccion, **verdad)
        lado = f" {LADO[oido]}" if oido in LADO and donde in ("mastoides", "pabellon") else ""
        if donde == "pabellon":
            self._decir(f"Tú: pones el diapasón frente al pabellón del oído{lado}.")
        elif donde == "mastoides":
            self._decir(f"Tú: apoyas el diapasón en la mastoides{lado}.")
        else:
            self._decir(f"Tú: apoyas el diapasón {DONDE_TEXTO[donde]}.")
        # Para comparar en el Rinne: las dos posiciones del mismo oído con
        # el mismo golpe
        if donde in ("pabellon", "mastoides"):
            if not self._rinne or self._rinne["oido"] != oido or self._rinne["golpe"] != self._golpe:
                self._rinne = {"oido": oido, "golpe": self._golpe, "vistos": set()}
            self._rinne["vistos"].add(donde)
        respuesta = self._al_sentirlo(apoyo, oye)
        if respuesta:
            self._decir(f"Paciente: {respuesta}")

    def _al_sentirlo(self, apoyo, oye):
        """Lo que dice el paciente al ponerle el diapasón, según la
        instrucción vigente.

        Solo "Avíseme si lo escucha" lo hace hablar solo. Con "Compare dónde suena más fuerte" (Rinne) y "Dígame dónde
        lo escucha" (Weber) espera callado a que le pregunten: el alumno
        apoya, pregunta "¿Lo escucha?", cambia de posición, vuelve a
        preguntar y recién con "¿Dónde lo escuchó más fuerte?" compara."""
        contacto = apoyo["zona"] != "pabellon"
        if self._instruccion in ("compare_sonidos", "diga_donde"):
            return None
        if not self._vibra():
            if self._instruccion in INSTRUCCIONES:
                return "No escucho nada."
            return None
        if self._instruccion not in INSTRUCCIONES:
            return NO_SABE
        no_oye = "Siento que vibra, pero no lo escucho." if contacto else "No escucho nada."
        return "Sí, lo escucho." if oye else no_oye

    def _contestar_despues(self, clave, ultimo):
        """Con el diapasón ya retirado: contesta por lo que sintió mientras
        estaba puesto (como se hace en la consulta: se pone, se saca y se
        pregunta)."""
        oia = ultimo["oia"]
        contacto = ultimo["zona"] != "pabellon"
        if clave in ("lo_escucha", "sigue_escuchando"):
            return "Ahora no, ya lo sacó." if oia else "No, no lo escuché."
        if clave == "escucha_o_vibra":
            if oia:
                return "Lo escuchaba."
            return "Solo sentía que vibraba." if contacto else "No escuché nada."
        if clave == "donde_mas_fuerte":
            if self._rinne and ultimo["zona"] in ("pabellon", "mastoides") \
                    and self._rinne["vistos"] >= {"pabellon", "mastoides"}:
                return self._comparacion_rinne().replace("suena", "sonaba")
            if ultimo["zona"] in ("linea_media", "fuera_de_linea"):
                return DONDE_WEBER.get(self.modelo.weber(self.hz()), DONDE_WEBER["centrado"]) if oia \
                    else "No lo escuché."
            return "No sé... me lo puso en un solo lado."
        # igual_ambos
        if ultimo["zona"] in ("linea_media", "fuera_de_linea"):
            if not oia:
                return "No lo escuché."
            return {"od": "No, más en el derecho.", "oi": "No, más en el izquierdo."}.get(
                self.modelo.weber(self.hz()), "Sí, igual en los dos.")
        return "No sé, lo sentí de un lado nomás."

    def _comparacion_rinne(self):
        """Negativo y falso negativo suenan igual para el paciente: la
        trampa del falso negativo la descubre el alumno."""
        if self.modelo.rinne(self.hz(), self._rinne["oido"]) == "positivo":
            return "Adelante, frente a la oreja. Ahí suena más fuerte."
        return "Atrás, en el hueso. Ahí suena más fuerte."

    # ------------------------------------------------------------ lo que se le dice
    def _frase(self, clave):
        """Una frase del panel: se dice (FrasesHabladas), queda en la
        conversación y el paciente la contesta. Una instrucción queda
        vigente hasta que se dé otra; una pregunta se contesta y no la
        reemplaza."""
        if clave == SILENCIO:
            return
        texto = next((t for _g, frases in GRUPOS for t, c in frases if c == clave), clave)
        self._decir(f"Tú: «{texto}»")
        if not self.data:
            self._decir("Paciente: (no hay un caso cargado)")
            return
        if clave == "explicar_diapasones":
            respuesta = "Bueno, ya."
        elif clave in INSTRUCCIONES:
            self._instruccion = clave
            respuesta = "Ya, bueno."
        else:
            respuesta = self._contestar(clave)
        self._decir(f"Paciente: {respuesta}")
        tipo = "ac_instruccion" if clave in INSTRUCCIONES or clave == "explicar_diapasones" else "ac_pregunta"
        apoyo = self._apoyo or self._ultimo or {}
        self._log(tipo, clave=clave, respuesta=respuesta, hz=self.hz(), zona=apoyo.get("zona"),
                  oido=apoyo.get("oido"), vibrando=self._vibra(), retirado=self._apoyo is None and bool(apoyo),
                  oye=apoyo.get("oia") if self._apoyo is None else self._oye_ahora(apoyo))

    def _contestar(self, clave):
        apoyo = self._apoyo
        if not self.modelo.disponible():
            return "No escucho nada."
        if apoyo is None and self._ultimo is not None:
            return self._contestar_despues(clave, self._ultimo)
        if apoyo is None or not self._vibra():
            if clave in ("donde_mas_fuerte", "igual_ambos"):
                return "¿Qué cosa?"
            return "¿Qué cosa? No siento nada." if apoyo is None else "No, nada."
        oye = self._oye_ahora(apoyo)
        contacto = apoyo["zona"] != "pabellon"
        if clave == "lo_escucha":
            return "Sí." if oye else ("Siento que vibra nomás." if contacto else "No.")
        if clave == "sigue_escuchando":
            return "Sí, todavía." if oye else "No, ya no."
        if clave == "escucha_o_vibra":
            if oye:
                return "Lo escucho."
            return "Solo siento que vibra." if contacto else "No escucho nada."
        if clave == "donde_mas_fuerte":
            if self._rinne and apoyo["zona"] in ("pabellon", "mastoides") \
                    and self._rinne["vistos"] >= {"pabellon", "mastoides"}:
                return self._comparacion_rinne()
            if apoyo["zona"] in ("linea_media", "fuera_de_linea"):
                return DONDE_WEBER.get(self.modelo.weber(self.hz()), DONDE_WEBER["centrado"]) if oye \
                    else "No lo escucho."
            return "No sé... me lo puso en un solo lado."
        # igual_ambos
        if apoyo["zona"] in ("linea_media", "fuera_de_linea") and oye:
            return {"od": "No, más en el derecho.", "oi": "No, más en el izquierdo."}.get(
                self.modelo.weber(self.hz()), "Sí, igual en los dos.")
        if apoyo["zona"] in ("linea_media", "fuera_de_linea"):
            return "No lo escucho."
        return "No sé, lo siento de este lado nomás."
