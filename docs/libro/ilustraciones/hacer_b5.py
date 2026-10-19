#!/usr/bin/env python3
"""Ilustraciones del capítulo B5 (Salud pública y prevención en ORL). SVG propios, no IA.

    b5-niveles.svg        historia natural de la enfermedad y niveles de prevención (Leavell y Clark; Jamoulle)
    b5-determinantes.svg  determinantes sociales en capas (Dahlgren y Whitehead), con ejemplos de audición y nariz
    b5-gantt.svg          carta Gantt del proyecto de ejemplo (12 semanas)
"""
from hacer_b4 import Lienzo, TINTA, TENUE, GRILLA, FUERTE, COCLEAR, RETRO, AVISO, AZUL, VERDE, VIOLETA


def caja(c, x, y, w, h, texto, fill, stroke, size=9, color=TINTA, peso=400):
    c.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.2, r=6)
    lineas = texto.split('\n')
    y0 = y + h / 2 - (len(lineas) - 1) * size * 0.75 + size * 0.4
    for i, s in enumerate(lineas):
        c.t(x + w / 2, y0 + i * size * 1.5, s, size, color, peso=peso)


def niveles():
    c = Lienzo(760, 410)
    etapas = [('Susceptibilidad', 'oído sano,\nsin exposición'), ('Exposición', 'ruido, otitis,\nototóxicos'),
              ('Daño sin\nsíntomas', 'lesión coclear\nsubclínica'), ('Enfermedad\ncon síntomas', 'hipoacusia\nque se nota'),
              ('Secuela', 'discapacidad\ncomunicativa')]
    x0, w, sep = 22, 125, 15
    c.t(380, 22, 'Historia natural de la enfermedad (ejemplo: hipoacusia)', 11, TINTA, peso=700)
    for i, (t, d) in enumerate(etapas):
        x = x0 + i * (w + sep)
        caja(c, x, 40, w, 62, t, '#f6f1ea', FUERTE, 9.5, peso=700)
        c.t(x + w / 2, 122, d.split('\n')[0], 8, TENUE)
        c.t(x + w / 2, 134, d.split('\n')[1], 8, TENUE)
        if i < 4:
            c.l(x + w + 1, 71, x + w + sep - 1, 71, TENUE, 1.4, punta='tenue')
    cols = [(COCLEAR, 'Primaria', 'Antes de la enfermedad: evitar que aparezca', 'Protección auditiva, vacunas, control de otitis,\nlímites de volumen en audífonos personales', x0, 2 * w + sep),
            (AZUL, 'Secundaria', 'Detección precoz', 'Tamizaje neonatal,\naudiometría\nde vigilancia', x0 + 2 * (w + sep), w + 0),
            (RETRO, 'Terciaria', 'Limitar el daño y rehabilitar', 'Audífono, implante coclear,\nrehabilitación auditiva', x0 + 3 * (w + sep), 2 * w + sep)]
    for col, nom, que, ej, x, ww in cols:
        c.rect(x, 160, ww, 118, fill='#fff', stroke=col, sw=1.6, r=6)
        c.rect(x, 160, ww, 24, fill=col, stroke=col, sw=1, r=6)
        c.t(x + ww / 2, 177, nom, 10.5, '#fff', peso=700)
        ys = 200
        for ln in wrap(que, int(ww / 7.2)):
            c.t(x + ww / 2, ys, ln, 8.5, TINTA, peso=700); ys += 13
        ys += 4
        for ln in ej.split('\n'):
            for l2 in wrap(ln, int(ww / 6.4)):
                c.t(x + ww / 2, ys, l2, 8.2, TENUE); ys += 12
    # cuaternaria
    c.rect(x0, 300, 5 * w + 4 * sep, 76, fill='#faf3f3', stroke=AVISO, sw=1.6, r=6)
    c.rect(x0, 300, 5 * w + 4 * sep, 24, fill=AVISO, stroke=AVISO, sw=1, r=6)
    c.t(380, 317, 'Cuaternaria: en todas las etapas', 10.5, '#fff', peso=700)
    c.t(380, 343, 'Proteger a la persona del exceso de medicina: sobrediagnóstico, sobretratamiento y exámenes que no cambian la conducta.', 8.5, TINTA, peso=700)
    c.t(380, 360, 'Ejemplo: pedir una resonancia por un acúfeno simétrico, sin otros signos, que no cambia lo que se hará.', 8.2, TENUE)
    c.guardar('b5-niveles.svg')


def wrap(s, n):
    out, cur = [], ''
    for p in s.split():
        if len(cur) + len(p) + 1 > n and cur:
            out.append(cur); cur = p
        else:
            cur = (cur + ' ' + p).strip()
    return out + ([cur] if cur else [])


def determinantes():
    c = Lienzo(760, 380)
    caps = [('#efe6dc', 'Condiciones socioeconómicas, culturales y ambientales generales', 10, 10, 440, 360),
            ('#e7eef0', 'Condiciones de vida y de trabajo', 38, 50, 384, 300),
            ('#eef0e1', 'Redes sociales y comunitarias', 66, 90, 328, 240),
            ('#f4e4e2', 'Estilos de vida individuales', 94, 130, 272, 180)]
    for fill, t, x, y, w, h in caps:
        c.rect(x, y, w, h, fill=fill, stroke=FUERTE, sw=1.2, r=18)
        c.t(x + w / 2, y + 21, t, 8.8, TINTA, peso=700)
    c.rect(150, 198, 160, 66, fill='#fff', stroke=TINTA, sw=1.4, r=14)
    c.t(230, 225, 'Edad, sexo y', 9.2, TINTA, peso=700); c.t(230, 241, 'factores constitucionales', 9.2, TINTA, peso=700)
    # sub-etiquetas de las capas de condiciones de vida
    c.t(150, 72, 'educación · trabajo · vivienda · agua y saneamiento · servicios de salud', 7.6, TENUE, anchor='start') if False else None
    ejs = [('Condiciones generales', 'pobreza, políticas de ruido y de aire,\nfinanciamiento de audífonos', 10),
           ('Condiciones de vida y trabajo', 'ruido laboral, vivienda con humedad,\nacceso a especialista', 100),
           ('Redes sociales y comunitarias', 'familia que reconoce la sordera,\nclubes de adultos mayores', 190),
           ('Estilos de vida', 'volumen de los audífonos personales,\ntabaco, higiene nasal', 280),
           ('Constitución', 'edad, genética, sexo', 370)]
    for t, d, y in ejs:
        yb = 40 + (y - 10) * 0.72
        c.t(478, yb, t, 8.8, TINTA, anchor='start', peso=700)
        yy = yb + 14
        for ln in d.split('\n'):
            c.t(478, yy, ln, 8.2, TENUE, anchor='start'); yy += 12
    c.guardar('b5-determinantes.svg')


def gantt():
    c = Lienzo(760, 300)
    tareas = [('1. Diagnóstico y encuesta de base', 1, 2, COCLEAR), ('2. Permisos y coordinación con el colegio', 1, 2, COCLEAR),
              ('3. Capacitación de monitores', 3, 3, AZUL), ('4. Talleres con estudiantes (6 sesiones)', 4, 9, AZUL),
              ('5. Afiches y campaña en el recreo', 5, 10, VERDE), ('6. Medición intermedia (proceso)', 7, 7, VIOLETA),
              ('7. Encuesta final y análisis', 11, 12, RETRO), ('8. Informe y devolución al colegio', 12, 12, RETRO)]
    x0, y0, cw, rh = 258, 48, 38, 30
    c.t(380, 20, 'Carta Gantt de 12 semanas', 11, TINTA, peso=700)
    for k in range(12):
        c.t(x0 + k * cw + cw / 2, y0 - 8, f'S{k + 1}', 8.2, TENUE)
        c.l(x0 + k * cw, y0, x0 + k * cw, y0 + rh * len(tareas), GRILLA, 0.8)
    c.l(x0 + 12 * cw, y0, x0 + 12 * cw, y0 + rh * len(tareas), GRILLA, 0.8)
    for i, (t, a, b, col) in enumerate(tareas):
        y = y0 + i * rh
        c.l(18, y, x0 + 12 * cw, y, GRILLA, 0.8)
        c.t(22, y + rh / 2 + 3, t, 8.8, TINTA, anchor='start')
        c.rect(x0 + (a - 1) * cw + 2, y + 7, (b - a + 1) * cw - 4, rh - 14, fill=col, stroke=col, sw=1, r=4, op=0.85)
    c.l(18, y0 + rh * len(tareas), x0 + 12 * cw, y0 + rh * len(tareas), FUERTE, 1.2)
    c.guardar('b5-gantt.svg')


if __name__ == '__main__':
    niveles(); determinantes(); gantt()
