"""Estilo común de todas las figuras del libro.

Un solo lugar para colores, grosores y tipografía: cambiar algo acá cambia
todas las figuras al rehacerlas. Los colores de oído siguen la convención
clínica (OD rojo, OI azul) que usa también la app.
"""

# Tinta (texto y ejes) y papel
TINTA = '#1d1d1f'        # títulos
TINTA_2 = '#55555b'      # rótulos
TENUE = '#8a8a90'        # ejes y números
MUY_TENUE = '#b0b0b5'    # rótulos secundarios
GRILLA = '#e7e5e0'
GRILLA_FUERTE = '#cfccc5'
PAPEL = '#ffffff'
LAVADO = '#f4f2ee'       # zona de referencia (normalidad)

# Oídos
OD = '#c62f3a'
OI = '#2c5cb0'
COLOR_LADO = {'OD': OD, 'OI': OI}
# Campo libre (S y A): el sonido llega a los dos oídos, así que no es rojo ni
# azul. Verde, como en el laboratorio.
CAMPO_LIBRE = '#2e8540'
NOMBRE_LADO = {'OD': 'Oído derecho', 'OI': 'Oído izquierdo'}

# Tipografía (la misma del manual: docs/manual/fuentes)
FUENTE = "'Plus Jakarta Sans', sans-serif"
T_TITULO = 10
T_ROTULO = 8.5
T_EJE = 8
T_CHICO = 7

# Trazos
LINEA = 1.6              # dato principal
LINEA_FINA = 0.8         # dato secundario (subpromedios, réplicas)
OPACIDAD_SECUNDARIA = 0.28
