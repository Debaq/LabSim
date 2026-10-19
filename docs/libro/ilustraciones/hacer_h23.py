#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H23 (acúfeno: impacto, modelos y terapias sonoras):

    h23-jastreboff.svg   modelo neurofisiológico de Jastreboff como diagrama de bloques
    h23-ganancia.svg     ganancia central tras la desaferentación (esquema cualitativo)
    h23-manejo.svg       flujo del manejo escalonado

SVG propios, no IA. Son esquemas: ninguna forma de curva ni posición es un dato.
El modelo de bloques sigue a Jastreboff (1990) y Jastreboff y Hazell (1993); la ganancia central,
a Eggermont y Roberts (2004) y Noreña (2011); el flujo de manejo, a Tunkel y cols. (2014),
Adams y cols. (2026) y NICE NG155 (2020)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h25 import Lienzo as _L, TINTA, TENUE, GRILLA, FUERTE, AVISO, RETRO, COCLEAR, punta  # noqa: E402

AZUL = '#2d5f9a'
SUAVE_R, SUAVE_C, SUAVE_A, SUAVE_G = '#e3f1ee', '#fbeadf', '#fbe3e4', '#f3f1ec'


class Lienzo(_L):
    def raw(self, s):
        self.out.append(s)

    def caja(self, x, y, w, h, titulo, sub=None, fill='#fff', stroke=TINTA, col=TINTA):
        self.rect(x, y, w, h, fill, stroke, 1.4, 8)
        if sub:
            self.t(x + w / 2, y + h / 2 - 3, titulo, 9.5, col, 'middle', 700)
            for k, s in enumerate(sub if isinstance(sub, list) else [sub]):
                self.t(x + w / 2, y + h / 2 + 11 + k * 11, s, 8, TENUE)
        else:
            self.t(x + w / 2, y + h / 2 + 3, titulo, 9.5, col, 'middle', 700)

    def flecha(self, x1, y1, x2, y2, color=TINTA, w=1.6, dash=None, marca='pf'):
        self.l(x1, y1, x2, y2, color, w, dash, f' marker-end="url(#{marca})"')


DEFS = punta('pf', TINTA) + punta('pr', AVISO) + punta('pv', RETRO) + punta('pc', COCLEAR)


def jastreboff():
    c = Lienzo(760, 412)
    c.t(14, 20, 'Modelo neurofisiológico del acúfeno (Jastreboff)', 10.5, TINTA, 'start', 700)
    # fuente
    c.caja(24, 150, 130, 80, 'Fuente', ['señal neuronal anómala', 'cóclea y vía auditiva'], SUAVE_G)
    c.caja(210, 150, 140, 80, 'Detección', ['centros subcorticales', 'la señal se registra'], SUAVE_C, COCLEAR, COCLEAR)
    c.caja(410, 150, 150, 80, 'Percepción', ['corteza auditiva', '"oigo un sonido"'], SUAVE_C, COCLEAR, COCLEAR)
    c.caja(210, 40, 140, 70, 'Sistema límbico', ['miedo, ansiedad, atención'], SUAVE_A, AVISO, AVISO)
    c.caja(410, 40, 150, 70, 'Sistema autónomo', ['alerta, insomnio, tensión'], SUAVE_A, AVISO, AVISO)
    c.caja(600, 150, 140, 80, 'Reacción', ['molestia, sufrimiento', 'el acúfeno "importa"'], SUAVE_A, AVISO, AVISO)
    c.flecha(154, 190, 208, 190)
    c.flecha(350, 190, 408, 190)
    c.flecha(560, 190, 598, 190)
    # a límbico y autónomo
    c.flecha(280, 148, 280, 112, AVISO, 1.6, None, 'pr')
    c.flecha(485, 148, 485, 112, AVISO, 1.6, None, 'pr')
    c.flecha(350, 75, 408, 75, AVISO, 1.6, None, 'pr')
    # retroalimentación: reacción vuelve a detección y percepción
    c.raw(f'<path d="M670,232 L670,268 L280,268 L280,232" fill="none" stroke="{AVISO}" stroke-width="1.6" '
          f'stroke-dasharray="5 4" marker-end="url(#pr)"/>')
    c.t(475, 284, 'refuerzo: cuanto más reacciona, más se detecta y más se percibe', 8.5, AVISO, 'middle', 700)
    # intervenciones
    c.rect(24, 318, 340, 84, SUAVE_R, RETRO, 1.2, 8)
    c.t(36, 336, 'Consejería (educación)', 9.5, RETRO, 'start', 700)
    c.t(36, 351, 'Actúa sobre la reacción: el acúfeno pasa de amenaza a', 8.3, TINTA, 'start')
    c.t(36, 363, 'estímulo neutro, y las conexiones con el límbico y el', 8.3, TINTA, 'start')
    c.t(36, 375, 'autónomo se debilitan (habituación de la reacción).', 8.3, TINTA, 'start')
    c.rect(396, 318, 340, 84, SUAVE_C, COCLEAR, 1.2, 8)
    c.t(408, 336, 'Terapia sonora (enriquecimiento)', 9.5, COCLEAR, 'start', 700)
    c.t(408, 351, 'Actúa sobre el contraste: un sonido de fondo baja la fuerza', 8.3, TINTA, 'start')
    c.t(408, 363, 'de la señal frente al ruido y facilita que el cerebro', 8.3, TINTA, 'start')
    c.t(408, 375, 'la deje de percibir (habituación de la percepción).', 8.3, TINTA, 'start')
    c.flecha(194, 316, 280, 232, RETRO, 1.4, '4 3', 'pv')
    c.flecha(566, 316, 480, 232, COCLEAR, 1.4, '4 3', 'pc')
    c.guardar('h23-jastreboff.svg', DEFS)


def ganancia():
    c = Lienzo(760, 345)
    c.t(14, 20, 'Ganancia central tras la desaferentación (esquema cualitativo)', 10.5, TINTA, 'start', 700)
    # panel izquierdo: audiograma
    x0, y0, w, h = 60, 52, 280, 200
    c.t(x0 + w / 2, 42, 'Lo que llega desde la cóclea', 9.5, TINTA, 'middle', 700)
    c.l(x0, y0 + h, x0 + w, y0 + h, TINTA, 1.3)
    c.l(x0, y0, x0, y0 + h, TINTA, 1.3)
    fr = ['250', '500', '1k', '2k', '4k', '8k']
    for i, f in enumerate(fr):
        x = x0 + 20 + i * (w - 40) / 5
        c.l(x, y0 + h, x, y0 + h + 4, TINTA, 1.2)
        c.t(x, y0 + h + 16, f, 8.3)
    c.t(x0 + w / 2, y0 + h + 32, 'frecuencia (Hz)', 9)
    c.t(x0 - 8, y0 + 8, 'más', 8, TENUE, 'end'); c.t(x0 - 8, y0 + 19, 'señal', 8, TENUE, 'end')
    c.t(x0 - 8, y0 + h - 4, 'menos', 8, TENUE, 'end')
    xs = [x0 + 20 + i * (w - 40) / 5 for i in range(6)]
    entrada = [0.80, 0.80, 0.78, 0.70, 0.42, 0.18]
    ys = [y0 + h - v * h for v in entrada]
    c.poli(list(zip(xs, ys)), AZUL, 2.6)
    c.raw(f'<rect x="{xs[4] - 14}" y="{y0}" width="{xs[5] - xs[4] + 28}" height="{h}" fill="{AVISO}" opacity=".08"/>')
    c.t(xs[4] + 20, y0 + 14, 'zona con pérdida', 8.3, AVISO, 'middle', 700)
    # flecha
    c.flecha(354, 150, 400, 150, TINTA, 2)
    # panel derecho: actividad central
    X0 = 440
    c.t(X0 + w / 2, 42, 'Lo que hace la vía auditiva central', 9.5, TINTA, 'middle', 700)
    c.l(X0, y0 + h, X0 + w, y0 + h, TINTA, 1.3)
    c.l(X0, y0, X0, y0 + h, TINTA, 1.3)
    xr = [X0 + 20 + i * (w - 40) / 5 for i in range(6)]
    for i, f in enumerate(fr):
        c.l(xr[i], y0 + h, xr[i], y0 + h + 4, TINTA, 1.2)
        c.t(xr[i], y0 + h + 16, f, 8.3)
    c.t(X0 + w / 2, y0 + h + 32, 'frecuencia (Hz)', 9)
    antes = [0.80, 0.80, 0.78, 0.70, 0.42, 0.18]
    # salida central: la ganancia sube más donde falta entrada, hasta recuperar o exceder el nivel previo
    gan = [1.0, 1.0, 1.02, 1.1, 1.75, 3.0]
    despues = [min(0.95, a * g) for a, g in zip(antes, gan)]
    c.poli([(x, y0 + h - v * h) for x, v in zip(xr, antes)], AZUL, 1.6, '5 4')
    c.poli([(x, y0 + h - v * h) for x, v in zip(xr, despues)], AVISO, 2.6)
    c.raw(f'<rect x="{xr[4] - 14}" y="{y0}" width="{xr[5] - xr[4] + 28}" height="{h}" fill="{AVISO}" opacity=".08"/>')
    c.t(X0 + w - 4, y0 + 14, 'actividad espontánea más alta', 8.3, AVISO, 'end', 700)
    c.t(X0 + w - 4, y0 + 26, 'y más sincronizada', 8.3, AVISO, 'end', 700)
    c.l(X0 + 14, y0 + h + 56, X0 + 40, y0 + h + 56, AZUL, 1.6, '5 4')
    c.t(X0 + 46, y0 + h + 59, 'antes de la pérdida', 8.3, TENUE, 'start')
    c.l(X0 + 170, y0 + h + 56, X0 + 196, y0 + h + 56, AVISO, 2.6)
    c.t(X0 + 202, y0 + h + 59, 'con ganancia aumentada', 8.3, TENUE, 'start')
    c.t(380, 334, 'Esquema: la forma de las curvas ilustra la idea, no son datos de un paciente.', 8, TENUE)
    c.guardar('h23-ganancia.svg', DEFS)


def manejo():
    c = Lienzo(760, 520)
    c.t(14, 20, 'Manejo escalonado del acúfeno persistente', 10.5, TINTA, 'start', 700)
    # fila 1: evaluación
    c.caja(260, 36, 240, 50, 'Evaluación inicial', ['anamnesis dirigida, audiometría, cuestionario'], SUAVE_G)
    c.caja(24, 36, 190, 50, 'Bandera roja', ['pulsátil, unilateral, súbito, ', 'focalidad, riesgo de autolesión'], SUAVE_A, AVISO, AVISO)
    c.flecha(258, 61, 216, 61, AVISO, 1.6, None, 'pr')
    c.t(24, 102, 'Derivación al médico', 8.5, AVISO, 'start', 700)
    # decisión
    c.caja(260, 112, 240, 44, '¿Le molesta?', None, SUAVE_G)
    c.flecha(380, 88, 380, 110)
    # no molesta
    c.caja(24, 190, 190, 60, 'No le molesta', ['información, tranquilidad,', 'control si cambia'], SUAVE_R, RETRO, RETRO)
    c.l(260, 134, 119, 134, TINTA, 1.6); c.flecha(119, 134, 119, 188)
    c.t(190, 128, 'no', 8.5, TENUE)
    # molesta
    c.flecha(380, 158, 380, 190)
    c.t(392, 176, 'sí', 8.5, TENUE, 'start')
    c.caja(260, 192, 240, 56, 'Peldaño 1: consejería', ['educación, desmitificar, plan', 'seguridad, sueño, sonido de fondo'], SUAVE_R, RETRO, RETRO)
    # peldaño 2
    c.caja(24, 286, 220, 66, 'Peldaño 2a: hay pérdida auditiva', ['audífonos (con o sin función', 'de sonido), según la pérdida'], SUAVE_C, COCLEAR, COCLEAR)
    c.caja(270, 286, 220, 66, 'Peldaño 2b: enriquecimiento', ['sonido ambiental o generador,', 'a un nivel que no tape'], SUAVE_C, COCLEAR, COCLEAR)
    c.caja(516, 286, 220, 66, 'Peldaño 2c: TRT', ['consejería estructurada +', 'terapia sonora, meses'], SUAVE_C, COCLEAR, COCLEAR)
    c.l(380, 250, 380, 268, TINTA, 1.6)
    c.l(134, 268, 626, 268, TINTA, 1.6)
    for x in (134, 380, 626):
        c.flecha(x, 268, x, 284)
    # peldaño 3
    c.caja(150, 392, 460, 52, 'Peldaño 3: TCC (derivación a psicología)', ['la intervención con mejor evidencia si el sufrimiento persiste'], SUAVE_A, AVISO, AVISO)
    c.l(380, 354, 380, 372, TINTA, 1.6, '4 3'); c.flecha(380, 372, 380, 390, TINTA, 1.6, '4 3')
    c.t(392, 376, 'si no basta', 8.3, TENUE, 'start')
    # seguimiento
    c.caja(150, 468, 460, 40, 'Seguimiento con el mismo cuestionario (THI o TFI)', None, SUAVE_G)
    c.flecha(380, 446, 380, 466)
    c.raw(f'<path d="M612,488 L740,488 L740,332 L738,332" fill="none" stroke="{TENUE}" stroke-width="1.3" stroke-dasharray="4 3"/>')
    c.t(676, 502, 'se ajusta el peldaño', 8, TENUE)
    c.guardar('h23-manejo.svg', DEFS)


if __name__ == '__main__':
    jastreboff()
    ganancia()
    manejo()
