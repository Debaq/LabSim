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
    'colocar_fonos', 'colocar_vibrador', 'mano_levantada', 'ruido_otro_oido',
    'ruido_blanco_contralateral', 'pitos_fuertes', 'dos_pitos',
    'cambie_de_volumen', 'escuche_mi_voz',
}


def _claves():
    return [clave for _t, frases in GRUPOS for _r, clave in frases]


def test_estan_todas_las_del_motor():
    assert CLAVES_DEL_MOTOR <= set(_claves())
    assert len(_claves()) == len(set(_claves())) == 28   # + 6 de tinnitumetría, 2026-11-06; + diploacusia; + solo el mío; - ¿Mismo volumen? (2026-11-13); 3 de ruido -> 1 aviso, - ¿Molesta?, - pa pa pa, Rosemberg = Mano levantada, - NME, - Solo si molesta, + Weber e IWA, + Reger (2026-11-13)


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
    c.botones['ruido_otro_oido'].click()
    c.btn_silencio.click()
    assert dichas == ['mano_levantada', 'escucha', SILENCIO, 'ruido_otro_oido', SILENCIO]
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


def test_un_solo_boton_de_ruido():
    """El equipo acordó un solo aviso de enmascaramiento (2026-11-13): los
    de Aérea + ruido, Vibrador + ruido y Mano levantada en ruido no vuelven."""
    claves = set(_claves())
    assert 'ruido_otro_oido' in claves
    assert not claves & {'aerea_+_ruido', 'vibrador_+_ruido', 'mano_levantada_en_ruido'}


def test_el_aviso_no_cambia_la_instruccion():
    """"Ruido en el otro oído" se dice además de la instrucción de la
    prueba: el paciente sigue con ella (vía ósea, Carhart...)."""
    from audiometria.response import ResponseAudiometry

    class _Audio:
        pass

    r = ResponseAudiometry(_Audio())
    for instr in ('colocar_fonos', 'colocar_vibrador', 'mano_levantada'):
        r.history_command = []
        r.rol_player(instr)
        r.rol_player('escucha')
        r.rol_player('ruido_otro_oido')
        assert r._instruccion() == instr
        assert r._pregunta is None
    # muchos avisos seguidos no empujan afuera la instrucción
    r.history_command = []
    r.rol_player('colocar_vibrador')
    for _ in range(20):
        r.rol_player('ruido_otro_oido')
    assert r._instruccion() == 'colocar_vibrador'


def test_pa_pa_pa_y_molesta_fuera_de_las_frases():
    """Pa pa pa pasó al panel de las listas y ¿Molesta? se fusionó con
    ¿Muy fuerte? (2026-11-13). El audio de pa pa pa sigue: lo usa el SDT."""
    assert not set(_claves()) & {'pa_pa_pa', 'molesta'}
    assert os.path.exists(os.path.join(RAIZ, "resources", "audio", "comandos", "pa_pa_pa.mp3"))
