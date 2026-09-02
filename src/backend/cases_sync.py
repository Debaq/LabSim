"""Traduce entre cases.json (dict case_id -> caso) y la tabla cases del backend."""


def backend_state_to_cases(state: dict) -> dict:
    return {c["id"]: c["data"] for c in state.get("cases", [])}


def diff_and_push_cases(client, new_cases: dict, old_cases: dict) -> None:
    """Sube solo los casos nuevos o modificados (no hay borrado de casos hoy)."""
    for case_id, data in new_cases.items():
        if old_cases.get(case_id) != data:
            print(f"[cases_sync] push case_id={case_id!r}")
            result = client.upsert_case(str(case_id), data)
            print(f"[cases_sync] respuesta: {result!r}")
