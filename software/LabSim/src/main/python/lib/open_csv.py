import pandas as pd
from pandas.io.json import json_normalize  
import json  

ABC = ['A','B','C','D','E','F','G','H','I','J','K','L']

class dataFrame():
    
    def read(self, file, mime):
        if mime == 'csv':
            #print("file")

            self.data = pd.read_csv(file, header=None)
            numheaders = len(self.data.columns)
            self.newHeader=[]
            x = 0
            while x < numheaders:
                self.newHeader.append(ABC[x])
                x+=1

            self.data.columns = self.newHeader

        if mime == 'json':
            self.data = pd.read_json(file, orient='index')
            self.data = self.data.T
            


    def onlyColumn(self, column):
        column = self.data[column].tolist()
        return column
    
    def header(self):
        return self.data
    
    def column(self):
        return self.newHeader
    
    def numberCol(self):
        return len(self.newHeader)
    
    def array2d(self):
        return self.data.values.tolist()
        
        
        
"""
dicvalue={}

for x in newHeader:
    y = csv[x].tolist()
    dicvalue[x] = y



print(dicvalue['D'])


"""