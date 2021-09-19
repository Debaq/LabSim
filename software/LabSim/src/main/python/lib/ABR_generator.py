import numpy as np
import bezier_prop as bz

class ABR_generator:
    def __init__(self):
        pass


    def ABR_Curve( curve_I, curve_III, curve_V ):
        sn10 = (curve_V[0]+1, curve_V[0])
        sn10_array = np.array(
                            [sn10[0] -0.2,sn10[1]],
                            [sn10[0]+ 0.4,sn10[1]],
                            [sn10[0]+ 1,0],
                            )
            
            _curves = ()
    
    def ABR_Int():
        pass

    curve_I = (1.3,.13)
    curve_Ip = (1.3,-.13)
    curve_II = ()
    curve_IIp = ()
    curve_III = (3.7,0.3)
    curve_IIIp = (3.7,0.3)
    curve_IV = ()
    curve_V = ()
    curve_V = (5.6,0.7)
    sn10 = (6.5,-.3)

    points = np.array([
            [0,0],
            [curve_I[0] - 0.5,0],
            [curve_I[0],curve_I[1]],
            [curve_I[0]+ 0.5,0],
        
            [curve_III[0] - 0.5,0],
            [curve_III[0],curve_III[1]],
            [curve_III[0]+ 0.5,0],
        
            [curve_V[0] - 0.5,0],
            [curve_V[0],curve_V[1]],
            [curve_V[0]+ 0.5,0],
        
            [sn10[0] -0.2,sn10[1]],
            [sn10[0]+ 0.4,sn10[1]],
            [sn10[0]+ 1,0],
            
    ])
    Bezi = bz.Bezier()
    path = Bezi.evaluate_bezier(points, 20)

    # extract x & y coordinates of points
    x, y = points[:,0], points[:,1]
    px, py = path[:,0], path[:,1]


    y_noise = np.random.normal(0, .01, py.shape)
    y_new = py + y_noise

