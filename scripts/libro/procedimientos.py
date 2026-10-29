"""Qué procedimiento lleva cada paciente del libro en la práctica libre.

Lo usan sql_practica.py (lo que se carga en practice_items) y previos.py (qué
exámenes trae cada paciente en cada carpeta), para que los dos digan lo mismo.
"""

# Examen -> como se nombra en el procedimiento, en este orden
# (el Tomo I nombra distinto las suyas: audiograma, timpanograma, reflejos, acumetria)
PROC = [('acumetria', 'Acumetría'), ('audiosupra', 'Audiometría'), ('audiograma', 'Audiometría'),
        ('logoaudiometria', 'Audiometría'), ('impedancia', 'Impedanciometría'),
        ('timpanograma', 'Impedanciometría'), ('reflejos', 'Impedanciometría'),
        ('teoae', 'EOA'), ('dpoae', 'EOA'), ('abr', 'PEATC'), ('ecochg', 'ECochG'), ('cortical', 'Corticales'),
        ('vemp', 'VEMP')]
# El libro no tiene figura de ASSR: los casos hechos para practicarlo lo dicen acá
CON_ASSR = {'h13_lactante', 'h13_nino_tea', 'cap28_no_colabora'}


# Lo que enseña cada capítulo que trata de un examen: el procedimiento nombra
# solo eso, y los demás exámenes que el libro muestra de ese paciente llegan
# hechos (la ficha los muestra con su hoja, ver scripts/libro/previos.py y
# core/ficha.examenes_que_trae). Así el paciente del capítulo del PEATC no
# cree que viene a la audiometría; hacerla igual queda como repetición. Los
# capítulos que no están acá enseñan un cuadro con toda la batería: el
# procedimiento sigue nombrando todo lo de sus figuras.
FOCO = {
    9: {'ECochG', 'VEMP'}, 11: {'PEATC', 'VEMP'}, 12: {'PEATC', 'VEMP'}, 14: {'PEATC'},
    18: {'PEATC'}, 20: {'VEMP'}, 30: {'Corticales'},
    'H7': {'Impedanciometría'}, 'H9': {'EOA'}, 'H10': {'PEATC'}, 'H11': {'ECochG'},
    'H12': {'VEMP'}, 'H13': {'ASSR'},
}


# Pacientes cuyo procedimiento no sale de las figuras: el de H21 viene a probarse
# audífonos (su figura es campo_libre, que no está en PROC) y salía con el
# "Otoscopía + Acumetría" por defecto, que además le quitaba lo que trae.
PROC_PROPIO = {'h21_p36': 'Prueba de audífonos'}


def procedimiento(figs, clave='', cap=None):
    if clave in PROC_PROPIO:
        return PROC_PROPIO[clave]
    nombres = _examenes(figs) + (['ASSR'] if clave in CON_ASSR else [])
    if cap in FOCO:
        nombres = [n for n in nombres if n in FOCO[cap]] or sorted(FOCO[cap])
    return ' + '.join(nombres) or 'Otoscopía + Acumetría'


def _examenes(figs):
    vistos = []
    for f, nombre in PROC:
        if f in figs and nombre not in vistos:
            vistos.append(nombre)
    return vistos


def capitulo(clave):
    """'cap11_schwannoma' -> 11; 'h7_p34' -> 'H7' (como en el catálogo)."""
    pre = clave.split('_', 1)[0]
    return int(pre[3:]) if pre.startswith('cap') else pre.upper()
