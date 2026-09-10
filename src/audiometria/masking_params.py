# -*- coding: utf-8 -*-
"""Parametros de enmascaramiento, en un solo lugar.

Vive aparte de response.py y de logoaudiometry.py porque los usan los dos y
response.py ya importa (via response_A) a logoaudiometry: importarlo al
reves cerraria el ciclo.

Es tambien el lugar donde deberian aterrizar estos valores cuando se hagan
configurables por curso desde la plataforma (app_config / AppConfig.php, el
mismo camino que 'normative_data.abr'), en vez de estar repartidos por los
modulos que los consumen. Ver TODO.md.
"""

# Indices de stim_list (resources/json/config_audiometer.json):
# ["Tono","FM","Habla","Narrow Band Noise","Withe Noise","Speech Noise","Pink Noise"]
STIM_TONO = 0
STIM_FM = 1
STIM_HABLA = 2
STIM_NBN = 3
STIM_WN = 4
STIM_SN = 5
STIM_PN = 6

RUIDOS_ENMASCARANTES = (STIM_NBN, STIM_WN, STIM_SN, STIM_PN)

NOMBRE_RUIDO = {
    STIM_NBN: "Narrow Band Noise",
    STIM_WN: "Withe Noise",
    STIM_SN: "Speech Noise",
    STIM_PN: "Pink Noise",
}

# CE (coeficiente de enmascaramiento): cuantos dB de mas hay que subir,
# respecto del ruido que corresponde a la prueba, para lograr el mismo
# enmascaramiento con otro ruido.
#
# TONAL: lo que tapa un tono es la energia que cae dentro de su banda
# critica. El NBN la concentra ahi --su dial ya viene calibrado en dB EM, CE
# 0--; un ruido de espectro ancho reparte la energia y desperdicia la parte
# que queda afuera. El pink cae 3 dB/octava, asi que en graves se parece al
# NBN y en agudos al blanco: queda en el medio.
CE_TONAL = {
    STIM_NBN: 0,
    STIM_PN: 5,
    STIM_WN: 10,
    STIM_SN: 10,   # conformado al habla, cae en los agudos
}

# LOGO: al reves. El habla ocupa todo el espectro, asi que el ruido correcto
# es el conformado al habla (speech noise, CE 0). Una banda estrecha tapa una
# porcion chica del espectro del habla y deja pasar el resto: por eso el NBN
# es el peor de los cuatro, no el mejor.
CE_LOGO = {
    STIM_SN: 0,
    STIM_PN: 5,
    STIM_WN: 5,
    STIM_NBN: 20,
}

# OJO: las cifras son de arranque y falta confirmarlas con la docente (ver
# TODO.md). Lo que no es opinable es el orden: NBN < PN < WN/SN en tonal, y
# SN < PN/WN < NBN en logoaudiometria.


def ce_tonal(stim):
    """CE del ruido `stim` para la via tonal. 0 si no es un enmascarante."""
    return CE_TONAL.get(stim, 0)


def ce_logo(stim):
    """CE del ruido `stim` para logoaudiometria. Sin dato, se asume el ruido
    correcto (speech noise) para no penalizar a los casos viejos."""
    return CE_LOGO.get(stim, 0)


def es_ruido(stim):
    return stim in RUIDOS_ENMASCARANTES
