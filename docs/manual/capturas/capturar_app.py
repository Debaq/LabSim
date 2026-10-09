"""Capturas de la app de escritorio para los manuales (docs/manual/).

    micromamba run -n labsim python docs/manual/capturas/capturar_app.py [nombre ...]

Abre las ventanas reales de LabSim sin pantalla (QT_QPA_PLATFORM=offscreen),
con los pacientes de práctica (casos inventados de casos_demo.json) y sin
red: todo lo que va al servidor se reemplaza por dobles, la cola de
acciones no se toca y los datos locales van a una carpeta temporal. Sin
argumentos saca todas; con nombres, solo esas.

Las imágenes quedan en docs/manual/img/estudiante/.
"""
import json
import os
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parents[3]
SALIDA = RAIZ / "docs" / "manual" / "img" / "estudiante"
CASOS = json.loads((pathlib.Path(__file__).with_name("casos_demo.json")).read_text(encoding="utf-8"))

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["LABSIM_DATA_DIR"] = tempfile.mkdtemp(prefix="labsim-manual-")
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz
sys.path.insert(0, str(RAIZ / "src"))
_OUT = sys.__stdout__

# Sin red, a nivel de requests: ninguna llamada de ningún módulo llega a un
# servidor (este equipo puede tener una sesión real en session.json).
import requests  # noqa: E402


def _sin_red(*a, **k):
    raise requests.ConnectionError("capturas del manual: sin red")


requests.Session.request = _sin_red
requests.request = _sin_red
requests.get = requests.post = _sin_red

from PySide6.QtCore import QPoint, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import core.app_layout as app_layout  # noqa: E402

# El layout sale de la copia local, sin pedirlo al servidor.
app_layout.fetch_layout = lambda url: app_layout.load_cache()
app_layout.last_source = "network"

import main  # noqa: E402
from core import registro  # noqa: E402
from backend.shedule_sync import AgendaEntry  # noqa: E402
import agenda.Agenda as agenda_mod  # noqa: E402
from core import inbox as inbox_mod  # noqa: E402
from core import mis_pacientes as mis_mod  # noqa: E402

APP = QApplication.instance()


class _ColaMuda:
    """La cola de acciones real escribe en logs.db y después se sube: acá no."""
    def push(self, *a, **k):
        pass

    def set_usuario(self, *a, **k):
        pass


main.LOCAL_LOG_QUEUE = _ColaMuda()
main.MainWindow._logged_in_client = lambda self: None
main.MainWindow._start_log_uploader = lambda self: None
main.MainWindow._start_sync_thread = lambda self: None
main.MainWindow._subir_pendientes_en_fondo = lambda self: None

HOY = agenda_mod.QDate.currentDate().toString("dd-MM-yy")
PACIENTES = [  # (case_id, hora, estado)
    ("33", "08:30", "atendido"), ("34", "09:15", "atendiendo"), ("36", "10:00", None),
    ("38", "11:00", None), ("39", "12:00", None),
]


def _caso(cid):
    return CASOS[cid]


def _agenda():
    filas = {}
    for i, (cid, hora, estado) in enumerate(PACIENTES):
        snap = _caso(cid)["paciente_snapshot"]
        nombre, apellido = snap["nombre"].split()[0], snap["apellido"]
        filas[str(100 + i)] = AgendaEntry(
            fecha=HOY, hora=hora, nombre=nombre, apellido=apellido, rut=snap["rut"],
            fecha_nac=snap["fecha_nac"], procedimiento="Audiometría + impedanciometría", case_id=cid,
            atencion={ALUMNO["user"]: {"estado": estado}} if estado else {})
    return {"agenda_1": filas}


_ESTADO = {}


class _SheduleFalso:
    """La agenda del alumno, en memoria: atender la marca acá y no en el servidor."""
    def __init__(self, *a, **k):
        if not _ESTADO:
            _ESTADO.update(_agenda())
        self.data = _ESTADO

    def get(self):
        return self.data

    def set(self, data):
        self.data = data


class _CasosFalsos:
    def get_cases(self):
        return {cid: dict(d, box=d.get("box", "Box_1")) for cid, d in CASOS.items()}


PRACTICA = [dict(id=i + 1, case_id=cid, procedimiento="Audiometría + impedanciometría", show_study_sheet=True,
                 curso="Audiología aplicada ETMP176", nombre=_caso(cid)["paciente_snapshot"]["nombre"].split()[0],
                 apellido=_caso(cid)["paciente_snapshot"]["apellido"], rut=_caso(cid)["paciente_snapshot"]["rut"],
                 fecha_nac=_caso(cid)["paciente_snapshot"]["fecha_nac"], intentos=n,
                 ultimo="2026-10-08 20:00:00" if n else None, ultimo_cerrado=None, abierto=None)
            for i, (cid, n) in enumerate([("33", 0), ("34", 2), ("35", 0), ("36", 1), ("37", 0),
                                          ("38", 0), ("39", 0), ("40", 0), ("41", 0), ("42", 0)])]

agenda_mod.Shedule = _SheduleFalso
agenda_mod.lista_practica = lambda: [dict(x) for x in PRACTICA]
agenda_mod.iniciar_practica = lambda pid: {}
inbox_mod.inbox_list = lambda *a, **k: []
main.Shedule = _SheduleFalso
main.CasesOffline = _CasosFalsos
agenda_mod.CasesOffline = _CasosFalsos
main.MainWindow._subir_logs_ahora = lambda self: None
main.MainWindow._recuperar_informes = lambda self, key: None
main.MainWindow.sync_ahora = lambda self: False

ALUMNO = {"user": "valentina.rojas", "name": "Valentina Rojas", "permission": 444, "prefs": {},
          "modules": ["A", "W", "Z", "ABR", "AABR", "VEMP", "EOAS", "CVOICE", "AGENDA", "CHAT", "AC",
                      "OT", "INBOX", "FICHA", "EVOLUCION", "MIS_PACIENTES"]}


def procesar(n=6):
    for _ in range(n):
        APP.processEvents()


def guardar(widget, nombre):
    procesar()
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"{nombre}.png"
    widget.grab().save(str(ruta))
    print(f"  {ruta.relative_to(RAIZ)}", file=_OUT)


def recortar(w, nombre, rect):
    """Guarda solo un pedazo de la ventana (sin el área gris vacía)."""
    from PySide6.QtCore import QRect
    procesar()
    r = QRect(*rect).intersected(w.rect())
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"{nombre}.png"
    w.grab().copy(r).save(str(ruta))
    print(f"  {ruta.relative_to(RAIZ)}", file=_OUT)


def rect_de(w, widget, margen=0):
    p = widget.mapTo(w, QPoint(0, 0))
    return (p.x() - margen, p.y() - margen, widget.width() + 2 * margen, widget.height() + 2 * margen)


BARRA = 62  # título + barra de botones


def ventana_principal(ancho=1280, alto=760):
    _ESTADO.clear()  # cada captura parte con la agenda del día sin tocar
    w = main.MainWindow()
    main.Preferences.get_style(w)
    w.show()
    procesar()
    w.setMinimumSize(ancho, alto)
    w.resize(ancho, alto)
    procesar()
    return w


def entrar(w, datos=None):
    """Lo que pasa al ingresar: se abre el login y llega el usuario."""
    w.toggle_login()
    procesar()
    w._data_login(dict(datos or ALUMNO))
    procesar()


CAPTURAS = {}


def captura(fn):
    CAPTURAS[fn.__name__] = fn
    return fn


@captura
def inicio():
    w = ventana_principal()
    w.toggle_login()
    procesar()
    from core.h_win import FrameSubMdi
    login = next(f for f in w.findChildren(FrameSubMdi) if f.isVisible())
    x, y, ancho, alto = rect_de(w, login, 24)
    recortar(w, "login", (x, 0, ancho, y + alto))
    w.close()


@captura
def sala_de_espera():
    w = ventana_principal()
    entrar(w)
    recortar(w, "barra-sala", (0, 0, w.width(), BARRA))
    w.close()


def abrir(w, nombre):
    """Abre la subventana como el botón de la barra."""
    w.activate_auto(nombre)
    procesar()
    return w.subw[nombre]


def agenda_lista(w):
    frame = abrir(w, "AGENDA")
    ag = frame.obj
    ag.refresh_async = ag.refresh
    ag._pedir_practica = lambda: ag._on_practica_fetched(agenda_mod.lista_practica())
    ag.refresh()
    procesar()
    return frame, ag


def fila_de(ag, apellido):
    for r in range(ag.tableWidget.rowCount()):
        for c in range(ag.tableWidget.columnCount()):
            item = ag.tableWidget.item(r, c)
            if item is not None and item.text() == apellido:
                return r
    raise LookupError(apellido)


@captura
def agenda():
    w = ventana_principal()
    entrar(w)
    frame, ag = agenda_lista(w)
    ag.tableWidget.selectRow(fila_de(ag, "Rivas Henríquez"))
    guardar(frame, "agenda")
    ag.btn_practica.setChecked(True)
    procesar()
    ag.tableWidget.selectRow(fila_de(ag, "Muñoz Sepúlveda"))
    guardar(frame, "practica-libre")
    w.close()


def atendiendo(cid="38", datos=None, grande=False):
    """La ventana con una atención abierta del paciente `cid` de la agenda."""
    w = ventana_principal(*((1600, 1000) if grande else (1280, 760)))
    entrar(w, datos)
    frame, ag = agenda_lista(w)
    key = next((k for k, e in _ESTADO["agenda_1"].items() if e.case_id == cid), None)
    if key is None:  # paciente que no está en la agenda del día: se le agrega la cita
        snap = _caso(cid)["paciente_snapshot"]
        key = str(200 + int(cid))
        _ESTADO["agenda_1"][key] = AgendaEntry(
            fecha=HOY, hora="12:00", nombre=snap["nombre"].split()[0], apellido=snap["apellido"],
            rut=snap["rut"], fecha_nac=snap["fecha_nac"], procedimiento="EOA+PEATC", case_id=cid, atencion={})
        ag.refresh()
    # Llegó a la hora: la cita era hace dos minutos.
    _ESTADO["agenda_1"][key].hora = agenda_mod.QTime.currentTime().addSecs(-120).toString("HH:mm")
    w.atender_paciente(key)
    procesar()
    w.lbl_cronometro.setText("00:12:34")
    ag.refresh()
    ag.tableWidget.selectRow(fila_de(ag, _caso(cid)["paciente_snapshot"]["apellido"]))
    procesar()
    return w, frame, ag


@captura
def atencion():
    w, frame, ag = atendiendo()
    x, y, ancho, alto = rect_de(w, frame, 10)
    recortar(w, "atendiendo", (0, 0, w.width(), y + alto))
    recortar(w, "barra-estado", (0, w.height() - 26, w.width() // 2, 26))
    w.close()


import agenda.ChatPaciente as chat_mod  # noqa: E402
from core import secretaria as secretaria_mod  # noqa: E402
from core import configuracion as configuracion_mod  # noqa: E402
from core.preferencias import preferencias  # noqa: E402
from PySide6.QtWidgets import QTabWidget, QMessageBox  # noqa: E402


def _sala(cid):
    out = []
    for p in _caso(cid)["Sala"]["personas"]:
        rol = p["rol"]
        etiqueta = p["nombre"] if p.get("es_paciente") else f"{p['nombre'].split()[0]} ({'Esposa' if rol == 'conyuge' else rol.capitalize()})"
        out.append({"id": p["id"], "nombre": p["nombre"], "rol": rol, "etiqueta": etiqueta,
                    "es_paciente": bool(p.get("es_paciente")), "informante": bool(p.get("informante"))})
    return out


chat_mod.sala_del_caso = lambda cid, *a, **k: _sala(cid)
chat_mod.foto_paciente = lambda *a, **k: None


@captura
def ficha_y_chat():
    w, frame, ag = atendiendo("36")
    ag.btn_ver_ficha.click()
    procesar()
    guardar(w.subw["FICHA"], "ficha-clinica")
    w.abrir_chat_paciente()
    procesar(20)
    chat = w.subw["CHAT"].obj
    chat._aplicar_sala(_sala("36"))
    chat._burbuja_usuario("Buenos días, don Hernán. ¿Qué lo trae por acá?")
    chat._burbuja_persona("p1", "Hernán", "Buenos días. Mire, la verdad yo escucho bien, pero mi señora insiste en que viniera.")
    chat._burbuja_persona("a1", "Gladys (Esposa)", "Es que pone la tele fortísimo y en los almuerzos no entiende nada de lo que le dicen los nietos.")
    chat._burbuja_usuario("¿Siente algún ruido o zumbido en los oídos?")
    chat._burbuja_persona("p1", "Hernán", "Un siseo, en los dos oídos, más que nada cuando está todo en silencio.")
    procesar()
    frame_chat = w.subw["CHAT"]
    frame_chat.resize(600, 660)
    guardar(frame_chat, "chat")
    w.close()


@captura
def evolucion():
    w, frame, ag = atendiendo("38")
    ag.btn_atender.click()
    procesar()
    evo = w.subw["EVOLUCION"]
    from PySide6.QtWidgets import QPlainTextEdit, QTextEdit
    caja = evo.obj.findChild(QPlainTextEdit) or evo.obj.findChild(QTextEdit)
    caja.setPlainText("Paciente de 46 años, consulta por crisis de vértigo con plenitud aural y zumbido en OI. "
                      "Se realiza audiometría tonal con enmascaramiento, logoaudiometría, pruebas supraliminares "
                      "e impedanciometría.")
    evo.resize(520, 430)
    guardar(evo, "evolucion")
    w.close()


@captura
def karime():
    w, frame, ag = atendiendo("38")
    sec = w.secretaria
    sec.avisar("Raúl Saavedra ya llegó y está en la sala de espera. ¿Le falta mucho?")
    procesar()
    import time
    t0 = time.time()
    while time.time() - t0 < 0.6:
        procesar()
    aviso = sec._avisos[-1]
    x, y, ancho, alto = rect_de(w, aviso, 16)
    recortar(w, "karime", (x - 200, y - 40, ancho + 200, alto + 56))
    w.close()


INBOX = [
    {"id": 2, "remitente": "OIRS (simulada)", "asunto": "Sugerencia de mejora sobre tu atención", "leido": False,
     "created_at": "2026-10-08 18:40", "tipo_label": "Sugerencia de mejora",
     "aviso": "Mensaje simulado: lo escribe el paciente virtual del caso según cómo se sintió tratado. Es parte del ejercicio para practicar el trato, no es un reclamo real ni queda en ningún registro fuera de LabSim.",
     "cuerpo": "La señorita fue amable, pero me hizo muchas preguntas seguidas y no me explicó para qué era cada examen. "
               "Me habría gustado saber al final qué tenía que hacer."},
    {"id": 1, "remitente": "Docente", "asunto": "Bienvenida a la práctica libre", "leido": True,
     "created_at": "2026-10-07 09:00", "tipo_label": "Mensaje docente",
     "cuerpo": "Ya están disponibles los pacientes de práctica. Pueden atenderlos las veces que quieran."},
]
inbox_mod.inbox_list = lambda *a, **k: [dict(x) for x in INBOX]
inbox_mod.inbox_marcar_leido = lambda *a, **k: None


@captura
def bandeja():
    w = ventana_principal()
    entrar(w)
    frame = abrir(w, "INBOX")
    frame.obj.refresh()
    frame.obj.tabla.selectRow(0) if hasattr(frame.obj, "tabla") else None
    procesar()
    guardar(frame, "bandeja-oirs")
    w.close()


mis_mod.mis_atenciones = lambda: [
    {"appointment_id": 101, "case_id": "34", "nombre": "Carolina", "apellido": "Muñoz Sepúlveda",
     "fecha": "08-10-26", "hora": "20:00", "hora_real": "20:02", "updated_at": "2026-10-08 20:41",
     "procedimiento": "Audiometría + impedanciometría", "practica": True, "n_chat_messages": 14,
     "stats": {"n_sessions": 3, "total_duration_s": 2410, "avg_delta_s": 6.2, "long_pauses": 2, "no_pause_actions": 11},
     "nota": "Hipoacusia conductiva moderada OD. Se sugiere evaluación por otorrinolaringología.",
     "evolucion_comments": [{"comment": "Bien la conclusión. Falta mencionar el resultado de la impedanciometría.",
                             "teacher_name": "Docente", "created_at": "2026-10-09 10:15"}],
     "ficha_estudio": True},
    {"appointment_id": 100, "case_id": "33", "nombre": "Tomás", "apellido": "Fuentes Riquelme",
     "fecha": "07-10-26", "hora": "18:30", "procedimiento": "Audiometría + impedanciometría", "practica": True},
]
mis_mod.mi_conversacion = lambda cita: [
    {"role": "user", "content": "Hola, ¿cómo está? ¿Qué la trae por acá?", "created_at": "20:03"},
    {"role": "assistant", "content": "Hola. Desde mi segundo embarazo escucho menos por el oído derecho, y tengo un zumbido.", "created_at": "20:03",
     "comments": [{"comment": "Buena pregunta abierta para partir.", "teacher_name": "Docente", "created_at": "2026-10-09 10:12"}]},
] if cita == 101 else []
mis_mod.mis_informes = lambda cita: [{"tipo": "EOA", "updated_at": "2026-10-08 20:30", "data": {}},
                                     {"tipo": "ABR", "updated_at": "2026-10-08 20:38", "data": {}}] if cita == 101 else []
mis_mod.Shedule = _SheduleFalso
mis_mod.CasesOffline = _CasosFalsos


@captura
def mis_pacientes():
    w = ventana_principal()
    entrar(w)
    frame = abrir(w, "MIS_PACIENTES")
    mp = frame.obj
    mp.refresh()
    mp.tabla.selectRow(0)
    procesar()
    for i, nombre in enumerate(["mis-pacientes", "mis-pacientes-conversacion", "mis-pacientes-ficha", "mis-pacientes-examenes"]):
        mp.tabs.setCurrentIndex(i)
        guardar(frame, nombre)
    w.close()


@captura
def configuracion():
    preferencias().cargar({})
    d = configuracion_mod.ConfiguracionDialog()
    main.Preferences.get_style(d)
    d.show()
    tabs = d.findChild(QTabWidget)
    for i, nombre in enumerate(["config-atajos", "config-mouse", "config-reportar"]):
        tabs.setCurrentIndex(i)
        guardar(d, nombre)
    d.close()


@captura
def sesion_vencida():
    w = ventana_principal()
    entrar(w)

    def sacar():
        m = QApplication.activeModalWidget()
        if m is not None:
            m._esperado = True
            guardar(m, "sesion-vencida")
            m.done(0)
    QTimer.singleShot(300, sacar)
    try:
        w._sesion_perdida("vencida")
    except Exception:
        pass
    procesar()
    w.close()


import numpy as np  # noqa: E402
from PySide6.QtWidgets import QPushButton  # noqa: E402


def mover(frame, x, y):
    from PySide6.QtWidgets import QMdiSubWindow
    sub = frame
    while sub is not None and not isinstance(sub, QMdiSubWindow):
        sub = sub.parentWidget()
    (sub or frame).move(x, y)
    procesar()


def ir_a_box(w, texto):
    for b in w.findChildren(QPushButton):
        if b.text() == texto and b.isVisible():
            b.click()
            procesar()
            return
    raise LookupError(texto)


@captura
def audiometro():
    w, frame, ag = atendiendo("38")
    frame.hide()
    ir_a_box(w, "Box Audiología")
    recortar(w, "barra-audiologia", (0, 0, w.width(), BARRA))
    fa = abrir(w, "A")
    a = fa.obj
    a.lbl_int_ch0.setText("40 dB HL")
    a.lbl_int_ch1.setText("60 dB HL")
    a.lbl_output_ch1.setText("Izquierda")
    a.lbl_stimOn_ch0.setStyleSheet("background-color: rgb(170,170,255);")
    a.response.upHand()
    fc = abrir(w, "CVOICE")
    for b in fc.obj.findChildren(QPushButton):
        if b.text() == "Colocar fonos":
            b.setChecked(True)
    mover(fa, 8, 8)
    mover(fc, 8 + fa.width() + 24, 8)
    x, y, ancho, alto = rect_de(w, fa, 10)
    recortar(w, "audiometro-con-comandos", (0, 0, w.width(), y + alto))
    guardar(fa, "audiometro")
    guardar(fc, "comandos-de-voz")
    w.close()


@captura
def listas_de_palabras():
    w, frame, ag = atendiendo("38")
    frame.hide()
    ir_a_box(w, "Box Audiología")
    fl = w.subw["W"]
    w.activate_auto("W")
    procesar()
    guardar(fl, "listas-de-palabras")
    w.close()


@captura
def acumetria():
    w, frame, ag = atendiendo("34")
    frame.hide()
    ir_a_box(w, "Box Audiología")
    fac = abrir(w, "AC")
    ac = fac.obj
    botones = {b.text(): b for b in ac.findChildren(QPushButton)}
    for t in ("Apoyar en mastoides (vía ósea)", "Presentar frente al pabellón (vía aérea)",
              "Preguntar: ¿dónde lo escuchas más fuerte?"):
        if t in botones:
            botones[t].click()
    procesar()
    guardar(fac, "acumetria-rinne")
    ac.findChild(QTabWidget).setCurrentIndex(1)
    for b in ac.findChildren(QPushButton):
        if b.text().startswith("Apoyar en la frente") and b.isVisible():
            b.click()
    procesar()
    guardar(fac, "acumetria-weber")
    w.close()


@captura
def impedanciometro():
    w, frame, ag = atendiendo("34")
    frame.hide()
    ir_a_box(w, "Box Audiología")
    fz = abrir(w, "Z")
    z = fz.obj
    z.new = [False, False]
    z.refresh()
    procesar()
    guardar(fz, "impedanciometro-timpanograma")
    z.reflex_results[0]["IPSI"] = [None, None, None, None]
    z.reflex_results[1]["CONTRA"] = [None, None, 100, 110, None]
    z.show_screen(z.Z_reflex)
    z.refresh_reflex_table()
    procesar()
    guardar(fz, "impedanciometro-reflejos")
    w.close()


@captura
def impedanciometro_decay_etf():
    w, frame, ag = atendiendo("38")
    frame.hide()
    ir_a_box(w, "Box Audiología")
    fz = abrir(w, "Z")
    z = fz.obj
    # Decay en OI (reflejo presente, se sostiene)
    z.side_change()
    z.show_screen(z.Z_decay)
    z.dial.setValue(95)
    z.decay_stimulus()
    while z.time_decay.isActive():
        z.decay_animate()
    z.reflex_tone.stop()
    guardar(fz, "impedanciometro-decay")
    # ETF, membrana íntegra: reposo, +400 y tragar, -400 y tragar
    z.side_change()
    z.show_screen(z.Z_etf)
    z.btn1_click()
    for maniobra in ("reposo", "positiva", "negativa"):
        z.etf_maniobra(maniobra)
    guardar(fz, "impedanciometro-etf")
    w.close()


@captura
def otoscopia():
    w, frame, ag = atendiendo("41")
    frame.hide()
    ir_a_box(w, "Box Audiología")
    fo = abrir(w, "OT")
    o = fo.obj
    guardar(fo, "otoscopio")
    o.tabs.setCurrentIndex(1)
    o.informe.from_dict({"od": {"cae": ["cae_normal"]},
                         "oi": {"cuadrantes": {"pars_flaccida": ["retraction", "cholesteatoma"]},
                                "cae": ["cae_otorrhea"], "observaciones": "Otorrea escasa en el conducto."}})
    procesar()
    guardar(fo, "otoscopia-informe")
    w.close()


def _pico(grafico, curva, desde, hasta, maximo=True):
    x, y = grafico.data[curva]["ipsi_xy"]
    x, y = np.asarray(x), np.asarray(y)
    m = (x >= desde) & (x <= hasta)
    i = np.argmax(y[m]) if maximo else np.argmin(y[m])
    return float(x[m][i])


def _abr_listo(cid, prueba="ABR"):
    w, frame, ag = atendiendo(cid, grande=True)
    frame.hide()
    ir_a_box(w, "Box Electrofisiología")
    recortar(w, "barra-electrofisiologia", (0, 0, w.width(), BARRA))
    fa = abrir(w, "ABR")
    v = fa.obj
    if prueba != "ABR":
        v.control.cb_test.setCurrentText(prueba)
    # Un registro bien configurado (al alumno le toca armarlo: arranca con
    # tasa y promediaciones al azar). El ECochG trae su estándar de docente.
    if prueba == "ABR":
        v.control.set_data({"stim": "Click", "pol": "Alternada", "int": 80, "rate": 21.1,
                            "filter_passhigh": "100", "filter_down": "3000", "average": 2000})
    else:
        v.docente = True
        v.apply_standard_setup(prueba)
        v.docente = False
    procesar()
    return w, fa, v


def _registrar(v, intensidad, lado="OD"):
    v.control.cb_side.setCurrentIndex(v.control.cb_side.findText(lado))
    v.control.sb_intencity.setValue(intensidad)
    v.control.start_capture()
    for _ in range(800):
        v.capture()
        if v.state_capture != "record":
            break


@captura
def abr():
    w, fa, v = _abr_listo("33")
    for intensidad in (80, 60, 40, 20):
        _registrar(v, intensidad, "OD")
    for intensidad in (80, 40):
        _registrar(v, intensidad, "OI")
    for _ in range(15):
        v.refresh_eeg()
    v.btn_scale_plus.click()
    v.btn_scale_plus.click()
    g = v.graph_r
    curva = max(g.curve_int, key=lambda k: g.curve_int[k])  # la de 80 dB
    g.act_curve = curva
    for onda, (a, b) in {"I": (1.2, 2.0), "III": (3.3, 4.2), "V": (5.2, 6.4)}.items():
        g.current_lat = _pico(g, curva, a, b)
        g.create_marks(onda)
    procesar()
    guardar(fa, "abr")
    v.tabWidget.setCurrentIndex(1) if hasattr(v, "tabWidget") else None
    for tabs in fa.findChildren(QTabWidget):
        textos = [tabs.tabText(i) for i in range(tabs.count())]
        if "Latencia/Intensidad" in textos:
            tabs.setCurrentIndex(textos.index("Latencia/Intensidad"))
            guardar(fa, "abr-latencia-intensidad")
            tabs.setCurrentIndex(textos.index("Conclusiones"))
            v.report.text_edit_1.setPlainText("Ondas I, III y V presentes y reproducibles en OD a 80 dB nHL.")
            guardar(fa, "abr-conclusiones")
            tabs.setCurrentIndex(0)
    w.close()


@captura
def abr_avanzados():
    from abr.AbrAdvanceSettings import AbrAdvanceSettings
    w, fa, v = _abr_listo("33")
    d = AbrAdvanceSettings(v.technical, "ABR", v)
    main.Preferences.get_style(d)
    d.show()
    for tabs in d.findChildren(QTabWidget):
        for i in range(tabs.count()):
            tabs.setCurrentIndex(i)
            guardar(d, f"abr-avanzados-{i + 1}")
        break
    d.close()
    w.close()


@captura
def ecochg():
    w, fa, v = _abr_listo("38", "ECochG")
    v.control.sb_prom.setValue(1500)
    _registrar(v, 90, "OI")
    g = v.graph_l
    curva = max(g.curve_int, key=lambda k: g.curve_int[k])
    g.act_curve = curva
    x, y = g.data[curva]["ipsi_xy"]
    x, y = np.asarray(x), np.asarray(y)
    ap = v.last_metadata.get("ecochg_ap_lat") or float(x[np.argmin(y[(x > 0.8) & (x < 2.5)]) + np.argmax(x > 0.8)])
    from abr import ecochg as ec
    base = float(np.mean(y[x < 0.25]))
    i_pa = int(np.argmin(np.abs(x - ap)))
    cruces = np.where(y[i_pa:] >= base)[0]
    puestas = [("BL", 0.15), ("PS", ap - ec.SP_SHOULDER_MS), ("PA", ap)]
    if len(cruces):
        puestas.append(("FIN", float(x[i_pa + cruces[0]])))
    for marca, lat in puestas:
        g.current_lat = lat
        g.create_marks(marca)
    procesar()
    guardar(fa, "ecochg")
    w.close()


@captura
def aabr():
    w, frame, ag = atendiendo("33", grande=True)
    frame.hide()
    ir_a_box(w, "Box Electrofisiología")
    rn = dict(_caso("35"), nombre="RN Soto", edad=0, edad_horas=30)
    fa = abrir(w, "AABR")
    a = fa.obj
    a.la_super(rn, 7)
    a.start()
    procesar()
    if a.corriendo:
        a.probe.fit_quality = 0.9
        a._sonda_lista()
        if a.corriendo:
            a._fase_registro()
            for _ in range(3000):
                if not a.corriendo:
                    break
                a._tick()
    procesar()
    guardar(fa, "aabr")
    w.close()


def _correr_oae(panel, lado):
    for b in panel.findChildren(QPushButton):
        if b.text() == lado:
            b.click()
    panel._on_start()
    panel._run_capture()
    for _ in range(3000):
        if not panel._anim_timer.isActive():
            break
        panel._anim_tick()
    procesar()


@captura
def eoa():
    w, frame, ag = atendiendo("34", grande=True)
    frame.hide()
    ir_a_box(w, "Box Electrofisiología")
    fe = abrir(w, "EOAS")
    o = fe.obj
    _correr_oae(o.teoae_panel, "OI")
    guardar(fe, "eoa-teoae")
    o.tabs.setCurrentIndex(1)
    _correr_oae(o.dpoae_panel, "OD")
    _correr_oae(o.dpoae_panel, "OI")
    guardar(fe, "eoa-dpoae")
    o.tabs.setCurrentIndex(o.tabs.count() - 1)
    procesar()
    guardar(fe, "eoa-informe")
    w.close()


@captura
def vemp():
    w, frame, ag = atendiendo("38", grande=True)
    frame.hide()
    ir_a_box(w, "Box Electrofisiología")
    fv = abrir(w, "VEMP")
    v = fv.obj
    for lado in ("OD", "OI"):
        (v.control.btn_od if lado == "OD" else v.control.btn_oi).click()
        procesar()
        aju = v.control.ajustes()
        reg = v.sesion.nuevo(aju, v.motor.eje(aju.subtipo))
        reg.acumular(v.motor.lote(aju, 60.0, 200))
        reg.terminado = True
        v.trazas[reg.lado].agregar(reg)
        for pico, lat in (("p13", 13.0), ("n23", 23.0)):
            plat, amp = reg.pico_cercano(lat, pico)
            v._marcar(reg.nombre, pico, plat, amp)
    v._refrescar_tabla()
    v._refrescar_analisis()
    procesar()
    guardar(fv, "vemp")
    w.close()


def _vigilante():
    """Un aviso modal inesperado colgaría el script: se anota y se cierra."""
    m = QApplication.activeModalWidget()
    if m is not None and not getattr(m, "_esperado", False):
        texto = getattr(m, "text", lambda: "")()
        print(f"  [modal cerrado] {m.windowTitle()}: {texto}", file=_OUT)
        m.done(0)


_TIMER_VIGILANTE = QTimer()
_TIMER_VIGILANTE.timeout.connect(_vigilante)
_TIMER_VIGILANTE.start(1500)


if __name__ == "__main__":
    pedidas = sys.argv[1:] or list(CAPTURAS)
    try:
        for nombre in pedidas:
            print(nombre, file=_OUT)
            CAPTURAS[nombre]()
    finally:
        registro.marcar_salida()
