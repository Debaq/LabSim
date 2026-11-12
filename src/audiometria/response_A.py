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
        # (género, número) de la voz del paciente; la pone
        # ResponseAudiometry.set_case según el caso (h_audio.voz_del_paciente).
        self.voz = ("feme", 1)

    def set_fowler_data(self, thr_od, thr_oi, cuts, diplacusia=False):
        """Configura el motor de Fowler/ABLB (audiometria.Fowler.Fowler) con los
        umbrales aereos del caso, el patrón de reclutamiento y si el caso
        marca diploacusia (los tonos de un oído y otro suenan distintos en
        forma: lo dice cuando se le pregunta, no cambia la sonoridad)."""
        self.fowler_engine = FowlerEngine()
        self.fowler_engine.set_th(thr_od, thr_oi)
        self.fowler_engine.set_cut(*cuts)
        self.fowler_engine.diplacusia = diplacusia

    def fowler_q(self, n, data_audio):
        if self.fowler_engine is None:
            # aun no se ha activado "dos_pitos" para setear los datos del Fowler
            return
        output = data_audio['audio']['output']
        if n == 3:
            # "¿Los dos sonidos eran diferentes en forma?", en cualquier nivel
            # (al terminar ya no suena nada: data_audio es lo último que
            # oyó). La diploacusia de esa frecuencia; si no oyó los dos
            # tonos, no tiene cómo compararlos.
            a = data_audio['audio']
            oyo = output[0] != output[1] and self.fowler_engine.oye_los_dos(
                a['int'][output.index(0)], a['int'][output.index(1)])
            if not oyo:
                self.create_voice_('nose')
            else:
                self.create_voice_('si' if self.fowler_engine.diplacusia else 'no')
            return
        if output[0] == output[1]:
            # ambos canales apuntan al mismo oido, no se puede comparar
            return

        int_od = data_audio['audio']['int'][output.index(0)]
        int_oi = data_audio['audio']['int'][output.index(1)]
        equals, side, _state = self.fowler_engine.evaluate(int_od, int_oi)

        if n == 1:
            # "¿Los escucha al mismo volumen?": solo sonoridad. La
            # diploacusia no la cambia (se pregunta aparte, n == 3).
            self.create_voice_('si' if equals else 'no')
        elif side is not None:
            sides = ["elderecho", "elizquierdo"]
            self.create_voice_(sides[side])

    def media_change(self, sender):
        state = self.sender().playbackState()
        if str(state) == 'PlaybackState.StoppedState':
            self.sender().setPosition(0)

    def create_voice_(self, response_text):
        # lo que dice el paciente (molesta, sí, el derecho...) al registro;
        # ResponseAudiometry le pasa el _log del audiómetro
        log = getattr(self, "log", None)
        if log is not None:
            log("audio_paciente_dice", frase=response_text)
        voice_ldl = create_voice(response_text, *self.voz)
        self.channel_0.setSource(voice_ldl)
        self.channel_0.play()
