# LEGACY: creador de casos de escritorio (Python/PySide6). Se está
# reemplazando por labsim_backend/public/admin/case_create.php -- las
# funciones nuevas del modelo de caso (p.ej. tipo de curva de reflejo)
# se agregan ahí, no acá. No agregar features nuevas a este archivo.
from agenda.UI.ui_Audimetry_create_profile import Ui_generator_audio
from PySide6.QtWidgets import QWidget, QSpinBox, QMessageBox
from core.helpers import CreatePatient, CasesOffline, Shedule
from datetime import datetime
import itertools


def _parse_birth_year(date_str):
    """Año de nacimiento desde 'dd-mm-YYYY' (formato actual) o 'dd-mm-yy'
    (formato antiguo, ambiguo: solo 2 dígitos de año). Para el formato
    antiguo, si el año da en el futuro se asume el siglo anterior."""
    for fmt in ("%d-%m-%Y", "%d-%m-%y"):
        try:
            birth = datetime.strptime(date_str, fmt)
        except ValueError:
            continue
        year = birth.year
        if fmt == "%d-%m-%y" and year > datetime.now().year:
            year -= 100
        return year
    return None


HIST_CHECKBOXES = [
    "chbox_hist_hipoacusia_familiar",
    "chbox_hist_ototoxicos",
    "chbox_hist_trauma_acustico",
    "chbox_hist_otitis",
    "chbox_hist_meningitis",
    "chbox_hist_tce",
    "chbox_hist_diabetes",
    "chbox_hist_hta",
]


class CreateA(QWidget,Ui_generator_audio):
    def __init__(self, username, main_window) -> None:
        super().__init__()
        self.setupUi(self)
        self.username = username
        self.main_window = main_window
        self._name_parts = None
        self._edit_case_id = None
        self._edit_agenda_key = None
        self.btn_create.clicked.connect(self.create)
        self.btn_cancel.clicked.connect(self.cancel)
        self.pushButton.clicked.connect(self.generate_name)
        self.chbox_peg_od.stateChanged.connect(self.equal_osea)
        self.chbox_peg_oi.stateChanged.connect(self.equal_osea)
        self.chbox_ldl_od.stateChanged.connect(self.toggle_ldl)
        self.chbox_ldl_oi.stateChanged.connect(self.toggle_ldl)

        self._sdt_manual = [False, False]
        self._srt_manual = [False, False]
        self.spbox_sdt_od_0.valueChanged.connect(lambda: self._mark_manual(self._sdt_manual, 0))
        self.spbox_sdt_oi_0.valueChanged.connect(lambda: self._mark_manual(self._sdt_manual, 1))
        self.spbox_srt_od_0.valueChanged.connect(lambda: self._mark_manual(self._srt_manual, 0))
        self.spbox_srt_oi_0.valueChanged.connect(lambda: self._mark_manual(self._srt_manual, 1))
        for n in range(9):
            self.findChild(QSpinBox, f"spbox_a_od_{n}").valueChanged.connect(self._recalc_fletcher)
            self.findChild(QSpinBox, f"spbox_a_oi_{n}").valueChanged.connect(self._recalc_fletcher)

    def _mark_manual(self, flags, idx):
        flags[idx] = True

    def _air_pairs(self):
        return [
            [self.findChild(QSpinBox, f"spbox_a_od_{n}").value(),
             self.findChild(QSpinBox, f"spbox_a_oi_{n}").value()]
            for n in range(9)
        ]

    def _fletcher_avg(self, pairs):
        """Promedio de Fletcher: mejores 2 de 500/1000/2000 Hz (indices 2,3,4), igual que response.calc_sdt"""
        sublista = pairs[2:5]
        result = []
        for side in (0, 1):
            minimos = sorted(item[side] for item in sublista)[:2]
            promedio = sum(minimos) / len(minimos)
            result.append(int((promedio // 5) * 5))
        return result

    def _recalc_fletcher(self):
        fletcher = self._fletcher_avg(self._air_pairs())
        for idx, side in enumerate(("od", "oi")):
            if not self._sdt_manual[idx]:
                spin = getattr(self, f"spbox_sdt_{side}_0")
                spin.blockSignals(True)
                spin.setValue(fletcher[idx])
                spin.blockSignals(False)
            if not self._srt_manual[idx]:
                spin = getattr(self, f"spbox_srt_{side}_0")
                spin.blockSignals(True)
                spin.setValue(fletcher[idx])
                spin.blockSignals(False)

    def generate_name(self):
        gender = "men" if self.radioButton.isChecked() else "women"
        self._name_parts = CreatePatient().generar_nombre(gender)
        nombre1, nombre2, apellido1, apellido2, _ = self._name_parts
        self.led_name.setText(f"{nombre1} {nombre2} {apellido1} {apellido2}")

    def create(self):
        if self._edit_case_id is not None:
            try:
                self._save_edit()
            except Exception as e:
                # En modo backend esto empuja por red (case_upsert.php /
                # appointment_upsert.php) -- sin este catch, un timeout o un
                # 401 revienta el slot en silencio y el admin no se entera
                # de que el cambio no llegó al servidor.
                QMessageBox.critical(self, "Editar paciente", f"No se pudo guardar en el servidor:\n{e}")
            return

        if not self._name_parts:
            QMessageBox.warning(self, "Crear paciente", "Falta generar el nombre del paciente.")
            return

        letters = self._read_audiometry()
        extra = self._read_extra_tests()
        try:
            case_id = self._save_case(letters, extra)
            self._add_to_agenda(case_id)
        except Exception as e:
            QMessageBox.critical(self, "Crear paciente", f"No se pudo guardar en el servidor:\n{e}")
            return

        QMessageBox.information(self, "Crear paciente", f"Paciente {self.led_name.text()} creado. Queda pendiente de habilitar en la Agenda (fecha y hora).")
        self.reset_form()
        self.main_window.close_sub_window("CREATE_A")

    def cancel(self):
        """Cierra la ventana sin guardar el paciente actual"""
        self.reset_form()
        self.main_window.close_sub_window("CREATE_A")

    def reset_form(self):
        """Deja el formulario listo para crear el siguiente paciente"""
        self._name_parts = None
        self._edit_case_id = None
        self._edit_agenda_key = None
        self.btn_create.setText("Crear")
        self.led_name.clear()
        self.spinBox.setValue(self.spinBox.minimum())
        for chbox in (self.chbox_peg_od, self.chbox_peg_oi, self.chbox_ldl_od, self.chbox_ldl_oi,
                      self.chbox_recrut_od, self.chbox_recrut_oi, self.chbox_det_od, self.chbox_det_oi,
                      self.chbox_stenger_od, self.chbox_stenger_oi):
            chbox.setChecked(False)
        for spin in self.findChildren(QSpinBox):
            if spin.objectName().startswith("spbox_"):
                spin.setValue(spin.minimum())
        self.spbox_fowler_cut_1.setValue(15)
        self.spbox_fowler_cut_2.setValue(30)
        self.spbox_fowler_cut_3.setValue(50)
        self.cb_fowler_freq.setCurrentIndex(0)
        self.cb_z_od.setCurrentIndex(0)
        self.cb_z_oi.setCurrentIndex(0)
        self.cb_etf_od.setCurrentIndex(0)
        self.cb_etf_oi.setCurrentIndex(0)
        for name in HIST_CHECKBOXES:
            getattr(self, name).setChecked(False)
        self.led_medicamentos.clear()
        self.led_cirugias.clear()
        self.txt_otros_antecedentes.clear()
        self._sdt_manual = [False, False]
        self._srt_manual = [False, False]

    # TODO: limpiar -- sin llamadas desde la app tras sacar "Ver/Editar" de
    # Agenda.py (la gestión de pacientes/casos ahora vive solo en el backend web).
    def load_for_edit(self, case_id, agenda_key, agenda_row):
        """Carga un paciente existente en el formulario para verlo/editarlo"""
        cases = CasesOffline().get_cases()
        case = cases.get(case_id)
        print(f"[create_a] load_for_edit case_id={case_id!r} (type={type(case_id).__name__}) "
              f"cases_keys_sample={list(cases.keys())[:10]!r} found={case is not None} "
              f"Anamnesis={case.get('Anamnesis') if case else None!r}")
        if case is None:
            QMessageBox.warning(self, "Editar paciente", "El caso ya no existe.")
            return

        self.reset_form()
        self._edit_case_id = case_id
        self._edit_agenda_key = agenda_key

        self.led_name.setText(f"{agenda_row[3]} {agenda_row[4]}".strip())
        self.radioButton.setChecked(case.get("gender") == 0)
        self.radioButton_2.setChecked(case.get("gender") != 0)

        try:
            birth_year = _parse_birth_year(agenda_row[5])
            if birth_year is None:
                raise ValueError
            age = datetime.now().year - birth_year
        except (ValueError, IndexError):
            age = self.spinBox.minimum()
        self.spinBox.setValue(max(age, self.spinBox.minimum()))

        self._load_audiometry(case)
        self._load_extra_tests(case)

        self.chbox_ldl_od.setChecked(True)
        self.chbox_ldl_oi.setChecked(True)
        self.chbox_recrut_od.setChecked(bool(case.get("recruit", [False, False])[0]))
        self.chbox_recrut_oi.setChecked(bool(case.get("recruit", [False, False])[1]))
        self.chbox_det_od.setChecked(bool(case.get("decay", [False, False])[0]))
        self.chbox_det_oi.setChecked(bool(case.get("decay", [False, False])[1]))
        self.cb_z_od.setCurrentText(case.get("Z_OD", "A"))
        self.cb_z_oi.setCurrentText(case.get("Z_OI", "A"))

        etf = case.get("ETF", ["Normal", "Normal"])
        self.cb_etf_od.setCurrentText(etf[0])
        self.cb_etf_oi.setCurrentText(etf[1])

        self.btn_create.setText("Guardar cambios")

    def _save_edit(self):
        cases_store = CasesOffline()
        cases = cases_store.get_cases()
        case = cases.get(self._edit_case_id)
        if case is None:
            QMessageBox.warning(self, "Editar paciente", "El caso ya no existe.")
            self.reset_form()
            return

        letters = self._read_audiometry()
        extra = self._read_extra_tests()

        gender = 0 if self.radioButton.isChecked() else 1
        age = self.spinBox.value()
        case["gender"] = gender
        case["volume"] = [CreatePatient().ear_volume(age, gender), CreatePatient().ear_volume(age, gender), "N/D"]
        case["Aerea"] = letters["a"]
        case["Osea"] = letters["o"]
        case["LDL"] = letters["l"]
        case["Aerea_mkg"] = letters["a"]
        case["Osea_mkg"] = letters["o"]
        case["Z_OD"] = self.cb_z_od.currentText()
        case["Z_OI"] = self.cb_z_oi.currentText()
        case["SDT"] = extra["SDT"]
        case["SRT"] = extra["SRT"]
        case["UMD"] = extra["UMD"]
        case["recruit"] = [self.chbox_recrut_od.isChecked(), self.chbox_recrut_oi.isChecked()]
        case["decay"] = [self.chbox_det_od.isChecked(), self.chbox_det_oi.isChecked()]
        case["Fowler"] = extra["Fowler"]
        case["Stenger"] = extra["Stenger"]
        case["SISI"] = extra["SISI"]
        case["Reflex"] = extra["Reflex"]
        case["ETF"] = [self.cb_etf_od.currentText(), self.cb_etf_oi.currentText()]
        case["Anamnesis"] = extra["Anamnesis"]

        cases[self._edit_case_id] = case
        cases_store.set_cases(cases)

        shedule = Shedule()
        row = shedule.data.get("agenda_1", {}).get(self._edit_agenda_key)
        if row is not None:
            if self._name_parts:
                nombre1, nombre2, apellido1, apellido2, _ = self._name_parts
                row[3] = f"{nombre1} {nombre2}"
                row[4] = f"{apellido1} {apellido2}"
            age = self.spinBox.value()
            birth_year = datetime.now().year - age
            row[5] = f"01-01-{birth_year:04d}"
            shedule.set(shedule.data)

        QMessageBox.information(self, "Editar paciente", f"Paciente {self.led_name.text()} actualizado.")
        self.reset_form()
        self.main_window.close_sub_window("CREATE_A")

        agenda_win = self.main_window.subw.get("AGENDA")
        if agenda_win is not None:
            agenda_win.obj.refresh()

    def _read_audiometry(self):
        letters = {"a":[],"o":[], "l":[]}
        side = ["od", "oi"]

        for l in letters:
            for letter, n in itertools.product(l, range(9)):
                temp = [0,0]
                letter_name = "ldl" if letter == "l" else letter
                for s in side:
                    name = f"spbox_{letter_name}_{s}_{n}"
                    spin_obj = self.findChildren(QSpinBox, name)

                    if s == "od":
                        temp[0]=spin_obj[0].value()
                    else:
                        temp[1]=spin_obj[0].value()
                letters[l].append(temp)

        return letters

    def _load_audiometry(self, case):
        letters = {"a": case.get("Aerea", []), "o": case.get("Osea", []), "l": case.get("LDL", [])}
        side = ["od", "oi"]

        for letter, values in letters.items():
            letter_name = "ldl" if letter == "l" else letter
            for n in range(9):
                temp = values[n] if n < len(values) else [130, 130]
                for s_idx, s in enumerate(side):
                    name = f"spbox_{letter_name}_{s}_{n}"
                    spin_obj = self.findChildren(QSpinBox, name)
                    if spin_obj:
                        spin_obj[0].setValue(temp[s_idx])

    def _read_extra_tests(self):
        return {
            "SDT": [self.spbox_sdt_od_0.value(), self.spbox_sdt_oi_0.value()],
            "SRT": [self.spbox_srt_od_0.value(), self.spbox_srt_oi_0.value()],
            "UMD": [
                {"int": self.spbox_umd_od_0.value(), "percentage": self.spbox_umd_od_1.value()},
                {"int": self.spbox_umd_oi_0.value(), "percentage": self.spbox_umd_oi_1.value()},
            ],
            "Fowler": {
                "freq": self.cb_fowler_freq.currentIndex(),
                "cuts": [self.spbox_fowler_cut_1.value(), self.spbox_fowler_cut_2.value(),
                         self.spbox_fowler_cut_3.value()],
            },
            "Stenger": [self.chbox_stenger_od.isChecked(), self.chbox_stenger_oi.isChecked()],
            "SISI": [self.spbox_sisi_od.value(), self.spbox_sisi_oi.value()],
            "Reflex": self._read_reflex(),
            "Anamnesis": self._read_anamnesis(),
        }

    def _load_extra_tests(self, case):
        sdt = case.get("SDT", [0, 0])
        srt = case.get("SRT", [0, 0])
        for idx, side in enumerate(("od", "oi")):
            sdt_spin = getattr(self, f"spbox_sdt_{side}_0")
            srt_spin = getattr(self, f"spbox_srt_{side}_0")
            # si el valor guardado no calza con el Fletcher ya recalculado desde
            # los umbrales tonales recien cargados, es porque el docente lo
            # sobrescribio a mano: se respeta y se bloquea el autocalculo
            self._sdt_manual[idx] = sdt[idx] != sdt_spin.value()
            self._srt_manual[idx] = srt[idx] != srt_spin.value()
            sdt_spin.blockSignals(True)
            sdt_spin.setValue(sdt[idx])
            sdt_spin.blockSignals(False)
            srt_spin.blockSignals(True)
            srt_spin.setValue(srt[idx])
            srt_spin.blockSignals(False)
        umd = case.get("UMD", [{"int": 35, "percentage": 100}, {"int": 35, "percentage": 100}])
        self.spbox_umd_od_0.setValue(umd[0]["int"])
        self.spbox_umd_od_1.setValue(umd[0]["percentage"])
        self.spbox_umd_oi_0.setValue(umd[1]["int"])
        self.spbox_umd_oi_1.setValue(umd[1]["percentage"])

        fowler = case.get("Fowler", {"freq": 0, "cuts": [15, 30, 50]})
        if not isinstance(fowler, dict):
            # formato viejo (lista): se muestra el default, el docente lo reconfigura y se migra al guardar
            fowler = {"freq": 0, "cuts": [15, 30, 50]}
        self.cb_fowler_freq.setCurrentIndex(fowler.get("freq") or 0)
        cuts = fowler.get("cuts", [15, 30, 50])
        self.spbox_fowler_cut_1.setValue(cuts[0])
        self.spbox_fowler_cut_2.setValue(cuts[1])
        self.spbox_fowler_cut_3.setValue(cuts[2])

        stenger = case.get("Stenger", [False, False])
        self.chbox_stenger_od.setChecked(bool(stenger[0]))
        self.chbox_stenger_oi.setChecked(bool(stenger[1]))

        sisi = case.get("SISI", [0, 0])
        self.spbox_sisi_od.setValue(sisi[0])
        self.spbox_sisi_oi.setValue(sisi[1])

        self._load_reflex(case)
        self._load_anamnesis(case)

    def _read_anamnesis(self):
        antecedentes = {
            name[len("chbox_hist_"):]: getattr(self, name).isChecked()
            for name in HIST_CHECKBOXES
        }
        return {
            "antecedentes": antecedentes,
            "medicamentos": self.led_medicamentos.text(),
            "cirugias": self.led_cirugias.text(),
            "otros": self.txt_otros_antecedentes.toPlainText(),
        }

    def _load_anamnesis(self, case):
        anamnesis = case.get("Anamnesis", {})
        antecedentes = anamnesis.get("antecedentes", {})
        for name in HIST_CHECKBOXES:
            key = name[len("chbox_hist_"):]
            getattr(self, name).setChecked(bool(antecedentes.get(key, False)))
        self.led_medicamentos.setText(anamnesis.get("medicamentos", ""))
        self.led_cirugias.setText(anamnesis.get("cirugias", ""))
        self.txt_otros_antecedentes.setPlainText(anamnesis.get("otros", ""))

    # Frecuencias por modo: contra suma WN (ruido blanco, índice 4), ipsi no se toma con WN.
    REFLEX_COUNTS = {"ipsi": 4, "contra": 5}

    def _read_reflex(self):
        """Umbrales de reflejos acústicos (dB HL) por frecuencia (500/1000/2000/4000 Hz + WN
        en contra), modo (ipsi/contra) y oído. 130 = ausente, mismo criterio que LDL/UMD."""
        reflex = {"ipsi": [], "contra": []}
        side = ["od", "oi"]
        for mode, count in self.REFLEX_COUNTS.items():
            for n in range(count):
                temp = [0, 0]
                for s_idx, s in enumerate(side):
                    name = f"spbox_reflex_{mode}_{s}_{n}"
                    spin_obj = self.findChildren(QSpinBox, name)
                    if spin_obj:
                        temp[s_idx] = spin_obj[0].value()
                reflex[mode].append(temp)
        return reflex

    def _load_reflex(self, case):
        defaults = {mode: [[130, 130]] * count for mode, count in self.REFLEX_COUNTS.items()}
        reflex = case.get("Reflex", defaults)
        side = ["od", "oi"]
        for mode, count in self.REFLEX_COUNTS.items():
            values = reflex.get(mode, defaults[mode])
            for n in range(count):
                temp = values[n] if n < len(values) else [130, 130]
                for s_idx, s in enumerate(side):
                    name = f"spbox_reflex_{mode}_{s}_{n}"
                    spin_obj = self.findChildren(QSpinBox, name)
                    if spin_obj:
                        spin_obj[0].setValue(temp[s_idx])

    def _save_case(self, letters, extra):
        cases_store = CasesOffline()
        cases = cases_store.get_cases()
        next_id = str(max((int(k) for k in cases), default=0) + 1)

        gender = 0 if self.radioButton.isChecked() else 1
        age = self.spinBox.value()
        patient = CreatePatient()

        cases[next_id] = {
            "gender": gender,
            "id": int(next_id),
            "Aerea": letters["a"],
            "Osea": letters["o"],
            "LDL": letters["l"],
            "Aerea_mkg": letters["a"],
            "Osea_mkg": letters["o"],
            "Z_OD": self.cb_z_od.currentText(),
            "Z_OI": self.cb_z_oi.currentText(),
            "sector": "Camara_sono",
            "volume": [patient.ear_volume(age, gender), patient.ear_volume(age, gender), "N/D"],
            "UMD": extra["UMD"],
            "SDT": extra["SDT"],
            "SRT": extra["SRT"],
            "Fowler": extra["Fowler"],
            "Stenger": extra["Stenger"],
            "SISI": extra["SISI"],
            "box": "Box_1",
            "result": 1,
            "state_login": 1,
            "recruit": [self.chbox_recrut_od.isChecked(), self.chbox_recrut_oi.isChecked()],
            "decay": [self.chbox_det_od.isChecked(), self.chbox_det_oi.isChecked()],
            "Reflex": extra["Reflex"],
            "ETF": [self.cb_etf_od.currentText(), self.cb_etf_oi.currentText()],
            "Anamnesis": extra["Anamnesis"],
            "tipo": "normal",
        }
        cases_store.set_cases(cases)
        return next_id

    def _add_to_agenda(self, case_id):
        nombre1, nombre2, apellido1, apellido2, _ = self._name_parts
        age = self.spinBox.value()
        today = datetime.now()
        birth_year = today.year - age

        shedule = Shedule()
        agenda = shedule.data.setdefault("agenda_1", {})
        next_row = str(max((int(k) for k in agenda), default=-1) + 1)

        ruts_existentes = {row[2] for row in agenda.values() if len(row) > 2}
        patient = CreatePatient()
        rut = str(patient.rut_from_age(age))
        while rut in ruts_existentes:
            rut = str(patient.rut_from_age(age))

        agenda[next_row] = [
            "",
            "",
            rut,
            f"{nombre1} {nombre2}",
            f"{apellido1} {apellido2}",
            f"01-01-{birth_year:04d}",
            "Audiometría",
            case_id,
            {},
        ]
        shedule.set(shedule.data)

        agenda_win = self.main_window.subw.get("AGENDA")
        if agenda_win is not None:
            agenda_win.obj.refresh()

    def equal_osea(self, sender):
        _,_,side = self.sender().objectName().split("_")
        if sender == 2:
            for n in range(9):
                name_in = f"spbox_a_{side}_{n}"
                name_out = f"spbox_o_{side}_{n}"
                spin_in = self.findChildren(QSpinBox, name_in)
                spin_out = self.findChildren(QSpinBox, name_out)
                spin_in[0].valueChanged.connect(self.equal_osea_invivo)
                spin_out[0].setDisabled(True)
                spin_out[0].setValue(spin_in[0].value())
        if sender == 0:
                for n in range(9):
                    name_out = f"spbox_o_{side}_{n}"
                    name_in = f"spbox_a_{side}_{n}"
                    spin_in = self.findChildren(QSpinBox, name_in)
                    spin_out = self.findChildren(QSpinBox, name_out)
                    spin_in[0].disconnect(self.equal_osea_invivo)
                    spin_out[0].setDisabled(False)

    def equal_osea_invivo(self,sender):
        _,_,side,n = self.sender().objectName().split("_")
        name_in = f"spbox_o_{side}_{n}"
        spin_out = self.findChildren(QSpinBox, name_in)
        spin_out[0].setValue(sender)

    def toggle_ldl(self, state):
        _,_,side = self.sender().objectName().split("_")
        enabled = state == 2
        for n in range(9):
            name = f"spbox_ldl_{side}_{n}"
            spin = self.findChildren(QSpinBox, name)
            spin[0].setEnabled(enabled)

                
        
