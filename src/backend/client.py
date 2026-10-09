"""
Cliente REST de labsim_backend.

Todas las llamadas llevan timeout: si el hosting compartido no responde,
la app no se cuelga esperando -- se propaga requests.RequestException y
quien llame decide (reintentar, avisar "sin conexión", etc.).
"""
import json
import time
from datetime import datetime
from pathlib import Path

import requests

from core import equipo

DEFAULT_TIMEOUT = 10
# Cuanto se le tolera al reloj de la maquina antes de avisar, en segundos.
# Dos minutos es latencia y deriva normal; mas que eso ya mueve una cita de
# hora y hace llegar tarde a alguien convencido de que llega a tiempo.
CLOCK_SKEW_TOLERANCE_S = 120


# Lo fija MainWindow: se llama (desde cualquier hilo) cuando el servidor deja
# de aceptar la sesión, con el motivo: "vencida" (401: pasó la duración de
# las sesiones o la revocaron, ver admin/tokens.php) o "bloqueada" (403 con
# codigo cuenta_bloqueada, ver Bloqueos.php). Vale para todas las
# instancias de BackendClient (cada módulo crea la suya).
al_perder_sesion = None


def _revisar_sesion(resp, *args, **kwargs):
    """Hook de requests: mira cada respuesta a una petición con token."""
    aviso = al_perder_sesion
    if aviso is None or not resp.request.headers.get("Authorization"):
        return
    motivo = None
    if resp.status_code == 401:
        motivo = "vencida"
    elif resp.status_code == 403:
        try:
            codigo = (resp.json() or {}).get("codigo")
        except (ValueError, AttributeError):
            codigo = None
        if codigo == "cuenta_bloqueada":
            motivo = "bloqueada"
    if motivo is not None:
        try:
            aviso(motivo)
        except Exception as exc:  # noqa: BLE001 -- el aviso no corta la petición
            print(f"backend: no se pudo avisar la sesión perdida: {exc}")


class BackendClient:
    def __init__(self, base_url: str, session_file: str | Path):
        self._base_url = base_url.rstrip("/")
        self._session_file = Path(session_file)
        self.token: str | None = None
        self.user: dict | None = None
        # Session en vez de requests.get/post sueltos: reusa la conexión TCP/TLS
        # entre llamadas -- sin esto, SyncThread (polling cada 15s, ver
        # sync_thread.py) repetía el handshake completo en cada ciclo.
        self._http = requests.Session()
        self._http.hooks["response"].append(_revisar_sesion)
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
        resp = self._http.get(
            f"{self._base_url}{path}", params=params, headers=self._headers(), timeout=DEFAULT_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()

    def _get_bytes(self, path: str, params: dict | None = None) -> bytes | None:
        """Como _get(), pero para un endpoint que devuelve la imagen cruda
        (no JSON) -- ver patient_photo.php. None = sin foto (404), que acá
        no es un error sino el caso normal de un paciente sin foto subida."""
        resp = self._http.get(
            f"{self._base_url}{path}", params=params, headers=self._headers(), timeout=DEFAULT_TIMEOUT
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.content

    def _raise_for_status_with_detail(self, resp: requests.Response) -> None:
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

    def _post(self, path: str, data: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
        resp = self._http.post(
            f"{self._base_url}{path}", json=data, headers=self._headers(), timeout=timeout
        )
        self._raise_for_status_with_detail(resp)
        return resp.json()

    # -- endpoints ------------------------------------------------------

    def pair_exchange(self, code: str) -> dict:
        """Cambia el código mostrado tras el login LTI por un token de sesión."""
        result = self._post("/api/pair_exchange.php", {"code": code, "equipo": equipo.identidad()})
        self.token = result["token"]
        self.user = result["user"]
        self._save_session()
        return result

    def login_admin(self, username: str, password: str) -> dict:
        result = self._post("/api/admin_login.php", {
            "username": username, "password": password, "equipo": equipo.identidad(),
        })
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

    def get_clock(self) -> dict:
        """Reloj del servidor, para comparar con el de esta máquina.

        Ver api/clock.php y src/Clock.php en el backend. El backend calcula
        y muestra todo en la zona de la institución, declarada en su código
        y no en el php.ini del hosting, así que este dato NO se usa para
        reinterpretar fechas: las horas de una cita son las del curso y no
        las del computador que las lee.

        Sirve para lo otro: darse cuenta de que el reloj de esta máquina
        está corrido. Un alumno con la hora mal puesta llega tarde
        convencido de que llega a tiempo.
        """
        return self._get("/api/clock.php")

    def clock_skew(self) -> dict | None:
        """Cuánto se aparta el reloj de esta máquina del del servidor.

        Devuelve {'segundos', 'zona_local', 'zona_servidor', 'en_hora'}, o
        None si no se pudo preguntar (sin conexión, sin sesión). El
        desfase se calcula contra el epoch UTC del servidor, que es lo
        único que no depende de zonas horarias.
        """
        try:
            reloj = self.get_clock()
        except Exception:
            return None
        epoch = reloj.get("epoch")
        if not epoch:
            return None
        desfase = time.time() - float(epoch)
        return {
            "segundos": round(desfase),
            "zona_local": str(datetime.now().astimezone().tzinfo or ""),
            "zona_servidor": reloj.get("zona"),
            # Dos minutos es latencia y deriva normal de reloj, no un
            # problema: el aviso tiene que salir cuando de verdad importa.
            "en_hora": abs(desfase) <= CLOCK_SKEW_TOLERANCE_S,
        }

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
        # Cerrar ('atendido') dispara la evaluación OIRS del lado del
        # servidor; con 10 s el cliente cortaba antes de la respuesta y
        # creía que no se había cerrado.
        timeout = 40 if action == "atendido" else DEFAULT_TIMEOUT
        return self._post("/api/attendance_action.php", body, timeout=timeout)

    def get_case_sala(self, case_id: str, nombre: str = "", edad: int = 0) -> dict:
        """Quiénes están en el box de un caso (ver case_sala.php). Se pide
        al abrir el chat, antes del primer mensaje: el alumno tiene que ver
        con quién viene el paciente al entrar, no enterarse después."""
        return self._get(
            "/api/case_sala.php", {"case_id": case_id, "nombre": nombre, "edad": edad}
        )

    def llm_chat(
        self, case_id: str, nombre: str, edad: int, procedimiento: str,
        history: list[dict], message: str, appointment_id: int | None = None,
    ) -> dict:
        """Turno de chat con el paciente y quienes lo acompañan (ver
        Sala.php y llm_chat.php). Devuelve `respuestas`: una entrada por
        cada persona que habló en el turno, con quién la dijo.

        A quién le habla el alumno no se manda como parámetro: va dicho en
        el propio mensaje ("mamita, ¿su hijo escucha bien?") y lo resuelve
        el modelo, que es quien puede leerlo.

        Timeout más largo que el resto de endpoints: LlmChat.php espera
        hasta 30s por la respuesta del LLM (CURLOPT_TIMEOUT) -- con el
        timeout por defecto (10s) el cliente se rendía antes que el propio
        servidor.

        appointment_id: si se manda, el backend guarda el turno (mensaje +
        cada intervención, con quién habló) en llm_chat_logs contra esa
        cita/alumno. None = no guardar (usado por "Atender (prueba)").
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

    def save_prefs(self, prefs: dict) -> dict:
        """Guarda las preferencias personales (atajos, mouse para zurdos) en
        la cuenta -- ver my_prefs.php. Devuelve las que quedaron guardadas."""
        return self._post("/api/my_prefs.php", {"prefs": prefs}).get("prefs", {})

    def get_inbox(self) -> dict:
        """Bandeja de entrada del usuario logueado (ver inbox.php): avisos
        automáticos sobre el trato a pacientes + mensajes que un docente
        mandó a mano."""
        return self._get("/api/inbox.php")

    def mark_inbox_read(self, message_id: int) -> dict:
        return self._post("/api/inbox.php", {"action": "mark_read", "id": message_id})

    def get_patient_avatar(self, case_id: str, persona: str = "") -> bytes | None:
        """Avatar circular de alguien de la sala del caso (PNG, ver
        PatientPhoto::avatarPath en labsim_backend). None si no tiene foto
        subida. persona vacío = el paciente, que conserva la clave
        histórica del caso; cada acompañante va con su id (ver Sala.php)."""
        return self._get_bytes(
            "/api/patient_photo.php", {"case_id": case_id, "type": "avatar", "persona": persona}
        )

    def get_otoscopia_photo(self, case_id: str, side: str, fase: int = 0) -> bytes | None:
        """Imagen de otoscopia (JPEG, ver OtoscopiaPhoto::path en
        labsim_backend) de un oído/fase puntual. None si no hay imagen
        subida para ese oído/fase."""
        return self._get_bytes("/api/otoscopia_photo.php", {"case_id": case_id, "side": side, "fase": fase})

    def send_ticket(self, descripcion: str, equipo_info: dict | None, detalle: dict,
                    log_gz: bytes | None, timeout: int = 60,
                    cierre_inesperado: bool = False, anonimo: bool = False) -> dict:
        """Reporte de problema (Configuración → Reportar un problema, ver
        core/soporte.py y ticket.php). Solo se llama después de que el
        usuario aceptó mandar esta información. Devuelve {id}.

        `cierre_inesperado` + `anonimo`: el que se ofrece al reabrir tras
        una caída, sin sesión (el servidor lo acepta solo en ese caso)."""
        form = {
            "descripcion": descripcion,
            "equipo": json.dumps(equipo_info or {}, ensure_ascii=False),
            "detalle": json.dumps(detalle, ensure_ascii=False, default=str),
            "acepta": "1",
        }
        if cierre_inesperado:
            form["cierre_inesperado"] = "1"
        files = {"log": ("labsim.log.gz", log_gz, "application/gzip")} if log_gz else None
        resp = self._http.post(f"{self._base_url}/api/ticket.php", data=form, files=files,
                               headers={} if anonimo else self._headers(), timeout=timeout)
        self._raise_for_status_with_detail(resp)
        return resp.json()

    def post_logs_batch(self, entries: list[dict]) -> dict:
        return self._post("/api/logs_batch.php", {"entries": entries})

    def get_my_attendances(self) -> dict:
        """Historial propio de pacientes atendidos, con stats de
        comportamiento por atención (ver my_attendances.php)."""
        return self._get("/api/my_attendances.php")

    def get_practica(self) -> list[dict]:
        """Pacientes de práctica deliberada de los cursos del alumno, con
        sus intentos y el que tenga abierto (ver api/practica.php)."""
        return self._get("/api/practica.php").get("items", [])

    def iniciar_practica(self, practice_id: int) -> dict:
        """Abre un intento: devuelve la cita (la que quedó abierta en ese
        paciente, o una nueva)."""
        return self._post("/api/practica.php", {"action": "iniciar", "id": practice_id})["appointment"]

    def get_ficha_estudio(self, appointment_id: int) -> bytes | None:
        """PDF de la ficha de estudio de un intento de práctica cerrado,
        si el docente la dejó disponible (ver api/practica_ficha.php)."""
        resp = self._http.get(
            f"{self._base_url}/api/practica_ficha.php", params={"appointment_id": appointment_id},
            headers=self._headers(), timeout=60,
        )
        self._raise_for_status_with_detail(resp)
        return resp.content

    def get_my_chat_history(self, appointment_id: int) -> dict:
        """Conversación con el paciente simulado de una atención propia,
        más los comentarios que el docente haya dejado (ver
        my_chat_history.php)."""
        return self._get("/api/my_chat_history.php", {"appointment_id": appointment_id})

    def get_patient_reports(self, appointment_id: int) -> list[dict]:
        """Sesiones de ABR/electrococleo propias con el mismo paciente de
        esa cita, sin la cita misma, con `data` completo (curvas y trazos)
        -- ver my_patient_reports.php."""
        return self._get("/api/my_patient_reports.php",
                         {"appointment_id": appointment_id}).get("reports", [])

    def get_my_report(self, appointment_id: int, tipos: list[str] | None = None) -> list[dict]:
        """Informes propios ya guardados en ESA cita (el más nuevo primero),
        para recuperarlos al retomar la atención -- ver my_report.php."""
        params = {"appointment_id": appointment_id}
        if tipos:
            params["tipos"] = ",".join(tipos)
        return self._get("/api/my_report.php", params).get("reports", [])

    def upload_report(
        self, appointment_id: int, tipo: str, data: dict, images: dict[str, str], timeout: int = 30,
        version_base: int | None = None,
    ) -> dict:
        """Sube (o rehace) el informe de un módulo "de examen" (ABR/EOA/VEMP/
        electrococleo) de una atención propia -- ver report_upload.php. El
        backend resuelve solo el attendance_id a partir de appointment_id +
        el usuario del token (no hace falta que el cliente lo conozca --
        vive puramente del lado del backend, ver schema.sql). `images`:
        {suffix: ruta} de JPEG ya exportados (suffixes: '0', '1', 'lat_int',
        todos opcionales -- solo se mandan los que existan).

        Se puede rehacer mientras la atención siga 'atendiendo'; una vez
        'atendido' el backend lo rechaza (409) -- responsabilidad de quien
        llama decidir si eso es un error real o no (ver AbrMainWindow).

        `version_base`: la versión del servidor sobre la que se armó (0 =
        ninguna conocida). Si allá hay otra, el servidor guarda aparte la
        que se pisa (report_versions). Devuelve {ok, report_id, version}."""
        opened = []
        try:
            files = {}
            for suffix, path in images.items():
                f = open(path, "rb")
                opened.append(f)
                files[f"image_{suffix}"] = (f"{suffix}.jpg", f, "image/jpeg")
            form = {
                "appointment_id": str(appointment_id),
                "tipo": tipo,
                "data": json.dumps(data, ensure_ascii=False),
            }
            if version_base is not None:
                form["version_base"] = str(int(version_base))
            resp = self._http.post(
                f"{self._base_url}/api/report_upload.php",
                data=form, files=files, headers=self._headers(), timeout=timeout,
            )
            self._raise_for_status_with_detail(resp)
            return resp.json()
        finally:
            for f in opened:
                f.close()
