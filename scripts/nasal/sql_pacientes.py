"""SQL de los pacientes nasales del libro (caps. 35 a 37) con su nariz o su
pulmón, para la demo interna (docs/roadmap_nasal.md, F3b y F6).

    python3 -I scripts/nasal/sql_pacientes.py SALIDA.sql

Cada caso es el que armó LabSim para el libro (libro-orl,
material/casos/generados/<clave>.json) más su bloque NASAL: el mismo cuadro
y la misma semilla de RinoSim con que se hicieron sus figuras
(libro-orl/material/ilustraciones/hacer_cap3{5,6}_rinosim.sh), así la nariz
del paciente es la del libro. Los del cap. 37 llevan en cambio su bloque
ESPIRO: la FVC, el FEV1 y el PEF de sus informes en el libro
(libro-orl/material/ilustraciones/hacer_cap37.py, ASMA y ESTEN).

Los del cap. 38 llevan su bloque SUENO: el perfil del libro, la misma noche
simulada de libro-orl/material/ilustraciones/hacer_cap38.py (F7).

Tres llevan además olfatometría o prick (F5), con lo que cuenta su historia:
Rocío (olfato disminuido tras un cuadro viral) trae los puntajes del informe
de ejemplo de H28; Sofía y Óscar (pruebas cutáneas "según relata") traen la
hoja de ejemplo de H29 ajustada a lo que relatan. Esos bloques también van
como UPDATE: las fichas ya estaban en producción.

Van a la carpeta de fichas "Libro · nariz (demo)" y NO a la práctica libre:
los equipos nasales solo los ve el admin. Los números de ficha se anotan en
scripts/libro/ids_libro.json, como los de sql_practica.py, para que no se
pisen. Se puede volver a correr: no duplica nada.
"""
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'src'))
from nasal import espirometria, modelo, olfatometria, prick, sueno  # noqa: E402

LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
IDS = RAIZ / 'scripts/libro/ids_libro.json'
CARPETA = 'Libro · nariz (demo)'
ADMIN = 1
PROCEDIMIENTO = 'Rinomanometría anterior y rinometría acústica'
PROCEDIMIENTO_ESPIRO = 'Espirometría con prueba broncodilatadora'

# clave del caso -> (cuadro de RinoSim, semilla), los de sus figuras.
NARICES = {
    'cap35_desviacion': ('desviacion_derecha', None),
    'cap35_valvula': ('colapso_valvular', None),
    'cap35_discordancia': ('normal', None),
    'cap36_alergica': ('cornetes', None),
    'cap36_medicamentosa': ('cornetes', 1),
    'cap36_mixta': ('mixta', None),
}

# clave del caso -> bloque ESPIRO. La estenosis del libro es la curva normal
# (FVC 3,25, PEF 7,4, p 1,5: su FEV1 es 2,71) recortada por los topes; no
# responde al broncodilatador (sin bd).
PULMONES = {
    'cap37_asma': {'talla': 176, 'peso': 74, 'pre': {'fvc': 4.90, 'fev1': 3.20, 'pef': 7.4},
                   'bd': {'fvc': 5.10, 'fev1': 3.80, 'pef': 8.8}, 'tope_e': None, 'tope_i': None,
                   'colaboracion': 'buena'},
    'cap37_estenosis': {'talla': 160, 'peso': 68, 'pre': {'fvc': 3.25, 'fev1': 2.71, 'pef': 7.4},
                        'tope_e': 3.2, 'tope_i': 3.0, 'colaboracion': 'buena'},
}

# clave del caso -> bloque OLFATO (H28, informe de ejemplo: T 4,5, D 10, I 9).
OLFATOS = {
    'cap35_discordancia': {'lados': {l: {'T': 4.5, 'D': 10, 'I': 9} for l in ('D', 'I')},
                           'conducta': 'buena', 'preparacion': 'ok'},
}

# clave del caso -> bloque PRICK (H29, hoja de ejemplo), con lo que relata
# cada uno y su antihistamínico "cuando hay síntomas" suspendido a tiempo.
PIELES = {
    'cap36_alergica': {'histamina': 6, 'dermografismo': 0,
                       'alergenos': {'dpte': 8, 'dfar': 6, 'perro': 2, 'pastos': 5},
                       'farmaco': {'clave': 'loratadina', 'horas': 240}},
    'cap37_asma': {'histamina': 6, 'dermografismo': 0,
                   'alergenos': {'dpte': 7, 'dfar': 6, 'gato': 5},
                   'farmaco': {'clave': 'cetirizina', 'horas': 200}},
}
# clave del caso -> bloque SUENO (cap. 38) y su procedimiento.
SUENOS = {
    'cap38_roncador': ({'perfil': 'roncador'}, 'Poligrafía respiratoria'),
    'cap38_moderado': ({'perfil': 'moderado'}, 'Poligrafía respiratoria'),
    'cap38_grave': ({'perfil': 'grave'}, 'Polisomnografía'),
    'cap38_dudosa': ({'perfil': 'dudosa'}, 'Polisomnografía (la poligrafía previa no alcanzó)'),
}
OTROS = {'cap35_discordancia': ('OLFATO', 'olfatometría'), 'cap36_alergica': ('PRICK', 'prick test'),
         'cap37_asma': ('PRICK', 'prick test')}


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def main(salida):
    ids = json.loads(IDS.read_text(encoding='utf-8'))
    siguiente = max(map(int, ids.values())) + 1
    sql = [f"INSERT INTO case_folders (name, created_by) SELECT {q(CARPETA)}, {ADMIN} "
           f"WHERE NOT EXISTS (SELECT 1 FROM case_folders WHERE name = {q(CARPETA)} COLLATE NOCASE);"]
    for clave in list(NARICES) + list(PULMONES) + list(SUENOS):
        if clave not in ids:
            ids[clave] = str(siguiente)
            siguiente += 1
        case_id = ids[clave]
        gen = json.loads((LIBRO / 'material/casos/generados' / f'{clave}.json').read_text(encoding='utf-8'))
        data = gen['data']
        snap = dict(data['paciente_snapshot'])
        if clave in NARICES:
            cuadro, semilla = NARICES[clave]
            p = modelo.paciente(cuadro, semilla)
            data['NASAL'] = {k: p[k] for k in ('nombre', 'cuadro', 'semilla', 'lados', 'ciclo', 'perforacion')
                             if k in p}
            snap['procedimiento'] = PROCEDIMIENTO
            que = f"nariz de RinoSim {cuadro}{'' if semilla is None else f' (semilla {semilla})'}"
        elif clave in SUENOS:
            bloque, proc = SUENOS[clave]
            data['SUENO'] = sueno.normaliza(bloque)
            snap['procedimiento'] = proc
            que = f"noche del libro, perfil {bloque['perfil']}"
        else:
            data['ESPIRO'] = espirometria.normaliza(PULMONES[clave])
            snap['procedimiento'] = PROCEDIMIENTO_ESPIRO
            que = 'espirometría del informe del libro'
            cuadro, semilla = 'espiro', None
        extra = None
        if clave in OLFATOS:
            extra = ('OLFATO', olfatometria.normaliza(OLFATOS[clave]))
        elif clave in PIELES:
            extra = ('PRICK', prick.normaliza(PIELES[clave]))
        if extra:
            data[extra[0]] = extra[1]
            snap['procedimiento'] += ' y ' + OTROS[clave][1]
            que += f' + {OTROS[clave][1]}'
        data['id'] = int(case_id)
        data['paciente_snapshot'] = snap
        comentario = f"Libro, cap. {clave[3:5]}, {clave}: {que}. Demo interna."
        sql.append(
            "INSERT INTO patients (rut, nombre, apellido, fecha_nac, historia_clinica, comentario_docente) VALUES "
            f"({q(snap['rut'])}, {q(snap['nombre'])}, {q(snap['apellido'])}, {q(snap['fecha_nac'])}, "
            f"{q(data.get('historia_clinica', ''))}, {q(comentario)}) "
            "ON CONFLICT(rut) WHERE rut <> '' DO NOTHING;")
        sql.append(
            "INSERT OR IGNORE INTO cases (id, data, updated_at, patient_id, created_at, created_by, updated_by, folder_id) VALUES "
            f"({q(case_id)}, {q(json.dumps(data, ensure_ascii=False))}, CURRENT_TIMESTAMP, "
            f"(SELECT id FROM patients WHERE rut = {q(snap['rut'])}), CURRENT_TIMESTAMP, {ADMIN}, {ADMIN}, "
            f"(SELECT id FROM case_folders WHERE name = {q(CARPETA)} COLLATE NOCASE));")
        if extra:
            sql.append(
                f"UPDATE cases SET data = json_set(json_set(data, '$.{extra[0]}', json({q(json.dumps(extra[1]))})), "
                f"'$.paciente_snapshot.procedimiento', {q(snap['procedimiento'])}), updated_at = CURRENT_TIMESTAMP "
                f"WHERE id = {q(case_id)};")
        print(f"{case_id:>4}  {clave:22} {snap['nombre']} {snap['apellido']} (RUT {snap['rut']})  "
              f"{que}")
    pathlib.Path(salida).write_text('\n'.join(sql) + '\n', encoding='utf-8')
    IDS.write_text(json.dumps(ids, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1])
