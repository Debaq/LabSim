"""
El examen en curso: qué se registró, qué midió el alumno y qué sale de eso.

Separado de la ventana a propósito. Lo que vale de un VEMP no es la traza:
son las cuentas que se hacen sobre ella (pico-pico, corregida por EMG,
asimetría, umbral, sintonía) y esas cuentas tienen que poder correrse y
probarse sin levantar Qt.

Una nota sobre la amplitud, que es de lo que se trata el examen: la CRUDA
--los µV de la pantalla-- no compara nada, porque depende de cuánto contrajo
el paciente en ese registro. La que compara es la CORREGIDA (cruda dividida
por el EMG rectificado con el que se registró), y es la que entra en la
asimetría. Las dos se guardan; cuál se informa lo decide quien informa.
"""

import numpy as np

from vemp import protocol


class Registro:
    """Una curva: sus condiciones, su promedio acumulado y sus marcas."""

    def __init__(self, nombre, ajustes, x):
        self.nombre = nombre
        self.ajustes = ajustes
        self.x = np.asarray(x, dtype=float)
        self.y = np.zeros_like(self.x)
        self.aceptados = 0
        self.rechazados = 0
        self.emg_suma = 0.0           # ponderada por barridos aceptados
        self.marcas = {}              # pico -> [lat_ms, amp_uV]
        self.terminado = False
        self.info = {}

    # ------------------------------------------------------------------
    # Promediación
    # ------------------------------------------------------------------

    def acumular(self, lote):
        """Suma un lote al promedio acumulado.

        Promedio corrido ponderado por barridos: acumular 20 barridos sobre
        180 ya promediados mueve la curva un 10%, no la reemplaza.
        """
        self.rechazados += lote.rechazados
        if lote.aceptados <= 0:
            return
        total = self.aceptados + lote.aceptados
        peso_nuevo = lote.aceptados / total
        self.y = self.y * (1.0 - peso_nuevo) + lote.promedio * peso_nuevo
        self.emg_suma += lote.emg * lote.aceptados
        self.aceptados = total
        if lote.info:
            self.info = lote.info

    @property
    def emg_medio(self):
        if self.aceptados <= 0:
            return 0.0
        return self.emg_suma / self.aceptados

    @property
    def subtipo(self):
        return self.ajustes.subtipo

    @property
    def lado(self):
        return self.ajustes.lado

    @property
    def intensidad(self):
        return self.ajustes.intensidad

    @property
    def condicion(self):
        return self.ajustes.clave_registro()

    # ------------------------------------------------------------------
    # Marcas y medidas
    # ------------------------------------------------------------------

    def marcar(self, pico, lat, amp):
        self.marcas[pico] = [float(lat), float(amp)]

    def desmarcar(self, pico=None):
        if pico is None:
            self.marcas.clear()
        else:
            self.marcas.pop(pico, None)

    @property
    def picos_esperados(self):
        return protocol.PEAKS.get(self.subtipo, protocol.PEAKS[protocol.CVEMP])

    def completo(self):
        return all(p in self.marcas for p in self.picos_esperados)

    def p2p(self):
        """Amplitud pico-pico marcada (µV). Los dos picos son de signo
        opuesto, así que la resta con signo es lo que se informa."""
        if not self.completo():
            return None
        amps = [self.marcas[p][1] for p in self.picos_esperados]
        return abs(amps[0] - amps[1])

    def p2p_corregida(self):
        """Pico-pico dividida por el EMG con el que se registró.

        Adimensional: es "cuánto modula el estímulo a la contracción que
        había". Es la que se puede comparar entre oídos y entre registros.
        """
        bruta = self.p2p()
        if bruta is None or self.emg_medio <= 0:
            return None
        return bruta / self.emg_medio

    def interpico_ms(self):
        if not self.completo():
            return None
        lats = [self.marcas[p][0] for p in self.picos_esperados]
        return abs(lats[1] - lats[0])

    def valor_en(self, lat_ms):
        """Amplitud de la curva en esa latencia (para los cursores)."""
        if self.x.size == 0:
            return 0.0
        idx = int(np.abs(self.x - lat_ms).argmin())
        return float(self.y[idx])

    def pico_cercano(self, lat_ms, pico):
        """Extremo del signo correcto más cercano a `lat_ms`.

        Marcar un pico es decir dónde está, no acertarle al punto: el clic
        cae cerca y la marca se pega al máximo (o mínimo) local de la
        polaridad que corresponde al nombre del pico.
        """
        if self.x.size == 0:
            return lat_ms, 0.0
        signo = protocol.signo_pico(pico)
        ventana = 3.5
        mask = (self.x >= lat_ms - ventana) & (self.x <= lat_ms + ventana)
        if not mask.any():
            return lat_ms, self.valor_en(lat_ms)
        xs = self.x[mask]
        ys = self.y[mask] * signo
        idx = int(np.argmax(ys))
        return float(xs[idx]), float(self.y[mask][idx])

    # ------------------------------------------------------------------
    # Serialización (informe)
    # ------------------------------------------------------------------

    def a_dict(self):
        """Ficha de la curva para el informe. Mantiene las claves que ya
        imprime ReportPdfBuilder (side/int/waves/LatAmp/p2p/maniobra/emg_uv)
        y agrega las del VEMP nuevo."""
        ajustes = self.ajustes
        return {
            'side': ajustes.lado,
            'subtipo': ajustes.subtipo,
            'int': ajustes.intensidad,
            'freq': ajustes.freq,
            'stim': 'tone burst',
            'pol': ajustes.polaridad,
            'transductor': ajustes.transductor,
            'rate': ajustes.tasa,
            'filter_passhigh': ajustes.filtro_alto,
            'filter_down': ajustes.filtro_bajo,
            'maniobra': ajustes.maniobra,
            'montaje': protocol.descripcion_montaje(ajustes.subtipo, ajustes.lado),
            'emg_uv': round(self.emg_medio, 1),
            'emg_ok': protocol.emg_en_banda(ajustes.subtipo, self.emg_medio),
            'waves': list(self.picos_esperados),
            'LatAmp': {p: list(self.marcas.get(p, [None, None]))
                       for p in self.picos_esperados},
            'p2p': None if self.p2p() is None else round(self.p2p(), 1),
            'p2p_corregida': (None if self.p2p_corregida() is None
                              else round(self.p2p_corregida(), 3)),
            'interpico': None if self.interpico_ms() is None else round(self.interpico_ms(), 2),
            'tecnica': {
                'barridos_aceptados': self.aceptados,
                'barridos_rechazados': self.rechazados,
                'barridos_pedidos': ajustes.promedios,
            },
            # Con esto la curva se vuelve a armar tal cual al retomar la
            # atención (ver desde_dict): antes solo viajaban las medidas y
            # el trazo se perdía con la app.
            'traza': {'x': [round(float(v), 4) for v in self.x],
                      'y': [round(float(v), 5) for v in self.y]},
            'ajustes': dict(ajustes.__dict__),
            'emg_suma': round(self.emg_suma, 4),
            'terminado': self.terminado,
        }

    @classmethod
    def desde_dict(cls, nombre, d):
        """La curva guardada por a_dict(), o None si no trae el trazo
        (informes de antes de que se guardara)."""
        from vemp.engine import Ajustes
        traza = d.get('traza') or {}
        if not traza.get('x'):
            return None
        campos = {k: v for k, v in (d.get('ajustes') or {}).items()
                  if k in Ajustes.__dataclass_fields__}
        registro = cls(nombre, Ajustes(**campos), traza['x'])
        registro.y = np.asarray(traza['y'], dtype=float)
        tecnica = d.get('tecnica') or {}
        registro.aceptados = int(tecnica.get('barridos_aceptados') or 0)
        registro.rechazados = int(tecnica.get('barridos_rechazados') or 0)
        registro.emg_suma = float(d.get('emg_suma') or 0.0)
        registro.terminado = bool(d.get('terminado', True))
        for pico, valores in (d.get('LatAmp') or {}).items():
            if valores and valores[0] is not None and valores[1] is not None:
                registro.marcar(pico, valores[0], valores[1])
        return registro


class Sesion:
    """Todas las curvas del examen y lo que se deduce de ellas."""

    def __init__(self):
        self.registros = {}      # nombre -> Registro
        self.umbral_informado = {}   # (lado, subtipo) -> dB declarados por el alumno

    # ------------------------------------------------------------------
    # Altas y bajas
    # ------------------------------------------------------------------

    def nuevo(self, ajustes, x):
        nombre = self._nombre(ajustes)
        registro = Registro(nombre, ajustes.copia(), x)
        self.registros[nombre] = registro
        return registro

    def _nombre(self, ajustes):
        """Nombre corto y legible: subtipo, oído y número de orden.

        El número sale del máximo usado y no de la cuenta: borrar una curva
        del medio no puede devolver un nombre que otra sigue usando.
        """
        prefijo = f'{ajustes.subtipo[0]}-{ajustes.lado}-'
        usados = [int(n[len(prefijo):]) for n in self.registros
                  if n.startswith(prefijo) and n[len(prefijo):].isdigit()]
        return f'{prefijo}{max(usados, default=0) + 1}'

    def borrar(self, nombre):
        return self.registros.pop(nombre, None)

    def limpiar(self):
        self.registros.clear()
        self.umbral_informado.clear()

    def get(self, nombre):
        return self.registros.get(nombre)

    def por_lado(self, lado, subtipo=None):
        return [r for r in self.registros.values()
                if r.lado == lado and (subtipo is None or r.subtipo == subtipo)]

    def por_condicion(self, lado, subtipo, transductor=None, freq=None):
        salida = []
        for r in self.por_lado(lado, subtipo):
            if transductor is not None and r.ajustes.transductor != transductor:
                continue
            if freq is not None and r.ajustes.freq != freq:
                continue
            salida.append(r)
        return sorted(salida, key=lambda r: r.intensidad, reverse=True)

    # ------------------------------------------------------------------
    # Medidas del examen
    # ------------------------------------------------------------------

    def mejor(self, lado, subtipo, transductor=None, freq=None):
        """Registro con la mayor amplitud corregida en esa condición.

        Corregida y no cruda: si el paciente contrajo más en un registro que
        en otro, el crudo elige el registro equivocado.
        """
        candidatos = [r for r in self.por_condicion(lado, subtipo, transductor, freq)
                      if r.p2p_corregida() is not None]
        if not candidatos:
            return None
        return max(candidatos, key=lambda r: r.p2p_corregida())

    def asimetria(self, subtipo, transductor=None, freq=None):
        """Razón de asimetría de Jongkees sobre las amplitudes CORREGIDAS.

        Devuelve (mejor_od, mejor_oi, ratio_%). Sin las dos, ratio None: una
        asimetría con un solo oído medido no es una asimetría.
        """
        od = self.mejor('OD', subtipo, transductor, freq)
        oi = self.mejor('OI', subtipo, transductor, freq)
        if od is None or oi is None:
            return od, oi, None
        a, b = od.p2p_corregida(), oi.p2p_corregida()
        if (a + b) <= 0:
            return od, oi, None
        return od, oi, abs(a - b) / (a + b) * 100.0

    def serie(self, lado, subtipo, transductor=None, freq=None):
        """[(intensidad, corregida, cruda)] ordenada por intensidad.

        Es la serie con la que se busca el umbral: una intensidad puede
        tener más de un registro y queda el de mayor amplitud corregida.
        """
        mejores = {}
        for r in self.por_condicion(lado, subtipo, transductor, freq):
            corregida = r.p2p_corregida()
            if corregida is None:
                continue
            previo = mejores.get(r.intensidad)
            if previo is None or corregida > previo[1]:
                mejores[r.intensidad] = (r.intensidad, corregida, r.p2p())
        return [mejores[k] for k in sorted(mejores)]

    def umbral_medido(self, lado, subtipo, transductor=None, freq=None):
        """Menor intensidad con respuesta marcada: el umbral que muestra la
        serie. Lo que el alumno informa lo escribe él (`umbral_informado`);
        esto es lo que sus marcas dicen."""
        serie = self.serie(lado, subtipo, transductor, freq)
        return serie[0][0] if serie else None

    def sintonia(self, lado, subtipo, transductor=None):
        """{frecuencia: mejor amplitud corregida} -- en qué frecuencia
        responde mejor ese oído."""
        salida = {}
        for freq in protocol.FRECUENCIAS:
            mejor = self.mejor(lado, subtipo, transductor, freq)
            if mejor is not None:
                salida[freq] = mejor.p2p_corregida()
        return salida

    # ------------------------------------------------------------------
    # Informe
    # ------------------------------------------------------------------

    def resumen(self, subtipo, transductor=None, freq=None):
        od, oi, ratio = self.asimetria(subtipo, transductor, freq)
        return {
            'subtipo': subtipo,
            'od': None if od is None else round(od.p2p(), 1),
            'oi': None if oi is None else round(oi.p2p(), 1),
            'od_corregida': None if od is None else round(od.p2p_corregida(), 3),
            'oi_corregida': None if oi is None else round(oi.p2p_corregida(), 3),
            'ratio': None if ratio is None else round(ratio, 1),
            'umbral_od': self.umbral_medido('OD', subtipo, transductor, freq),
            'umbral_oi': self.umbral_medido('OI', subtipo, transductor, freq),
        }

    def curvas_dict(self):
        return {nombre: registro.a_dict()
                for nombre, registro in self.registros.items()}
