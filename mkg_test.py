## List attenuattions for each frequency
## (frequency, attenuation)
## (125,35)
## (250,40)
## (500,40)
## (1000,40)
## (2000,45)
## (3000,45)
## (4000,50)
## (6000,50)
## (8000,50)
attenuations_a = [35,40,40,40,45,45,50,50,50,100,100,100,100,100,100,100]
attenuations_o = [0 for _ in range(16)]

def mkg_calculate(l:list, a:list) -> list:
    new_list = []
    for idx, i in enumerate(l):
        new_set = [0,0]
        resto = abs(i[0]-i[1])
        if i[0] < i[1]:
            new_set[0] = i[0]
            idx_mayor = 1
        else:
            new_set[1] = i[1]
            idx_mayor = 0
            
        if resto >= a[idx]:
            #(EST-ATI) = resto
            # resto > 0
            # (ONE - resto) = EST_contra
            # est_contra > 0
            
            new_set[idx_mayor] = i[idx_mayor] - a[idx]
            

        else:
            new_set[idx_mayor] = i[idx_mayor]
        new_list.append(new_set)
    
    print(new_list)
            
               
        
        
        
lista = [[45,10],[45,10],[60,15],[60,15],[50,10],
        [55,10],[45,20],[40,20],[40,20],[50,50],
        [50,50],[50,50],[50,50],[50,50],[50,50]]

mkg_calculate(lista, attenuations_o)
    
    