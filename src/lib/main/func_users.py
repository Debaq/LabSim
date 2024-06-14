import xlrd
import cryptocode
from base import context


class XLSReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = {}

    def read_xls(self):
        file_path = context.get_resource(self.file_path)
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)

            
        for row in range(sheet.nrows):
            value_in_column_e = sheet.cell_value(row, 4).replace(" ", "")
            if value_in_column_e == "INSCRITO":  # Columna E
                columna_c = str(sheet.cell_value(row, 2)).lstrip('0').split('-')[0]  # Columna C
                columna_d = sheet.cell_value(row, 3).strip()# Columna D
                columna_f = sheet.cell_value(row, 5).strip()  # Columna F

                message = cryptocode.encrypt(columna_d, columna_c)
                self.data[columna_f.replace(";", "")] = { "key": message,"permission": 444,"modules": ["A", "Z"]}
                


    def get_data(self):
        return self.data

