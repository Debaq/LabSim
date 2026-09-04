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
    cancelada: bool = False


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
            cancelada=bool(appt.get("cancelada")),
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

    return {"agenda_1": agenda}


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
        "cancelada": row.cancelada,
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

    for key in old_agenda:
        if key not in new_agenda:
            client.delete_appointment(int(key))
