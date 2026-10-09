"""
Hilo de sincronización por polling.

Sin websockets (el hosting compartido no los garantiza): cada `interval_s`
pregunta al backend "qué cambió desde la última vez" y avisa la diferencia.
Con ~14 clientes y un intervalo de 15s esto es liviano; si el admin edita la
agenda en otra terminal, el resto la ve reflejada en el próximo ciclo.

Es un hilo de Python (core.hilos.Ciclo), no un QThread: el resultado le
llega a la ventana por hilos.avisar, sin pasar un dict por una señal de Qt
cada 15 s (ver los cierres del 2026-10-09 en core/hilos.py).
"""
import requests

from core import hilos


class SyncThread(hilos.Ciclo):
    def __init__(self, client, interval_s: int = 15, since: str = "1970-01-01 00:00:00",
                 al_sincronizar=None, dueno=None):
        super().__init__(interval_s, "SyncThread")
        self._client = client
        self._since = since
        self._al_sincronizar = al_sincronizar
        self._dueno = dueno

    def paso(self) -> None:
        try:
            result = self._client.get_sync(self._since)
        except requests.RequestException:
            return   # silencioso: se reintenta en el próximo ciclo
        self._since = result.get("server_time", self._since)
        # El contador de la bandeja de entrada se consulta acá y no en el
        # hilo de la ventana (ver MainWindow._on_backend_sync).
        try:
            result["_inbox"] = self._client.get_inbox().get("items", [])
        except requests.RequestException:
            result["_inbox"] = None
        if self._al_sincronizar is not None and not self.isInterruptionRequested():
            hilos.avisar(self._al_sincronizar, result, dueno=self._dueno)
