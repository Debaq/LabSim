"""
Cliente REST de labsim_backend.

Todas las llamadas llevan timeout: si el hosting compartido no responde,
la app no se cuelga esperando -- se propaga requests.RequestException y
quien llame decide (reintentar, avisar "sin conexión", etc.).
"""
import json
from pathlib import Path

import requests

DEFAULT_TIMEOUT = 10


class BackendClient:
    def __init__(self, base_url: str, session_file: str | Path):
        self._base_url = base_url.rstrip("/")
        self._session_file = Path(session_file)
        self.token: str | None = None
        self.user: dict | None = None
        self._load_session()

    # -- sesión local -----------------------------------------------------

    def _load_session(self) -> None:
        if not self._session_file.exists():
            return
        try:
            data = json.loads(self._session_file.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        self.token = data.get("token")
        self.user = data.get("user")

    def _save_session(self) -> None:
        self._session_file.parent.mkdir(parents=True, exist_ok=True)
        self._session_file.write_text(
            json.dumps({"token": self.token, "user": self.user}, ensure_ascii=False), "utf-8"
        )

    def logout(self) -> None:
        self.token = None
        self.user = None
        if self._session_file.exists():
            self._session_file.unlink()

    def is_logged_in(self) -> bool:
        return self.token is not None

    # -- requests -----------------------------------------------------------

    def _headers(self) -> dict:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = requests.get(
            f"{self._base_url}{path}", params=params, headers=self._headers(), timeout=DEFAULT_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()

    def _get_bytes(self, path: str, params: dict | None = None) -> bytes | None:
        """Como _get(), pero para un endpoint que devuelve la imagen cruda
        (no JSON) -- ver patient_photo.php. None = sin foto (404), que acá
        no es un error sino el caso normal de un paciente sin foto subida."""
        resp = requests.get(
            f"{self._base_url}{path}", params=params, headers=self._headers(), timeout=DEFAULT_TIMEOUT
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.content

    def _post(self, path: str, data: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
        resp = requests.post(
            f"{self._base_url}{path}", json=data, headers=self._headers(), timeout=timeout
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            # El backend manda el motivo real en el body ({"error": "..."} --
            # ver Response::error en labsim_backend) -- sin esto, quien llame
            # solo ve "502 Server Error: Bad Gateway for url: ..." genérico,
            # que no dice si fue el LLM, la config o la red.
            try:
                detail = resp.json().get("error")
            except ValueError:
                detail = None
            raise requests.HTTPError(detail or str(exc), response=resp) from exc
        return resp.json()

    # -- endpoints ------------------------------------------------------

    def pair_exchange(self, code: str) -> dict:
        """Cambia el código mostrado tras el login LTI por un token de sesión."""
        result = self._post("/api/pair_exchange.php", {"code": code})
        self.token = result["token"]
        self.user = result["user"]
        self._save_session()
        return result

    def login_admin(self, username: str, password: str) -> dict:
        result = self._post("/api/admin_login.php", {"username": username, "password": password})
        self.token = result["token"]
        self.user = result["user"]
        self._save_session()
        return result

    def get_sync(self, since: str) -> dict:
        return self._get("/api/sync.php", {"since": since})

    def get_admin_dump(self) -> dict:
        return self._get("/api/admin_dump.php")

    def get_full_state(self) -> dict:
        """
        Pull completo de casos/agenda/atenciones. admin_dump trae además la
        lista de alumnos (id->username), que hace falta para armar el
        historial cruzado; para un alumno no hace falta (su propio id/user
        ya se conoce), así que basta un sync 'desde el principio'.
        """
        if self.user and self.user.get("role") == "admin":
            return self.get_admin_dump()
        return self.get_sync("1970-01-01 00:00:00")

    def upsert_case(self, case_id: str, data: dict) -> dict:
        return self._post("/api/case_upsert.php", {"id": case_id, "data": data})

    def upsert_appointment(self, appointment_id: int | None, **fields) -> dict:
        body = dict(fields)
        if appointment_id is not None:
            body["id"] = appointment_id
        return self._post("/api/appointment_upsert.php", body)

    def delete_appointment(self, appointment_id: int) -> dict:
        return self._post("/api/appointment_delete.php", {"id": appointment_id})

    def post_attendance_action(self, appointment_id: int, action: str, nota: str | None = None) -> dict:
        body = {"id": appointment_id, "action": action}
        if nota is not None:
            body["nota"] = nota
        return self._post("/api/attendance_action.php", body)

    def llm_chat(
        self, case_id: str, nombre: str, edad: int, procedimiento: str,
        history: list[dict], message: str, appointment_id: int | None = None,
    ) -> dict:
        """Turno de chat con el paciente simulado por LLM (ver LlmChat.php).

        Timeout más largo que el resto de endpoints: LlmChat.php espera hasta
        30s por la respuesta del LLM (CURLOPT_TIMEOUT) -- con el timeout por
        defecto (10s) el cliente se rendía antes que el propio servidor.

        appointment_id: si se manda, el backend guarda el turno (mensaje +
        respuesta) en llm_chat_logs contra esa cita/alumno para poder
        revisarlo después. None = no guardar (usado por "Atender (prueba)").
        """
        body = {
            "case_id": case_id,
            "nombre": nombre,
            "edad": edad,
            "procedimiento": procedimiento,
            "history": history,
            "message": message,
        }
        if appointment_id is not None:
            body["appointment_id"] = appointment_id
        return self._post("/api/llm_chat.php", body, timeout=35)

    def get_inbox(self) -> dict:
        """Bandeja de entrada del usuario logueado (ver inbox.php): avisos
        automáticos sobre el trato a pacientes + mensajes que un docente
        mandó a mano."""
        return self._get("/api/inbox.php")

    def mark_inbox_read(self, message_id: int) -> dict:
        return self._post("/api/inbox.php", {"action": "mark_read", "id": message_id})

    def get_patient_avatar(self, case_id: str) -> bytes | None:
        """Avatar circular del paciente (PNG, ver PatientPhoto::avatarPath en
        labsim_backend). None si el paciente no tiene foto subida."""
        return self._get_bytes("/api/patient_photo.php", {"case_id": case_id, "type": "avatar"})

    def get_otoscopia_photo(self, case_id: str, side: str, fase: int = 0) -> bytes | None:
        """Imagen de otoscopia (JPEG, ver OtoscopiaPhoto::path en
        labsim_backend) de un oído/fase puntual. None si no hay imagen
        subida para ese oído/fase."""
        return self._get_bytes("/api/otoscopia_photo.php", {"case_id": case_id, "side": side, "fase": fase})

    def post_logs_batch(self, entries: list[dict]) -> dict:
        return self._post("/api/logs_batch.php", {"entries": entries})
