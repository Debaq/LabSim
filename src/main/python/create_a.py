from UI.ui_Audimetry_create_profile import Ui_generator_audio
from PySide6.QtWidgets import QWidget, QSpinBox
import itertools


class CreateA(QWidget,Ui_generator_audio):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.btn_create.clicked.connect(self.create)
        self.chbox_peg_od.stateChanged.connect(self.equal_osea)
        self.chbox_peg_oi.stateChanged.connect(self.equal_osea)
        
        
    def create(self):
        letters = {"a":[],"o":[], "l":[]}
        side = ["od", "oi"]


        for l in letters:
            temp = [0,0]    

            for letter, n in itertools.product(l, range(9)):
                letter = "ldl" if letter == "l" else letter
                for s in side:
                    name = f"spbox_{letter}_{s}_{n}"
                    spin_obj = self.findChildren(QSpinBox, name)

                    if s == "od":
                        temp[0]=spin_obj[0].value()
                    else:
                        temp[1]=spin_obj[0].value()
                letters[l].append(temp)
        
        print(letters)
    
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
                    name_in = f"spbox_o_{side}_{n}"
                    spin_in = self.findChildren(QSpinBox, name_in)
                    spin_out = self.findChildren(QSpinBox, name_out)
                    spin_in[0].disconnect(self.equal_osea_invivo)
                    spin_out[0].setDisabled(False)

    def equal_osea_invivo(self,sender):
        _,_,side,n = self.sender().objectName().split("_")
        name_in = f"spbox_o_{side}_{n}"
        spin_out = self.findChildren(QSpinBox, name_in)
        spin_out[0].setValue(sender)

                
        
