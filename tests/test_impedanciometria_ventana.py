"""El impedanciómetro en una sola ventana (impedanciometria/ventana.py):
reparto 1:3:1 como el audiómetro, instrucciones al paciente a la izquierda,
cada una con su audio y en el registro, y las teclas del equipo andando
dentro de la escena escalada."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtCore import QPoint, QRect, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from impedanciometria.instrucciones import GRUPOS, PRUEBA  # noqa: E402
from impedanciometria.ventana import ImpedanciometriaWindow  # noqa: E402


def _ventana(ancho=1366, alto=660):
    v = ImpedanciometriaWindow()
    v.resize(ancho, alto)
    v.show()
    QApplication.processEvents()
    return v


def _dibujado(v):
    e = v.escalado
    return QRect(e.mapTo(v, e.mapFromScene(0, 0)), e.base * e.escala)


def test_reparto_1_3_1_con_el_equipo_al_centro():
    for ancho, alto in ((1920, 970), (1366, 660), (1024, 660)):
        v = _ventana(ancho, alto)
        quinto = (ancho - 4 * 6) / 5
        assert abs(v.col_izq.width() - quinto) <= 2, ancho
        assert abs(v.col_der.width() - quinto) <= 2, ancho
        a = _dibujado(v)
        assert abs(a.center().x() - ancho / 2) <= 3, ancho
        izq = QRect(v.instrucciones.mapTo(v, QPoint(0, 0)), v.instrucciones.size())
        assert izq.right() < a.left(), ancho
        v.close()


def test_cada_instruccion_tiene_su_audio():
    carpeta = os.path.join("resources", "audio", "comandos_z")
    for _titulo, frases in GRUPOS:
        for _rotulo, clave in frases:
            assert os.path.exists(os.path.join(carpeta, f"{clave}.mp3")), clave
    claves = {c for _t, frases in GRUPOS for _r, c in frases}
    assert set(PRUEBA) <= claves


def test_tocar_la_dice_y_la_registra():
    v = _ventana()
    registro = []
    v.z.log_queue.push = lambda accion, payload: registro.append((accion, payload))
    btn = v.instrucciones.botones["no_hablar_ni_tragar"]
    btn.click()
    btn.click()   # sin talkback, tocarla de nuevo la repite, no la suelta
    assert btn.isChecked()
    assert [a for a, _ in registro] == ["z_instruccion", "z_instruccion"]
    assert registro[0][1]["clave"] == "no_hablar_ni_tragar"
    assert "Timpanometría" in v.instrucciones.lbl_pista.text()
    v.instrucciones.silencio()
    assert len(registro) == 2 and not btn.isChecked()
    v.close()


def test_las_teclas_del_equipo_andan_dentro_de_la_escena():
    v = _ventana()
    v.activateWindow()
    v.z.btn_tymp.click()
    QApplication.processEvents()
    antes = v.z.dial.value()
    tecla = v.z.shortcut_dial_up.key()[0].key()
    QTest.keyClick(v.z, tecla)
    QApplication.processEvents()
    assert v.z.dial.value() != antes
    v.close()


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
