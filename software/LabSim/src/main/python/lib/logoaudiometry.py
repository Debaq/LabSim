
import copy

class CalculateLogo():
    def __init__(self, thr, umd):
        self.thr = thr
        recruit = thr["recruit"]
        self.scale_htl = {str(i*5):1 for i in range(21)}
        self.por_logo = [i*4 for i in range(26)]

        self.sdt = self.sdt_calcule(self.thr)
        self.data = self.calNewUmd(umd, recruit, self.sdt)

        #self.srt = [self.thr["Aerea_mkg"][4][0],self.thr["Aerea_mkg"][4][1]]
        #for i in range(len(self.srt)):
        #    if self.srt[i] == self.sdt[i]:
        #        self.srt[i] = self.srt[i]+10
        #print("sdt:{},{}".format(self.sdt[0], self.sdt[1]))
        #print("srt:{},{}".format(self.srt[0], self.srt[1]))
        #self.umd = [self.srt[0]+25, self.srt[1]+25]
        #print("umd:{},{}".format(self.umd[0], self.umd[1]))

        
        #self.porcentajes_logo = [0,24,52,64,76,88,96,100]
        #self.curve_normal = [0,5,10,15,20,25,30,35]
        #self.data = self.calculate_result()


    def calNewUmd(self, data, recruit, sdt):
        #por_logo = [0,24,52,64,76,80,96,100]
        max_response = [data[0]["int"],data[1]["int"]]
        max_percentage = [data[0]["percentage"],data[1]["percentage"]]
        result = [copy.copy(self.scale_htl),copy.copy(self.scale_htl)]
        #establecer la maxima respuesta
        for idx, _ in enumerate(data):
            sdt_0 = sdt[idx]
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

            #print(f"{zero_sdt},{sdt_umd},{umd_end}")
        return result
    
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
        
    def cal_range_umd_end(self, data:dict, rangex:list, perc_umd:int, umd:int, recruit: bool):
        count = 1
        for idx, i_result in enumerate(data):
            if rangex[0] < idx:
                if recruit:
                    umd = umd-count*5
                    if umd < 0:
                        umd = 0
                    data[i_result] = data[str(umd)]
                else:
                    data[i_result] = perc_umd


    def sdt_calcule(self, data):
        return data["SDT"]

    
    def get(self):
        return self.data
    
if __name__ == '__main__':

    umb = [{"int":85, "percentage": 40},{"int":40,"percentage":96}]

    thr = {"SDT" :[50,10], "recruit":[False, True]}

        
    b = CalculateLogo(thr, umb)