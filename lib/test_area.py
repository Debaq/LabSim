
from math import sqrt

def flow(a1, a2,  p1,  p2,  d):
    num = 2*(p1-p2)
    den = d*(1-pow((a2/a1),2))
    t1= num/den
    return a2*sqrt(t1)
    


test = flow(2,1,2,1,1000)
list_p =[(2,1), (3,2), (7,6),(9,1),(10,5)] 
for i in list_p:
    print(flow(2,1,i[0], i[1], 1000))