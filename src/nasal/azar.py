"""Azar con semilla: el mismo paciente y la misma medición cada vez que se
pide con la misma semilla, igual que en RinoSim (js/azar.js).

mulberry32 para los números y una mezcla FNV-1a de 32 bits para convertir
un texto ("desviacion_derecha/7") en semilla. No es criptográfico ni lo
necesita: solo tiene que ser estable entre máquinas y versiones, y dar
BIT A BIT lo mismo que el JS. Por eso los enteros de 32 bits se emulan con
máscaras (Math.imul, `| 0` y `>>> 0` de JS) y no se usa hash() de Python,
que cambia en cada proceso.
"""

import math

_M32 = 0xFFFFFFFF


def a_texto(x):
    """String(x) de JS para lo que llega como semilla o como minuto.

    Un float entero se escribe sin ".0" ("30" y no "30.0"): la semilla del
    azar es un texto y tiene que salir igual que en el JS.
    """
    if x is None:
        return 'null'
    if isinstance(x, bool):
        return 'true' if x else 'false'
    if isinstance(x, float):
        if math.isnan(x):
            return 'NaN'
        if math.isinf(x):
            return 'Infinity' if x > 0 else '-Infinity'
        if x == int(x) and abs(x) < 1e21:
            return str(int(x))
        return repr(x)
    return str(x)


def a_fijo(x, dec):
    """Number.prototype.toFixed: con empate exacto gana el de mayor módulo."""
    from decimal import ROUND_HALF_UP, Decimal
    q = Decimal(1).scaleb(-dec)
    return format(Decimal(x).quantize(q, rounding=ROUND_HALF_UP), 'f')


def semilla(x):
    """Semilla de 32 bits a partir de un texto o un número (FNV-1a)."""
    s = a_texto(x)
    h = 0x811C9DC5
    # charCodeAt devuelve unidades UTF-16, no puntos de código.
    b = s.encode('utf-16-le')
    for i in range(0, len(b), 2):
        h ^= b[i] | (b[i + 1] << 8)
        h = (h * 0x01000193) & _M32  # Math.imul
    return h


class Generador:
    """Generador con semilla: `uniforme()`, `normal(media, de)` y `entre(a, b)`."""

    def __init__(self, x):
        self._a = semilla(x)

    def uniforme(self):
        self._a = (self._a + 0x6D2B79F5) & _M32
        a = self._a
        t = ((a ^ (a >> 15)) * (1 | a)) & _M32
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & _M32)) & _M32) ^ t
        return ((t ^ (t >> 14)) & _M32) / 4294967296

    def normal(self, media=0, de=1):
        # Box-Muller; 1 - u para no tomar log(0).
        u = 1 - self.uniforme()
        v = self.uniforme()
        return media + de * math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)

    def entre(self, lo, hi):
        return lo + (hi - lo) * self.uniforme()


def generador(x):
    return Generador(x)
