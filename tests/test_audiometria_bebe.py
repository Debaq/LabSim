"""Un bebé no hace audiometría ni acumetría: el equipo se reemplaza por el
aviso y el intento queda registrado. Y la voz del paciente sale del sexo
del caso (gender 1 = mujer), que se leía al revés."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtWidgets import QApplication  # noqa: E402

from audiometria import no_realizable  # noqa: E402
from audiometria.Acumetria import Acumetria  # noqa: E402
from audiometria.h_audio import voz_del_paciente  # noqa: E402
from audiometria.ventana import AudiometriaWindow  # noqa: E402


def _tabla(v):
    return [[v, v] for _ in range(15)]


def _caso(edad, edad_horas=None, gender=0):
    return {"id": 7, "gender": gender, "edad": edad, "edad_horas": edad_horas,
            "sector": "Camara_sono", "Z_OD": None, "Z_OI": None,
            "Aerea": _tabla(10), "Osea": _tabla(10), "Aerea_mkg": _tabla(10),
            "Osea_mkg": _tabla(10), "LDL": _tabla(100), "SDT": [10, 10],
            "SRT": [15, 15], "UMD": [{"int": 60, "percentage": 100}] * 2,
            "recruit": [False, False]}


def test_edad_del_bebe():
    assert no_realizable.edad_texto(_caso(0, 10)) == "10 horas de vida"
    assert no_realizable.edad_texto(_caso(0, 240)) == "10 días"
    assert no_realizable.edad_texto(_caso(0, 720 * 8)) == "8 meses"
    assert no_realizable.edad_texto(_caso(0)) == "menos de un año"
    assert no_realizable.edad_texto(_caso(2)) == "2 años"
    for edad in (0, 1, 2):
        assert no_realizable.es_bebe(_caso(edad))
    assert not no_realizable.es_bebe(_caso(3))
    assert not no_realizable.es_bebe(_caso(None))
    assert not no_realizable.es_bebe(None)


def test_el_audiometro_no_se_abre_con_un_bebe():
    v = AudiometriaWindow(None)
    registro = []
    v.audiometro._log = lambda accion, **p: (
        accion == "audio_no_realizable" and registro.append((accion, p)))
    assert v.pila.currentWidget() is v.equipo

    bebe = _caso(0, 720 * 8)
    v.la_super(bebe, 3)
    assert v.pila.currentWidget() is v.aviso_bebe
    assert "8 meses" in v.aviso_bebe.texto.text()
    assert registro == []                    # todavía no lo abrió
    v.show()
    QApplication.processEvents()
    assert [a for a, _ in registro] == ["audio_no_realizable"]
    assert registro[0][1]["edad_horas"] == 720 * 8
    assert not v.audiometro.isVisible()      # sin equipo: sin teclas ni sonido
    v.hide()
    v.show()
    QApplication.processEvents()
    assert len(registro) == 1                # una vez por caso

    v.la_super(_caso(30), 4)
    QApplication.processEvents()
    assert v.pila.currentWidget() is v.equipo
    assert v.audiometro.isVisible()          # vuelve el equipo
    assert len(registro) == 1
    v.close()


def test_la_acumetria_tampoco():
    a = Acumetria(_caso(1))
    assert a.pila.currentWidget() is a.aviso_bebe
    assert "1 año" in a.aviso_bebe.texto.text()
    a.la_super(_caso(5))
    assert a.pila.currentWidget() is a.equipo


def test_voz_por_sexo_y_edad():
    assert voz_del_paciente(_caso(30, gender=1)) == ("feme", 1)
    assert voz_del_paciente(_caso(30, gender=0)) == ("male", 1)
    assert voz_del_paciente(_caso(8, gender=1)) == ("nina", 1)
    assert voz_del_paciente(_caso(8, gender=0)) == ("nino", 1)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
