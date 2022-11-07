import random
from lib.helpers import CasesOffline

"""_summary_
tipo->condición -> respuesta
in:estimulo out:bool respuesta
"""

class Response:
    def __init__(self):
        super().__init__()
        self.data = self.profile_data_load("1")    
    
    def profile_data_load(self, profile:str):
        base_data = CasesOffline().get_cases("labsim")
        return base_data[profile]
        
    
    def threshold(self):
        pass
    
    
class ResponseThresholdAudiometry(Response):
    def __init__(self):
        super().__init__()
        self.frecuency =         [125,250, 500,1000,2000,3000,4000,6000,8000]
        self.attenuations = [35, 40,  40,  40, 40,  45,  45,  50, 50]
        self.aerea = [[self.data["Aerea"][i][0] for i in range(len(self.data["Aerea"]))], 
                      [self.data["Aerea"][i][1] for i in range(len(self.data["Aerea"]))]]
        self.oseo = [[self.data["Osea"][i][0] for i in range(len(self.data["Osea"]))], 
                      [self.data["Osea"][i][1] for i in range(len(self.data["Osea"]))]]
        
        
    def response_aerea(self, side, frecuency,stim, mkg, cfmkg):
        index_frecuency = self.frecuency.index(frecuency)
        int_thr = self.aerea[side][index_frecuency]
        int_thr_cnt = self.aerea[int(not side)][index_frecuency]
        int_thr_o_cnt = self.oseo[int(not side)][index_frecuency]

        attenuation = self.attenuations[index_frecuency]
        if_need_mkg = int_thr > int_thr_o_cnt + attenuation
        if not if_need_mkg:
            #print("no necesita mkg")
            return stim >= int_thr
        #print("necesita mkg")
        if mkg==0:
            #print("el mkg esta apagado")
            sombra = list(range(0,15,5))
            random.shuffle(sombra)
            return stim - attenuation >= int_thr_o_cnt + sombra[0]
        if mkg > 0:
            int_thr_o = self.oseo[side][index_frecuency]
            #print("el mkg esta prendido")
            range_mkg = self.min_max_mkg_aereo(stim, int_thr,int_thr_cnt,int_thr_o,
                                            int_thr_o_cnt,attenuation,cfmkg)
            if range_mkg == 0:
                print("estamos en cero")
            if mkg in range_mkg:
                #print("esta enmascarado correctamente")
                return stim >= int_thr
            if mkg > range_mkg[-1]:
                #print("esta sobre enmascarado")
                return False
            elif mkg < range_mkg[0]:
                #print("esta subenmascarado")
                return stim - attenuation >= int_thr_cnt
                    
        
                
        
    def min_max_mkg_aereo(self, stim, a_ipsi,a_contra,o_ipsi,o_contra, attenuation, cfmkg):
        #print(f"estimulo con:{a_ipsi}, le resto {attenuation}, pasan {a_ipsi-attenuation}")
        min_mkg = 5 + a_contra
        max_mkg = attenuation + a_contra + o_ipsi
        #min_mkg = a_ipsi - attenuation - o_contra + a_contra + cfmkg
        #max_mkg = o_ipsi + attenuation
        #print(f"{min_mkg}-{max_mkg}")
        return list(range(min_mkg, max_mkg,5)) if min_mkg < max_mkg else 0 
        
        
    
        


class ResponseTimpanometry():
    pass

class ResponseAbr():
    pass

"""a = ResponseThresholdAudiometry()
side = 0
frecuencia = 125
mkg = 0
cfmkg = 0
lista = list(range(0,100,5))
lista.reverse()
for i in lista:
    intensidad = i
    response = a.response_aerea(side, frecuencia, intensidad, mkg, cfmkg)
    
    print(f"{i} - {response}")"""