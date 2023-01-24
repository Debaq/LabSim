"""
necesito ayuda en la creación de una función que detecte el movimiento de la pupila en un video desde la webcam con python y opencv

Para detectar el movimiento de la pupila en un video desde la webcam con Python y OpenCV, puedes usar la función cv2.findContours(). Esta función encuentra los contornos en una imagen, que se pueden usar para detectar objetos específicos. Para detectar los contornos de la pupila, primero deberás obtener una imagen de la pupila desde la webcam. Esto puede hacerse usando la función cv2.VideoCapture(). Una vez que tengas la imagen, puedes usar la función cv2.findContours() para encontrar los contornos de la pupila. Una vez que hayas encontrado los contornos, puedes usar la función cv2.matchShapes() para detectar el movimiento de la pupila. Esta función toma dos contornos y determina la similitud entre ellos. 

me das un ejemplo

A continuación se muestra un ejemplo de cómo detectar el movimiento de la pupila usando la función cv2.findContours() y cv2.matchShapes() en Python y OpenCV. 
"""
# Importar OpenCV
import cv2

# Obtener imagen de la pupila desde la webcam
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

# Encontrar los contornos de la pupila
imgray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
ret, thresh = cv2.threshold(imgray, 127, 255, 0)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Comparar los contornos para detectar el movimiento
cnt1 = contours[0]
cnt2 = contours[1]

ret = cv2.matchShapes(cnt1, cnt2, 1, 0.0)

# Si la similitud es menor a 0.1, significa que la pupila se ha movido
if ret < 0.1:
    print("La pupila se ha movido")
else:
    print("La pupila no se ha movido")

# Liberar la webcam
cap.release()

"""

Para reducir el ruido y mejorar la captura cuando la persona parpadea, puedes usar la función cv2.GaussianBlur(). Esta función aplica un filtro Gaussiano a la imagen para suavizar el ruido. Esto puede mejorar la calidad de la imagen y hacer que sea más fácil de procesar. También puedes usar la función cv2.dilate() para dilatar los contornos de la pupila, lo que los hace más fáciles de detectar.

me das un ejemplo de uso 


A continuación se muestra un ejemplo de cómo usar la función cv2.GaussianBlur() y cv2.dilate() para reducir el ruido y mejorar la captura cuando la persona parpadea. 
"""
# Importar OpenCV
import cv2

# Obtener imagen de la pupila desde la webcam
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

# Aplicar filtro Gaussiano para suavizar el ruido
blur = cv2.GaussianBlur(frame, (5, 5), 0)

# Encontrar los contornos de la pupila
imgray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
ret, thresh = cv2.threshold(imgray, 127, 255, 0)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Dilatar los contornos para mejorar la detección
kernel = np.ones((5, 5), np.uint8)
dilate = cv2.dilate(thresh, kernel, iterations=1)

# Comparar los contornos para detectar el movimiento
cnt1 = contours[0]
cnt2 = contours[1]

ret = cv2.matchShapes(cnt1, cnt2, 1, 0.0)

# Si la similitud es menor a 0.1, significa que la pupila se ha movido
if ret < 0.1:
    print("La pupila se ha movido")
else:
    print("La pupila no se ha movido")

# Liberar la webcam
cap.release()
