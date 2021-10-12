
            # threshold
            test = self.lbl_prueba.text()
            prev = self.random_response
            if self.activate_response[0]:
                thr = self.thr
            else:
                thr = _THR_
            #print(thr)

            def test_response(thr, freq, ch, lvl, output, trans):

                freq_index = self.frecuency_list.index(freq)
                trans_index = trans_list.index(trans[ch])
                ouput_index = output_list.index(output[ch])

                UA = thr[0][trans_index][freq_index][ouput_index]
                UO = thr[0][1][freq_index][ouput_index]
                if ouput_index == 0:
                    ouput_contra = 1
                else:
                    ouput_contra = 0

                UAOne = thr[0][1][freq_index][ouput_contra]

                listforMinMax = [freq_index, UA, UO, UAOne]

                curve_z = self.curve_z[ouput_contra]
                name_mkg = self.lbl_stim_ch1.text()
                test_minMax = self.minMax(
                    trans_index, listforMinMax, curve_z, name_mkg)

                if self.lbl_stim_ch1.text() == "Narrow Band Noise" and self.lbl_rev_ch1.text() == "Invertido":
                    #print("{}>{}".format(test_minMax, lvl[ouput_contra]))

                    if test_minMax <= lvl[ouput_contra]:
                        select_thr = 1
                    else:
                        select_thr = 0
                else:
                    select_thr = 0

                threshold_result = thr[select_thr][trans_index][freq_index][ouput_index]
                LDL_result = thr[0][2][freq_index][ouput_index]

                LDL_true = lvl[ch] >= LDL_result

                # responde si el nivel del canal es igual o mayor al umbral
                response_true = lvl[ch] >= threshold_result
                # diferencia entre el umbral del paciente y el nivel del canal
                dif = lvl[ch] - threshold_result

                if dif < -10:  # si esta abajo abajo
                    faraway = -3
                if -10 <= dif < -5:  # 10 abajo
                    faraway = -2
                if -5 <= dif < 0:  # 5 abajo
                    faraway = -1
                if 0 <= dif < 5:  # normal
                    faraway = 0
                if 5 <= dif:  # 5 arriba
                    faraway = 1
                return response_true, faraway, LDL_true

            if activate:
                if test == "Umbrales":
                    stim = [self.lbl_stim[0].text(), self.lbl_stim[1].text()]
                    lvl = [int(self.lbl_intencity[0].text().split(' dB HL')[0]),
                        int(self.lbl_intencity[1].text().split(' dB HL')[0])]
                    freq = int(self.lbl_freq.text().split(' Hz')[0])
                    output = [self.lbl_output[0].text(), self.lbl_output[1].text()]
                    trans = [self.lbl_trans[0].text(), self.lbl_trans[1].text()]
                    continuo = [self.lbl_contin[0].text(),
                                self.lbl_contin[1].text()]

                    # se verifica de que canal proviene el tono
                    if stim[0] == 'Tono' and stim[1] != 'Tono':
                        ch = 0
                        response_true, faraway, LDL = test_response(
                            thr, freq, ch, lvl, output, trans)

                    if stim[0] != 'Tono' and stim[1] == 'Tono':
                        ch = 1
                        response_true, faraway, LDL = test_response(
                            thr, freq, ch, lvl, output, trans)
                    if stim[0] == 'Tono' and stim[1] == 'Tono':
                        ch = 0
                        response_true, faraway, LDL = test_response(
                            thr, freq, ch, lvl, output, trans)

                    # se ramdomiza la respuesta en las intensidades distantes
                    state_response, self.random_response, rise = random_response(
                        series=response_true, prev=prev, faraway=faraway)

                    if state_response:
                        self.time_var_response = [False, False, 0, rise, 500]
                        self.time_response.start(100)

                    if LDL:
                        voice_ldl = create_voice("molesta", self.gender, self.id)
                        if self.channel_on[0] == False:
                            self.channels[0].setSource(voice_ldl)
                            self.channels[0].play()
                        if self.channel_on[1] == False:
                            self.channels[1].setSource(voice_ldl)

                            self.channels[1].play()

                        self.lbl_response.setText("¡MOLESTA!")

            else:
                rise = random.randint(1, 8)*100
                self.time_var_response = [True, False, 0, 300, rise]
                self.time_response.start(100)
                self.lbl_response.setText("")



class CalculateLogo():
    def __init__(self, thr):
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