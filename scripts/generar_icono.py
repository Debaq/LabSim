#!/usr/bin/env python3
"""Genera el ícono de LabSim: icons/Icon.ico (exe e instalador de Windows) y
resources/img/icono_app.png (ventana y barra de tareas, ver main.py).

Mismo diseño que el ícono original (círculo #5D1049 con "LabSim" en DejaVu
Sans), pero dibujado en cada tamaño que pide Windows en vez de un solo
228x228 que el sistema reescalaba: en 16-32 px "LabSim" no se lee y va
"LS". El texto queda adentro del círculo (en el original se salía).

    micromamba run -n labsim python scripts/generar_icono.py

Los archivos generados van al repo: el build no corre este script.
"""
import os

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MORADO = (93, 16, 73, 255)
BLANCO = (255, 255, 255, 255)
FUENTE = "/usr/share/fonts/TTF/DejaVuSans.ttf"
FUENTE_NEGRITA = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
TAMANOS_ICO = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
SOBREMUESTREO = 8
# Ancho máximo del texto respecto del diámetro: con esto las puntas de la
# "L" y la "m" quedan dentro del círculo.
ANCHO_TEXTO = 0.74


def dibujar(tamano: int) -> Image.Image:
    lado = tamano * SOBREMUESTREO
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, lado - 1, lado - 1), fill=MORADO)
    chico = tamano <= 32
    texto = "LS" if chico else "LabSim"
    ruta = FUENTE_NEGRITA if chico else FUENTE
    ancho_max = lado * (0.62 if chico else ANCHO_TEXTO)
    puntos = lado
    while puntos > 1:
        fuente = ImageFont.truetype(ruta, puntos)
        x0, y0, x1, y1 = d.textbbox((0, 0), texto, font=fuente)
        if x1 - x0 <= ancho_max:
            break
        puntos -= max(1, puntos // 50)
    d.text(((lado - (x1 - x0)) / 2 - x0, (lado - (y1 - y0)) / 2 - y0),
           texto, font=fuente, fill=BLANCO)
    return img.resize((tamano, tamano), Image.Resampling.LANCZOS)


def main():
    imagenes = [dibujar(t) for t in TAMANOS_ICO]
    ico = os.path.join(RAIZ, "icons", "Icon.ico")
    imagenes[-1].save(ico, format="ICO", sizes=[(t, t) for t in TAMANOS_ICO],
                      append_images=imagenes[:-1])
    png = os.path.join(RAIZ, "resources", "img", "icono_app.png")
    dibujar(512).save(png, optimize=True)
    print(f"{ico}: {', '.join(str(t) for t in TAMANOS_ICO)} px")
    print(f"{png}: 512 px")


if __name__ == "__main__":
    main()
