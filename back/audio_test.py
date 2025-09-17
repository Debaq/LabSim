# test_audio_gui.py
# Pequeña GUI con PySide6 para probar audio_proc.py
# Requisitos: pip install PySide6 numpy sounddevice (opcional si usas ese backend)
from __future__ import annotations
import sys
import threading
from dataclasses import dataclass
from typing import Optional

import numpy as np  # noqa: F401 (requerido por audio_proc internamente)
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QComboBox, QDoubleSpinBox,
    QSpinBox, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox, QMessageBox
)

# Importa la librería que te pasé antes
from audio_proc import AudioEngine, AUDIO_FREQS

# -----------------------
# Pequeño "runner" seguro
# -----------------------
@dataclass
class PlaybackJob:
    """Describe el estímulo a reproducir."""
    stim_type: str                 # "Tone", "Tone Pulsatile", "Tone FM", "White", "Pink", "Speech", "NBN"
    freq: float
    duration: float
    level_dbfs: float
    pulsatile_hz: Optional[float] = None
    duty_cycle: float = 0.5
    fm_dev: float = 0.0
    fm_rate: float = 5.0
    nbn_bandwidth_hz: float = 160.0


class AudioWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Procedimental – Demo (PySide6)")
        self.setMinimumWidth(520)

        # ---------- Backend ----------
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["qt", "sounddevice"])  # por defecto usaremos "qt"

        self.sr_spin = QSpinBox()
        self.sr_spin.setRange(8000, 192000)
        self.sr_spin.setSingleStep(1000)
        self.sr_spin.setValue(48000)

        self.block_spin = QSpinBox()
        self.block_spin.setRange(64, 8192)
        self.block_spin.setSingleStep(64)
        self.block_spin.setValue(1024)

        # ---------- Estímulo ----------
        self.stim_combo = QComboBox()
        self.stim_combo.addItems([
            "Tone (continuous)",
            "Tone (pulsatile)",
            "Tone (FM)",
            "White noise",
            "Pink noise",
            "Speech-shaped noise",
            "Narrow-band noise (NBN)",
        ])
        self.stim_combo.currentIndexChanged.connect(self._update_visibility)

        self.freq_combo = QComboBox()
        for f in AUDIO_FREQS:
            self.freq_combo.addItem(f"{f} Hz", float(f))
        self.freq_combo.setCurrentIndex(AUDIO_FREQS.index(1000))

        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 60.0)
        self.duration_spin.setDecimals(2)
        self.duration_spin.setSingleStep(0.1)
        self.duration_spin.setValue(3.0)

        self.level_spin = QDoubleSpinBox()
        self.level_spin.setRange(-80.0, 0.0)
        self.level_spin.setDecimals(1)
        self.level_spin.setSingleStep(0.5)
        self.level_spin.setValue(-12.0)

        # Parámetros Pulsátil
        self.puls_hz = QDoubleSpinBox()
        self.puls_hz.setRange(0.1, 20.0)
        self.puls_hz.setValue(2.5)
        self.puls_dc = QDoubleSpinBox()
        self.puls_dc.setRange(0.05, 0.95)
        self.puls_dc.setSingleStep(0.05)
        self.puls_dc.setValue(0.5)

        # Parámetros FM
        self.fm_dev = QDoubleSpinBox()
        self.fm_dev.setRange(0.1, 500.0)
        self.fm_dev.setValue(10.0)
        self.fm_rate = QDoubleSpinBox()
        self.fm_rate.setRange(0.1, 20.0)
        self.fm_rate.setValue(5.0)

        # NBN bandwidth (1/3 octava aprox por defecto)
        self.nbn_bw = QDoubleSpinBox()
        self.nbn_bw.setRange(5.0, 10000.0)
        self.nbn_bw.setValue(self._one_third_oct_bw(1000.0))  # inicial

        self.freq_combo.currentIndexChanged.connect(self._sync_nbn_bw_default)

        # ---------- Botones ----------
        self.play_btn = QPushButton("▶ Reproducir")
        self.play_btn.clicked.connect(self.on_play)
        self.play_btn.setDefault(True)

        self.status_lbl = QLabel("Listo.")
        self.status_lbl.setWordWrap(True)

        # ---------- Layout ----------
        backend_box = QGroupBox("Backend de audio")
        f1 = QFormLayout()
        f1.addRow("Backend:", self.backend_combo)
        f1.addRow("Sample rate:", self.sr_spin)
        f1.addRow("Block size:", self.block_spin)
        backend_box.setLayout(f1)

        stim_box = QGroupBox("Parámetros del estímulo")
        f2 = QFormLayout()
        f2.addRow("Tipo:", self.stim_combo)
        f2.addRow("Frecuencia (si aplica):", self.freq_combo)
        f2.addRow("Duración (s):", self.duration_spin)
        f2.addRow("Nivel (dBFS):", self.level_spin)

        # Subgrupos
        puls_box = QGroupBox("Pulsátil")
        f_p = QFormLayout()
        f_p.addRow("Frecuencia pulso (Hz):", self.puls_hz)
        f_p.addRow("Duty cycle (0–1):", self.puls_dc)
        puls_box.setLayout(f_p)

        fm_box = QGroupBox("FM")
        f_fm = QFormLayout()
        f_fm.addRow("Desviación (Hz):", self.fm_dev)
        f_fm.addRow("Tasa (Hz):", self.fm_rate)
        fm_box.setLayout(f_fm)

        nbn_box = QGroupBox("NBN")
        f_nbn = QFormLayout()
        f_nbn.addRow("Ancho de banda (Hz):", self.nbn_bw)
        nbn_box.setLayout(f_nbn)

        vsub = QVBoxLayout()
        vsub.addWidget(puls_box)
        vsub.addWidget(fm_box)
        vsub.addWidget(nbn_box)

        row = QHBoxLayout()
        row.addLayout(f2, 1)
        row.addLayout(vsub, 1)
        stim_box.setLayout(row)

        bottom = QHBoxLayout()
        bottom.addWidget(self.play_btn)
        bottom.addWidget(self.status_lbl, 1)

        root = QVBoxLayout(self)
        root.addWidget(backend_box)
        root.addWidget(stim_box)
        root.addLayout(bottom)

        self._update_visibility()
        self._play_thread: Optional[threading.Thread] = None

    # ---------------------------
    # Helpers de UI / comportamiento
    # ---------------------------
    def _current_freq(self) -> float:
        return float(self.freq_combo.currentData())

    def _one_third_oct_bw(self, center_hz: float) -> float:
        # BW ≈ f0*(2^(1/6) - 2^(-1/6))  (aprox FWHM 1/3 de octava)
        return float(center_hz * ((2 ** (1/6)) - (2 ** (-1/6))))

    @Slot()
    def _sync_nbn_bw_default(self):
        # Al cambiar la frecuencia, si el usuario no tocó el BW, poner 1/3 octava para esa f
        self.nbn_bw.setValue(self._one_third_oct_bw(self._current_freq()))

    @Slot()
    def _update_visibility(self):
        t = self.stim_combo.currentText()
        # Mostrar/ocultar subgrupos
        needs_freq = ("Tone" in t) or ("Narrow-band" in t)
        self.freq_combo.setEnabled(needs_freq)

        # Subpaneles
        self.findChild(QGroupBox, "Pulsátil")
        # más simple: según el tipo
        self._set_group_visible("Pulsátil", "pulsatile" in t.lower())
        self._set_group_visible("FM", t.endswith("(FM)"))
        self._set_group_visible("NBN", "Narrow-band" in t)

    def _set_group_visible(self, title: str, visible: bool):
        for gb in self.findChildren(QGroupBox):
            if gb.title() == title:
                gb.setVisible(visible)

    def _build_job(self) -> PlaybackJob:
        t = self.stim_combo.currentText()
        job = PlaybackJob(
            stim_type=t,
            freq=self._current_freq(),
            duration=float(self.duration_spin.value()),
            level_dbfs=float(self.level_spin.value()),
            pulsatile_hz=None,
            duty_cycle=float(self.puls_dc.value()),
            fm_dev=float(self.fm_dev.value()),
            fm_rate=float(self.fm_rate.value()),
            nbn_bandwidth_hz=float(self.nbn_bw.value()),
        )
        if "pulsatile" in t.lower():
            job.pulsatile_hz = float(self.puls_hz.value())
        return job

    # -------------
    # Reproducción
    # -------------
    @Slot()
    def on_play(self):
        if self._play_thread and self._play_thread.is_alive():
            QMessageBox.information(self, "Reproducción en curso", "Espera a que termine el estímulo actual.")
            return

        try:
            backend = self.backend_combo.currentText()
            sr = int(self.sr_spin.value())
            bs = int(self.block_spin.value())
            eng = AudioEngine(sample_rate=sr, backend=backend, block_size=bs)

            job = self._build_job()
            sig = self._make_signal(eng, job)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo preparar el estímulo:\n{e}")
            return

        self.play_btn.setEnabled(False)
        self.status_lbl.setText("Reproduciendo…")

        def run():
            try:
                eng.play(sig)
            except Exception as e:
                # En hilos no podemos abrir MessageBox; usamos una señal simple:
                print("Error en reproducción:", e, file=sys.stderr)
            finally:
                # Volver a habilitar UI en hilo principal
                self.play_btn.setEnabled(True)
                self.status_lbl.setText("Listo.")

        self._play_thread = threading.Thread(target=run, daemon=True)
        self._play_thread.start()

    def _make_signal(self, eng: AudioEngine, job: PlaybackJob):
        t = job.stim_type
        if t == "Tone (continuous)":
            return eng.pure_tone(freq=job.freq, duration=job.duration,
                                 level_dbfs=job.level_dbfs)
        elif t == "Tone (pulsatile)":
            if job.pulsatile_hz is None or job.pulsatile_hz <= 0:
                raise ValueError("Configura la frecuencia de pulso (>0).")
            return eng.pure_tone(freq=job.freq, duration=job.duration,
                                 level_dbfs=job.level_dbfs,
                                 pulsatile_hz=job.pulsatile_hz,
                                 duty_cycle=job.duty_cycle)
        elif t == "Tone (FM)":
            if job.fm_dev <= 0:
                raise ValueError("Configura la desviación FM (>0).")
            return eng.pure_tone(freq=job.freq, duration=job.duration,
                                 level_dbfs=job.level_dbfs,
                                 fm_dev=job.fm_dev, fm_rate=job.fm_rate)
        elif t == "White noise":
            return eng.white_noise(duration=job.duration, level_dbfs=job.level_dbfs)
        elif t == "Pink noise":
            return eng.pink_noise(duration=job.duration, level_dbfs=job.level_dbfs)
        elif t == "Speech-shaped noise":
            return eng.speech_noise(duration=job.duration, level_dbfs=job.level_dbfs)
        elif t == "Narrow-band noise (NBN)":
            return eng.nbn(center_hz=job.freq, bandwidth_hz=job.nbn_bandwidth_hz,
                           duration=job.duration, level_dbfs=job.level_dbfs)
        else:
            raise ValueError(f"Tipo de estímulo no soportado: {t}")


def main():
    app = QApplication(sys.argv)
    w = AudioWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
