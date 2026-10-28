"""Si LabSim se cierra con un paciente en atención, al entrar se vuelve a él
directo, sin pasar por la agenda (main.MainWindow._retomar_atencion_abierta),
y en el ABR los electrodos siguen donde quedaron (AbrMainWindow.la_super)."""
import os
import sys
import tempfile
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["LABSIM_DATA_DIR"] = tempfile.mkdtemp(prefix="labsim_datos_")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(RAIZ)

from test_abr_panel import _banda, _capturar, _caso  # noqa: E402  (crea el QApplication)
import main  # noqa: E402
from abr.AbrMainWindow import AbrMainWindow  # noqa: E402


def _fila(estado=None, user="alumno1", fecha="2026-10-28", hora="10:00:00"):
    atencion = {user: {"estado": estado, "hora_real": hora}} if estado else {}
    return SimpleNamespace(atencion=atencion, fecha=fecha, nombre="Rosa", apellido="Fuentes")


def _ventana(filas, permiso=1):
    abiertas = []
    w = SimpleNamespace(
        data_login={"user": "alumno1", "permission": permiso},
        data_current_key=None,
        subw={"AGENDA": SimpleNamespace(obj=SimpleNamespace(shedule={"agenda_1": filas}))},
        statusbar=SimpleNamespace(showMessage=lambda m: abiertas.append(("msg", m))),
    )

    def atender(key):
        abiertas.append(key)
        w.data_current_key = key
    w.atender_paciente = atender
    w.atender_paciente_base = lambda key: abiertas.append(("base", key))
    return w, abiertas


def test_vuelve_a_la_atencion_abierta():
    w, abiertas = _ventana({"15": _fila("atendido"), "16": _fila("atendiendo"), "17": _fila()})
    main.MainWindow._retomar_atencion_abierta(w)
    assert abiertas[0] == "16"
    assert "Retomaste" in abiertas[1][1]


def test_sin_atencion_abierta_no_abre_nada():
    w, abiertas = _ventana({"15": _fila("atendido"), "17": _fila("atendiendo", user="otro")})
    main.MainWindow._retomar_atencion_abierta(w)
    assert abiertas == []


def test_docente_retoma_su_atencion_base():
    w, abiertas = _ventana({"16": _fila("atendiendo")}, permiso=777)
    main.MainWindow._retomar_atencion_abierta(w)
    assert abiertas == [("base", "16")]


def test_los_electrodos_siguen_puestos_al_volver():
    login = {"name": "Alumno", "user": "alumno1", "permission": 1}
    w = AbrMainWindow(login)
    w.la_super(_caso(), 77)
    w.montaje.de_libro(2)
    antes = {r: v["sitio"] for r, v in w.montaje.montaje().items()}
    w._guardar_montaje()
    # Se cierra LabSim: otra ventana, la misma atención.
    w2 = AbrMainWindow(login)
    w2.la_super(_caso(), 77)
    assert {r: v["sitio"] for r, v in w2.montaje.montaje().items()} == antes
    assert w2.montaje.impedancias.medido and w2.montaje.impedancias.piel.trazos
    assert w2.technical["electrodes"]["vertex"] == "Cz"
    # Otra atención empieza sin electrodos.
    w3 = AbrMainWindow(login)
    w3.la_super(_caso(), 78)
    assert w3.montaje.colocados == {}


def test_en_otro_equipo_vuelve_el_del_informe():
    login = {"name": "Alumno", "user": "alumno1", "permission": 1}
    w = AbrMainWindow(login)
    w.la_super(_caso(), 80)
    w.montaje.de_libro(1)
    w.tabWidget.setCurrentWidget(w.abr)
    _banda(w, '100', '3000')
    _capturar(w, 80, 'OD')
    data = w.session_payload()
    # Otro equipo: sin el archivo local, con el informe del servidor.
    from abr import AbrMainWindow as modulo
    modulo._archivo_montaje(login["user"], 80).unlink(missing_ok=True)
    w2 = AbrMainWindow(login)
    w2.la_super(_caso(), 80)
    assert w2.montaje.colocados == {}
    w2.apply_restored([{"tipo": "ABR", "data": data}], "u", 80)
    assert set(w2.montaje.colocados) == {"activo", "referencia", "tierra"}


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
