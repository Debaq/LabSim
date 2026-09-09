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
    render_ficha_html, resolver_fechas_historia_clinica)


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


def test_las_atenciones_previas_van_aparte_del_historial_de_alumnos():
    """No son atenciones de alumnos: son parte del caso."""
    html = _ficha(HISTORIA)
    assert "Atenciones previas" in html
    assert html.index("Atenciones previas") < html.index("Historial de atenciones")


def test_sin_historia_no_aparece_la_seccion():
    html = _ficha("")
    assert "Atenciones previas" not in html


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
