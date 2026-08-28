"""
Traduce entre el formato legado de la agenda (dict de listas posicionales,
ver lib/helpers.Shedule / entry_* helpers) y las tablas appointments/
attendances del backend. Funciones puras -- sin red, sin Qt -- para poder
testearlas sin levantar la app.

Fila legada (índices): [fecha, hora, rut, nombre, apellido, fecha_nac,
procedimiento, case_id, {username: {estado, nota, hora_real}}, nota_admin,
"cancelada"|""]
"""

ESTADOS_EMPUJABLES = ("atendiendo", "atendido", "no_show")


def _get(row, idx, default=""):
    if row is None or len(row) <= idx:
        return default
    valor = row[idx]
    return default if valor is None else valor


def backend_state_to_shedule(state: dict, own_user_id: int, own_username: str) -> dict:
    """Arma {"agenda_1": {key: row}} a partir de la respuesta de get_full_state()."""
    id_to_username = {own_user_id: own_username}
    for student in state.get("students", []):
        id_to_username[student["id"]] = student["username"]

    agenda = {}
    for appt in state.get("appointments", []):
        key = str(appt["id"])
        agenda[key] = [
            appt.get("fecha") or "",
            appt.get("hora") or "",
            appt.get("rut") or "",
            appt.get("nombre") or "",
            appt.get("apellido") or "",
            appt.get("fecha_nac") or "",
            appt.get("procedimiento") or "",
            appt.get("case_id") or "",
            {},
            appt.get("nota_admin") or "",
            "cancelada" if appt.get("cancelada") else "",
        ]

    for att in state.get("attendances", []):
        row = agenda.get(str(att["appointment_id"]))
        if row is None:
            continue
        username = id_to_username.get(att["student_id"])
        if username is None:
            continue
        row[8][username] = {
            "estado": att.get("estado"),
            "nota": att.get("nota") or "",
            "hora_real": att.get("hora_real") or "",
        }

    return {"agenda_1": agenda}


def _appointment_fields(row):
    return {
        "fecha": _get(row, 0),
        "hora": _get(row, 1),
        "rut": _get(row, 2),
        "nombre": _get(row, 3),
        "apellido": _get(row, 4),
        "fecha_nac": _get(row, 5),
        "procedimiento": _get(row, 6),
        "case_id": _get(row, 7) or None,
        "nota_admin": _get(row, 9),
        "cancelada": _get(row, 10) == "cancelada",
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

        atencion_nueva = _get(row, 8, {}) or {}
        atencion_vieja = _get(old_row, 8, {}) or {}
        propia_nueva = atencion_nueva.get(own_username)
        propia_vieja = atencion_vieja.get(own_username)
        if propia_nueva is not None and propia_nueva != propia_vieja:
            estado = propia_nueva.get("estado")
            if estado in ESTADOS_EMPUJABLES:
                client.post_attendance_action(appointment_id, estado, nota=propia_nueva.get("nota", ""))

    for key in old_agenda:
        if key not in new_agenda:
            client.delete_appointment(int(key))
