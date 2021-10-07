
class CalculateLogo():
    def __init__(self, thr ):
        self.thr = thr
        self.sdt = self.sdt_calcule(self.thr)
        self.srt = [self.thr["Aérea"][4][0],self.thr["Aérea"][4][1]]
        if self.srt[0] == self.sdt[0]:
            self.srt[0] = self.srt[0]+10
        if self.srt[1] == self.sdt[1]:
            self.srt[1]=self.srt[1]+10
        self.umd = [self.srt[0]+25, self.srt[1]+25]
        #self.porcentajes_logo = [[0,0],[5,24],[10,52],[15,64],[20,76],[25,84],[30,96],[35,100]]
        self.porcentajes_logo = [0,24,52,64,76,84,96,100]
        self.curve_normal = [0,5,10,15,20,25,30,35]
        self.data = self.calculate_result()
        


    def sdt_calcule(self, data):
        od = [data["Aérea"][1][0],data["Aérea"][2][0],data["Aérea"][3][0],data["Aérea"][4][0],data["Aérea"][5][0],data["Aérea"][6][0]]
        oi = [data["Aérea"][1][1],data["Aérea"][2][1],data["Aérea"][3][1],data["Aérea"][4][1],data["Aérea"][5][1],data["Aérea"][6][1]]
        od.sort()
        oi.sort()
        def prom(x):
            result = sum(x)/len(x)
            return result

        prom_od = prom([od[0], od[1]])
        prom_oi = prom([oi[0], oi[1]])

        result_prev = [prom_od, prom_oi]
        result = [int(result_prev[0]/5)*5,int(result_prev[1]/5)*5 ]
        return result
    
    def calculate_result(self):
        def generate(sdt , srt, umd, por):
            temp = {}
            idx_sdt = 0
            idx_srt = 2
            idx_umd = 7
            temp[str(sdt)] = int(por[idx_sdt]/4)
            temp[str(sdt+5)] = int(por[1]/4)
            temp[str(srt)] = int(por[idx_srt]/4)
            temp[str(sdt+5)] = int(por[3]/4)
            temp[str(sdt+10)] = int(por[4]/4)
            temp[str(sdt+15)] = int(por[5]/4)
            temp[str(sdt+20)] = int(por[6]/4)
            temp[str(sdt+25)] = int(por[6]/4)

            temp[str(umd)] = int(por[idx_umd]/4)
            return temp
    
        od = generate(self.sdt[0], self.srt[0], self.umd[0], self.porcentajes_logo )
        oi = generate(self.sdt[1], self.srt[1], self.umd[1], self.porcentajes_logo )
        data = [od, oi]
        return data
    
    def get(self):
        return self.data