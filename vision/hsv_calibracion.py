import cv2
import numpy as np
from utils import obtener_fuente_video

def nada(x): pass

# 2. Configurar cámara
fuente = obtener_fuente_video() # Usa tu función de antes
cap = cv2.VideoCapture(fuente)

# Ventana y Trackbars
cv2.namedWindow("Calibracion")
cv2.createTrackbar("L - H", "Calibracion", 0, 179, nada)
cv2.createTrackbar("L - S", "Calibracion", 0, 255, nada)
cv2.createTrackbar("L - V", "Calibracion", 0, 255, nada)
cv2.createTrackbar("U - H", "Calibracion", 179, 179, nada)
cv2.createTrackbar("U - S", "Calibracion", 255, 255, nada)
cv2.createTrackbar("U - V", "Calibracion", 255, 255, nada)

print("\n--- INSTRUCCIONES ---")
print("1. Ajusta los sliders.")
print("2. Pulsa 'a' para fijar valores de AMARILLO (en memoria).")
print("3. Pulsa 'z' para fijar valores de AZUL (en memoria).")
print("4. Pulsa 's' para GUARDAR TODO en el archivo.")
print("5. Pulsa 'q' para salir.\n")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Opcional: Invertir si es necesario
    # frame = cv2.flip(frame, -1)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Leer sliders
    l_h = cv2.getTrackbarPos("L - H", "Calibracion")
    l_s = cv2.getTrackbarPos("L - S", "Calibracion")
    l_v = cv2.getTrackbarPos("L - V", "Calibracion")
    u_h = cv2.getTrackbarPos("U - H", "Calibracion")
    u_s = cv2.getTrackbarPos("U - S", "Calibracion")
    u_v = cv2.getTrackbarPos("U - V", "Calibracion")

    lower = np.array([l_h, l_s, l_v])
    upper = np.array([u_h, u_s, u_v])

    # Mostrar máscara en vivo
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("Calibracion", result)
    cv2.imshow("Original", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    
    elif key == ord('a'):
        am_min, am_max = lower, upper
        print(f"--> Amarillo actualizado en memoria (falta guardar 's')")
        
    elif key == ord('z'):
        az_min, az_max = lower, upper
        print(f"--> Azul actualizado en memoria (falta guardar 's')")

    elif key == ord('s'):
        # AQUÍ ES DONDE SE GUARDA EL ARCHIVO ÚNICO
        np.savez('colores_calibrados.npz', 
                 amarillo_min=am_min, amarillo_max=am_max,
                 azul_min=az_min, azul_max=az_max)
        print("\n✅ ¡ARCHIVO 'colores_calibrados.npz' GUARDADO CON ÉXITO!\n")

cap.release()
cv2.destroyAllWindows()