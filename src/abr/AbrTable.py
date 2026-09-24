from PySide6.QtCore import QCoreApplication, Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QTableWidgetItem, QHeaderView
from abr.UI.AbrTableInfo_ui import Ui_TableData

tr = QCoreApplication.translate

class AbrTable(QWidget, Ui_TableData):
    sig_measure_value = Signal(dict)
    def __init__(self, side) -> None:
        QWidget.__init__(self)
        self.setupUi(self)
        self.side = side
        self.side_text = 'OD' if side == 0 else 'OI'
        # Rangos de normalidad de ESTE paciente a ESTA intensidad (los
        # entrega ABR_generator.normative_limits). Sin esto la tabla pinta
        # el fondo segun el oido y nada mas: no dice si una latencia esta
        # fuera de rango, que es justamente la lectura clinica.
        self.norms = None
        self.set_table()
        self.data =   [ ['', ''],
                        ['', ''],
                        ['', ''],
                        ['', ''],
                        ['', '']]

    def set_table(self)->None:
        tables = [self.tw_latamp, self.tw_inter]
        color = self.get_color_table()
        s = f"QTableWidget::item{{ background-color:{color}; }}"
        for i in tables:
            i.cellClicked.connect(self.on_cell_clicked)
            i.setStyleSheet(s)
            i.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            i.resizeColumnsToContents()
            i.setMaximumWidth(16777215)
            width = i.verticalHeader().width() + i.horizontalHeader().length() + 2 * i.frameWidth() + 2
            i.setMinimumWidth(width)

        self.label.setText(self.side_text)

    # ------------------------------------------------------------ normativa
    WAVE_ROWS = {'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4}
    # Filas de tw_inter, en el orden en que las llena calcule_others().
    INTER_ROWS = {'I-V': 0, 'III-V': 1, 'I-III': 2}
    RATIO_ROW = 3
    OUT_COLOR = QColor(255, 120, 120, 170)

    def set_norms(self, norms) -> None:
        """Fija los rangos normativos y repinta lo que ya este cargado."""
        self.norms = norms
        self.check_norms()

    def flag_cell(self, table, row, col, dentro, rango, unidad='ms') -> None:
        item = table.item(row, col)
        if item is None:
            return
        if dentro or rango is None:
            item.setBackground(QColor(0, 0, 0, 0))
            item.setToolTip('')
            return
        lo, hi = rango
        if lo is None:
            texto = f'esperado ≤ {hi:.2f} {unidad}'
        elif hi is None:
            texto = f'esperado ≥ {lo:.2f} {unidad}'
        else:
            texto = f'esperado {lo:.2f} – {hi:.2f} {unidad}'
        item.setBackground(self.OUT_COLOR)
        item.setToolTip(f'Fuera de rango: {texto}')

    @staticmethod
    def fmt(valor) -> str:
        # Un decimal en pantalla; self.data guarda el valor sin redondear
        # para los interpicos y la normativa.
        if not isinstance(valor, (int, float)):
            return ''
        return f'{valor:.1f}'

    @staticmethod
    def in_range(valor, rango) -> bool:
        lo, hi = rango
        if lo is not None and valor < lo:
            return False
        if hi is not None and valor > hi:
            return False
        return True

    def check_norms(self) -> None:
        """Marca latencias, interpicos y razon V/I fuera de rango."""
        if not self.norms:
            return
        latencias = self.norms.get('lat') or {}
        for wave, row in self.WAVE_ROWS.items():
            rango = latencias.get(wave)
            valor = self.data[row][0]
            if rango is None or not isinstance(valor, (int, float)):
                self.flag_cell(self.tw_latamp, row, 0, True, None)
                continue
            self.flag_cell(self.tw_latamp, row, 0,
                           self.in_range(valor, rango), rango)

        interpicos = self.norms.get('interpeak') or {}
        pares = {'I-V': (0, 4), 'III-V': (2, 4), 'I-III': (0, 2)}
        for clave, row in self.INTER_ROWS.items():
            rango = interpicos.get(clave)
            a, b = pares[clave]
            va, vb = self.data[a][0], self.data[b][0]
            if rango is None or not isinstance(va, (int, float)) or not isinstance(vb, (int, float)):
                self.flag_cell(self.tw_inter, row, 0, True, None)
                continue
            self.flag_cell(self.tw_inter, row, 0,
                           self.in_range(abs(vb - va), rango), rango)

        rango = self.norms.get('v_i_ratio')
        amp_i, amp_v = self.data[0][1], self.data[4][1]
        if rango and isinstance(amp_i, (int, float)) and isinstance(amp_v, (int, float)) and amp_i:
            self.flag_cell(self.tw_inter, self.RATIO_ROW, 0,
                           self.in_range(amp_v / amp_i, rango), rango, unidad='')
        else:
            self.flag_cell(self.tw_inter, self.RATIO_ROW, 0, True, None)

    def get_color_table(self) -> QColor:
        if self.side == 0:
            color = 'rgba(255, 0, 127, 30)'
        else:
            color = '#9965f4'
        return color

    def get_cols_rows(self, table) -> (int,int):
        cols = table.columnCount()
        rows = table.rowCount()
        return cols,rows

    def on_cell_clicked(self, row:int, column:int) -> None:
        table = self.sender().objectName()
        if table == 'tw_latamp':
            coord = (row, column)
            str_coords = self.curve_coord(coord)
            self.request_values(str_coords)

    def curve_coord(self, coord:str|tuple) -> str|tuple:
        coords_text =   [['I_L', 'I_A'],
                        ['II_L', 'II_A'],
                        ['III_L', 'III_A'],
                        ['IV_L', 'IV_A'],
                        ['V_L', 'V_A']]

        if isinstance(coord, str):
            for fila, lista in enumerate(coords_text):
                if coord in lista:
                    return (fila, lista.index(coord))
        else:
            return coords_text[coord[0]][coord[1]]

    def request_values(self, data:str) -> None:
        request = {f'{self.side}':{f'{data}':None}}
        self.sig_measure_value.emit(request)

    def set_data(self, data):
        command = list(data[str(self.side)].keys())[0]
        coords = self.curve_coord(command)
        value = data[str(self.side)][command]
        self.data[coords[0]][coords[1]] = value
        item = QTableWidgetItem(self.fmt(value))
        self.tw_latamp.setItem(coords[0], coords[1], item)
        #print(f"command {command} ,  row {coords[0]}, column {coords[1]}")
        self.calcule_others()

    def calcule_others(self)->None:
        ##I-V column 1, i:row 0 v:row 4
        ##III-V column 1, iii:row 2 v:row 4
        ##I-III column 1, i:row 0 iii:row 2
        if self.data[0][0] and self.data[4][0]:
            self.cal_interpeak(0,4,0)
        else:
            self.erase_cell(0)
        if self.data[2][0] and self.data[4][0]:
            self.cal_interpeak(2,4,1)
        else:
            self.erase_cell(1)
        if self.data[0][0] and self.data[2][0]:
            self.cal_interpeak(0,2,2)
        else:
            self.erase_cell(2)
        if self.data[0][1] and self.data[4][1]:
            self.cal_rel_v_i()
        else:
            self.erase_cell(3)
        self.check_norms()

    def reset_others(self)->None:
        if self.data[0][0] is None:
            self.tw_inter.setItem(0, 0, QTableWidgetItem(""))
            self.tw_inter.setItem(2, 0, QTableWidgetItem(""))
            self.tw_inter.setItem(3, 0, QTableWidgetItem(""))
        if self.data[2][0] is None:
            self.tw_inter.setItem(1, 0, QTableWidgetItem(""))
            self.tw_inter.setItem(2, 0, QTableWidgetItem(""))
        if self.data[4][0] is None:
            self.tw_inter.setItem(0, 0, QTableWidgetItem(""))
            self.tw_inter.setItem(1, 0, QTableWidgetItem(""))
            self.tw_inter.setItem(3, 0, QTableWidgetItem(""))
        if self.data[4][1] is None or self.data[0][1] is None:
            self.tw_inter.setItem(3, 0, QTableWidgetItem(""))

    def cal_rel_v_i(self,)->None:
        ##column 0, i:row 0 v:row 4
        value_i = self.data[0][1]
        value_v = self.data[4][1]
        relation = value_v/value_i
        item = QTableWidgetItem(self.fmt(relation))
        self.tw_inter.setItem(3,0, item)
        
    def erase_cell(self, cell) ->None:
        item = QTableWidgetItem("")
        self.tw_inter.setItem(cell,0, item)

    def cal_interpeak(self, pos_a:int, pos_b:int, cell:int) ->None:
        value_a = self.data[pos_a][0]
        value_b = self.data[pos_b][0]
        interpeak = abs(value_a - value_b)
        item = QTableWidgetItem(self.fmt(interpeak))
        self.tw_inter.setItem(cell,0, item)

    def change_value_lat(self, data:dict):
        for i in data:
            for t in data[i]:
                coord = self.curve_coord(f"{t}_L")
                if coord is None:
                    # Marca de otra prueba (el ECochG marca BL/PS/PA/FIN,
                    # que no son ondas): esta tabla no tiene donde ponerla.
                    continue
                if data[i][t] is None:
                    self.tw_latamp.setItem(coord[0], 0, QTableWidgetItem(""))
                    self.tw_latamp.setItem(coord[0], 1, QTableWidgetItem(""))
                    self.data[coord[0]][0] = None
                    self.data[coord[0]][1] = None
                # else: la marca sigue puesta, no hay nada que borrar.

                self.reset_others()

    def update_latamp_table(self, latamp_dict):
        # Mapeo de las ondas a las filas de la tabla
        wave_mapping = {
            'I': 0,
            'II': 1,
            'III': 2,
            'IV': 3,
            'V': 4
        }

        for wave, row_index in wave_mapping.items():
            # Obtener los valores de latencia y amplitud
            lat, amp = latamp_dict['LatAmp'][wave]
            # Crear los QTableWidgetItems, manejar valores None
            lat_item = QTableWidgetItem(self.fmt(lat))
            amp_item = QTableWidgetItem(self.fmt(amp))

            # Asignar los valores a la celda correspondiente en la fila y columna adecuada
            self.tw_latamp.setItem(row_index, 0, lat_item)  # Columna para latencia
            self.tw_latamp.setItem(row_index, 1, amp_item)  # Columna para amplitud
            self.data[row_index][0]=lat
            self.data[row_index][1]=amp

        self.calcule_others()


    def clear_all(self):
        tables = [self.tw_latamp, self.tw_inter]
        for table in tables:
            for row in range(table.rowCount()):
                for column in range(table.columnCount()):
                    # Opción 1: Eliminar el ítem (lo que podría eliminar también widgets incrustados)
                    #table.takeItem(row, column)
                    
                    # Opción 2: Establecer un ítem vacío
                    table.setItem(row, column, QTableWidgetItem(""))
        self.data =   [ ['', ''],
                        ['', ''],
                        ['', ''],
                        ['', ''],
                        ['', '']]
        self.calcule_others()



    def get_data(self):
        return self.data



        







def hex_to_rgba(hex_value):
###ya no lo uso pero lo dejare por aquí
    """
    Convierte un color en formato hexadecimal a una tupla RGBA.

    Argumentos:
    - hex_value (str): Color en formato hexadecimal. Debe empezar con '#' y puede ser de 7 o 9 caracteres
    (por ejemplo: #FF5733 o #AAFF5733).

    Retorna:
    - Tupla con cuatro valores int que representan los valores RGBA del color.
    """
    if len(hex_value) == 7:  # Formato #RRGGBB
        r = int(hex_value[1:3], 16)
        g = int(hex_value[3:5], 16)
        b = int(hex_value[5:7], 16)
        a = 255
    elif len(hex_value) == 9:  # Formato #AARRGGBB
        a = int(hex_value[1:3], 16)
        r = int(hex_value[3:5], 16)
        g = int(hex_value[5:7], 16)
        b = int(hex_value[7:9], 16)
    else:
        raise ValueError("El valor hexadecimal no tiene un formato válido.")
    
    return (r, g, b, a)

                
