"""
Smoke test del generador SOAE (emisiones otoacústicas espontáneas).

Verifica lo que define el comportamiento clínico del módulo:
- normative_data.json trae la sección 'soae' con las claves que usa el
  generador (si falta una, load_normative no falla pero el panel revienta
  al pintar).
- Los picos sorteados respetan el rango de frecuencia/nivel y la
  separación mínima entre SOAE del mismo oído.
- Patología: coclear/transmisión apagan los SOAE, neural los conserva
  (mismo contraste con ABR que el resto del módulo OAE).
- Al promediar espectros de potencia el NIVEL medio del ruido no baja
  (no hay promediación coherente sin estímulo) pero sí su dispersión, y
  los picos se quedan quietos: por eso emergen al final del registro.
- Ruido del paciente alto -> el piso sube y el registro deja de ser
  concluyente (no se informa "sin SOAE" con el conducto sucio).
- El seed es estable ENTRE ejecuciones (no usa hash() salteado): el mismo
  paciente no puede tener SOAE hoy y no tenerlos mañana.
- Con el caso tal como lo guarda el backend (case_create.php, tab EOA) las
  tasas quedan en rango clínico: ~40-50% de los oídos normales/neurales
  con SOAE, 0% en coclear/transmisión.
- soae_mode / soae_peaks del caso mandan sobre el sorteo: el docente puede
  fijar el hallazgo (y los picos cargados salen con el nivel pedido, sin
  atenuarse por patología).

core.base crea un QApplication al importarse, así que el test corre con
QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import json

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

REQUIRED_KEYS = [
    "fft_n", "spectrum_low_hz", "spectrum_high_hz", "default_record_s",
    "min_record_s", "max_record_s", "n_frames", "noise_floor_db_spl",
    "noise_floor_lf_rise_db_per_oct", "noise_floor_hf_rise_db_per_oct",
    "min_snr_db", "min_snr_half_db", "valid_floor_max_db_spl",
    "floor_window_bins", "peak_separation_bins", "prevalence_pct",
    "prevalence_right_ear_factor", "peak_count_lambda", "max_peaks",
    "peak_freq_min_hz", "peak_freq_max_hz", "peak_freq_center_hz",
    "peak_freq_spread_oct", "min_peak_spacing_ratio",
    "peak_level_mean_db_spl", "peak_level_sd_db", "peak_level_max_db_spl",
    "peak_level_jitter_db", "peak_bandwidth_bins",
]


def test_normative_data_structure():
    with open("resources/oae/normative_data.json", encoding="utf-8") as f:
        n = json.load(f)
    assert "soae" in n and "default" in n["soae"]
    soae = n["soae"]["default"]
    missing = [k for k in REQUIRED_KEYS if k not in soae]
    assert not missing, f"faltan claves en soae.default: {missing}"


def _gen():
    from oae.generators.soae import SoaeGenerator
    return SoaeGenerator()


def test_true_peaks_respect_normative():
    """Frecuencia, nivel y separación de los picos sorteados."""
    g = _gen()
    import numpy as np
    norm = g.normative
    found = 0
    for i in range(40):
        rng = np.random.default_rng(i)
        peaks = g.true_peaks("OD", {"type": "normal", "umbral": 10}, rng)
        found += len(peaks)
        assert len(peaks) <= norm["max_peaks"]
        for p in peaks:
            assert norm["peak_freq_min_hz"] <= p["freq_hz"] <= norm["peak_freq_max_hz"]
            assert p["level_db_spl"] <= norm["peak_level_max_db_spl"]
        for a, b in zip(peaks, peaks[1:]):
            assert b["freq_hz"] / a["freq_hz"] >= norm["min_peak_spacing_ratio"]
    assert found > 0, "ningún oído normal con SOAE en 40 sorteos"


def test_prevalence_is_not_universal():
    """Los SOAE no están en todos los oídos normales (~40-50%)."""
    import numpy as np
    g = _gen()
    con = sum(bool(g.true_peaks("OD", {"type": "normal", "umbral": 10},
                                np.random.default_rng(i)))
              for i in range(120))
    assert 0 < con < 120, f"prevalencia degenerada: {con}/120"


def test_pathology_gates_emissions():
    """Coclear/transmisión apagan los SOAE; neural los conserva."""
    import numpy as np
    g = _gen()
    for tipo, umbral in (("coclear", 55), ("transmission", 35)):
        for i in range(15):
            peaks = g.true_peaks("OD", {"type": tipo, "umbral": umbral},
                                 np.random.default_rng(i))
            piso = g._noise_floor_db(np.array([p["freq_hz"] for p in peaks] or [1500.0]),
                                     None)
            for p, nf in zip(peaks, piso):
                assert p["level_db_spl"] < nf, (
                    f"{tipo} {umbral} dB dejó un SOAE audible: {p}")
    neural = sum(len(g.true_peaks("OD", {"type": "neural", "umbral": 60},
                                  np.random.default_rng(i)))
                 for i in range(30))
    assert neural > 0, "la pérdida neural no debe apagar los SOAE"


def test_peaks_emerge_from_noise_with_averaging():
    """El ruido se aplana con los promedios y los picos se mantienen."""
    import numpy as np
    g = _gen()
    for ear in ("OD", "OI"):
        for umbral in (5, 10, 15, 20):
            r = g.generate(ear=ear, case={"type": "normal", "umbral": umbral})
            if not r["peaks"]:
                continue
            primero, ultimo = r["frames"][0], r["frames"][-1]
            freqs = r["freqs"]
            # Zona sin SOAE (agudos) para medir solo ruido.
            solo_ruido = freqs > 5000
            disp_ini = float(np.std(primero["spec_db"][solo_ruido]))
            disp_fin = float(np.std(ultimo["spec_db"][solo_ruido]))
            assert disp_fin < 0.5 * disp_ini, (
                f"la dispersión del ruido no cayó al promediar: "
                f"{disp_ini:.1f} -> {disp_fin:.1f} dB")
            # El nivel medio del ruido, en cambio, se mantiene.
            nivel_ini = float(np.mean(primero["spec_db"][solo_ruido]))
            nivel_fin = float(np.mean(ultimo["spec_db"][solo_ruido]))
            assert abs(nivel_fin - nivel_ini) < 6.0
            # Y los picos siguen ahí, con SNR sobre el criterio.
            assert all(p["snr_db"] >= g.normative["min_snr_db"]
                       for p in ultimo["peaks"])
            return
    raise AssertionError("ningún registro con SOAE detectados para evaluar")


def test_false_positive_rate_on_silent_ear():
    """Sin emisiones reales casi no aparecen picos, y los que aparecen
    quedan pegados al criterio (el artefacto borderline que en la clínica
    obliga a repetir el registro), nunca un pico franco."""
    g = _gen()
    registros = 40
    falsos = []
    for i in range(registros):
        r = g.generate(ear="OD", case={"type": "coclear", "umbral": 70,
                                       "atten_db": i * 0.1})
        falsos += r["peaks"]
    assert len(falsos) <= registros * 0.05, (
        f"{len(falsos)} picos espurios en {registros} registros silentes")
    for p in falsos:
        assert p["snr_db"] < g.normative["min_snr_db"] + 2


def test_seed_is_stable_across_processes():
    """El seed de SOAE no puede depender de hash() (salteado por proceso).

    Valores golden: si cambian, o se tocó stable_seed/case_fingerprint o
    alguien volvió a hash() y el hallazgo dejó de estar pegado al caso.
    Los goldens de los otros tres generadores están en test_oae_seeds.py.
    """
    from oae.generators.base import case_fingerprint, stable_seed
    assert stable_seed("soae", "OD", "type=normal", 30.0) == 4222648189
    assert case_fingerprint({"type": "normal", "desviaciones": {"4000": 8.0}}) \
        == "desviaciones=4000=8.0|type=normal"
    g = _gen()
    assert g._seed_from_params("OD", _caso(), 30.0) == g._seed_from_params("OD", _caso(), 30.0)
    assert g._seed_from_params("OD", _caso(), 30.0) != g._seed_from_params("OI", _caso(), 30.0)


def test_backend_case_shape_gives_clinical_rates():
    """Con el caso que arma el form del backend, las tasas son las clínicas."""
    g = _gen()

    def caso(tipo, umbral, **kw):
        base = {
            "type": tipo, "umbral": umbral, "atten_db": 0.0, "ruido_db": 0.0,
            "sello_pct": 85, "variabilidad_db": 2.5,
            "desviaciones": {str(h): 0.0 for h in
                             (500, 1000, 1500, 2000, 3000, 4000, 6000, 8000)},
        }
        base.update(kw)
        return base

    def tasa(tipo, umbrales):
        det = tot = 0
        for u in umbrales:
            for ear in ("OD", "OI"):
                for extra in ({}, {"sello_pct": 90}, {"variabilidad_db": 1.0}):
                    tot += 1
                    det += bool(g.generate(ear=ear, case=caso(tipo, u, **extra))["peaks"])
        return det / tot

    normal = tasa("normal", range(5, 30))
    neural = tasa("neural", range(30, 65, 5))
    assert 0.25 <= normal <= 0.65, f"prevalencia normal fuera de rango: {normal:.0%}"
    assert 0.25 <= neural <= 0.65, f"la pérdida neural debe conservar SOAE: {neural:.0%}"
    assert tasa("coclear", (30, 40, 50)) == 0.0
    assert tasa("transmission", (20, 30)) == 0.0


def _caso(**kw):
    """Perfil EOA de un oído con el shape que guarda el backend."""
    base = {
        "type": "normal", "umbral": 20, "atten_db": 0.0, "ruido_db": 0.0,
        "sello_pct": 85, "variabilidad_db": 2.5, "soae_mode": "auto",
        "desviaciones": {str(h): 0.0 for h in
                         (500, 1000, 1500, 2000, 3000, 4000, 6000, 8000)},
    }
    base.update(kw)
    return base


def test_soae_mode_ausentes_forces_empty():
    g = _gen()
    for ear in ("OD", "OI"):
        for tipo in ("normal", "neural"):
            r = g.generate(ear=ear, case=_caso(type=tipo, soae_mode="ausentes"))
            assert r["peaks"] == [] and r["true_peaks"] == []


def test_soae_mode_presentes_without_peaks_guarantees_one():
    """'Presentes' sin picos cargados: el sorteo elige cuáles, pero hay."""
    g = _gen()
    for umbral in range(5, 25):
        for ear in ("OD", "OI"):
            case = _caso(umbral=umbral, soae_mode="presentes")
            assert g.generate(ear=ear, case=case)["true_peaks"], (
                f"'presentes' dejó el oído {ear} sin SOAE (umbral {umbral})")


def test_configured_peaks_are_shown_as_asked():
    """Los picos cargados salen en la frecuencia y el nivel pedidos, aunque
    la patología del oído atenuaría la OEA: manda el docente."""
    g = _gen()
    picos = [{"hz": 1200, "db": 6.0}, {"hz": 1850, "db": 4.0}]
    for tipo, umbral in (("normal", 15), ("coclear", 50), ("transmission", 30)):
        case = _caso(type=tipo, umbral=umbral, soae_mode="presentes",
                     soae_peaks=picos)
        detectados = g.generate(ear="OD", case=case)["peaks"]
        assert len(detectados) == len(picos), f"{tipo}: {detectados}"
        for pedido, medido in zip(picos, detectados):
            assert abs(medido["freq_hz"] - pedido["hz"]) < 10
            assert abs(medido["level_db_spl"] - pedido["db"]) < 2.0


def test_configured_peaks_ignore_bad_rows():
    """Filas rotas del caso no tumban la captura."""
    g = _gen()
    case = _caso(soae_mode="presentes",
                 soae_peaks=[{"hz": 1500, "db": 6.0}, {"hz": 0}, {}, None])
    picos = g.generate(ear="OD", case=case)["true_peaks"]
    assert len(picos) == 1 and abs(picos[0]["freq_hz"] - 1500) < 1


def test_patient_noise_buries_configured_peaks():
    """El ruido del paciente sí puede tapar un pico forzado: el registro
    queda no concluyente, que es el hallazgo que se quiere enseñar."""
    g = _gen()
    case = _caso(soae_mode="presentes", ruido_db=12.0,
                 soae_peaks=[{"hz": 1500, "db": 6.0}])
    r = g.generate(ear="OD", case=case)
    assert r["true_peaks"] and not r["peaks"]


def test_patient_noise_raises_floor():
    """El ruido del paciente sube el piso sobre el máximo válido."""
    g = _gen()
    case = {"type": "normal", "umbral": 10}
    ruidoso = dict(case, ruido_db=12)
    import numpy as np
    freqs = np.array([1000.0, 2000.0, 4000.0])
    limpio_db = g._noise_floor_db(freqs, case)
    sucio_db = g._noise_floor_db(freqs, ruidoso)
    assert np.allclose(sucio_db - limpio_db, 12.0)
    assert sucio_db.mean() > g.normative["valid_floor_max_db_spl"]
    assert limpio_db.mean() <= g.normative["valid_floor_max_db_spl"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
