
class CalculateLogo():
    def __init__(self, thr, umd):
        self.thr = thr

        self.umd_test = self.calNewUmd(umd)
        self.sdt = self.sdt_calcule(self.thr)
        print(f"sdt: {self.sdt}")
        print(f"umd: {self.umd_test}")
        print(f"thr: {self.thr}")
        self.srt = [self.thr["Aerea_mkg"][4][0],self.thr["Aerea_mkg"][4][1]]
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


    def calNewUmd(self, data):
        por_logo = [0,24,52,64,76,80,96,100]
        curve_normal = [0,5,10,15,20,25,30,35]
        result = [[],[]]
        maxUMD = [0,0]
        maxINT = [0,0]
        self.recl = [data[0][0], data[1][0]]

        for i in range(len(self.recl)):
            for k,j in data[i][1].items():
                #print(k,j)
                maxUMD[i] = j
                maxINT[i] = int(k)

        for i in range(len(self.recl)):
            if self.recl[i]:
                idx = por_logo.index(maxUMD[i])
                new_logo = por_logo[:idx+1]
                step = len(por_logo[idx+1:])
                dot = 0
                for _ in range(step):
                    dot +=1
                    new_logo.append(por_logo[idx-dot])
                result[i] = new_logo
            else:
                result[i] = por_logo

        self.porcentajes_logo = result
    

    def sdt_calcule(self, data):
        print(f"data: {data['SDT']}")
        return data["SDT"]
    
    def calculate_result(self):
        def generate(rec, sdt , srt, umd, por):
            curve = [0,5,10,15,20,25,30,35]
            temp = {}
            if rec:
                plus = 10
            else:
                plus = 0
            for i in range(len(curve)):
                
                key = str(sdt+curve[i]+plus)
                val = int(por[i]/4)
                temp[key] = val


            
            return temp

        od = generate(self.recl[0], self.sdt[0], self.srt[0], self.umd[0], self.porcentajes_logo[0])
        oi = generate(self.recl[1],self.sdt[1], self.srt[1], self.umd[1], self.porcentajes_logo[1])
        data = [od, oi]
        print(data)
        return data
    
    def get(self):
        return self.data