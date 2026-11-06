# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.3 - Acumetria                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
"""Diapasones sobre la cabeza del paciente (2026-11-06).

A la izquierda lo que se le dice al paciente (frases_habladas.py), al
centro la cabeza (cabeza_examen.py: se gira y se le apoya el diapasón donde
uno quiera) y a la derecha el diapasón (512 o 1024 Hz, golpearlo, cuánto
vibra todavía) y la conversación.

No hay botones de "Rinne" ni de "Weber": la prueba la hace el alumno con
dónde pone el diapasón y lo que le dice al paciente.

- Mastoides: vía ósea de ese lado (responde la mejor cóclea).
- Frente a la oreja: vía aérea de ese oído.
- Línea media (frente, vértex): el Weber.
- Golpeado: se apaga solo; sin golpear no suena.

El paciente contesta lo que le instruyeron o le preguntaron, con lo que
dice el caso (diapasones.py: los tiempos salen del audiograma y mandan el
Rinne y el Weber que marcó el docente). Sin instrucción, al sentir el
diapasón no sabe qué hacer. Con "Avíseme cuando deje de escucharlo" avisa
solo cuando el diapasón baja de su umbral. Sin Rinne/Weber en el caso, el
diapasón suena con armónicos y no sirve.

Todo va a action_logs con prefijo ac_ y la verdad del caso en el payload.
"""
import html
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy,
    QStackedLayout, QTextEdit, QVBoxLayout, QWidget,
)

from audiometria import diapasones as dp
from audiometria import no_realizable
from audiometria.cabeza_examen import VISTA_ARRIBA, VISTA_FRENTE, CabezaExamen, zona
from audiometria.comandos_voz import SILENCIO
from audiometria.frases_habladas import FrasesHabladas
from backend.log_queue import get_log_queue
from core import iconos, tema

EXTRA_QSS = f"""
QPushButton[paso="true"] {{ text-align: left; padding: 8px 12px; }}
QTextEdit[conversacion="true"] {{ border: none; background: transparent; font-size: 10pt; }}
QProgressBar#vibracion {{ border: 1px solid {tema.BORDE}; border-radius: 5px; background: {tema.TARJETA_ALT};
                          max-height: 10px; text-align: center; }}
QProgressBar#vibracion::chunk {{ background: {tema.ACENTO}; border-radius: 4px; }}
QLabel#armonicos {{ color: {tema.ALERTA}; font-weight: 600; }}
"""

# Lo que el evaluador le dice al paciente (audiometria/frases_habladas.py).
# Las claves son también el nombre del audio (resources/audio/comandos_ac/,
# scripts/voces_comandos.py --ac): no se cambian aunque cambie el rótulo.
GRUPOS = (
    ("PREPARAR", (
        ("Explicar el examen", "explicar_diapasones"),
    )),
    ("INSTRUCCIONES", (
        ("Avíseme si lo escucha", "avise_si_escucha"),
        ("Avíseme cuando deje de escucharlo", "avise_cuando_deje"),
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
PRUEBA = {"compare_sonidos": "Rinne", "diga_donde": "Weber", "igual_ambos": "Weber",
          "avise_cuando_deje": "Rinne por tiempo"}
INSTRUCCIONES = {"avise_si_escucha", "avise_cuando_deje", "compare_sonidos", "diga_donde"}
NO_SABE = "¿Y qué tengo que hacer?"
DONDE_WEBER = {"od": "En el oído derecho.", "oi": "En el oído izquierdo.",
               "centrado": "Al medio, en toda la cabeza."}
ARMONICOS = "Diapasón sonando con armónicos"
LADO = {"od": "derecho", "oi": "izquierdo"}
DONDE_TEXTO = {"mastoides": "en la mastoides", "pabellon": "frente al pabellón",
               "linea_media": "en la línea media", "fuera_de_linea": "en la frente, a un lado de la línea media",
               "otro": "en la cabeza"}
TICK_MS = 200


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
        self._aviso_id = 0          # para el "ya no lo escucho" programado
        self._reloj = time.monotonic

        tema.aplicar_estilo(self, EXTRA_QSS)
        self.equipo = QWidget()
        fila = QHBoxLayout(self.equipo)
        fila.setContentsMargins(12, 8, 12, 12)
        fila.setSpacing(12)
        self.frases = FrasesHabladas(GRUPOS, PRUEBA, "comandos_ac")
        self.frases.setFixedWidth(250)
        self.frases.btn_checked.connect(self._frase)
        fila.addWidget(self.frases)
        fila.addWidget(self._centro(), 1)
        fila.addWidget(self._derecha())

        self.aviso_bebe = no_realizable.AvisoNoRealizable("Acumetría no realizable")
        self.pila = QStackedLayout(self)
        self.pila.addWidget(self.equipo)
        self.pila.addWidget(self.aviso_bebe)

        self._tick = QTimer(self)
        self._tick.setInterval(TICK_MS)
        self._tick.timeout.connect(self._mostrar_vibracion)
        self.la_super(thr)

    # ------------------------------------------------------------ armado
    @staticmethod
    def _tarjeta():
        tarjeta = QFrame()
        tarjeta.setProperty("card", "true")
        col = QVBoxLayout(tarjeta)
        col.setContentsMargins(14, 12, 14, 14)
        col.setSpacing(8)
        return tarjeta, col

    @staticmethod
    def _seccion(texto):
        lbl = QLabel(texto)
        lbl.setProperty("role", "seccion")
        return lbl

    def _centro(self):
        tarjeta, col = self._tarjeta()
        self.cabeza = CabezaExamen()
        self.cabeza.poner_herramienta("diapason")
        self.cabeza.apoyado.connect(self._apoyar)
        col.addWidget(self.cabeza, 1)
        vistas = QHBoxLayout()
        vistas.setSpacing(6)
        pista = QLabel("Arrastra para girar la cabeza. Clic en la piel: ahí se apoya el diapasón.")
        pista.setProperty("role", "hint")
        pista.setWordWrap(True)
        vistas.addWidget(pista, 1)
        for texto, vista in (("Frente", VISTA_FRENTE), ("Derecha", (90, 0)), ("Izquierda", (270, 0)),
                             ("Arriba", VISTA_ARRIBA)):
            b = QPushButton(texto)
            b.clicked.connect(lambda _c=False, v=vista: self.cabeza.mirar(*v))
            vistas.addWidget(b)
        col.addLayout(vistas)
        return tarjeta

    def _derecha(self):
        caja = QWidget()
        caja.setFixedWidth(340)
        col = QVBoxLayout(caja)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(10)

        tarjeta, v = self._tarjeta()
        v.addWidget(self._seccion("DIAPASÓN"))
        fila = QHBoxLayout()
        fila.setSpacing(6)
        self.grupo_hz = QButtonGroup(self)
        self.botones_hz = {}
        for hz, texto in dp.DIAPASONES:
            b = QPushButton(texto)
            b.setCheckable(True)
            self.grupo_hz.addButton(b)
            self.botones_hz[hz] = b
            fila.addWidget(b, 1)
        # Marcado antes de conectar: el cambio de diapasón necesita la barra
        self.botones_hz["500"].setChecked(True)
        for hz, b in self.botones_hz.items():
            b.toggled.connect(lambda marcado, h=hz: marcado and self._cambiar_diapason(h))
        v.addLayout(fila)
        self.btn_golpear = QPushButton(" Golpear el diapasón")
        self.btn_golpear.setIcon(iconos.icono("diapason", tema.ACENTO, 18))
        self.btn_golpear.setProperty("paso", "true")
        self.btn_golpear.clicked.connect(self._golpear)
        v.addWidget(self.btn_golpear)
        self.barra = QProgressBar()
        self.barra.setObjectName("vibracion")
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        v.addWidget(self.barra)
        self.lbl_estado = QLabel("Quieto, sin golpear.")
        self.lbl_estado.setProperty("role", "hint")
        v.addWidget(self.lbl_estado)
        self.btn_retirar = QPushButton(" Retirar el diapasón")
        self.btn_retirar.setIcon(iconos.icono("x", tema.TEXTO_SUAVE, 16))
        self.btn_retirar.setProperty("paso", "true")
        self.btn_retirar.clicked.connect(self._retirar)
        v.addWidget(self.btn_retirar)
        self.lbl_armonicos = QLabel(ARMONICOS)
        self.lbl_armonicos.setObjectName("armonicos")
        self.lbl_armonicos.setWordWrap(True)
        self.lbl_armonicos.hide()
        v.addWidget(self.lbl_armonicos)
        col.addWidget(tarjeta)

        tarjeta, v = self._tarjeta()
        v.addWidget(self._seccion("CONVERSACIÓN"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setProperty("conversacion", "true")
        self.log.setPlaceholderText("Lo que le digas al paciente y lo que él conteste.")
        v.addWidget(self.log, 1)
        col.addWidget(tarjeta, 1)
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
        self._aviso_id += 1
        self.frases.callar()
        self.frases.silencio()
        self.log.clear()
        self.cabeza.poner_diapason(None)
        self.cabeza.mirar(*VISTA_FRENTE)
        sirve = not data or self.modelo.disponible()
        self.lbl_armonicos.setVisible(not sirve)
        self.btn_golpear.setEnabled(sirve)
        self._mostrar_vibracion()
        motivo = no_realizable.motivo(data, "acumetría")
        if motivo:
            self.aviso_bebe.texto.setText(motivo)
        self.pila.setCurrentWidget(self.aviso_bebe if motivo else self.equipo)

    def callar(self):
        self.frases.callar()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.frases.callar()

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
        self._aviso_id += 1
        self.cabeza.poner_diapason(None)
        self._mostrar_vibracion()

    def _golpear(self):
        if not self.modelo.disponible():
            return
        self._golpe = self._reloj()
        self._apoyo = None
        self._rinne = None
        self._aviso_id += 1
        self.cabeza.poner_diapason(None)
        self._log("ac_golpe", hz=self.hz())
        self._decir(f"Tú: golpeas el diapasón de {dict(dp.DIAPASONES)[self.hz()]}.")
        self._tick.start()
        self._mostrar_vibracion()

    def _retirar(self):
        if self._apoyo is None:
            return
        self._log("ac_retirar", hz=self.hz(), zona=self._apoyo["zona"])
        self._apoyo = None
        self._aviso_id += 1
        self.cabeza.poner_diapason(None)
        self._decir("Tú: retiras el diapasón.")

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
        self._aviso_id += 1
        self.cabeza.poner_diapason(punto, normal)
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
        if oye and self._instruccion == "avise_cuando_deje":
            self._programar_aviso(apoyo)

    def _al_sentirlo(self, apoyo, oye):
        """Lo que dice el paciente al ponerle el diapasón, según la
        instrucción vigente."""
        contacto = apoyo["zona"] != "pabellon"
        if not self._vibra():
            if self._instruccion in INSTRUCCIONES:
                return "No escucho nada."
            return None
        if self._instruccion not in INSTRUCCIONES:
            return NO_SABE
        no_oye = "Siento que vibra, pero no lo escucho." if contacto else "No escucho nada."
        if self._instruccion in ("avise_si_escucha", "avise_cuando_deje"):
            return "Sí, lo escucho." if oye else no_oye
        if self._instruccion == "compare_sonidos":
            if apoyo["zona"] not in ("pabellon", "mastoides"):
                return "¿Comparar con qué?"
            if self._rinne and self._rinne["vistos"] >= {"pabellon", "mastoides"}:
                return self._comparacion_rinne()
            return "Ya." if oye else no_oye
        # diga_donde
        if apoyo["zona"] in ("linea_media", "fuera_de_linea"):
            return DONDE_WEBER.get(self.modelo.weber(self.hz()), DONDE_WEBER["centrado"]) if oye else no_oye
        if apoyo["zona"] in ("pabellon", "mastoides"):
            return f"En el oído {LADO[apoyo['oido']]}." if oye else no_oye
        return "Acá, donde me lo puso." if oye else no_oye

    def _comparacion_rinne(self):
        """Negativo y falso negativo suenan igual para el paciente: la
        trampa del falso negativo la descubre el alumno."""
        if self.modelo.rinne(self.hz(), self._rinne["oido"]) == "positivo":
            return "Adelante, frente a la oreja. Ahí suena más fuerte."
        return "Atrás, en el hueso. Ahí suena más fuerte."

    def _programar_aviso(self, apoyo):
        """Con "Avíseme cuando deje de escucharlo": avisa cuando el
        diapasón baja de su umbral en esa posición."""
        self._aviso_id += 1
        mi_aviso = self._aviso_id
        quedan = dp.segundos_que_quedan(self._dura(apoyo), self._desde_golpe() or 0.0)
        QTimer.singleShot(int(quedan * 1000) + 300, self, lambda: self._ya_no(mi_aviso, apoyo))

    def _ya_no(self, mi_aviso, apoyo):
        if mi_aviso != self._aviso_id or self._apoyo is not apoyo:
            return   # lo movieron, lo retiraron o lo volvieron a golpear
        t = self._desde_golpe()
        self._log("ac_deja_de_oir", hz=self.hz(), zona=apoyo["zona"], oido=apoyo["oido"],
                  desde_golpe_s=None if t is None else round(t, 1))
        self._decir("Paciente: Ya no lo escucho.")

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
            if clave == "avise_cuando_deje" and self._apoyo is not None and self._oye_ahora(self._apoyo):
                self._programar_aviso(self._apoyo)
        else:
            respuesta = self._contestar(clave)
        self._decir(f"Paciente: {respuesta}")
        tipo = "ac_instruccion" if clave in INSTRUCCIONES or clave == "explicar_diapasones" else "ac_pregunta"
        apoyo = self._apoyo or {}
        self._log(tipo, clave=clave, respuesta=respuesta, hz=self.hz(), zona=apoyo.get("zona"),
                  oido=apoyo.get("oido"), vibrando=self._vibra(),
                  oye=bool(apoyo) and self._oye_ahora(apoyo))

    def _contestar(self, clave):
        apoyo = self._apoyo
        if not self.modelo.disponible():
            return "No escucho nada."
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
