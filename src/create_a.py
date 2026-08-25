from UI.ui_Audimetry_create_profile import Ui_generator_audio
from PySide6.QtWidgets import QWidget, QSpinBox, QMessageBox
from lib.helpers import CreatePatient, CasesOffline, Shedule
from datetime import datetime
import itertools


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

    def generate_name(self):
        gender = "men" if self.radioButton.isChecked() else "women"
        self._name_parts = CreatePatient().generar_nombre(gender)
        nombre1, nombre2, apellido1, apellido2, _ = self._name_parts
        self.led_name.setText(f"{nombre1} {nombre2} {apellido1} {apellido2}")

    def create(self):
        if self._edit_case_id is not None:
            self._save_edit()
            return

        if not self._name_parts:
            QMessageBox.warning(self, "Crear paciente", "Falta generar el nombre del paciente.")
            return

        letters = self._read_audiometry()
        extra = self._read_extra_tests()
        case_id = self._save_case(letters, extra)
        self._add_to_agenda(case_id)

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
                      self.chbox_recrut_od, self.chbox_recrut_oi, self.chbox_det_od, self.chbox_det_oi):
            chbox.setChecked(False)
        for spin in self.findChildren(QSpinBox):
            if spin.objectName().startswith("spbox_"):
                spin.setValue(spin.minimum())
        self.cb_z_od.setCurrentIndex(0)
        self.cb_z_oi.setCurrentIndex(0)

    def load_for_edit(self, case_id, agenda_key, agenda_row):
        """Carga un paciente existente en el formulario para verlo/editarlo"""
        case = CasesOffline().get_cases().get(case_id)
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
            birth = datetime.strptime(agenda_row[5], "%d-%m-%y")
            age = datetime.now().year - birth.year
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

        case["gender"] = 0 if self.radioButton.isChecked() else 1
        case["Aerea"] = letters["a"]
        case["Osea"] = letters["o"]
        case["LDL"] = letters["l"]
        case["Aerea_mkg"] = letters["a"]
        case["Osea_mkg"] = letters["o"]
        case["Z_OD"] = self.cb_z_od.currentText()
        case["Z_OI"] = self.cb_z_oi.currentText()
        case["SDT"] = extra["SDT"]
        case["UMD"] = extra["UMD"]
        case["recruit"] = [self.chbox_recrut_od.isChecked(), self.chbox_recrut_oi.isChecked()]
        case["decay"] = [self.chbox_det_od.isChecked(), self.chbox_det_oi.isChecked()]

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
            row[5] = f"01-01-{birth_year % 100:02d}"
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
            "UMD": [
                {"int": self.spbox_umd_od_0.value(), "percentage": self.spbox_umd_od_1.value()},
                {"int": self.spbox_umd_oi_0.value(), "percentage": self.spbox_umd_oi_1.value()},
            ],
        }

    def _load_extra_tests(self, case):
        sdt = case.get("SDT", [0, 0])
        self.spbox_sdt_od_0.setValue(sdt[0])
        self.spbox_sdt_oi_0.setValue(sdt[1])
        umd = case.get("UMD", [{"int": 35, "percentage": 100}, {"int": 35, "percentage": 100}])
        self.spbox_umd_od_0.setValue(umd[0]["int"])
        self.spbox_umd_od_1.setValue(umd[0]["percentage"])
        self.spbox_umd_oi_0.setValue(umd[1]["int"])
        self.spbox_umd_oi_1.setValue(umd[1]["percentage"])

    def _save_case(self, letters, extra):
        cases_store = CasesOffline()
        cases = cases_store.get_cases()
        next_id = str(max((int(k) for k in cases), default=0) + 1)

        cases[next_id] = {
            "gender": 0 if self.radioButton.isChecked() else 1,
            "id": int(next_id),
            "Aerea": letters["a"],
            "Osea": letters["o"],
            "LDL": letters["l"],
            "Aerea_mkg": letters["a"],
            "Osea_mkg": letters["o"],
            "Z_OD": self.cb_z_od.currentText(),
            "Z_OI": self.cb_z_oi.currentText(),
            "sector": "Camara_sono",
            "volume": [0, 0, "N/D"],
            "UMD": extra["UMD"],
            "SDT": extra["SDT"],
            "Fowler": [[], 0, 0],
            "Carhart": [False, False],
            "box": "Box_1",
            "result": 1,
            "state_login": 1,
            "recruit": [self.chbox_recrut_od.isChecked(), self.chbox_recrut_oi.isChecked()],
            "decay": [self.chbox_det_od.isChecked(), self.chbox_det_oi.isChecked()],
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
        agenda[next_row] = [
            "",
            "",
            str(CreatePatient().rut_from_age(age)),
            f"{nombre1} {nombre2}",
            f"{apellido1} {apellido2}",
            f"01-01-{birth_year % 100:02d}",
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

                
        
