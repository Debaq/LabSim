class Fowler:
    def __init__(self) -> None:
        self.th_est = None
        self.th_ref = None
        self.cuts = [None, None, None]
        self.side_b = None
        self.int_est = None
        self.int_ref = None
        self.diff_rest = 0
        self.step3_acum = {'level': None, 'idx': 0, 'steps':[]}
        self.first_reclut = 0
        self.list_recruit = []


    def set_th(self, th_od:int, th_oi:int) -> None:
        #se evalua el mejor oído se almacena el string para otras funciones
        if th_od < th_oi:
            self.th_ref, self.th_est = th_od, th_oi
            self.side_b = 0
        else:
            self.th_ref, self.th_est = th_oi, th_od
            self.side_b = 1

        self.diff_rest = self.th_ref - self.th_est

    def set_cut(self, cut_1, cut_2, cut_3) ->None:
        self.cuts[0] = self.th_est + cut_1 #reclutamiento parcial
        self.cuts[1] = self.th_est + cut_2 #reclutamiento
        self.cuts[2] = self.th_est + cut_3 #sobre reclutamiento
        print(self.cuts)
        

    def define_ints(self, ints:list) -> None:
        if self.side_b == 0:
            self.int_ref = ints[0]
            self.int_est = ints[1]
        else:
            self.int_ref = ints[1]
            self.int_est = ints[0]

    def step3(self, int_ref):
        if self.step3_acum['level'] != int_ref:
            acum = 0 if self.step3_acum['level'] == None else 1
            self.step3_acum['level'] = int_ref
            down = int_ref+5
            up = int_ref + 20
            list_int = list(range(down,up,5))
            rev = list(reversed(list_int))
            self.step3_acum['steps'] = rev
            self.step3_acum['idx'] += acum
            if self.step3_acum['idx'] + 1 > len(self.step3_acum['steps']):
                self.step3_acum['idx'] = len(self.step3_acum['steps']) - 1
            #si se hace otro fowler hay que resetear esto
 

    def evaluate(self, int_od:int, int_oi:int):
        self.define_ints([int_od, int_oi])
 
        if self.int_est == self.th_est and self.int_ref == self.th_ref:  
            #paso 1: estamos en umbral
            if not [self.int_ref, self.int_est] in self.list_recruit:
                self.list_recruit.append([self.int_ref, self.int_est])
                return True, None, 0
            else:
                return True, None, 0
        
        if self.int_est < self.cuts[0]:
            #paso 2: estamos bajo el reclutamiento
            if [self.int_ref, self.int_est] in self.list_recruit:
                return True, None, 1

            self.int_est = 0 if self.int_est < self.th_est else self.int_est
            diff = (self.int_ref-self.th_ref) - (self.int_est-self.th_est)
            equals = diff == 0

            if equals:
                side = None
                self.list_recruit.append([self.int_ref, self.int_est])

            elif diff >= 0:
                side = self.side_b
            elif diff < 0:
                side = int(not self.side_b)
            return equals, side, 1


        if self.cuts[0] <= self.int_est < self.cuts[1]:
            #paso 3: comienza a reclutar 
            if [self.int_ref, self.int_est] in self.list_recruit:
                return True, None, 2

            equals = True
            side = None
            state = 2
            if self.first_reclut == 0 and self.int_est != self.int_ref:
                self.first_reclut = self.int_est
            else:
                if self.first_reclut == self.int_est and self.int_est != self.int_ref:
                    pass
                else:
                    self.step3(self.int_ref)
                    idx = self.step3_acum['idx']
                    test_value = self.step3_acum['steps'][idx]
                    equals = test_value == self.int_est
                    state = 2
                    side = self.side_b
                    if self.int_est  >= self.int_ref + 20:
                        side = int(not self.side_b)
            if equals:
                self.list_recruit.append([self.int_ref, self.int_est])
            return equals, side, state


        if self.cuts[2] > self.int_est >= self.cuts[1]:
            #paso 4 a reclutar se ha dicho
            diff = self.int_ref - self.int_est
            equals = diff == 0
            if diff == 0:
                side = None
            if diff > 0:
                side = self.side_b
            if diff < 0 :
                side = int(not self.side_b)
            return equals, side, 3

        if self.int_est >= self.cuts[2]:
            diff = self.int_ref - self.int_est -10
            equals = diff < 0

            if equals:
                side = None
            elif diff >= 0:
                side = self.side_b
            elif diff < 0 :
                side = int(not self.side_b)
            return equals, side, 4

        return False, 33

"""
# Datos iniciales
fowler = Fowler()
fowler.set_th(20,40)
fowler.set_cut(20,40,60)
val_min = 20
val_max = 30
# Loop para probar la función
contador_true = 0
while True:
    resultado = fowler.evaluate(val_min, val_max)

    if resultado[0]:
        print(f"({val_min}) x---o ({val_max}), {resultado}")

        contador_true += 1
        val_min += 20
    else:
        if resultado[1] == 0:
            side_letter = "<---"
        else:
            side_letter = "--->"
        #print(f"({val_min}) {side_letter} ({val_max}), {resultado}")

        contador_true = 0
        val_max += 5
        
    # Añadir condición de parada para evitar un bucle infinito
    if val_min > 150 or val_max > 150:
        break


val_min = 80
val_max = 100
resultado = fowler.evaluate(val_min, val_max)
print(f"({val_min}) ---- ({val_max}), {resultado}")
"""
