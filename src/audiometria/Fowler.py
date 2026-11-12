import math

# Requisitos clínicos de aplicabilidad de Fowler/I.W.A. (ABLB) -- deben
# coincidir exactamente con CaseBuilder::fowlerValidationError en el backend
# (labsim_backend/src/CaseBuilder.php). El alumno no sabe de antemano en qué
# frecuencia el caso "califica" -- puede calificar en más de una -- así que
# esto se evalúa en vivo contra la frecuencia que el alumno esté probando,
# no contra un único valor guardado en el caso.
FOWLER_NORMAL_HL = 20
FOWLER_SNHL_GAP_MAX = 10
FOWLER_DIFF_MIN = 20
FOWLER_DIFF_MAX = 40
FOWLER_FREQ_MIN_HZ = 250
FOWLER_FREQ_MAX_HZ = 4000
FOWLER_FREQUENCIES = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]


def fowler_applicable(freq_idx, air_pair, bone_pair):
    """True si Fowler/ABLB es clínicamente aplicable en esta frecuencia con
    estos umbrales: oído de referencia (mejor) en rango normal, oído en
    estudio sensorioneural y fuera de rango normal, diferencia interaural
    de 20 a 40 dB, frecuencia entre 250 y 4000 Hz."""
    if freq_idx < 0 or freq_idx >= len(FOWLER_FREQUENCIES):
        return False
    hz = FOWLER_FREQUENCIES[freq_idx]
    if hz < FOWLER_FREQ_MIN_HZ or hz > FOWLER_FREQ_MAX_HZ:
        return False

    od, oi = air_pair
    ref_side = 0 if od <= oi else 1
    study_side = 1 - ref_side
    ref_th = air_pair[ref_side]
    study_th = air_pair[study_side]
    diff = study_th - ref_th

    if ref_th > FOWLER_NORMAL_HL or study_th <= FOWLER_NORMAL_HL:
        return False
    if diff < FOWLER_DIFF_MIN or diff > FOWLER_DIFF_MAX:
        return False

    gap = study_th - bone_pair[study_side]
    if gap > FOWLER_SNHL_GAP_MAX:
        return False

    return True


# Patrón de reclutamiento -> (inicio_sl, fraccion_final, sobre_db), lo que
# recibe Fowler.set_cut(). Debe coincidir exactamente con
# CaseBuilder::FOWLER_PATTERNS (PHP).
#   inicio_sl: dB sobre su umbral desde los que el oído sano recluta (antes,
#     las dos curvas suben paralelas); 200 = nunca.
#   fraccion_final: qué parte de la diferencia interaural queda al final del
#     reclutamiento (1 = toda, 0.5 = la mitad, 0 = nada).
#   sobre_db: cuánto más abajo que el sano queda al final el afectado.
FOWLER_PATTERNS = {
    'none': (200, 1.0, 0),       # sin reclutamiento: paralelas, la diferencia se mantiene
    'partial': (15, 0.5, 0),     # parcial: la diferencia se achica a la mitad y no cierra
    'complete': (15, 0.0, 0),    # completo: iguala al mismo nivel en los dos oídos
    'over': (15, 0.0, 5),        # sobre-reclutamiento: el afectado iguala 5 dB bajo el sano
}

# Paso del atenuador: el paciente dice "iguales" en el nivel del afectado más
# cercano (de 5 en 5) al de igual sonoridad.
PASO_DB = 5


class Fowler:
    """Balance biaural de sonoridad (ABLB / Fowler).

    La curva de igual sonoridad es fija para el caso: para cada nivel del oído
    sano (referencia) hay un nivel del afectado (en estudio) que suena igual
    (igual_a). Hasta inicio_sl sobre el umbral del sano, las dos suben
    paralelas (la diferencia interaural se mantiene); desde ahí la diferencia
    se achica en línea recta hasta su valor final (fraccion_final de la
    diferencia, menos sobre_db) y se queda ahí. La rampa dura el doble de lo
    que se achica: el afectado sube 1 dB por cada 2 del sano mientras
    recluta.

    Sin estado: la respuesta depende solo de los dos niveles, así que da lo
    mismo el orden en que el alumno los pruebe. Antes recordaba la primera
    igualación del reclutamiento y desde ahí contestaba "iguales" a ese mismo
    nivel del afectado para cualquier nivel del sano.
    """

    def __init__(self) -> None:
        self.th_est = None
        self.th_ref = None
        self.side_b = None      # oído de referencia: 0 OD, 1 OI
        self.inicio_sl = 200
        self.fraccion_final = 1.0
        self.sobre_db = 0
        self.diplacusia = False

    def set_th(self, th_od: int, th_oi: int) -> None:
        """El mejor oído es la referencia; empate -> referencia OI."""
        if th_od < th_oi:
            self.th_ref, self.th_est = th_od, th_oi
            self.side_b = 0
        else:
            self.th_ref, self.th_est = th_oi, th_od
            self.side_b = 1

    def set_cut(self, inicio_sl, fraccion_final, sobre_db) -> None:
        self.inicio_sl = inicio_sl
        self.fraccion_final = fraccion_final
        self.sobre_db = sobre_db

    def igual_a(self, int_ref):
        """Nivel (dB HL, sin redondear) del afectado que suena igual que
        int_ref en el sano."""
        gap = self.th_est - self.th_ref
        final = gap * self.fraccion_final - self.sobre_db
        sl = int_ref - self.th_ref
        rampa = 2 * (gap - final)
        if sl <= self.inicio_sl or rampa <= 0:
            dif = gap
        elif sl >= self.inicio_sl + rampa:
            dif = final
        else:
            dif = gap - (gap - final) * (sl - self.inicio_sl) / rampa
        return int_ref + dif

    def igual_a_paso(self, int_ref):
        """igual_a, al paso del atenuador más cercano."""
        return PASO_DB * math.floor(self.igual_a(int_ref) / PASO_DB + 0.5)

    def evaluate(self, int_od: int, int_oi: int):
        """(iguales, oído que suena más fuerte o None, zona). Zona: 0 bajo
        umbral, 1 paralelas, 2 reclutando, 3 al final del reclutamiento."""
        if self.side_b == 0:
            int_ref, int_est = int_od, int_oi
        else:
            int_ref, int_est = int_oi, int_od
        oye_ref = int_ref >= self.th_ref
        oye_est = int_est >= self.th_est
        if not (oye_ref and oye_est):
            if oye_ref:
                return False, self.side_b, 0
            if oye_est:
                return False, 1 - self.side_b, 0
            return False, None, 0

        sl = int_ref - self.th_ref
        gap = self.th_est - self.th_ref
        rampa = 2 * (gap - (gap * self.fraccion_final - self.sobre_db))
        if sl <= self.inicio_sl or rampa <= 0:
            zona = 1
        elif sl < self.inicio_sl + rampa:
            zona = 2
        else:
            zona = 3

        objetivo = self.igual_a(int_ref)
        if abs(int_est - self.igual_a_paso(int_ref)) < PASO_DB / 2:
            return True, None, zona
        # bajo el nivel de igual sonoridad, el sano suena más fuerte
        return False, (self.side_b if int_est < objetivo else 1 - self.side_b), zona
