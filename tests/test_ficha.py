"""
Render de la ficha clínica (src/core/ficha.py), que ven tanto el docente
desde la agenda como el alumno desde "Mis pacientes".

Cubre lo que se rompía sin que nadie lo notara: la historia clínica se
interpolaba cruda en un <li>, así que sus saltos de línea colapsaban y las
tres o cuatro atenciones previas quedaban como un párrafo corrido.
"""

import os
import sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.ficha import (  # noqa: E402
    linea_tiempo, render_ficha_html, resolver_fechas_historia_clinica)


class FilaFalsa:
    """Lo mínimo que render_ficha_html le pide a una fila de agenda."""

    def __init__(self, historia=""):
        self.fecha = "10-09-26"
        self.hora = "09:00"
        self.rut = "11111111-1"
        self.nombre = "Ana"
        self.apellido = "Pérez"
        self.fecha_nac = "21-08-2026"
        self.procedimiento = "Evaluación auditiva"
        self.atencion = {}
        self.alumno = ""
        self.grupo = ""


HISTORIA = (
    "{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening: refiere OD.\n"
    "{{-12}} Control con pediatra, sin hallazgos.\n"
    "{{-5}} Se deriva a evaluación auditiva."
)


def _shedule_con_atencion(row, alumno, nota):
    """Un shedule con una atención cerrada de `alumno` sobre ese paciente."""
    row.atencion = {alumno: {"estado": "atendido", "nota": nota, "hora_real": "09:12:00"}}
    return {"agenda_1": {1: row}}


def _ficha(historia):
    row = FilaFalsa()
    caso = {"historia_clinica": historia}
    return render_ficha_html(row, caso, {"agenda_1": {}}, "alumno1", False)


def test_cada_atencion_previa_queda_en_su_propia_linea():
    """Tres líneas en el campo = tres <li>, no un párrafo corrido."""
    html = _ficha(HISTORIA)
    assert html.count("<li>") >= 3, html
    for trozo in ("Nace de 38 semanas", "Control con pediatra", "evaluación auditiva"):
        assert trozo in html, trozo


def test_las_llaves_de_fecha_se_resuelven_en_la_ficha():
    """{{-20}} tiene que salir como fecha real, no como la llave."""
    html = _ficha(HISTORIA)
    assert "{{-20}}" not in html
    assert "21-08-2026" in html, html      # 20 días antes del 10-09-26
    assert "05-09-2026" in html, html      # 5 días antes


def test_la_evolucion_del_alumno_va_despues_de_las_atenciones_previas():
    """Una ficha se lee en orden: primero de dónde viene el paciente."""
    entradas = linea_tiempo(HISTORIA, "10-09-26", [
        ("10-09-26", "09:12:00", "alumno1", "Se realiza audiometría."),
    ])
    assert [e["fecha"] for e in entradas] == [
        "21-08-2026", "29-08-2026", "05-09-2026", "10-09-2026"]
    assert entradas[-1]["alumno"] == "alumno1"
    assert entradas[0]["alumno"] == "", "lo del caso no es de ningún alumno"


def test_la_fecha_se_muestra_en_un_solo_formato():
    """La agenda guarda dd-MM-yy y la historia queda en dd-MM-yyyy."""
    entradas = linea_tiempo("{{-1}} Previa.", "10-09-26",
                            [("10-09-26", "09:00:00", "a", "Mía.")])
    assert all(len(e["fecha"]) == len("dd-MM-yyyy") for e in entradas), entradas


def test_el_orden_no_depende_del_texto_de_la_fecha():
    """dd-MM-yy ordenado como string pone enero antes que diciembre."""
    entradas = linea_tiempo("", "05-01-26", [
        ("05-01-26", "09:00:00", "a", "Segunda ronda."),
        ("10-12-25", "10:00:00", "a", "Primera ronda."),
    ])
    assert [e["texto"] for e in entradas] == ["Primera ronda.", "Segunda ronda."]


def test_dos_atenciones_el_mismo_dia_se_ordenan_por_hora():
    entradas = linea_tiempo("", "10-09-26", [
        ("10-09-26", "15:30:00", "a", "Tarde."),
        ("10-09-26", "09:00:00", "a", "Mañana."),
    ])
    assert [e["texto"] for e in entradas] == ["Mañana.", "Tarde."]


def test_una_atencion_sin_fecha_es_la_de_ahora_y_va_al_final():
    entradas = linea_tiempo(HISTORIA, "10-09-26", [("", "", "a", "Sin fecha.")])
    assert entradas[-1]["texto"] == "Sin fecha."


def test_el_alumno_ve_todas_las_entradas_iguales():
    """Marcar cuál escribió él rompe el realismo de la ficha."""
    row = FilaFalsa()
    caso = {"historia_clinica": HISTORIA}
    shedule = _shedule_con_atencion(row, "alumno1", "Se realiza audiometría.")
    html = render_ficha_html(row, caso, shedule, "alumno1", False)
    assert "Se realiza audiometría." in html
    assert "alumno1" not in html, "el alumno no se ve a sí mismo rotulado en su ficha"
    assert "tu atención" not in html.lower()


def test_el_docente_si_ve_quien_escribio_cada_nota():
    """Para el docente la ficha es herramienta de corrección, no el registro."""
    row = FilaFalsa()
    caso = {"historia_clinica": HISTORIA}
    shedule = _shedule_con_atencion(row, "alumno1", "Se realiza audiometría.")
    html = render_ficha_html(row, caso, shedule, "docente", True)
    assert "alumno1" in html


def test_sin_historia_ni_atenciones_lo_dice():
    html = _ficha("")
    assert "Sin historial registrado" in html


def test_lineas_en_blanco_no_generan_items_vacios():
    html = _ficha("{{-3}} Una sola atención.\n\n\n")
    assert html.count("<li>") == 1, html


def test_el_texto_del_caso_no_puede_romper_el_html():
    """Un "<" suelto rompía la ficha entera sin dejar rastro de por qué."""
    html = _ficha("{{-1}} Otoscopia: conducto <2 mm, cerumen impactado.")
    assert "&lt;2 mm" in html, html
    assert "<2 mm" not in html


def test_fecha_de_cita_invalida_deja_la_llave():
    """Mejor la llave a la vista que una fecha inventada."""
    assert resolver_fechas_historia_clinica("{{-5}} algo", "") == "{{-5}} algo"
    assert resolver_fechas_historia_clinica("{{-5}} algo", "no-es-fecha") == "{{-5}} algo"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
