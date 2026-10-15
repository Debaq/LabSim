
from audiometria.logo_curva import cfg_oido, pct_logo, rollover_de_caso
from audiometria.masking_params import ce_logo

class CalculateLogo():
    """Lo que discrimina el paciente simulado en las listas de palabras.

    La curva de cada oído es `logo_curva.pct_logo`: la MISMA que dibujan el
    PDF y el editor del caso (CaseCharts::pctLogo, logogram.js). Anclada al
    SRT de la ficha (ahí pasa la mitad de su máximo), llega a la UMD del caso
    y, pasado el máximo, meseta o rollover según el componente retrococlear
    del perfil (no el flag de reclutamiento: ver docs/decisiones.md,
    "Logoaudiometría: la curva anclada al SRT", 2026-10-15).

    `self.data[oido]` es la curva en la escala del audiómetro, de 0 a 100 dB
    de 5 en 5 ({'0': %, '5': %, ...}), con un decimal: las palabras que
    acierta salen de ahí (ListWords.calculate, 4 % cada una).
    """

    def __init__(self, thr, umd):
        self.thr = thr
        self.logo_attenuation = 45
        # SDT por Fletcher aéreo: lo usa la mano levantada del SDT
        # (response_A.logo_sdt) y el panel de enmascaramiento, no la curva.
        self.sdt = self.sdt_calcule(self.thr)
        datos = dict(thr)
        datos['UMD'] = umd
        self.ri = rollover_de_caso(datos)
        self.cfg = [cfg_oido(datos, i, self.ri[i]) for i in (0, 1)]
        self.data = [
            {str(db): round(pct_logo(cfg, float(db)), 1) for db in range(0, 101, 5)}
            for cfg in self.cfg
        ]

    def sdt_calcule(self, data):
        # Extraer los elementos de la lista desde el índice 1 hasta el 6 (inclusive)
        sublista = data["Aerea_mkg"][1:7]
        # Calcular el promedio para a y b
        minimos_a = sorted(item[0] for item in sublista)[:2]
        minimos_b = sorted(item[1] for item in sublista)[:2]

        # Calcular el promedio de los dos números más bajos
        promedio_minimos_a = sum(minimos_a) / len(minimos_a)
        promedio_minimos_b = sum(minimos_b) / len(minimos_b)

        # Redondear hacia abajo al múltiplo de 5 más cercano
        promedio_minimos_a_redondeado = (promedio_minimos_a // 5) * 5
        promedio_minimos_b_redondeado = (promedio_minimos_b // 5) * 5

        return [promedio_minimos_a_redondeado, promedio_minimos_b_redondeado]


    
    def get(self, side, mkg, intensity, int_mkg=None, stim_mkg=None):
        """
        Devuelve el % de discriminacion que responde el paciente simulado.

        El paciente contesta con lo que mejor entienda, no con lo que el
        examinador cree estar estudiando: se calculan las dos vias por las
        que le puede llegar el habla y se devuelve la mejor.

          - oido estudiado: su propia curva, corrida hacia arriba si el
            ruido puesto en el contralateral cruza de vuelta y lo tapa
            (sobre-enmascaramiento);
          - oido contralateral: el habla cruza por via osea con la
            atenuacion interaural (45 dB), asi que solo llega si la
            intensidad la supera, y el ruido que haya en ese oido la
            enmascara.

        El cruce solo puede sumar, nunca empeorar lo que discrimina el oido
        estudiado: sin enmascarar, el paciente responde igual o mejor que
        lo real (ese es el "engaño" clinico que el enmascaramiento existe
        para detectar), y enmascarar de mas solo puede tapar.

        `stim_mkg` es el indice de stim_list del ruido puesto (ver
        masking_params): sin dato se asume el que corresponde a la prueba.
        """
        other = 1 - side
        int_mkg = int_mkg if (mkg and int_mkg is not None) else 0
        at = self.logo_attenuation
        bone = self._bone_sdt()
        gap = self._air_bone_gap()

        # El tipo de ruido importa: el habla ocupa todo el espectro, asi que
        # el ruido conformado al habla (speech noise) es el que rinde, y una
        # banda estrecha deja pasar casi todo. El CE descuenta esa perdida de
        # eficiencia del nivel que realmente enmascara.
        ruido = int_mkg - ce_logo(stim_mkg) if int_mkg else 0

        # el ruido del contralateral cruza con la misma atenuacion interaural
        # y enmascara al oido estudiado por encima de su umbral oseo
        shift_e = max(0, (ruido - at) - bone[side])
        propio = self._curve(side, intensity - shift_e)

        # el habla cruzada llega a la coclea contralateral a (intensity - at);
        # la curva del contralateral esta en dB HL aereos, de ahi el + gap.
        # El ruido, aereo, llega a esa misma coclea atenuado por su gap.
        shift_ne = max(0, (ruido - gap[other]) - bone[other])
        cruce = self._curve(other, intensity - at + gap[other] - shift_ne)

        return max(propio, cruce)

    def _curve(self, side, intensity):
        """% de un oído a un nivel, en la grilla de 5 dB del audiómetro.

        Bajo 0 dB HL no se acota a 0: el habla que cruza por vía ósea llega
        a la cóclea contraria a (intensidad - 45), que puede ser negativo, y
        leerlo como 0 dB le daba al contralateral sano el % de su propio
        0 dB (con la curva anclada al SRT, un 20-50 %) a un nivel que no
        oye. Arriba sí se acota: 100 dB es el techo del canal de habla.
        """
        nivel = int(min(intensity, 100) // 5 * 5)
        if nivel >= 0:
            return self.data[side][str(nivel)]
        return round(pct_logo(self.cfg[side], float(nivel)), 1)

    def _air_bone_gap(self):
        """Gap aereo-oseo de habla por oido (SDT - Fletcher oseo)."""
        sdt = self.thr.get('SDT', self.sdt)
        bone = self._bone_sdt()
        return [max(0, sdt[i] - bone[i]) for i in (0, 1)]

    def _masking_range(self, side, other, intensity, stim_mkg=None):
        ce = ce_logo(stim_mkg)
        sdt = self.thr.get('SDT', self.sdt)
        bone = self._bone_sdt()
        at = self.logo_attenuation
        uane = sdt[other]
        uoe = bone[side]
        uone = bone[other]
        mkg_min = intensity - at - uone + uane + ce
        mkg_max = at + uoe + ce
        mkg_lo, mkg_hi = sorted([mkg_min, mkg_max])
        return {'mkg_min': mkg_lo, 'mkg_max': mkg_hi}

    def _bone_sdt(self):
        # Promedio de Fletcher (mejores 2 de 500/1000/2000Hz) sobre Osea_mkg,
        # igual criterio que response.py:calc_sdt.
        sublista = self.thr['Osea_mkg'][2:5]
        minimos_a = sorted(item[0] for item in sublista)[:2]
        minimos_b = sorted(item[1] for item in sublista)[:2]
        a = (sum(minimos_a) / len(minimos_a) // 5) * 5
        b = (sum(minimos_b) / len(minimos_b) // 5) * 5
        return [a, b]
