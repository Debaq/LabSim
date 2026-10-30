"""Comandos de voz: cada frase emite su clave de siempre.

La clave es el nombre del audio (resources/audio/comandos/<clave>.mp3) y lo que lee
ResponseAudiometry.history_command para decidir la respuesta del paciente.
Si un rótulo nuevo cambia la clave, el paciente deja de responder a esa
instrucción sin que nada avise.
"""
import os
import sys
import unicodedata

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from audiometria.comandos_voz import ComandosVoz, GRUPOS, SILENCIO  # noqa: E402

# Las que lee response.py (history_command / DECAY_TESTS).
CLAVES_DEL_MOTOR = {
    'colocar_fonos', 'colocar_vibrador', 'mano_levantada', 'mano_levantada_en_ruido',
    'ruido_blanco_contralateral', 'rosemberg_bilateral', 'pitos_fuertes', 'dos_pitos',
    'cambie_de_volumen', 'aerea_+_ruido', 'vibrador_+_ruido', 'escuche_mi_voz', 'pa_pa_pa',
}


def _claves():
    return [clave for _t, frases in GRUPOS for _r, clave in frases]


def test_estan_todas_las_del_motor():
    assert CLAVES_DEL_MOTOR <= set(_claves())
    assert len(_claves()) == len(set(_claves())) == 23


def test_cada_clave_tiene_su_audio():
    for clave in set(_claves()):
        plano = unicodedata.normalize('NFKD', clave).encode('ascii', 'ignore').decode()
        ruta = os.path.join(RAIZ, "resources", "audio", "comandos", f"{plano}.mp3")
        assert os.path.exists(ruta), ruta


def test_elegir_y_soltar():
    c = ComandosVoz()
    dichas = []
    c.btn_checked.connect(dichas.append)
    c.botones['mano_levantada'].click()
    c.botones['escucha'].click()
    assert [b for b in c.grupo.buttons() if b.isChecked()] == [c.botones['escucha']]
    c.botones['escucha'].click()          # tocarla de nuevo = Silencio
    c.botones['aerea_+_ruido'].click()
    c.btn_silencio.click()
    assert dichas == ['mano_levantada', 'escucha', SILENCIO, 'aerea_+_ruido', SILENCIO]
    assert not any(b.isChecked() for b in c.grupo.buttons())


def test_buscar_y_enter():
    c = ComandosVoz()
    dichas = []
    c.btn_checked.connect(dichas.append)
    c.buscar.setText("¿en que OIDO")
    visibles = [b for b in c.botones.values() if not b.isHidden()]
    assert visibles == [c.botones['en_qué_oído']]
    c.buscar.returnPressed.emit()
    assert dichas == ['en_qué_oído']
    c.buscar.setText("nada parecido")
    assert not c.sin_resultados.isHidden()


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
