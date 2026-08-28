"""
Cola local de logs de acciones del alumno.

Reemplaza el approach anterior de "imprimir/streamear cada acción" (lo que
colgaba la app: cada evento esperaba una respuesta de red antes de seguir).
Ahora `LocalLogQueue.push()` solo escribe en un sqlite local -- siempre
rápido, nunca toca la red -- y `LogUploaderThread` sube lo acumulado en
lotes cada cierto tiempo, en un hilo aparte del hilo de la UI.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal


class LocalLogQueue:
    def __init__(self, db_path):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT
                )
                """
            )

    def push(self, action: str, payload: dict | None = None) -> None:
        """Encola un evento. Escritura local, no bloquea por red."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO pending_logs (ts, action, payload) VALUES (?, ?, ?)",
                (ts, action, json.dumps(payload, ensure_ascii=False) if payload is not None else None),
            )

    def pop_batch(self, limit: int = 200) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, ts, action, payload FROM pending_logs ORDER BY id LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"id": r[0], "ts": r[1], "action": r[2], "payload": json.loads(r[3]) if r[3] else None}
            for r in rows
        ]

    def delete_ids(self, ids: list[int]) -> None:
        if not ids:
            return
        with self._connect() as conn:
            conn.executemany("DELETE FROM pending_logs WHERE id = ?", [(i,) for i in ids])

    def pending_count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM pending_logs").fetchone()[0]


class LogUploaderThread(QThread):
    """
    Sube los logs acumulados en lotes (nunca streaming). Si el POST falla
    (sin internet, backend caído) los eventos quedan en la cola local y se
    reintentan en el siguiente ciclo -- no se pierden.
    """

    upload_failed = Signal(str)

    def __init__(self, queue: LocalLogQueue, client, interval_s: int = 20, batch_size: int = 200, parent=None):
        super().__init__(parent)
        self._queue = queue
        self._client = client
        self._interval_s = interval_s
        self._batch_size = batch_size

    def run(self) -> None:
        while not self.isInterruptionRequested():
            self._flush_once()
            self._wait_interruptible(self._interval_s)

    def _flush_once(self) -> None:
        batch = self._queue.pop_batch(self._batch_size)
        if not batch:
            return
        entries = [{"ts": e["ts"], "action": e["action"], "payload": e["payload"]} for e in batch]
        try:
            self._client.post_logs_batch(entries)
        except requests.RequestException as exc:
            self.upload_failed.emit(str(exc))
            return
        self._queue.delete_ids([e["id"] for e in batch])

    def _wait_interruptible(self, seconds: float) -> None:
        elapsed = 0.0
        step = 0.5
        while elapsed < seconds and not self.isInterruptionRequested():
            self.msleep(int(step * 1000))
            elapsed += step

    def stop(self) -> None:
        self.requestInterruption()
        self.wait(2000)
