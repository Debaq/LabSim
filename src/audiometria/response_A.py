from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QWidget

from audiometria.h_audio import create_voice
from audiometria.Fowler import Fowler as FowlerEngine


class Response(QWidget):
    """Voz del paciente y preguntas del Fowler, para ResponseAudiometry.

    Lo que queda de la ruta vieja de respuestas: response.py la usa como
    `other_response` solo para hablar (create_voice_) y para el balance de
    sonoridad (set_fowler_data, fowler_q). Las respuestas a umbrales, SDT,
    LDL y Carhart que vivían acá eran código muerto --con el SDT viejo,
    distinto del de la ficha-- y se sacaron: las da response.py.
    """

    def __init__(self):
        super(Response, self).__init__()
        self.output_ch = QAudioOutput()
        self.channel_0 = QMediaPlayer()
        self.channel_0.mediaStatusChanged.connect(self.media_change)
        self.channel_0.setAudioOutput(self.output_ch)
        self.fowler_engine = None

    def set_fowler_data(self, thr_od, thr_oi, cuts, diplacusia=False):
        """Configura el motor de Fowler/ABLB (audiometria.Fowler.Fowler) con los
        umbrales aereos del caso, los 3 cortes de reclutamiento y si el caso
        marca diploacusia (el paciente igualado en sonoridad igual reporta
        que los tonos no son iguales "en forma"/tono)."""
        self.fowler_engine = FowlerEngine()
        self.fowler_engine.set_th(thr_od, thr_oi)
        self.fowler_engine.set_cut(*cuts)
        self.fowler_engine.diplacusia = diplacusia

    def fowler_q(self, n, data_audio):
        if self.fowler_engine is None:
            # aun no se ha activado "dos_pitos" para setear los datos del Fowler
            return
        output = data_audio['audio']['output']
        if output[0] == output[1]:
            # ambos canales apuntan al mismo oido, no se puede comparar
            return

        int_od = data_audio['audio']['int'][output.index(0)]
        int_oi = data_audio['audio']['int'][output.index(1)]
        equals, side, _state = self.fowler_engine.evaluate(int_od, int_oi)

        if n == 1:
            # Balance de sonoridad alcanzado (equals=True) no implica que el
            # paciente los reporte "iguales" si el caso marca diploacusia:
            # el paciente responde según si además son iguales en forma/tono.
            equals = equals and not self.fowler_engine.diplacusia
            self.create_voice_('si' if equals else 'no')
        elif side is not None:
            sides = ["elderecho", "elizquierdo"]
            self.create_voice_(sides[side])

    def media_change(self, sender):
        state = self.sender().playbackState()
        if str(state) == 'PlaybackState.StoppedState':
            self.sender().setPosition(0)

    def create_voice_(self, response_text):
        voice_ldl = create_voice(response_text, 'feme', 2)
        self.channel_0.setSource(voice_ldl)
        self.channel_0.play()
