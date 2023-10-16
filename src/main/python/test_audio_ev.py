class AudiometriaSimulador:

    def __init__(self, data):
        self.data = data
        self.frecuencias = [125, 250, 500, 1_000, 2_000, 3_000, 4_000, 6_000, 8_000]
        self.atenuaciones = [35, 40, 40, 40, 45, 45, 50, 50, 50]
        self.coef_enmascaramiento = {
            "nbn": 0,
            "rb": 10
        }
        
    def get_umbrales(self, tipo, oido, frecuencia):
        idx = self.frecuencias.index(frecuencia)
        if oido == "derecho":
            return self.data[tipo][idx][0]
        else:
            return self.data[tipo][idx][1]

    def calculate_masking(self, oido, frecuencia, tipo_masking):
        if oido == "derecho":
            oido_opuesto = "izquierdo"
        else:
            oido_opuesto = "derecho"
        
        UAE = self.get_umbrales("Aerea", oido, frecuencia)
        UANE = self.get_umbrales("Aerea", oido_opuesto, frecuencia)
        UOE = self.get_umbrales("Osea", oido, frecuencia)
        UONE = self.get_umbrales("Osea", oido_opuesto, frecuencia)
        AT = self.atenuaciones[self.frecuencias.index(frecuencia)]
        CE = self.coef_enmascaramiento[tipo_masking]

        minimo = UAE - AT - UONE + UANE + CE
        maximo = UOE + AT

        if minimo > maximo:
            minimo, maximo = maximo, minimo

        return minimo, maximo

    def evaluar(self, oido, frecuencia, intensidad, masking=False, oido_masking=None, tipo_masking=None, intensidad_masking=0):
        umbral_estudiado = self.get_umbrales("Aerea", oido, frecuencia)
        oido_opuesto = "derecho" if oido == "izquierdo" else "izquierdo"
        umbral_aereo_opuesto = self.get_umbrales("Aerea", oido_opuesto, frecuencia)
        umbral_oseo_opuesto = self.get_umbrales("Osea", oido_opuesto, frecuencia)
        AT = self.atenuaciones[self.frecuencias.index(frecuencia)]
        oido_mejor = min(umbral_aereo_opuesto, umbral_oseo_opuesto) 

        if not masking:
            return intensidad >= umbral_estudiado
        else:
            if not oido_masking or oido_masking == oido:
                return intensidad >= (oido_mejor + AT)
            else:
                minimo, maximo = self.calculate_masking(oido, frecuencia, tipo_masking)
                if intensidad_masking < minimo:
                    return intensidad >= (oido_mejor + AT)
                elif intensidad_masking > maximo:
                    return False
                else:
                    return intensidad >= umbral_estudiado




data = {
    "Aerea": [[30, 25], [35, 30], [40, 35], [45, 20], [50, 45], [50, 45], [45, 40], [40, 35], [40, 35]],
    "Osea":  [[15, 15], [10, 10], [10, 10], [10, 10], [30, 30], [35, 35], [30, 30], [20, 20], [15, 15]]
}

simulador = AudiometriaSimulador(data)
print(simulador.evaluar("derecho", 1_000, 45, False, "izquierdo", "rb", 10  ))  # Con masking y una intensidad de masking de 45
