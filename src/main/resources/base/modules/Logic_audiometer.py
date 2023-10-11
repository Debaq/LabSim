from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QEvent
from lib.SoundCreate import SoundCreate

import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

json_path = os.path.join(current_dir, "Config_audiometer.json")

with open(json_path, encoding="utf-8") as archivo:
    config = json.load(archivo)

class Funccion(QWidget):
    def __init__(self, ui_file_path):
        super().__init__()
        loader = QUiLoader()
        file = QFile(ui_file_path)
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file, self)
        file.close()
        #se crea un Layout para agregar el widget
        central_layout = QVBoxLayout(self)
        central_layout.addWidget(self.ui)
        # Aquí puedes hacer tus modificaciones o extensiones
        self.ui.btn_stim_ch0.pressed.connect(self.stim)
        self.ui.btn_stim_ch0.released.connect(self.stim)
        self.ui.btn_stim_ch1.pressed.connect(self.stim)
        self.ui.btn_stim_ch1.released.connect(self.stim)

        self.ui.btn_freq_plus.clicked.connect(self.change_frecuency)
        self.ui.btn_freq_minus.clicked.connect(self.change_frecuency)

        self.ui.dial_ch0.valueChanged.connect(self.change_intensity)
        self.ui.dial_ch1.valueChanged.connect(self.change_intensity)

        self.step_intencity = 5
        self.prev_dial_values = [10, 10]

        self.configure_btn_step()
        self.configure_btn_trans_type()
        self.configure_btn_stim_type()
        self.configure_btn_output()
        self.configure_channels()

        self.space_pressed = False

    def configure_channels(self):
        self.ch0 = SoundCreate(duration=5, channel="rigth")  # Sonará solo en el canal izquierdo
        self.ch1 = SoundCreate(duration=5, channel="left")  # Sonará solo en el canal izquierdo


    def play(self,ch):
        player = getattr(self, ch)
        player.play(noise_type="tone")

    
    def stop(self,ch):
        self.player.stop_playback()


    def configure_btn_output(self):
        for ch in ["ch0","ch1"]:
            for _type in ["r","l","sim"]:
                btn = getattr(self.ui, f"btn_output_{_type}_{ch}")
                btn.clicked.connect(self.change_output)

    def configure_btn_stim_type(self):
        for ch in ["ch0","ch1"]:
            for _type in ["tone", "fm", "speech", "wn", "nbn", "pn", "sn"]:
                btn = getattr(self.ui, f"btn_stim_{_type}_{ch}")
                btn.clicked.connect(self.change_stim_type)

    def configure_btn_step(self):
        for i in [1, 3, 5]:
            btn = getattr(self.ui, f"btn_step_{i}")
            btn.clicked.connect(self.change_step)

    def configure_btn_trans_type(self):
        for ch in ["ch0", "ch1"]:
            for _type in ["aer","cl","ose"]:
                btn = getattr(self.ui, f"btn_trans_{_type}_{ch}")
                btn.clicked.connect(self.change_trans_type)


    def change_intensity(self, value):
        sender = self.sender()
        channel = 0 if sender.objectName() == "dial_ch0" else 1
        # Detectar dirección del giro
        if value > self.prev_dial_values[channel]:
            direction = "derecha"
        else:
            direction = "izquierda"
        # Actualizar el valor previo del dial
        self.prev_dial_values[channel] = value
        # Modificar la intensidad según la dirección
        current_intensity = self.get_intensity(channel)
        if direction == "derecha":
            new_intensity = current_intensity + self.step_intencity
            # Ajusta este valor según tus necesidades
        else:
            new_intensity = current_intensity - self.step_intencity
            # Ajusta este valor según tus necesidades
        # Asegurarse de que la nueva intensidad esté dentro del rango permitido
        type_range = "extend" if self.ui.btn_ext_range.isChecked() else "normal"
        min_int = config["Range_intencity"][type_range][0]
        max_int = config["Range_intencity"][type_range][1]
        new_intensity = max(min_int, min(max_int, new_intensity))
        # Establecer la nueva intensidad
        self.set_intensity(channel, new_intensity)


    def change_output(self):
        _,_,out,ch = self.sender().objectName().split("_")
        out_ = config["Output"][out]
        lbl = getattr(self.ui, f"lbl_output_{ch}")
        lbl.setText(out_[0])

    def change_stim_type(self):
        _,_,stim,ch = self.sender().objectName().split("_")
        stim_ = config["Stimulus"][stim]
        lbl = getattr(self.ui, f"lbl_stim_{ch}")
        lbl.setText(stim_[0])
        #debo hacer una variable para manejar el estado actual no en texto sino en su nombre corto

    def change_trans_type(self):
        _,_,trans,ch = self.sender().objectName().split("_")
        trans_ = config["Transducer"][trans]
        lbl = getattr(self.ui, f"lbl_trans_{ch}")
        lbl.setText(trans_[0])
        #debo hacer una variable para manejar el estado actual no en texto sino en su nombre corto

    def change_frecuency(self):        
        _,_,button = self.sender().objectName().split("_")
        current_frecuency = self.get_frecuency()
        index = config["Frecuency"].index(current_frecuency)
        if button == "plus":
            end = len(config["Frecuency"])
            new_index = index + 1
            if new_index >= end:
                new_index = 0 
            new_frecuency = config["Frecuency"][new_index]
        elif button == "minus":
            new_frecuency = config["Frecuency"][index-1]
        self.set_frecuency(new_frecuency)

    def stim(self):
        button = self.sender()
        print(button.objectName())
        if button.isDown():
            event = "pressed"
            self.get_frecuency()
        else:
            event = "released"

    def change_step(self):
        _,_,step = self.sender().objectName().split("_")
        self.step_intencity = int(step)
        text = f"Pasos : {step} dB "
        for i in [0, 1]:
            lbl_step = getattr(self.ui, f"lbl_step_ch{i}")
            lbl_step.setText(text)

    #def create_intensity_list(self):
    #    r = config["Range_intencity"][self.type_range_intencity]
    #    return range(*r, self.step_intencity)

    def get_intensity(self, side):
        lbl_name = f"lbl_int_ch{side}"
        lbl = self.ui.findChild(QLabel, lbl_name)
        intencity, _= lbl.text().split(" ", 1)
        return int(intencity)

    def set_intensity(self, side, value):
        lbl_name = f"lbl_int_ch{side}"
        lbl = self.ui.findChild(QLabel, lbl_name)
        text_value = f"{value} dB HL"
        lbl.setText(text_value)

    def get_frecuency(self):
        hz, _ = self.ui.lbl_freq.text().split(' ')
        return int(hz)

    def set_frecuency(self, hz):
        frecuency_text = f"{hz} Hz"
        self.ui.lbl_freq.setText(frecuency_text)




    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not self.space_pressed:
            self.space_pressed = True
            self.ui.btn_stim_ch0.pressed.emit()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.space_pressed = False
            self.ui.btn_stim_ch0.released.emit()
        super().keyReleaseEvent(event)

    def eventFilter(self, obj, event):
        # Desactiva el "key repeat" para la tecla <space>
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Space and event.isAutoRepeat():
            return True  # Ignora el evento
        return super().eventFilter(obj, event)
