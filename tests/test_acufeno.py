"""Tinnitumetría: lo que contesta el paciente (audiometria/acufeno.py) y cómo
lo enchufa ResponseAudiometry.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from audiometria import acufeno  # noqa: E402
from audiometria.response import ResponseAudiometry  # noqa: E402

# umbral aéreo por oído y frecuencia: OD normal (10), OI con caída en agudos
UMBRAL = {0: [10] * 9, 1: [10, 10, 10, 15, 30, 45, 50, 55, 60]}
F = {hz: i for i, hz in enumerate(acufeno.FRECUENCIAS)}
TONO, NBN, WN = 0, 3, 4

BLOQUE = {"presente": "1", "lateralidad": "unilateral", "oido": "oi", "ruido": "Pitido",
          "frecuencia": 4000, "permanente": "1",
          "sonoridad_sl": "6", "nme_sl": "20", "inhibicion": "parcial", "inhibicion_mantiene": "no"}


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _oidos(ch, a):
    return [0, 1] if a.get("sim", [False, False])[ch] else [a["output"][ch]]


def _audio(on=(False, False), stim=(TONO, NBN), int_=(20, 20), output=(0, 1), freq=F[4000]):
    return {"stimOn": list(on), "stim": list(stim), "int": list(int_), "output": list(output),
            "freq": freq, "sim": [False, False], "test": "Umbrales"}


def _tin(bloque=BLOQUE, reloj=None):
    a = acufeno.Acufeno(bloque, "99")
    return acufeno.Tinnitumetria(a, lambda o, f: UMBRAL[o][f], _oidos, reloj or Reloj())


def test_sorteo_estable_y_fijado_por_el_docente():
    auto = {k: v for k, v in BLOQUE.items()
            if k not in ("sonoridad_sl", "nme_sl", "inhibicion", "inhibicion_mantiene")}
    a, b = acufeno.Acufeno(auto, "17"), acufeno.Acufeno(auto, "17")
    assert a.verdad() == b.verdad()
    assert acufeno.SONORIDAD_SL[0] <= a.sonoridad_sl <= acufeno.SONORIDAD_SL[1]
    assert a.nme_sl > a.sonoridad_sl
    assert set(a.verdad()["sorteados"]) == {"sonoridad_sl", "nme_sl", "inhibicion", "mantiene"}
    fijo = acufeno.Acufeno(BLOQUE, "17")
    assert (fijo.sonoridad_sl, fijo.nme_sl, fijo.inhibicion, fijo.mantiene) == (6, 20, "parcial", False)
    assert fijo.verdad()["sorteados"] == []
    assert fijo.oido_de_comparacion() == 0


def test_presente_como_el_backend():
    assert not acufeno.presente({})
    assert not acufeno.presente({"presente": ""})
    # caso viejo sin la casilla, en el default que nadie tocó
    assert not acufeno.presente({"lateralidad": "craneal", "ruido": "Silbido", "frecuencia": 125})
    assert acufeno.presente({"lateralidad": "craneal", "ruido": "Siseo", "frecuencia": 125})


def test_elige_el_mas_cercano_de_los_tres():
    tin = _tin()
    for hz in (1000, 4000, 8000):
        tin.ver(_audio(on=(True, False), freq=F[hz], int_=(70, 20)), acufeno.INSTR_TONO)
    resp, comparados = tin.cual()
    assert resp == "elsegundo", resp
    assert len(comparados) == 3
    # la pregunta vacía la comparación: de a dos con lo que venga
    assert tin.cual()[0] == "nose"
    tin.ver(_audio(on=(True, False), freq=F[6000], int_=(70, 20)), acufeno.INSTR_TONO)
    tin.ver(_audio(on=(True, False), freq=F[3000], int_=(70, 20)), acufeno.INSTR_TONO)
    # 3000 está a 0,415 octavas de 4000 y 6000 a 0,585: el segundo
    assert tin.cual()[0] == "elsegundo"


def test_no_cuenta_lo_que_no_oye():
    tin = _tin()
    tin.ver(_audio(on=(True, False), freq=F[4000], int_=(5, 20)), acufeno.INSTR_TONO)  # bajo el umbral
    tin.ver(_audio(on=(True, False), freq=F[1000], int_=(60, 20)), acufeno.INSTR_TONO)
    assert tin.cual()[0] == "nose"


def test_sonoridad_en_el_oido_de_comparacion():
    tin = _tin()
    assert not tin.iguala(_audio(on=(True, False), int_=(15, 20)))   # 5 dB SL
    assert tin.iguala(_audio(on=(True, False), int_=(16, 20)))       # 6 dB SL


def test_inhibicion_residual():
    reloj = Reloj()
    tin = _tin(reloj=reloj)
    sonando = _audio(on=(False, True), int_=(20, 80), freq=F[8000])   # una octava arriba
    callado = _audio()
    assert tin.como_esta(callado) == "igualqueantes"   # todavía no hay inhibición
    tin.ver(sonando, acufeno.INSTR_INHIBICION)
    reloj.t += 30
    tin.ver(callado, acufeno.INSTR_INHIBICION)
    assert tin.como_esta(callado) == "igualqueantes"   # medio minuto no alcanza
    tin.ver(sonando, acufeno.INSTR_INHIBICION)
    for _ in range(60):                                # pulsado: cortes de medio segundo
        reloj.t += 0.5
        tin.ver(callado, acufeno.INSTR_INHIBICION)
        reloj.t += 0.5
        tin.ver(sonando, acufeno.INSTR_INHIBICION)
    tin.ver(callado, acufeno.INSTR_INHIBICION)
    reloj.t += 3
    assert tin.como_esta(callado) == "seescuchamasbajito"
    assert tin.corrida()["duracion_s"] >= 60
    reloj.t += 60
    assert tin.como_esta(callado) == "igualqueantes"   # no se mantiene


def test_solo_el_suyo_al_tapar_el_acufeno():
    """'Avíseme cuando solo escuche el mío': lo dice una vez, cuando el
    estímulo (una octava abajo, en el oído del acúfeno) llega al NME; el
    pulsado no lo repite, bajar y volver a subir sí."""
    reloj = Reloj()
    tin = _tin(reloj=reloj)
    S = acufeno.INSTR_SOLO_EL_MIO
    # 2 kHz en OI: umbral 30, NME 20 SL -> 50 dB HL
    for db in (35, 40, 45):
        tin.ver(_audio(on=(True, False), stim=(TONO, NBN), int_=(db, 20), output=(1, 1), freq=F[2000]), S)
        assert tin.solo_el_suyo() is None
    tapa = _audio(on=(True, False), int_=(50, 20), output=(1, 1), freq=F[2000])
    tin.ver(tapa, S)
    assert tin.solo_el_suyo() == "ahorasoloescuchoelsuyo"
    assert tin.solo_el_suyo() is None                 # una sola vez
    reloj.t += 0.5
    tin.ver(_audio(), S)                               # corte del pulsado
    reloj.t += 0.5
    tin.ver(tapa, S)
    assert tin.solo_el_suyo() is None
    # en el oído sin acúfeno no lo tapa
    tin2 = _tin(reloj=Reloj())
    tin2.ver(_audio(on=(True, False), int_=(90, 20), output=(0, 1), freq=F[2000]), S)
    assert tin2.solo_el_suyo() is None
    # bajar y volver a subir: lo dice de nuevo
    reloj.t += 0.5
    tin.ver(_audio(), S)
    reloj.t += 5
    tin.ver(tapa, S)
    assert tin.solo_el_suyo() == "ahorasoloescuchoelsuyo"
    # el minuto corre desde ahí, siga o no con "un minuto de sonido"
    reloj.t += 30
    tin.ver(_audio(on=(True, False), int_=(65, 20), output=(1, 1), freq=F[2000]), acufeno.INSTR_INHIBICION)
    reloj.t += 31
    tin.ver(_audio(), acufeno.INSTR_INHIBICION)
    reloj.t += 2
    assert tin.como_esta(_audio()) == "seescuchamasbajito"


def test_sin_acufeno():
    tin = _tin({})
    tin.ver(_audio(on=(True, False)), acufeno.INSTR_TONO)
    assert tin.cual()[0] == "nosecomparar"
    assert tin.ante_instruccion() == "queruido"
    assert tin.ante_instruccion() == "notengoruido"
    assert tin.como_esta(_audio()) == "notengoruido"
    assert not tin.iguala(_audio(on=(True, False), int_=(100, 20)))


class _Lbl:
    def setStyleSheet(self, _s):
        pass


class _Audiometro:
    lbl_response = _Lbl()

    def __init__(self):
        self.registro = []

    def _log(self, accion, **payload):
        self.registro.append((accion, payload))


def _respuesta():
    aerea = [[UMBRAL[0][i], UMBRAL[1][i]] for i in range(9)]
    caso = {"id": "99", "gender": 0, "Aerea": aerea, "Osea": aerea, "Aerea_mkg": aerea,
            "Osea_mkg": aerea, "LDL": [[100, 100]] * 9, "Tinnitus": BLOQUE}
    audiometro = _Audiometro()
    r = ResponseAudiometry(audiometro)
    r.set_case(caso)
    return r, audiometro


def test_response_mano_en_sonoridad():
    r, _ = _respuesta()
    r.rol_player(acufeno.INSTR_SONORIDAD)
    r.data["audio"].update(_audio(on=(True, False), int_=(16, 20)))
    r.response_()
    assert r.mano
    r.data["audio"]["int"][0] = 12
    r.response_()
    assert not r.mano


def test_response_pregunta_queda_en_el_registro():
    r, audiometro = _respuesta()
    r.rol_player(acufeno.INSTR_TONO)
    for hz in (2000, 4000):
        r.data["audio"].update(_audio(on=(True, False), freq=F[hz], int_=(60, 20)))
        r.response_()
        r.data["audio"]["stimOn"] = [False, False]
        r.response_()
    r.rol_player(acufeno.PREG_CUAL)
    assert r._respuesta_tinnitus(acufeno.PREG_CUAL) == "elsegundo"
    accion, payload = audiometro.registro[-1]
    assert accion == "audio_acufeno_respuesta"
    assert [c["freq"] for c in payload["comparados"]] == [2000, 4000]
    # las preguntas no reemplazan la instrucción vigente
    assert r._instruccion() == acufeno.INSTR_TONO


def test_response_solo_el_suyo_queda_en_el_registro():
    r, audiometro = _respuesta()
    dichos = []
    r.other_response.create_voice_ = dichos.append
    r.rol_player(acufeno.INSTR_SOLO_EL_MIO)
    r.data["audio"].update(_audio(on=(True, False), int_=(45, 20), output=(1, 1), freq=F[2000]))
    r.response_()
    assert dichos == []
    r.data["audio"]["int"][0] = 50
    r.response_()
    assert dichos == ["ahorasoloescuchoelsuyo"]
    accion, payload = audiometro.registro[-1]
    assert accion == "audio_acufeno_respuesta"
    assert payload == {"pregunta": acufeno.INSTR_SOLO_EL_MIO, "respuesta": "ahorasoloescuchoelsuyo"}
    r.data["audio"]["int"][0] = 55
    r.response_()
    assert dichos == ["ahorasoloescuchoelsuyo"]


def test_response_sano_reacciona_a_la_instruccion():
    r, audiometro = _respuesta()
    r.set_case({**r.dbdata, "Tinnitus": {"presente": False}})
    r.rol_player(acufeno.INSTR_TONO)
    assert r._pregunta == acufeno.INSTR_TONO      # se contesta al terminar el talkback
    assert r._respuesta_tinnitus(acufeno.INSTR_TONO) == "queruido"
    assert audiometro.registro[-1][1]["respuesta"] == "queruido"
    r.data["audio"].update(_audio(on=(True, False), int_=(100, 20)))
    r.rol_player(acufeno.INSTR_SONORIDAD)
    r.response_()
    assert not r.mano
    # con acúfeno la instrucción no se contesta
    r2, _ = _respuesta()
    assert r2._respuesta_tinnitus(acufeno.INSTR_TONO) is None


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
