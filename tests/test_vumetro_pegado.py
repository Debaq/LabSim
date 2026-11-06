"""El vúmetro del audiómetro no queda pegado sin estímulo (2026-11-06).

Al soltar el estímulo, Player.stop() deja el vúmetro en 0, pero un bloque de
audio que venía en camino (la señal llega encolada desde el hilo de audio)
lo volvía a subir y quedaba así: ya no llega ningún otro.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication([])

from audiometria.audio_player import Player  # noqa: E402


def test_un_bloque_que_llega_despues_de_parar_no_mueve_el_vumetro():
    player = Player(2)
    niveles = []
    player.level_changed.connect(lambda ch, v: niveles.append((ch, v)))
    player.stop(0)
    assert niveles == [(0, 0.0)]
    player._on_audio_buffer(0, object())   # el atrasado: ni siquiera se lee
    assert niveles == [(0, 0.0)], niveles


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
