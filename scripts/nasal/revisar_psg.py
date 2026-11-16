"""Revisa los informes de polisomnografía de los alumnos contra la noche de
verdad: lo que corrigieron bien, lo que corrigieron mal y lo que se les pasó.

La app guarda en el informe POLISOMNOGRAFIA la puntuación final del alumno
(cada evento con su tiempo, duración y tipo), la regla de hipopnea, el
montaje, la gravedad elegida y el texto. La noche es la misma para el mismo
caso (nasal/sueno.py), así que aquí se rehace y se compara evento por evento:

- **bien**: el evento del alumno se cruza con uno de verdad del mismo tipo.
- **tipo equivocado**: se cruza con uno de verdad de otro tipo (p. ej. dejó
  como AC una que era AO).
- **sobra**: no se cruza con ningún evento de verdad.
- **se le pasó**: un evento de verdad (no RERA) sin nada puntuado encima.

Y los índices: el del alumno (con su regla), el de la automática sin tocar
(la misma que vio él: semilla psg/<cita>) y el de la noche bien puntuada con
la misma regla. La gravedad que eligió se compara con la que da su índice y
con la de verdad. Del texto solo marca lo que la guía prohíbe escribir
(diagnóstico, tratamiento) y si dice qué regla usó.

Uso (con el token de la consola remota, docs/consola_remota.md):

    python3 scripts/nasal/revisar_psg.py                 # informes de hoy
    python3 scripts/nasal/revisar_psg.py --desde 2026-11-16 --detalle
    python3 scripts/nasal/revisar_psg.py --csv notas_psg.csv
    python3 scripts/nasal/revisar_psg.py --pauta         # la pauta de las fichas 159-162, sin red
"""

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'src'))
sys.path.insert(0, str(RAIZ / 'scripts'))

from nasal import sueno as Z  # noqa: E402

CORTO = {'ao': 'AO', 'am': 'AM', 'ac': 'AC', 'h': 'H', 'rera': 'RERA'}
FICHAS_GUIA = {'159': 'roncador', '160': 'moderado', '161': 'grave', '162': 'dudosa'}
PROHIBIDO = (r'\bSA[HO]S\b', r's[ií]ndrome', r'\bCPAP\b', r'roncador simple', r'no tiene nada',
             r'debe dormir', r'necesita', r'\bdiagn[oó]stic', r'tratamiento', r'cirug[ií]a')


def f(v, d=1):
    return '—' if v is None else f'{v:.{d}f}'.replace('.', ',')


def hhmm(seg):
    seg = int(seg)
    return f'{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}'


def cruza(a, b):
    return a['t'] < b['t'] + b['dur'] and b['t'] < a['t'] + a['dur']


def comparar(S, eventos):
    """Clasifica la puntuación del alumno contra los eventos de verdad."""
    verdad = S['ev']
    bien, mal, sobra = [], [], []
    for e in eventos:
        v = next((x for x in verdad if cruza(e, x)), None)
        if v is None:
            sobra.append(e)
        elif v['tipo'] == e['tipo']:
            bien.append(e)
        else:
            mal.append((e, v))
    perdidos = [x for x in verdad if x['tipo'] != 'rera' and not any(cruza(e, x) for e in eventos)]
    rera_perdidos = [x for x in verdad if x['tipo'] == 'rera' and not any(cruza(e, x) for e in eventos)]
    return bien, mal, sobra, perdidos, rera_perdidos


def revisar(S, data, appointment_id):
    """Un informe -> dict con todo lo que se mira."""
    regla = data.get('regla') or '3'
    montaje = list(data.get('montaje') or [])
    eventos = [{'t': int(e['t']), 'dur': int(e['dur']), 'tipo': e['tipo'], 'auto': bool(e.get('auto'))}
               for e in data.get('eventos') or [] if isinstance(e, dict) and e.get('tipo') in CORTO]
    excluidos = [(int(a), int(b)) for a, b in data.get('excluidos') or []]
    bien, mal, sobra, perdidos, rera_perdidos = comparar(S, eventos)
    ideal = [{'t': x['t'], 'dur': x['dur'], 'tipo': x['tipo']} for x in S['ev']]
    r_alumno = Z.indices(S, [dict(e) for e in eventos], regla, excluidos)
    r_ideal = Z.indices(S, [dict(e) for e in ideal], regla)
    r_ideal3 = Z.indices(S, [dict(e) for e in ideal], '3')
    auto = Z.auto_puntuar(S, montaje, f'psg/{appointment_id}')
    r_auto = Z.indices(S, [dict(e) for e in auto], regla)
    texto = ' '.join([data.get('hallazgos') or '', data.get('conclusion') or ''])
    prohibido = sorted({m.group(0) for p in PROHIBIDO for m in re.finditer(p, texto, re.I)})
    dice_regla = bool(re.search(r'(3|4)\s*%|regla', texto, re.I))
    faltan = [k for k in Z.sensores_del_estudio(S['estudio']) if k not in montaje]
    return dict(
        estudio=S['estudio'], regla=regla, faltan=faltan,
        n=len(eventos), tocados=sum(1 for e in eventos if not e['auto']),
        bien=bien, mal=mal, sobra=sobra, perdidos=perdidos, rera_perdidos=rera_perdidos,
        iah_alumno=r_alumno['IAH'], iah_auto=r_auto['IAH'], iah_ideal=r_ideal['IAH'],
        idr_alumno=r_alumno['IDR'], r_alumno=r_alumno, r_ideal=r_ideal,
        gravedad=data.get('gravedad') or '', grav_su_indice=Z.gravedad_clave(r_alumno['IAH']),
        grav_verdad=Z.gravedad_clave(r_ideal3['IAH']),
        prohibido=prohibido, dice_regla=dice_regla,
        sin_texto=not (data.get('conclusion') or '').strip(),
    )


def resumen_errores(R):
    """Lo corregido mal, en pocas palabras: 'AC→AO ×3, H→AO ×1'."""
    cuenta = {}
    for e, v in R['mal']:
        k = f"{CORTO[e['tipo']]} (era {CORTO[v['tipo']]})"
        cuenta[k] = cuenta.get(k, 0) + 1
    return ', '.join(f'{k} ×{n}' for k, n in sorted(cuenta.items(), key=lambda x: -x[1]))


def observaciones(R):
    obs = []
    if R['faltan']:
        obs.append('sin ' + ', '.join(R['faltan']))
    if not R['gravedad']:
        obs.append('no eligió gravedad')
    elif R['gravedad'] != R['grav_su_indice']:
        obs.append(f"gravedad {R['gravedad']} no calza con su IAH ({R['grav_su_indice']})")
    if R['sin_texto']:
        obs.append('sin conclusión')
    elif not R['dice_regla']:
        obs.append('la conclusión no dice la regla')
    if R['prohibido']:
        obs.append('escribe: ' + ', '.join(f'"{p}"' for p in R['prohibido']))
    if R['regla'] == '4':
        obs.append('quedó con la regla del 4 %')
    return '; '.join(obs)


def detalle(R, S):
    lineas = []
    for e, v in R['mal']:
        lineas.append(f"    {hhmm(e['t'])} {Z.etapa_en(S, e['t'])} {Z.posicion_en(S, e['t'])}: "
                      f"puntuó {CORTO[e['tipo']]}, era {CORTO[v['tipo']]}")
    for e in R['sobra']:
        lineas.append(f"    {hhmm(e['t'])}: {CORTO[e['tipo']]} que no existe"
                      + (' (de la automática)' if e['auto'] else ' (agregado por el alumno)'))
    for x in R['perdidos']:
        lineas.append(f"    {hhmm(x['t'])} {x['etapa']} {x['pos']}: se le pasó una {CORTO[x['tipo']]} "
                      f"de {x['dur']} s (caída {x['drop']:.1f}, despertar {'sí' if x['arousal'] else 'no'})")
    return lineas


# ── Pauta (sin red) ───────────────────────────────────────────────────────

def pauta():
    todos = [k for k, *_ in Z.SENSORES]
    for ficha, perfil in FICHAS_GUIA.items():
        S = Z.noche(Z.normaliza({'perfil': perfil}), 'psg')
        R = Z.resumen(S, 'psg')
        ideal = [{'t': x['t'], 'dur': x['dur'], 'tipo': x['tipo']} for x in S['ev']]
        r3 = Z.indices(S, [dict(e) for e in ideal], '3')
        r4 = Z.indices(S, [dict(e) for e in ideal], '4')
        sin_rera = [e for e in ideal if e['tipo'] != 'rera']
        idr0 = Z.indices(S, [dict(e) for e in sin_rera], '3')['IDR']
        autos = [Z.indices(S, [dict(e) for e in Z.auto_puntuar(S, todos, f'psg/{a}')], '3')['IAH']
                 for a in range(1000, 1100)]
        c = R['n']
        print(f'\n## Ficha {ficha} ({perfil})')
        print(f"Noche de verdad: AO {c['ao']}, AM {c['am']}, AC {c['ac']}, H {c['h']} "
              f"({R['hip con desaturación']} con desaturación ≥ 3, {R['hip solo despertar']} solo con despertar), "
              f"RERA {c['rera']}")
        print(f"Sueño: TIB {f(r3['TIB'], 0)} min, TST {f(r3['TST'], 0)} min, eficiencia {f(r3['eficiencia'])} %, "
              f"latencia {f(r3['latencia'], 0)} min, WASO {f(r3['WASO'], 0)} min, "
              f"N1/N2/N3/REM {f(r3['% N1'])}/{f(r3['% N2'])}/{f(r3['% N3'])}/{f(r3['% R'])} %")
        print(f"IAH bien puntuado: regla 3 % o despertar {f(r3['IAH'])} ({Z.gravedad_clave(r3['IAH'])}); "
              f"regla 4 % {f(r4['IAH'])} ({Z.gravedad_clave(r4['IAH'])})")
        print(f"Automática sin tocar (cambia con la cita): {f(min(autos))} a {f(max(autos))}")
        print(f"Posición (regla 3): supino {f(r3['IAH supino'])}, izq. {f(r3['IAH izquierda'])}, "
              f"der. {f(r3['IAH derecha'])} · REM {f(r3['IAH REM'])}, NREM {f(r3['IAH NREM'])}")
        print(f"IDR: {f(idr0)} sin RERA puntuados, {f(r3['IDR'])} con todos")
        print(f"Oxígeno: IDO3 {f(r3['IDO3'])}, IDO4 {f(r3['IDO4'])}, SpO₂ media {f(r3['SpO2 media'])} %, "
              f"mínima {f(r3['SpO2 min'], 0)} %, T90 {f(r3['T90'])} % · ronquido {f(r3['ronquido %'], 0)} %")


# ── Informes de producción ────────────────────────────────────────────────

def consultar(sql, params):
    import consola
    url, token, _ = consola._cargar_env(None)
    r = consola._llamar(url, token, {'sql': sql, 'params': params})
    cols = r.get('columnas') or []
    return [fila if isinstance(fila, dict) else dict(zip(cols, fila)) for fila in r.get('filas') or []]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pauta', action='store_true', help='la pauta de las fichas 159-162 (sin red)')
    ap.add_argument('--desde', default=dt.date.today().isoformat(), help='informes guardados desde (AAAA-MM-DD)')
    ap.add_argument('--fichas', default=','.join(FICHAS_GUIA), help='fichas a revisar, separadas por coma')
    ap.add_argument('--detalle', action='store_true', help='cada evento mal, sobrante o perdido con su hora')
    ap.add_argument('--csv', help='guardar la tabla en este archivo')
    a = ap.parse_args()
    if a.pauta:
        pauta()
        return
    fichas = [x.strip() for x in a.fichas.split(',') if x.strip()]
    marcas = ','.join('?' * len(fichas))
    filas = consultar(
        f"SELECT r.id, r.data, r.updated_at, ap.id AS cita, ap.case_id, u.display_name AS alumno "
        f"FROM reports r JOIN attendances at ON at.id = r.attendance_id "
        f"JOIN appointments ap ON ap.id = at.appointment_id JOIN users u ON u.id = at.student_id "
        f"WHERE r.tipo = 'POLISOMNOGRAFIA' AND r.updated_at >= ? AND ap.case_id IN ({marcas}) "
        f"ORDER BY ap.case_id, u.display_name", [a.desde] + fichas)
    if not filas:
        print(f'No hay informes de polisomnografía desde {a.desde} en las fichas {", ".join(fichas)}.')
        return
    casos = {str(c['id']): c for c in consultar(
        f"SELECT id, data FROM cases WHERE id IN ({','.join('?' * len({str(x['case_id']) for x in filas}))})",
        sorted({str(x['case_id']) for x in filas}))}
    salida = []
    for x in filas:
        data = json.loads(x['data'])
        caso = json.loads(casos[str(x['case_id'])]['data'] or '{}')
        caso.setdefault('id', x['case_id'])
        s = Z.desde_caso(caso)
        S = Z.noche(s['sueno'], data.get('estudio') or 'psg')
        R = revisar(S, data, x['cita'])
        salida.append((x, R, S))

    print(f"| Ficha | Alumno | Estudio | Regla | IAH auto | IAH alumno | IAH correcto | Bien | Tipo mal | Sobran | "
          f"Se le pasaron | Gravedad (elegida / correcta) | Observaciones |")
    print('|' + '---|' * 13)
    for x, R, S in salida:
        print(f"| {x['case_id']} | {x['alumno']} | {R['estudio'].upper()} | {R['regla']} % | {f(R['iah_auto'])} | "
              f"{f(R['iah_alumno'])} | {f(R['iah_ideal'])} | {len(R['bien'])} | {len(R['mal'])} | "
              f"{len(R['sobra'])} | {len(R['perdidos'])} | {R['gravedad'] or '—'} / {R['grav_verdad']} | "
              f"{observaciones(R)} |")
    if a.detalle:
        for x, R, S in salida:
            print(f"\n### {x['alumno']} · ficha {x['case_id']} (cita {x['cita']}, informe {x['id']})")
            print(f"  {R['n']} eventos ({R['tocados']} tocados por el alumno). "
                  f"Tipo equivocado: {resumen_errores(R) or 'ninguno'}. "
                  f"RERA sin puntuar: {len(R['rera_perdidos'])}.")
            r, i = R['r_alumno'], R['r_ideal']
            print(f"  Suyo / correcto · supino {f(r['IAH supino'])}/{f(i['IAH supino'])}, izq. "
                  f"{f(r['IAH izquierda'])}/{f(i['IAH izquierda'])}, der. {f(r['IAH derecha'])}/{f(i['IAH derecha'])}"
                  f" · REM {f(r.get('IAH REM'))}/{f(i.get('IAH REM'))}, NREM {f(r.get('IAH NREM'))}/"
                  f"{f(i.get('IAH NREM'))} · IDR {f(r['IDR'])}/{f(i['IDR'])}")
            for linea in detalle(R, S):
                print(linea)
    if a.csv:
        with open(a.csv, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['ficha', 'alumno', 'cita', 'informe', 'estudio', 'regla', 'iah_auto', 'iah_alumno',
                        'iah_correcto', 'bien', 'tipo_mal', 'sobran', 'se_le_pasaron', 'gravedad_elegida',
                        'gravedad_correcta', 'observaciones'])
            for x, R, S in salida:
                w.writerow([x['case_id'], x['alumno'], x['cita'], x['id'], R['estudio'], R['regla'],
                            f(R['iah_auto']), f(R['iah_alumno']), f(R['iah_ideal']), len(R['bien']), len(R['mal']),
                            len(R['sobra']), len(R['perdidos']), R['gravedad'], R['grav_verdad'], observaciones(R)])
        print(f'\nTabla guardada en {a.csv}')


if __name__ == '__main__':
    main()
