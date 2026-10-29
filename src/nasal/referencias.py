"""Las cifras de referencia que RinoSim muestra, cada una con su fuente.

Regla: un número que se muestre como "normal" o "de referencia" tiene que
venir de la bibliografía que ya citan H26 y H27 del libro, y decir de cuál.
Lo que no tiene fuente se muestra como "orden de magnitud del modelo",
nunca como norma.
"""

# Resistencia unilateral a 150 Pa. Es el valor de trabajo del libro (H26,
# paso 7: "0,4 Pa/(cm³/s) o menos"), tomado del protocolo del curso; el
# propio libro aclara que depende de la población y del equipo.
REFERENCIA_UNILATERAL_150 = {
    'valor': 0.4,
    'texto': 'R unilateral a 150 Pa ≤ 0,4 Pa/(cm³/s)',
    'fuente': 'Valor de trabajo del libro (H26, paso 7). No es una norma poblacional.',
}

# Ren L, Zhang L, Duan S, Zhang W, Zhang Y. Nasal airflow resistance measured
# by rhinomanometry in a healthy population of China. Int Forum Allergy
# Rhinol. 2018;8:1308-14. doi:10.1002/alr.22177. Cifras tal como las cita H26.
REN_2018 = {
    'n': 505,
    'unilateral150': {'media': 0.51, 'ic95': [0.09, 0.94]},
    'total150': {'media': 0.24, 'ic95': [0.11, 0.37]},
    'texto': 'Ren y cols. (2018), 505 adultos sanos de China, a 150 Pa: unilateral media 0,51 (IC 95 %: 0,09-0,94); total media 0,24 (0,11-0,37) Pa/(cm³/s).',
}

# Vogt K y cols. Four-phase rhinomanometry: a multicentric retrospective
# analysis of 36,563 clinical measurements. Eur Arch Otorhinolaryngol.
# 2016;273:1185-98. Cifras tal como las cita H26.
VOGT_2016 = {
    'no_alcanza150': [0.045, 0.086],
    'n': 20069,
    'ciclos_promediados': [3, 5],
    'texto': 'Vogt y cols. (2016): entre 4,5 y 8,6 % de 20.069 mediciones en reposo no alcanzó 150 Pa; los equipos promedian de 3 a 5 ciclos.',
}

# Hilberg O, Jackson AC, Swift DL, Pedersen OF. Acoustic rhinometry:
# evaluation of nasal cavity geometry by acoustic reflection. J Appl Physiol.
# 1989;66:295-303. Cifras tal como las cita H27.
HILBERG_1989 = {
    'cv_areas': 0.02,  # "menor de 2 %"
    'cv_rinomanometria': 0.15,
    'texto': 'Hilberg y cols. (1989): coeficiente de variación de las áreas por rinometría menor de 2 %, contra 15 % en rinomanometría.',
}

# Corey JP, Kemker BJ, Nelson R, Gungor A. Evaluation of the nasal cavity by
# acoustic rhinometry in normal and allergic subjects. Otolaryngol Head Neck
# Surg. 1997;117:22-8. Cifras tal como las cita H27.
COREY_1997 = {
    'cambio_sanos': 0.156,
    'cambio_alergicos': 0.246,
    'texto': 'Corey y cols. (1997): con fenilefrina, el área del mínimo cambió en promedio 15,6 % en sanos y 24,6 % en alérgicos: un cambio así puede ocurrir sin enfermedad.',
}

# Criterio del protocolo del libro (H27, paso 6): tres registros con MCA1 y MCA2 a 0,03 cm² o menos entre sí.
PROTOCOLO_REPETICION = {
    'valor': 0.03,
    'texto': 'Protocolo del libro (H27): tres registros con MCA1 y MCA2 a 0,03 cm² o menos entre sí.',
}

# Áreas y volúmenes de la rinometría acústica: H27 NO da cifras normales
# (dice que dependen de sexo, talla, grupo étnico y equipo, y que se compare
# con la tabla del servicio; Millqvist y Bende, 1998; Corey y cols., 1998).
# RinoSim no inventa una: muestra la fosa normal DEL MODELO, rotulada así.
RINOMETRIA_SIN_NORMA = 'Sin norma universal (H27): se compara con la tabla del servicio. La fila "normal del modelo" es un orden de magnitud del simulador, no una referencia.'
