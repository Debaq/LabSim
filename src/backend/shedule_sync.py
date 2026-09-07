"""
Traduce entre el formato de la agenda en memoria (dict de AgendaEntry, ver
lib/helpers.Shedule / entry_* helpers) y las tablas appointments/
attendances del backend. Funciones puras -- sin red, sin Qt -- para poder
testearlas sin levantar la app.
"""
from dataclasses import dataclass, field

ESTADOS_EMPUJABLES = ("atendiendo", "atendido", "no_show")


@dataclass
class AgendaEntry:
    """Una fila de la agenda (una cita). Todas las filas se construyen acá
    (backend_state_to_shedule) -- no hay agenda offline ni filas parciales
    de un formato anterior que sobrevivan entre sesiones."""
    fecha: str = ""
    hora: str = ""
    rut: str = ""
    nombre: str = ""
    apellido: str = ""
    fecha_nac: str = ""
    procedimiento: str = ""
    case_id: str = ""
    atencion: dict = field(default_factory=dict)  # {username: {estado, nota, hora_real}}
    nota_admin: str = ""
    # True = fila sintética de un caso que NO tiene ninguna cita en
    # appointments (paciente "sin agendar", ver _cases_sin_cita). Existe solo
    # para que el docente lo vea/pruebe desde la agenda: no tiene
    # appointment_id, así que nunca se empuja al backend (ver
    # diff_and_push_shedule) ni admite atenciones reales.
    sin_cita: bool = False


def backend_state_to_shedule(state: dict, own_user_id: int, own_username: str) -> dict:
    """Arma {"agenda_1": {key: AgendaEntry}} a partir de get_full_state()."""
    id_to_username = {own_user_id: own_username}
    for student in state.get("students", []):
        id_to_username[student["id"]] = student["username"]

    agenda = {}
    for appt in state.get("appointments", []):
        key = str(appt["id"])
        agenda[key] = AgendaEntry(
            fecha=appt.get("fecha") or "",
            hora=appt.get("hora") or "",
            rut=appt.get("rut") or "",
            nombre=appt.get("nombre") or "",
            apellido=appt.get("apellido") or "",
            fecha_nac=appt.get("fecha_nac") or "",
            procedimiento=appt.get("procedimiento") or "",
            case_id=appt.get("case_id") or "",
            nota_admin=appt.get("nota_admin") or "",
        )

    for att in state.get("attendances", []):
        row = agenda.get(str(att["appointment_id"]))
        if row is None:
            continue
        username = id_to_username.get(att["student_id"])
        if username is None:
            continue
        row.atencion[username] = {
            "estado": att.get("estado"),
            "nota": att.get("nota") or "",
            "hora_real": att.get("hora_real") or "",
        }

    agenda.update(_cases_sin_cita(state, agenda))

    return {"agenda_1": agenda}


def _cases_sin_cita(state: dict, agenda: dict) -> dict:
    """Filas sintéticas para los casos que no tienen ninguna cita.

    La agenda se arma de appointments, así que un caso creado en el panel y
    todavía no agendado no aparecía en ninguna parte del cliente (sí en
    admin/patients.php). El docente los necesita ver para probarlos, así que
    se agregan como filas "sin agendar", con la identidad del paciente que
    manda el backend en cases (paciente_*) o, si el caso quedó huérfano de
    una cita borrada, con el snapshot que guardó esa cita.

    La key es "case:<id>" (no un id de appointments) -- ver AgendaEntry.sin_cita.
    """
    con_cita = {row.case_id for row in agenda.values() if row.case_id}

    filas = {}
    for case in state.get("cases", []):
        case_id = str(case["id"])
        if case_id in con_cita:
            continue
        data = case.get("data")
        snapshot = data.get("paciente_snapshot") or {} if isinstance(data, dict) else {}
        filas[f"case:{case_id}"] = AgendaEntry(
            rut=case.get("paciente_rut") or snapshot.get("rut") or "",
            nombre=case.get("paciente_nombre") or snapshot.get("nombre") or "",
            apellido=case.get("paciente_apellido") or snapshot.get("apellido") or "",
            fecha_nac=case.get("paciente_fecha_nac") or snapshot.get("fecha_nac") or "",
            case_id=case_id,
            sin_cita=True,
        )
    return filas


def _appointment_fields(row: AgendaEntry):
    return {
        "fecha": row.fecha,
        "hora": row.hora,
        "rut": row.rut,
        "nombre": row.nombre,
        "apellido": row.apellido,
        "fecha_nac": row.fecha_nac,
        "procedimiento": row.procedimiento,
        "case_id": row.case_id or None,
        "nota_admin": row.nota_admin,
    }


def diff_and_push_shedule(client, new_shedule: dict, old_shedule: dict, own_username: str) -> None:
    """
    Compara new_shedule contra la última foto conocida del servidor
    (old_shedule) y empuja al backend solo lo que cambió: citas nuevas/
    editadas/eliminadas, y el progreso propio del alumno logeado sobre cada
    cita (nunca el de otros alumnos -- eso lo escribe cada uno con su propio
    token, esta vista solo lo lee vía sync).
    """
    new_agenda = new_shedule.get("agenda_1", {})
    old_agenda = old_shedule.get("agenda_1", {})

    for key, row in new_agenda.items():
        if row.sin_cita:
            continue  # caso sin cita: no hay appointment_id que actualizar
        old_row = old_agenda.get(key)
        fields = _appointment_fields(row)

        if old_row is None:
            print(f"[shedule_sync] push cita nueva key={key!r} fields={fields!r}")
            result = client.upsert_appointment(None, **fields)
            print(f"[shedule_sync] respuesta: {result!r}")
            appointment_id = result["appointment"]["id"]
        else:
            appointment_id = int(key)
            if fields != _appointment_fields(old_row):
                print(f"[shedule_sync] push cita editada id={appointment_id} fields={fields!r}")
                result = client.upsert_appointment(appointment_id, **fields)
                print(f"[shedule_sync] respuesta: {result!r}")

        atencion_nueva = row.atencion
        atencion_vieja = old_row.atencion if old_row is not None else {}
        propia_nueva = atencion_nueva.get(own_username)
        propia_vieja = atencion_vieja.get(own_username)
        if propia_nueva is not None and propia_nueva != propia_vieja:
            estado = propia_nueva.get("estado")
            if estado in ESTADOS_EMPUJABLES:
                client.post_attendance_action(appointment_id, estado, nota=propia_nueva.get("nota", ""))

    for key, old_row in old_agenda.items():
        if old_row.sin_cita:
            continue  # nunca existió como cita (p.ej. el caso recién se agendó)
        if key not in new_agenda:
            client.delete_appointment(int(key))
