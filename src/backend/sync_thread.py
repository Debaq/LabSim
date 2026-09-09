"""
Hilo de sincronización por polling.

Sin websockets (el hosting compartido no los garantiza): cada `interval_s`
pregunta al backend "qué cambió desde la última vez" y emite la diferencia.
Con ~14 clientes y un intervalo de 15s esto es liviano; si el admin edita la
agenda en otra terminal, el resto la ve reflejada en el próximo ciclo.
"""
import requests
from PySide6.QtCore import QThread, Signal


class SyncThread(QThread):
    sync_ok = Signal(dict)
    sync_failed = Signal(str)

    def __init__(self, client, interval_s: int = 15, since: str = "1970-01-01 00:00:00", parent=None):
        super().__init__(parent)
        self._client = client
        self._interval_s = interval_s
        self._since = since

    def run(self) -> None:
        while not self.isInterruptionRequested():
            self._poll_once()
            self._wait_interruptible(self._interval_s)

    def _poll_once(self) -> None:
        try:
            result = self._client.get_sync(self._since)
        except requests.RequestException as exc:
            self.sync_failed.emit(str(exc))
            return
        self._since = result.get("server_time", self._since)
        self.sync_ok.emit(result)

    def _wait_interruptible(self, seconds: float) -> None:
        elapsed = 0.0
        step = 0.5
        while elapsed < seconds and not self.isInterruptionRequested():
            self.msleep(int(step * 1000))
            elapsed += step

    def stop(self) -> None:
        self.requestInterruption()
        self.wait(2000)
