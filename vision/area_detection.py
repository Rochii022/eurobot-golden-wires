import cv2
import numpy as np
import os

# Configuración de ArUco
ARUCO_DICT = cv2.aruco.DICT_4X4_50

# Definición de marcadores y sus tamaños
MARKERS_CONFIG = {
    36: {"color": "Azul", "size_mm": 40, "type": "campo"},
    47: {"color": "Amarillo", "size_mm": 40, "type": "campo"},
    41: {"color": "Negro", "size_mm": 40, "type": "campo"},
}

# Robots azules (1-5) y amarillos (6-10)
for i in range(1, 6):
    MARKERS_CONFIG[i] = {"color": "Robot Azul", "size_mm": 70, "type": "robot"}
for i in range(6, 11):
    MARKERS_CONFIG[i] = {"color": "Robot Amarillo", "size_mm": 70, "type": "robot"}

# Definición de áreas (cada área es un polígono de 4 puntos)
AREAS = [
    # Área 1
    [(594, 47), (588, 73), (698, 71), (694, 46)],
    # Área 2
    [(569, 147), (562, 199), (714, 198), (710, 147)],
    # Área 3
    [(239, 375), (120, 544), (420, 533), (476, 371)],
    # Área 4
    [(782, 370), (825, 533), (1130, 532), (1024, 369)],
    # Área 5
    [(1024, 141), (1077, 189), (1186, 183), (1143, 139)],
    # Área 6
    [(960, 37), (988, 67), (1098, 64), (1063, 39)],
]


def punto_en_poligono(punto, poligono):
    """
    Determina si un punto está dentro de un polígono usando el algoritmo de ray casting
    """
    x, y = punto
    n = len(poligono)
    inside = False
    
    p1x, p1y = poligono[0]
    for i in range(1, n + 1):
        p2x, p2y = poligono[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def detectar_area(centro, areas):
    """
    Detecta en qué área se encuentra un punto
    Retorna el índice del área (1-6) o None si no está en ninguna
    """
    for i, area in enumerate(areas):
        if punto_en_poligono(centro, area):
            return i + 1  # Retornamos 1-6 en lugar de 0-5
    return None


def generar_marcadores():
    """Genera todos los marcadores ArUco especificados"""
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    
    # Crear carpeta para los marcadores
    if not os.path.exists("marcadores_aruco"):
        os.makedirs("marcadores_aruco")
    
    print("Generando marcadores ArUco...")
    
    for marker_id, config in MARKERS_CONFIG.items():
        # Tamaño en píxeles (200px por defecto para buena calidad de impresión)
        marker_size = 200
        marker_image = np.zeros((marker_size, marker_size), dtype=np.uint8)
        marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size, marker_image, 1)
        
        # Añadir borde blanco y texto
        border = 50
        img_with_border = np.ones((marker_size + 2*border, marker_size + 2*border), dtype=np.uint8) * 255
        img_with_border[border:border+marker_size, border:border+marker_size] = marker_image
        
        # Añadir texto con información
        text = f"ID: {marker_id} - {config['color']}"
        size_text = f"Tamano: {config['size_mm']}mm"
        cv2.putText(img_with_border, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 0, 2)
        cv2.putText(img_with_border, size_text, (10, marker_size + 2*border - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, 0, 2)
        
        filename = f"marcadores_aruco/marker_{marker_id}_{config['color'].replace(' ', '_')}.png"
        cv2.imwrite(filename, img_with_border)
        print(f"  - Generado: {filename}")
    
    print(f"\n¡Marcadores generados en la carpeta 'marcadores_aruco'!")


def detectar_aruco():
    """Detecta marcadores ArUco en tiempo real desde la cámara"""
    # Inicializar cámara 
    url = f"http://10.194.148.249:4747/video"
    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print("Error: No se puede abrir la cámara")
        return
    
    # Configurar detector ArUco
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    
    print("\n=== Detector de ArUco Iniciado ===")
    print("Presiona 'q' para salir")
    print("Presiona 'a' para mostrar/ocultar áreas\n")
    
    mostrar_areas = True
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al leer frame")
            break
        
        # Dibujar las áreas definidas si está activado
        if mostrar_areas:
            for i, area in enumerate(AREAS):
                pts = np.array(area, np.int32)
                pts = pts.reshape((-1, 1, 2))
                # Dibujar polígono semi-transparente
                overlay = frame.copy()
                cv2.polylines(overlay, [pts], True, (0, 255, 0), 2)
                cv2.fillPoly(overlay, [pts], (0, 255, 0))
                cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
                
                # Añadir número de área
                centroid_x = int(np.mean([p[0] for p in area]))
                centroid_y = int(np.mean([p[1] for p in area]))
                cv2.putText(frame, f"Area {i+1}", (centroid_x - 40, centroid_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Detectar marcadores
        corners, ids, rejected = detector.detectMarkers(frame)
        
        # Si se detectan marcadores
        if ids is not None:
            # Dibujar marcadores detectados
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # Procesar cada marcador detectado
            for i, marker_id in enumerate(ids):
                marker_id = marker_id[0]
                
                # Verificar si el marcador está en nuestra configuración
                if marker_id in MARKERS_CONFIG:
                    config = MARKERS_CONFIG[marker_id]
                    
                    # Calcular centro del marcador
                    corner = corners[i][0]
                    center_x = int(np.mean(corner[:, 0]))
                    center_y = int(np.mean(corner[:, 1]))
                    
                    # Detectar en qué área está el marcador
                    area_id = detectar_area((center_x, center_y), AREAS)
                    
                    # Definir color según tipo
                    if config["color"] == "Azul":
                        color = (255, 0, 0)  # Azul en BGR
                    elif config["color"] == "Amarillo":
                        color = (0, 255, 255)  # Amarillo en BGR
                    elif config["color"] == "Negro":
                        color = (50, 50, 50)  # Gris oscuro en BGR
                    elif "Robot Azul" in config["color"]:
                        color = (255, 100, 0)  # Azul claro para robots
                    else:  # Robot Amarillo
                        color = (0, 200, 255)  # Amarillo claro para robots
                    
                    # Dibujar contorno grueso
                    pts = corner.reshape((-1, 1, 2)).astype(np.int32)
                    cv2.polylines(frame, [pts], True, color, 3)
                    
                    # Añadir texto con información (incluyendo área)
                    if area_id:
                        label = f"{config['color']} (ID:{marker_id}) - Area {area_id}"
                    else:
                        label = f"{config['color']} (ID:{marker_id}) - Fuera"
                    
                    # Fondo para el texto
                    (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, 
                                (center_x - text_width//2 - 5, center_y - 30),
                                (center_x + text_width//2 + 5, center_y - 5),
                                color, -1)
                    
                    # Texto
                    cv2.putText(frame, label, (center_x - text_width//2, center_y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
        # Mostrar información en pantalla
        cv2.putText(frame, "Presiona 'q' para salir | 'a' para areas", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Mostrar frame
        cv2.imshow('Detector ArUco - Competicion Robotica', frame)
        
        # Salir con 'q' o 'ESC'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q') or key == 27:  # 27 es ESC
            break
        elif key == ord('a') or key == ord('A'):
            mostrar_areas = not mostrar_areas
    
    cap.release()
    cv2.destroyAllWindows()


def main():
    print("=== Sistema de Detección ArUco para Competición de Robótica ===\n")
    print("Opciones:")
    print("1. Generar marcadores ArUco para imprimir")
    print("2. Iniciar detector en tiempo real")
    print("3. Hacer ambas cosas")
    
    opcion = input("\nSelecciona una opción (1/2/3): ").strip()
    
    if opcion == "1":
        generar_marcadores()
    elif opcion == "2":
        detectar_aruco()
    elif opcion == "3":
        generar_marcadores()
        print("\n")
        input("Presiona Enter para iniciar el detector...")
        detectar_aruco()
    else:
        print("Opción no válida")


if __name__ == "__main__":
    main()
