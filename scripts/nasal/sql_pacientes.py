"""SQL de los pacientes nasales del libro (caps. 35 y 36) con su nariz, para
la demo interna (docs/roadmap_nasal.md, F3b).

    python3 -I scripts/nasal/sql_pacientes.py SALIDA.sql

Cada caso es el que armó LabSim para el libro (libro-orl,
material/casos/generados/<clave>.json) más su bloque NASAL: el mismo cuadro
y la misma semilla de RinoSim con que se hicieron sus figuras
(libro-orl/material/ilustraciones/hacer_cap3{5,6}_rinosim.sh), así la nariz
del paciente es la del libro.

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
from nasal import modelo  # noqa: E402

LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl'
IDS = RAIZ / 'scripts/libro/ids_libro.json'
CARPETA = 'Libro · nariz (demo)'
ADMIN = 1
PROCEDIMIENTO = 'Rinomanometría anterior y rinometría acústica'

# clave del caso -> (cuadro de RinoSim, semilla), los de sus figuras.
NARICES = {
    'cap35_desviacion': ('desviacion_derecha', None),
    'cap35_valvula': ('colapso_valvular', None),
    'cap35_discordancia': ('normal', None),
    'cap36_alergica': ('cornetes', None),
    'cap36_medicamentosa': ('cornetes', 1),
    'cap36_mixta': ('mixta', None),
}


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def main(salida):
    ids = json.loads(IDS.read_text(encoding='utf-8'))
    siguiente = max(map(int, ids.values())) + 1
    sql = [f"INSERT INTO case_folders (name, created_by) SELECT {q(CARPETA)}, {ADMIN} "
           f"WHERE NOT EXISTS (SELECT 1 FROM case_folders WHERE name = {q(CARPETA)} COLLATE NOCASE);"]
    for clave, (cuadro, semilla) in NARICES.items():
        if clave not in ids:
            ids[clave] = str(siguiente)
            siguiente += 1
        case_id = ids[clave]
        gen = json.loads((LIBRO / 'material/casos/generados' / f'{clave}.json').read_text(encoding='utf-8'))
        data = gen['data']
        p = modelo.paciente(cuadro, semilla)
        data['NASAL'] = {k: p[k] for k in ('nombre', 'cuadro', 'semilla', 'lados', 'ciclo', 'perforacion') if k in p}
        data['id'] = int(case_id)
        snap = dict(data['paciente_snapshot'])
        snap['procedimiento'] = PROCEDIMIENTO
        data['paciente_snapshot'] = snap
        comentario = (f"Libro, cap. {clave[3:5]}, {clave}: nariz de RinoSim "
                      f"{cuadro}{'' if semilla is None else f' (semilla {semilla})'}. Demo interna.")
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
        print(f"{case_id:>4}  {clave:22} {snap['nombre']} {snap['apellido']} (RUT {snap['rut']})  "
              f"nariz: {cuadro}{'' if semilla is None else f'/{semilla}'}")
    pathlib.Path(salida).write_text('\n'.join(sql) + '\n', encoding='utf-8')
    IDS.write_text(json.dumps(ids, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1])
