class caracteristicas():
    def __init__(self, other,app):
        self.other=other
        self.app = app
    
    def cal(self, other):
        return 25 + other + self.app
    
    def colore(self):
        return self.other.color
    
    
class caracteristicas2(caracteristicas):
    def __init__(self):
        super().__init__(self, app)
        self.color = "rojo"
        caracteristicas.__init__(self,self.color, 10)
        print(self.cal(10))
        print(self.colore)
        
test = caracteristicas2()