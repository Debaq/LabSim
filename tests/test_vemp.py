"""
VEMP: lo que tiene que seguir siendo cierto y no se ve mirando una curva.

1. La respuesta VIVE DE LA CONTRACCIÓN, y por eso la amplitud que compara
   es la CORREGIDA: dos registros del mismo oído con distinta contracción
   tienen que dar amplitudes crudas distintas y corregidas parecidas.
2. El equipo NO ACEPTA barridos con el músculo fuera de banda. Un registro
   con el paciente relajado no avanza: no es que avance sucio.
3. PROMEDIAR SIRVE: el ruido residual baja con la raíz de los barridos.
4. La VÍA ÓSEA SALTA EL OÍDO MEDIO. Un oído con el umbral aéreo inflado por
   un gap conductivo responde por vibrador; es la razón de que el módulo
   lea el audiograma del mismo caso.
5. La PATOLOGÍA CRUZA CON EL SUBTIPO: sacular pega en el cVEMP y deja el
   oVEMP como está.
6. La morfología es BIFÁSICA (p arriba, n abajo) y el caso viejo (un solo
   subtipo en la raíz del oído) sigue abriendo.

Sin scipy en el sandbox se stubbea con filtros pasa-todo: lo que se prueba
es el modelo, no el filtrado. core.base crea un QApplication al importarse,
así que QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
REPO = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
os.chdir(REPO)


def stub_scipy():
    """scipy.signal con filtros pasa-todo, solo si no está el real."""
    try:
        import scipy.signal  # noqa: F401
        return
    except ImportError:
        pass
    import numpy as np
    fake = types.ModuleType("scipy.signal")
    fake.butter = lambda *a, **k: (np.array([1.0]), np.array([1.0]))
    fake.filtfilt = lambda b, a, x, **k: np.asarray(x)
    scipy = types.ModuleType("scipy")
    scipy.signal = fake
    sys.modules.setdefault("scipy", scipy)
    sys.modules["scipy.signal"] = fake


stub_scipy()

import numpy as np  # noqa: E402

from vemp import patient, protocol  # noqa: E402
from vemp.engine import Ajustes, MotorVemp  # noqa: E402
from vemp.session import Sesion  # noqa: E402

TABLA_PLANA = [[10, 10] for _ in range(15)]


def caso(umbral_od=60, umbral_oi=60, tipo_od="normal", tipo_oi="normal",
         gap_oi=0, edad=34, genero=1):
    """cases.data mínimo con el shape que guarda CaseForm::parseVemp."""
    aerea = [list(par) for par in TABLA_PLANA]
    osea = [list(par) for par in TABLA_PLANA]
    if gap_oi:
        for idx in (2, 3):                  # 500 y 1000 Hz
            aerea[idx] = [10, 10 + gap_oi]
    def oido(tipo, umbral):
        return {"type": tipo, "subtipos": {
            s: {"umbral": umbral, "repro": True, "repro_var": 0.2,
                "average_objetivo": 200, "desviaciones": {}}
            for s in protocol.SUBTIPOS}}
    return {
        "gender": genero, "edad": edad, "id": 1,
        "Aerea": aerea, "Osea": osea, "Aerea_mkg": aerea, "Osea_mkg": osea,
        "VEMP": {"OD": oido(tipo_od, umbral_od), "OI": oido(tipo_oi, umbral_oi)},
    }


def motor(data=None, semilla=7):
    datos = patient.desde_caso(data or caso())
    return MotorVemp(datos, rng=np.random.default_rng(semilla))


def ajustes(**kwargs):
    base = dict(subtipo=protocol.CVEMP, lado="OD", intensidad=100,
                promedios=300, maniobra="Rotación cefálica sostenida")
    base.update(kwargs)
    return Ajustes(**base)


def promediar(mot, aju, emg, barridos=300):
    """Promedia de una sola vez: devuelve el registro acumulado."""
    sesion = Sesion()
    registro = sesion.nuevo(aju, mot.eje(aju.subtipo))
    registro.acumular(mot.lote(aju, emg, barridos))
    return registro


def p2p(registro):
    """Pico a pico de la traza (sin marcar: mide el modelo, no al alumno)."""
    return float(registro.y.max() - registro.y.min())


# ---------------------------------------------------------------------------


def test_amplitud_corregida_no_depende_de_la_contraccion():
    mot = motor()
    aju = ajustes()
    flojo = promediar(mot, aju, 35.0)
    fuerte = promediar(mot, aju, 100.0)
    assert p2p(fuerte) > p2p(flojo) * 1.6, "la cruda tiene que subir con el EMG"
    corr_flojo = p2p(flojo) / 35.0
    corr_fuerte = p2p(fuerte) / 100.0
    # La corregida no es idéntica (el músculo satura y el ruido sube), pero
    # sí del mismo orden: es lo que la hace comparable entre registros.
    assert 0.5 < corr_fuerte / corr_flojo < 1.5


def test_fuera_de_banda_no_entra_un_solo_barrido():
    mot = motor()
    relajado, _fatiga = protocol.maniobra_emg(protocol.CVEMP, "Relajado (decúbito)")
    lote = mot.lote(ajustes(), relajado, 200)
    assert lote.aceptados == 0
    assert lote.rechazados == 200


def test_promediar_baja_el_ruido():
    """El residual de la ventana pre-estímulo cae con la raíz de los barridos."""
    mot = motor()
    aju = ajustes()
    t = mot.eje(aju.subtipo)
    pre = t < 0
    pocos = promediar(mot, aju, 55.0, barridos=25)
    muchos = promediar(mot, aju, 55.0, barridos=400)
    assert float(np.std(muchos.y[pre])) < float(np.std(pocos.y[pre])) / 2


def test_el_umbral_del_caso_manda():
    mot = motor(caso(umbral_od=95))
    alto = promediar(mot, ajustes(intensidad=100), 55.0)
    mot_sano = motor(caso(umbral_od=60))
    sano = promediar(mot_sano, ajustes(intensidad=100), 55.0)
    assert p2p(alto) < p2p(sano) / 2


def test_la_via_osea_salta_el_oido_medio():
    """Oído con umbral aéreo inflado por un gap de 40 dB."""
    data = caso(umbral_oi=95, gap_oi=40)
    mot = motor(data)
    aereo = promediar(mot, ajustes(lado="OI", intensidad=110), 55.0)
    oseo = promediar(mot, ajustes(lado="OI", intensidad=60,
                                  transductor=protocol.OSEO), 55.0)
    assert p2p(oseo) > p2p(aereo)

    oido = patient.desde_caso(data).oido("OI")
    assert oido.gap_db("500 Hz") == 40
    assert oido.umbral(protocol.CVEMP, protocol.OSEO, "500 Hz") < \
        oido.umbral(protocol.CVEMP, protocol.AEREO, "500 Hz")


def test_la_patologia_cruza_con_el_subtipo():
    sano = motor(caso())
    sacular = motor(caso(tipo_od="sacular"))
    cerv_sano = promediar(sano, ajustes(), 55.0)
    cerv_mal = promediar(sacular, ajustes(), 55.0)
    assert p2p(cerv_mal) < p2p(cerv_sano) / 2

    aju_ocular = ajustes(subtipo=protocol.OVEMP, maniobra="Mirada superior ~30°")
    ocu_sano = promediar(sano, aju_ocular, 45.0)
    ocu_mal = promediar(sacular, aju_ocular, 45.0)
    assert abs(p2p(ocu_mal) - p2p(ocu_sano)) < p2p(ocu_sano) * 0.6


def test_morfologia_bifasica():
    """P13 arriba, N23 abajo: la inicial del pico ES su polaridad."""
    mot = motor()
    aju = ajustes()
    picos, _info = mot.picos(aju, 55.0)
    assert picos["p13"]["amp"] > 0
    assert picos["n23"]["amp"] < 0
    assert picos["p13"]["lat"] < picos["n23"]["lat"]


def test_polaridad_alternante_cancela_el_artefacto():
    mot = motor()
    t = mot.eje(protocol.CVEMP)
    ventana = (t >= 0) & (t <= 3)
    rar = mot._artefacto_estimulo(t, ajustes(polaridad="Rarefacción"), 55.0, 100)
    alt = mot._artefacto_estimulo(t, ajustes(polaridad="Alternante"), 55.0, 100)
    assert np.abs(alt[ventana]).max() < np.abs(rar[ventana]).max() / 4


def test_caso_viejo_sigue_abriendo():
    """Antes de que fueran tres, el caso traía un subtipo en la raíz."""
    data = caso()
    data["VEMP"]["OD"] = {"type": "sacular", "subtipo": "CVEMP", "umbral": 85,
                          "repro": True, "repro_var": 0.2,
                          "average_objetivo": 250, "desviaciones": {}}
    oido = patient.desde_caso(data).oido("OD")
    assert oido.tipo == "sacular"
    assert oido.subtipos["CVEMP"].umbral == 85
    # Los otros dos arrancan en su default, igual que en el editor.
    assert oido.subtipos["OVEMP"].umbral == patient.DEFAULTS["OVEMP"]["umbral"]


def test_sin_vemp_en_el_caso_no_hay_examen():
    assert patient.desde_caso({"gender": 0}) is None
    assert patient.desde_caso(None) is None


def test_asimetria_usa_las_corregidas():
    """Dos oídos con la misma respuesta y distinta contracción no son
    asimétricos: la cruda dice que sí, la corregida que no."""
    sesion = Sesion()
    mot = motor()
    for lado, emg in (("OD", 45.0), ("OI", 95.0)):
        aju = ajustes(lado=lado)
        registro = sesion.nuevo(aju, mot.eje(aju.subtipo))
        registro.acumular(mot.lote(aju, emg, 300))
        for pico in registro.picos_esperados:
            base = 13.0 if pico == "p13" else 23.0
            registro.marcar(pico, *registro.pico_cercano(base, pico))

    od, oi, ratio = sesion.asimetria(protocol.CVEMP)
    assert ratio is not None
    crudas = abs(od.p2p() - oi.p2p()) / (od.p2p() + oi.p2p()) * 100
    assert ratio < crudas


def test_marcar_se_pega_al_extremo_del_signo_correcto():
    mot = motor()
    aju = ajustes()
    registro = promediar(mot, aju, 55.0, barridos=600)
    lat_p, amp_p = registro.pico_cercano(13.0, "p13")
    lat_n, amp_n = registro.pico_cercano(23.0, "n23")
    assert amp_p > 0 and amp_n < 0
    assert abs(lat_p - 13.0) < 3.5 and abs(lat_n - 23.0) < 3.5


def test_la_normativa_no_se_mutila_en_memoria():
    """El boost por sexo multiplicaba el dict del JSON: cada llamada devolvía
    una amplitud más alta que la anterior."""
    from vemp.norms import Normativa
    norma = Normativa()
    primera = norma.baseline("adult_female", protocol.CVEMP)["p13"]["amp"]
    for _ in range(5):
        norma.baseline("adult_female", protocol.CVEMP)
    assert norma.baseline("adult_female", protocol.CVEMP)["p13"]["amp"] == primera


def test_sintonia_invertida_responde_en_agudos():
    """Un umbral muy bajo (ventana de más) invierte la sintonía y sube la
    amplitud por encima de la normativa."""
    data = caso(umbral_od=45)
    oido = patient.desde_caso(data).oido("OD")
    assert oido.sintonia_invertida(protocol.CVEMP)
    assert oido.umbral(protocol.CVEMP, protocol.AEREO, "1000 Hz") < \
        oido.umbral(protocol.CVEMP, protocol.AEREO, "500 Hz")

    mot = motor(data)
    sano = motor(caso(umbral_od=60))
    grande = promediar(mot, ajustes(intensidad=90), 55.0)
    normal = promediar(sano, ajustes(intensidad=90), 55.0)
    assert p2p(grande) > p2p(normal)


def test_la_fatiga_baja_el_emg():
    mot = motor()
    fresco = mot.emg_instantaneo(protocol.CVEMP, "Elevación de la cabeza en decúbito", 0)
    cansado = mot.emg_instantaneo(protocol.CVEMP, "Elevación de la cabeza en decúbito", 90)
    assert cansado < fresco * 0.85


def test_el_ovemp_se_registra_cruzado():
    assert protocol.lado_registro(protocol.OVEMP, "OD") == "OI"
    assert protocol.lado_registro(protocol.CVEMP, "OD") == "OD"


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  {nombre} OK")
            except AssertionError as exc:
                fallos += 1
                print(f"  {nombre} FALLÓ: {exc}")
    print("TODOS LOS TESTS PASARON" if not fallos else f"{fallos} FALLARON")
