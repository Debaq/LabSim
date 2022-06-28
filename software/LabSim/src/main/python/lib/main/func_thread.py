from PySide6.QtCore import QThread, Signal
import json
import time
from software.LabSim.src.main.python.lib.main.func_login import LoginConnect


def request(data):
    connect = LoginConnect()
    return connect.request_api(data)

class ReadThread(QThread):
    """Theard para leer los datos del API en modo online"""
    name = ""
    passw = ""
    data_signal = Signal(dict)

    def run(self):
        """
        run del thread
        se activa al invocar self.start()
        """
        while True:
            time.sleep(1)
            name = self.name
            passw = self.passw
            data = {'user': name, passw: passw, 'request': 'state'}
            request_data = json.loads(request(data))
            if isinstance(request_data, int):
                response = {"result": request_data}
            else:
                response = request_data
                response['result'] = 1
            self.data_signal.emit(response)