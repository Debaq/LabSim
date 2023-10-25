class CalculateLogo():
    def __init__(self, thr, umd):
        self.thr = thr

        self.umd_test = self.calNewUmd(thr,umd)
        self.sdt = self.sdt_calcule(self.thr)
        self.srt = [self.thr["Aérea_mkg"][4][0],self.thr["Aérea_mkg"][4][1]]
        for i in range(len(self.srt)):
            if self.srt[i] == self.sdt[i]:
                self.srt[i] = self.srt[i]+10
        #print("sdt:{},{}".format(self.sdt[0], self.sdt[1]))
        #print("srt:{},{}".format(self.srt[0], self.srt[1]))
        self.umd = [self.srt[0]+25, self.srt[1]+25]
        #print("umd:{},{}".format(self.umd[0], self.umd[1]))
        #self.porcentajes_logo = [0,24,52,64,76,88,96,100]
        #self.curve_normal = [0,5,10,15,20,25,30,35]
        self.data = self.calculate_result()


    def calNewUmd(self, thr, data):
        best_od = [thr["Aérea_mkg"][i][0] for i in range(1,7)]
        best_od.sort()
        best_oi = [thr["Aérea_mkg"][i][1] for i in range(1,7)]
        best_oi.sort()
        thr_2k = [thr["Aérea_mkg"][4][i] for i in range(2)]
        umd_data = [list(i[0].values()) for i in data]

        sdt_od = sum(best_od[0:2])/2
        sdt_oi = sum(best_oi[0:2])/2
        data_sdt = [sdt_od, sdt_oi]

        if umd_data[0][2] > 52:
            srt_od = thr_2k[0] if thr_2k[0] >= sdt_od + 20 else sdt_od + 10
        else:
            srt_od = 130

        if umd_data[1][2] > 52:
            srt_oi = thr_2k[1] if thr_2k[1] >= sdt_oi + 20 else sdt_oi + 10
        else:
            srt_oi = 130
        data_srt = [srt_od, srt_oi]

        por_logo = list(range(0,104,4))
        curve_normal = list(range(0,120,5))
        
        if umd_data[0][0] is False:
            umd_od = {}
            if srt_od == 130:
                for i in curve_normal:
                    if i <= sdt_od +10:
                        value = 0
                    else:
                        value = umd_data[0][2]
                    umd_od[str(i)] = value
            else:
                for i in curve_normal:
                    if i <= srt_od:
                        value = 0
                    else:
                        pass
                        
                    
                

   
    

    def sdt_calcule(self, data):
        od = [data["Aérea_mkg"][1][0],data["Aérea_mkg"][2][0],data["Aérea_mkg"][3][0],data["Aérea_mkg"][4][0],data["Aérea_mkg"][5][0],data["Aérea_mkg"][6][0]]
        oi = [data["Aérea_mkg"][1][1],data["Aérea_mkg"][2][1],data["Aérea_mkg"][3][1],data["Aérea_mkg"][4][1],data["Aérea_mkg"][5][1],data["Aérea_mkg"][6][1]]
        od.sort()
        oi.sort()
        def prom(x):
            return sum(x)/len(x)

        prom_od = prom([od[0], od[1]])
        prom_oi = prom([oi[0], oi[1]])

        result_prev = [prom_od, prom_oi]
        result = [int(result_prev[0]/5)*5,int(result_prev[1]/5)*5 ]
        return result
    
    def calculate_result(self):
        def generate(rec, sdt , srt, umd, por):
            curve = [0,5,10,15,20,25,30,35]
            plus = 10 if rec else 0
            return {str(sdt+curve[i]+plus): int(por[i]/4) for i in range(len(curve))}

        od = generate(self.recl[0], self.sdt[0], self.srt[0], self.umd[0], self.porcentajes_logo[0])
        oi = generate(self.recl[1],self.sdt[1], self.srt[1], self.umd[1], self.porcentajes_logo[1])
        data = [od, oi]
        return data
    
    def get(self):
        return self.data