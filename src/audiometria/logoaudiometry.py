
import copy

from audiometria.masking_params import ce_logo

class CalculateLogo():
    def __init__(self, thr, umd):
        self.thr = thr
        #print(thr)
        recruit = thr["recruit"]
        self.logo_attenuation = 45
        self.scale_htl = {str(i*5):1 for i in range(21)}
        self.por_logo = [i*4 for i in range(26)]
        self.sdt = self.sdt_calcule(self.thr)
        self.data = self.cal_new_umd(umd, recruit, self.sdt)


    def cal_new_umd(self, data, recruit, sdt):
        #por_logo = [0,24,52,64,76,80,96,100]
        max_response = [data[0]["int"],data[1]["int"]]
        max_percentage = [data[0]["percentage"],data[1]["percentage"]]
        result = [copy.copy(self.scale_htl),copy.copy(self.scale_htl)]
        #establecer la maxima respuesta
        for idx, _ in enumerate(data):
            sdt_0 = int(sdt[idx])
            max_response_ear = max_response[idx]
            max_percentage_ear = max_percentage[idx]
            result[idx][str(max_response_ear)] = max_percentage_ear
            result[idx][str(sdt_0)] = 0
            idx_sdt_0 = 0
            idx_sdt_flag = False
            idf_umd_flag = False
            end_flag = False
            idx_max_response_ear = 0
            for idx_result, i_result in enumerate(result[idx]):
                if int(i_result) == sdt_0:
                    idx_sdt_0 = idx_result
                    idx_sdt_flag = True
                elif int(i_result) == max_response_ear:
                    idx_max_response_ear = idx_result
                    idf_umd_flag = True
                elif idx_sdt_flag:
                    zero_sdt = [0,idx_sdt_0]
                    self.cal_range_zero_sdt(result[idx], zero_sdt)
                    idx_sdt_flag = False
                elif idf_umd_flag:                    
                    sdt_umd = [idx_sdt_0,idx_max_response_ear]
                    self.cal_range_sdt_umd(result[idx], sdt_umd, max_percentage_ear)
                    idf_umd_flag = False
                    end_flag = True
                elif end_flag:
                    umd_end = [idx_max_response_ear,len(result[idx])-1]
                    self.cal_range_umd_end(result[idx], umd_end, max_percentage_ear,
                                           max_response_ear, recruit[idx])
                    end_flag = False

            self._rellenar_cola(result[idx])
            #print(f"{zero_sdt},{sdt_umd},{umd_end}")
        return result

    def _rellenar_cola(self, curva):
        """Arrastra el ultimo valor calculado sobre los que quedaron sin
        calcular.

        La escala arranca inicializada en 1 (scale_htl) y los tramos se van
        pisando a medida que se recorren los cortes. Si el UMD cae fuera de
        la escala --UMD a 110 dB, por ejemplo, cuando la curva llega hasta
        100-- el ultimo tramo nunca se recorre y quedan puntos con ese 1
        crudo: un oido anacusico terminaba 'discriminando' 1% en 95 y 100 dB.
        No se ve en las 25 palabras (int(1/4) = 0) pero ensucia la curva y el
        panel del docente.
        """
        ultimo = 0
        for clave in sorted(curva, key=int):
            if curva[clave] == 1:
                curva[clave] = ultimo
            else:
                ultimo = curva[clave]
    
    def cal_range_zero_sdt(self, data:dict, rangex:list):
        for idx, i_result in enumerate(data):
            if rangex[1] > idx:
                data[i_result] = 0
                
    def cal_range_sdt_umd(self, data:dict, rangex:list, umd:int):
        idx_umd = self.por_logo.index(umd)
        cant_values = rangex[1]-rangex[0]
        values = []
        prev = 130
        multiplo = 5 if umd > 92 else 2
        for count, _ in enumerate(range(cant_values-1), start=1):
            value = self.por_logo[idx_umd-count*multiplo]
            if value <= 0 or value > umd or value > prev:
                value = 4
            prev = value
            values.append(value)
        values.reverse()
        other_count = 130
        for idx, i_result in enumerate(data):
            if rangex[0] < idx and rangex[1] > idx:
                if other_count == 130:
                    other_count = idx
                idx_value = idx - other_count
                data[i_result] = values[idx_value]
        
    def cal_range_umd_end(self, data:dict, rangex:list, 
                          perc_umd:int, umd:int, recruit: bool):
        count = 1
        for idx, i_result in enumerate(data):
            if rangex[0] < idx:
                if recruit:
                    umd = umd-count*5
                    umd = max(umd, 0)
                    data[i_result] = data[str(umd)]
                else:
                    data[i_result] = perc_umd


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
        return self.data[side][str(self._clamp_scale(intensity))]

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

    def _clamp_scale(self, value):
        value = max(0, min(100, value))
        return int(value // 5 * 5)
