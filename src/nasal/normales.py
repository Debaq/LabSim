"""El paciente normal de cada examen nasal y de sueño, para el caso que no
trae ese bloque en `cases.data`.

Decidido por él el 2026-11-06: los pacientes creados y los del libro que no
traen datos de nariz, olfato, prick, espirometría o sueño son normales en
esos exámenes (antes el equipo no medía). Un bloque mal escrito también da
el normal: se valida al guardar el caso (CaseForm.php); el equipo no avisa
errores de la base de datos, solo los deja en el log.

Cada función devuelve el bloque tal como lo escribiría el docente, para que
pase por el mismo `normaliza` que un bloque del caso.
"""

from nasal import olfatometria

# Del bloque nasal no hace falta nada: modelo.normaliza({}) es la nariz normal.
NASAL = {'nombre': 'Normal (el caso no trae nariz)', 'cuadro': 'normal'}

# TDI normal para la edad = la media de su grupo (Oleszkiewicz y cols., 2019),
# repartida como en adultos sanos: umbral ~24 %, discriminación ~36 %,
# identificación ~40 % (p. ej. 21-30 años: T 8,75, D 13, I 14).
_REPARTO_TDI = (('T', 0.24), ('D', 0.36), ('I', 0.40))


def edad(data):
    """La edad del caso; si no viene o no es un número, la de un adulto (el
    dato se valida en la base de datos, no aquí)."""
    try:
        e = float(data.get('edad'))
    except (TypeError, ValueError):
        print('nasal: el caso no trae una edad válida, se usa 30')
        return 30.0
    return e if e == e and 0 <= e <= 120 else 30.0


def olfato(edad):
    g = olfatometria.grupo_edad(edad) or olfatometria.NORMAS[0 if (edad or 0) < 5 else -1]
    media = g[2]
    v = {}
    for k, f in _REPARTO_TDI:
        x = media * f
        v[k] = round(x * 4) / 4 if k == 'T' else float(round(x))
    v['T'] = min(max(v['T'], 1.0), 16.0)
    v['D'] = min(v['D'], 16.0)
    v['I'] = min(v['I'], 16.0)
    return {'lados': {'D': dict(v), 'I': dict(v)}, 'conducta': 'buena', 'preparacion': 'ok'}


# Histamina positiva (H29: el control positivo da 3 mm o más), sin pápula a
# ningún alérgeno, sin dermografismo ni fármacos.
PRICK = {'histamina': 5, 'dermografismo': 0, 'alergenos': {}, 'farmaco': None}

# Talla mediana por edad (cm), 3 a 18 años, y la del adulto; interpolada.
_TALLA = {
    'M': ((3, 96), (5, 110), (8, 128), (10, 138), (12, 149), (14, 164), (16, 172), (18, 174)),
    'F': ((3, 95), (5, 109), (8, 127), (10, 138), (12, 151), (14, 159), (16, 161), (18, 161)),
}
_TALLA_ADULTO = {'M': 171, 'F': 158}
# PEF / FEV1 de un adulto sano (~2,4: FEV1 4,2 L -> PEF 10 L/s).
_PEF_FEV1 = 2.4


def _talla(edad, sexo):
    tabla = _TALLA[sexo]
    if edad >= tabla[-1][0]:
        return _TALLA_ADULTO[sexo]
    if edad <= tabla[0][0]:
        return tabla[0][1]
    for (e0, t0), (e1, t1) in zip(tabla, tabla[1:]):
        if e0 <= edad <= e1:
            return t0 + (t1 - t0) * (edad - e0) / (e1 - e0)
    return _TALLA_ADULTO[sexo]


def espiro(edad, sexo):
    """La maniobra perfecta = el previsto GLI-2012 para su edad, sexo y talla;
    sin broncodilatador (un normal no lo necesita) ni obstrucción alta."""
    from nasal import espirometria as E
    sexo = sexo if sexo in ('M', 'F') else 'M'
    talla = round(_talla(edad, sexo))
    imc = 23.0 if edad >= 18 else 17.0
    peso = round(imc * (talla / 100) ** 2)
    fvc = E.previsto(sexo, 'FVC', edad, talla)
    fev1 = min(E.previsto(sexo, 'FEV1', edad, talla), fvc * 0.95)
    pef = min(max(fev1 * _PEF_FEV1, 1.0), 16.0)
    return {'talla': talla, 'peso': peso,
            'pre': {'fvc': round(min(max(fvc, 0.5), 8.0), 2),
                    'fev1': round(min(max(fev1, 0.3), 7.0), 2),
                    'pef': round(pef, 1)},
            'tope_e': None, 'tope_i': None, 'colaboracion': 'buena'}


def sueno(semilla):
    """Una noche normal: arquitectura normal y un IAH bajo 5."""
    return {'perfil': 'personalizado', 'canula_suelta': None, 'cpap': None,
            'params': {'tasa': 1.5, 'rem': 1.5, 'supino': 1.3,
                       'obstructivas': 0.2, 'mixtas': 0.0, 'centrales': 0.1,
                       'hipopneas': 0.7, 'rera': 0.0,
                       'caida_apnea': 3.0, 'caida_hipopnea': 3.0, 'hip_sin_desaturar': 0.3,
                       'spo2_basal': 96.5, 'tib': 470, 'semilla': semilla}}
