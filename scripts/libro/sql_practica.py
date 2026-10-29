"""Un .sql por capítulo para cargar la práctica libre (ver docs/roadmap_practica_libro.md).

    python3 -I scripts/libro/sql_practica.py CARPETA PRIMER_ID_LIBRE

CARPETA tiene catalogo_tomo2.json; deja ahí libro_capNN.sql e ids_libro.json, que se
cargan con consola.py script. Se puede volver a correr: no duplica nada.
"""
import json, pathlib, sys
S = pathlib.Path(sys.argv[1]); LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
# Tomo II por defecto; el Tomo I (H, B) con su catálogo como tercer argumento
cat = json.load(open(S / (sys.argv[3] if len(sys.argv) > 3 else 'catalogo_tomo2.json')))
LABSIM = {'audiosupra', 'logoaudiometria', 'impedancia', 'abr', 'teoae', 'dpoae', 'vemp', 'ecochg', 'cortical'}
# Examen -> como se nombra en el procedimiento, en este orden
# (el Tomo I nombra distinto las suyas: audiograma, timpanograma, reflejos, acumetria)
PROC = [('acumetria', 'Acumetría'), ('audiosupra', 'Audiometría'), ('audiograma', 'Audiometría'),
        ('logoaudiometria', 'Audiometría'), ('impedancia', 'Impedanciometría'),
        ('timpanograma', 'Impedanciometría'), ('reflejos', 'Impedanciometría'),
        ('teoae', 'EOA'), ('dpoae', 'EOA'), ('abr', 'PEATC'), ('ecochg', 'ECochG'), ('cortical', 'Corticales'),
        ('vemp', 'VEMP')]
RUT_NUEVO = {'cap12_esclerosis_multiple': '18087953', 'cap24_gentamicina': '12518779',
             'cap17_rubeola_congenita': '28268815', 'cap17_asfixia_perinatal': '28268816',
             'h10_lactante': '28267995'}
ADMIN = 1
q = lambda s: "'" + str(s).replace("'", "''") + "'"

# El libro no tiene figura de ASSR: los casos hechos para practicarlo lo dicen acá
CON_ASSR = {'h13_lactante', 'h13_nino_tea', 'cap28_no_colabora'}


def procedimiento(figs, clave=''):
    if clave in CON_ASSR:
        return procedimiento(figs) + ' + ASSR'
    return _procedimiento(figs)


def _procedimiento(figs):
    vistos = []
    for f, nombre in PROC:
        if f in figs and nombre not in vistos:
            vistos.append(nombre)
    return ' + '.join(vistos) or 'Otoscopía + Acumetría'

def comentario(clave, cap, pedido):
    lados = [f"{o} {pedido['cuadro'][o]}" + (f" {pedido.get('grado', {}).get(o)}" if pedido.get('grado', {}).get(o) else '')
             for o in ('OD', 'OI') if pedido['cuadro'].get(o, 'normal') != 'normal']
    return f"Libro, {cap['cap'] if isinstance(cap['cap'], str) else 'cap. ' + str(cap['cap'])} ({cap['titulo']}), {clave}: " + ('; '.join(lados) or 'normal')

# Los números ya cargados no se mueven: si no, sumar un caso corre a todos
# los que vienen después y las carpetas apuntarían a otra ficha.
previos = S / 'ids_libro.json'
ids = json.load(open(previos)) if previos.exists() else {}
siguiente = max([int(sys.argv[2]) - 1, *map(int, ids.values())]) + 1
resumen = []
# Capítulos vestibulares (nistagmo, vHIT, calórica, maniobras) y nasales:
# LabSim no los simula. El 20 (VEMP) sí va. En los demás entra todo paciente,
# aunque no traiga figura de examen: la otitis externa (1.3) se practica con
# otoscopía y acumetría.
FUERA = {21, 22, 23, 24, 25, 26, 27, 31, 32, 35, 36, 37, 38}
def es_tomo1(cap):
    return isinstance(cap['cap'], str)   # 'H3', 'B1'; el Tomo II es un número

for cap in cat:
    if cap['cap'] in FUERA:
        continue
    # El número del caso en el libro (caso 7.4 -> 4)
    pacientes = [dict(p, n=n) for n, p in enumerate(cap['pacientes'], 1)]
    if not pacientes:
        continue
    carpeta = f"{cap['cap']} · {cap['titulo']}" if es_tomo1(cap) else f"Cap. {cap['cap']} · {cap['titulo']}"
    # El Tomo I va antes que el II, como en el libro: H1 -> -99 ... antes que Cap. 1
    orden_carpeta = -100 + int(cap['cap'][1:]) if es_tomo1(cap) else cap['cap']
    archivo = f"libro_{cap['cap'][0]}{int(cap['cap'][1:]):02d}.sql" if es_tomo1(cap) else f"libro_cap{cap['cap']:02d}.sql"
    sql = [f"INSERT INTO case_folders (name, created_by) SELECT 'Libro', {ADMIN} WHERE NOT EXISTS (SELECT 1 FROM case_folders WHERE name = 'Libro' COLLATE NOCASE);"]
    filas = []
    for orden, p in enumerate(pacientes, 1):
        if p['origen'].startswith('demo:'):
            case_id = p['origen'].split(':')[1]
            sql.append(f"UPDATE cases SET archived_at = NULL, folder_id = (SELECT id FROM case_folders WHERE name = 'Libro' COLLATE NOCASE) WHERE id = {q(case_id)};")
        else:
            gen = json.load(open(LIBRO / 'material/casos/generados' / f"{p['clave']}.json"))
            data, pedido = gen['data'], gen['pedido']
            if p['clave'] not in ids:
                ids[p['clave']] = str(siguiente)
                siguiente += 1
            case_id = ids[p['clave']]
            snap = dict(data['paciente_snapshot'])
            if p['clave'] in RUT_NUEVO:
                snap['rut'] = RUT_NUEVO[p['clave']]
            snap['procedimiento'] = procedimiento(p['figuras'], p['clave'])
            data['paciente_snapshot'] = snap
            data['id'] = int(case_id)
            sql.append(
                "INSERT INTO patients (rut, nombre, apellido, fecha_nac, historia_clinica, comentario_docente) VALUES "
                f"({q(snap['rut'])}, {q(snap['nombre'])}, {q(snap['apellido'])}, {q(snap['fecha_nac'])}, "
                f"{q(data.get('historia_clinica', ''))}, {q(comentario(p['clave'], cap, pedido))}) "
                "ON CONFLICT(rut) WHERE rut <> '' DO NOTHING;")
            sql.append(
                "INSERT OR IGNORE INTO cases (id, data, updated_at, patient_id, created_at, created_by, updated_by, folder_id) VALUES "
                f"({q(case_id)}, {q(json.dumps(data, ensure_ascii=False))}, CURRENT_TIMESTAMP, "
                f"(SELECT id FROM patients WHERE rut = {q(snap['rut'])}), CURRENT_TIMESTAMP, {ADMIN}, {ADMIN}, "
                "(SELECT id FROM case_folders WHERE name = 'Libro' COLLATE NOCASE));")
        filas.append((case_id, p['clave'], procedimiento(p['figuras'], p['clave']), p['n']))
    sql.append(f"INSERT INTO practice_folders (nombre, orden, created_by) SELECT {q(carpeta)}, {orden_carpeta}, {ADMIN} "
               f"WHERE NOT EXISTS (SELECT 1 FROM practice_folders WHERE nombre = {q(carpeta)} AND active = 1);")
    for case_id, clave, proc, orden in filas:
        sql.append(
            "INSERT INTO practice_items (folder_id, case_id, procedimiento, show_study_sheet, orden, created_by) VALUES "
            f"((SELECT id FROM practice_folders WHERE nombre = {q(carpeta)} AND active = 1), {q(case_id)}, {q(proc)}, 1, {orden}, {ADMIN}) "
            "ON CONFLICT(folder_id, case_id) DO UPDATE SET orden = excluded.orden, "
            "procedimiento = excluded.procedimiento, active = 1;")
    (S / archivo).write_text('\n'.join(sql) + '\n', encoding='utf-8')
    resumen.append((cap['cap'], carpeta, [(f"{c}:{cap['cap']}.{n}", k.split('_', 1)[1]) for c, k, _, n in filas]))
json.dump(ids, open(S / 'ids_libro.json', 'w'), indent=1)
for cap, carpeta, f in resumen:
    print(f"{carpeta[:42]:42} " + ', '.join(f"{c}:{k}" for c, k in f))
print('fichas nuevas:', len(ids), 'ids', min(map(int, ids.values())), '-', max(map(int, ids.values())))
