"""Sesiones de ABR guardadas: empaquetar las curvas para el informe y
volver a dibujarlas.

Al mismo paciente se le puede hacer más de un ABR (uno por atención), y
el alumno tiene que poder volver a una sesión anterior para verla o
terminarla. Para eso el informe guarda, además de lo que ya llevaba
(setting, LatAmp, técnica, FSP), el TRAZO de cada curva y dónde quedaron
sus marcas en el gráfico: sin eso solo había números, no curvas que
mirar. El backend no deja cambiar ni los trazos ni el setting de una
sesión cerrada (ver labsim_backend/src/ReportRevision.php).
"""
from datetime import datetime

import numpy as np

# Decimales con que viaja cada serie. El tiempo va en ms (0.1 us sobra) y
# la amplitud en uV: 0.001 uV es 1 nV, muy por debajo del ruido residual.
DEC_T = 4
DEC_UV = 3


def _serie(valores, decimales):
    return [round(float(v), decimales) for v in np.asarray(valores)]


def pack_trace(values: dict) -> dict:
    """Lo que hace falta para redibujar una curva, en listas planas.

    El tiempo es el mismo para los cuatro trazos: va una sola vez.
    """
    t, ipsi = values['ipsi_xy']
    traza = {'t': _serie(t, DEC_T), 'ipsi': _serie(ipsi, DEC_UV),
             'repro': float(values.get('repro') or 0),
             'gap': float(values.get('gap') or 0)}
    for clave, nombre in (('contra_xy', 'contra'), ('sub_a', 'sub_a'),
                          ('sub_b', 'sub_b')):
        xy = values.get(clave)
        traza[nombre] = _serie(xy[1], DEC_UV) if xy is not None else None
    return traza


def unpack_trace(traza: dict, intensidad) -> dict:
    """La inversa de pack_trace, con la forma que espera AbrGraph.create_line."""
    t = np.asarray(traza['t'], dtype=float)

    def xy(nombre):
        serie = traza.get(nombre)
        return (t, np.asarray(serie, dtype=float)) if serie is not None else None

    return {'ipsi_xy': xy('ipsi'), 'contra_xy': xy('contra'),
            'sub_a': xy('sub_a'), 'sub_b': xy('sub_b'),
            'repro': traza.get('repro', 0), 'intencity': intensidad,
            # Una sesion guardada no se sigue promediando.
            'done': True}


def curve_order(nombre: str) -> tuple:
    """R1, R2, ..., R10: por numero, no alfabetico (R10 no va antes de R2)."""
    letra, numero = nombre[:1], nombre[1:]
    return (letra, int(numero) if numero.isdigit() else 0)


def session_label(report: dict) -> str:
    """Como se lista una sesion anterior en el combo."""
    fecha = report.get('fecha') or ''
    try:
        fecha = datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError:
        pass
    hora = (report.get('hora') or '')[:5]
    prueba = 'ECochG' if report.get('tipo') == 'ELECTROCOCLEO' else 'ABR'
    return ' '.join(p for p in (fecha, hora, '·', prueba) if p)


def editable_part(data: dict) -> dict:
    """Lo que el alumno puede cambiar en una sesion cerrada.

    Mismos campos que ReportRevision.php: si esto no cambio, no hay nada
    que guardar ni que preguntar al salir.
    """
    curvas = {}
    for nombre, curva in (data.get('curvas') or {}).items():
        curvas[nombre] = {k: curva.get(k) for k in
                          ('LatAmp', 'marcas', 'marcas_graf')}
    return {'curvas': curvas,
            'hallazgos': data.get('hallazgos', ''),
            'conclusion': data.get('conclusion', '')}
