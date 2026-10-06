import cv2
import numpy as np

# --- CONFIGURACIÓN ARUCO ---
ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKERS_CONFIG = {
    36: {"color": "Azul", "esquina": "top-left"},
    47: {"color": "Amarillo", "esquina": "top-right"},
    41: {"color": "Negro", "esquina": "bottom-left"},
}

# --- RANGOS DE COLOR ---
COLOR_PIEZAS = {
    "Azul": {
        "lower": np.array([85, 90, 50]), 
        "upper": np.array([125, 255, 255]), 
        "color_bgr": (255, 0, 0)
    },
    "Amarilla": {
        "lower": np.array([15, 100, 100]), 
        "upper": np.array([35, 255, 255]), 
        "color_bgr": (0, 255, 255)
    },
    "Negra": {
        "lower": np.array([0, 0, 0]), 
        "upper": np.array([180, 255, 50]),
        "color_bgr": (50, 50, 50)
    }
}

COLOR_ZONA = {
    "lower": np.array([35, 50, 50]),  
    "upper": np.array([85, 255, 255]),
    "color_bgr": (0, 255, 0)
}

def detectar_arucos(frame):
    """Detecta marcadores ArUco y devuelve sus esquinas y IDs"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    
    corners, ids, _ = detector.detectMarkers(gray)
    
    marcadores = {}
    if ids is not None:
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id in MARKERS_CONFIG:
                # Centro del marcador
                centro = corners[i][0].mean(axis=0)
                marcadores[marker_id] = {
                    'corners': corners[i][0],
                    'centro': centro,
                    'config': MARKERS_CONFIG[marker_id]
                }
    
    return marcadores

def obtener_transformacion_perspectiva(marcadores, frame_shape):
    """Crea transformación de perspectiva basada en ArUcos"""
    if len(marcadores) < 3:
        return None, None
    
    # Necesitas definir las posiciones esperadas de tus ArUcos
    # Ajusta estos valores según tu setup real
    ancho_deseado = 800
    alto_deseado = 600
    
    # Puntos destino (tablero rectificado)
    pts_destino = np.float32([
        [0, 0],                          # top-left
        [ancho_deseado, 0],              # top-right
        [0, alto_deseado],               # bottom-left
        [ancho_deseado, alto_deseado]    # bottom-right
    ])
    
    # Puntos origen (centros de ArUcos detectados)
    pts_origen = []
    orden_ids = [36, 47, 41]  # Ajusta según tu disposición
    
    for marker_id in orden_ids:
        if marker_id in marcadores:
            pts_origen.append(marcadores[marker_id]['centro'])
    
    if len(pts_origen) >= 3:
        # Si solo tienes 3 puntos, estima el 4to
        if len(pts_origen) == 3:
            # Calcula el 4to punto geométricamente
            pts_origen.append([
                pts_origen[1][0],
                pts_origen[2][1]
            ])
        
        pts_origen = np.float32(pts_origen)
        matriz = cv2.getPerspectiveTransform(pts_origen, pts_destino)
        return matriz, (ancho_deseado, alto_deseado)
    
    return None, None

def detectar_zonas_verdes(frame_hsv, frame_dibujo):
    """Detecta zonas verdes en imagen rectificada"""
    zonas_encontradas = []
    
    mask = cv2.inRange(frame_hsv, COLOR_ZONA["lower"], COLOR_ZONA["upper"])
    
    kernel = np.ones((10, 10), np.uint8) 
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 5000:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int32(box)
            
            zonas_encontradas.append(box)
            
            cv2.drawContours(frame_dibujo, [box], 0, (0, 255, 0), 2)
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(frame_dibujo, f"Z{i+1}", (cx-20, cy),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
    return zonas_encontradas

def detectar_piezas_y_contar(frame_hsv, frame_dibujo, zonas_verdes, conteo_global):
    """Detecta y cuenta piezas por color"""
    
    for nombre_pieza, valores in COLOR_PIEZAS.items():
        mask = cv2.inRange(frame_hsv, valores["lower"], valores["upper"])
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            min_area = 1000 if nombre_pieza == "Negra" else 500
            
            if area > min_area:
                M = cv2.moments(cnt)
                if M["m00"] == 0:
                    continue
                    
                centro_x = int(M["m10"] / M["m00"])
                centro_y = int(M["m01"] / M["m00"])
                centro_punto = (float(centro_x), float(centro_y))

                zona_id = -1
                texto_zona = ""
                
                for i, zona_contour in enumerate(zonas_verdes):
                    zona_float = zona_contour.astype(np.float32)
                    if cv2.pointPolygonTest(zona_float, centro_punto, False) >= 0:
                        zona_id = i
                        texto_zona = f"[Z{i+1}]"
                        conteo_global[i][nombre_pieza] += 1
                        break

                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(frame_dibujo, (x, y), (x+w, y+h), valores["color_bgr"], 2)
                cv2.circle(frame_dibujo, (centro_x, centro_y), 5, valores["color_bgr"], -1)
                cv2.putText(frame_dibujo, f"{nombre_pieza[:2]} {texto_zona}", (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, valores["color_bgr"], 2)

def mostrar_conteo_en_pantalla(frame, conteo_global, tiene_arucos):
    y_offset = 30
    
    # Indicador de estado
    estado = "CON ARUCOS ✓" if tiene_arucos else "SIN ARUCOS ✗"
    color = (0, 255, 0) if tiene_arucos else (0, 0, 255)
    cv2.putText(frame, estado, (10, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    y_offset += 35
    
    cv2.putText(frame, "--- CONTEO POR ZONA ---", (10, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    y_offset += 30
    
    for i, zona_data in conteo_global.items():
        texto = f"Z{i+1}: Az:{zona_data['Azul']} Am:{zona_data['Amarilla']} Ng:{zona_data['Negra']}"
        cv2.putText(frame, texto, (10, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 255, 200), 2)
        y_offset += 28

def procesar_video(cap):
    print("Iniciando detección...")
    print("Presiona 'q' para salir")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error leyendo frame")
            continue
            
        frame_out = frame.copy()
        
        # 1. DETECTAR ARUCOS
        marcadores = detectar_arucos(frame)
        
        # Dibujar ArUcos detectados
        for marker_id, data in marcadores.items():
            cv2.polylines(frame_out, [data['corners'].astype(int)], True, (0, 255, 255), 2)
            centro = tuple(data['centro'].astype(int))
            cv2.circle(frame_out, centro, 5, (0, 0, 255), -1)
            cv2.putText(frame_out, f"ID:{marker_id}", centro, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # 2. TRANSFORMACIÓN DE PERSPECTIVA (si hay suficientes ArUcos)
        matriz, tam_destino = obtener_transformacion_perspectiva(marcadores, frame.shape)
        
        if matriz is not None:
            # Usar vista rectificada
            frame_trabajo = cv2.warpPerspective(frame, matriz, tam_destino)
            frame_out = frame_trabajo.copy()
        else:
            # Usar vista original
            frame_trabajo = frame
        
        hsv_frame = cv2.cvtColor(frame_trabajo, cv2.COLOR_BGR2HSV)
        
        # 3. DETECCIÓN DE ZONAS Y PIEZAS
        zonas_contours = detectar_zonas_verdes(hsv_frame, frame_out)
        
        conteo_frame_actual = {}
        for i in range(len(zonas_contours)):
            conteo_frame_actual[i] = {"Azul": 0, "Amarilla": 0, "Negra": 0}

        detectar_piezas_y_contar(hsv_frame, frame_out, zonas_contours, conteo_frame_actual)

        # 4. MOSTRAR INFORMACIÓN
        mostrar_conteo_en_pantalla(frame_out, conteo_frame_actual, len(marcadores) >= 3)
        
        cv2.imshow('Detector con ArUco', frame_out)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    url = "http://10.248.210.42:4747/video"
    print(f"Intentando conectar a {url}...")
    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print("No se pudo conectar al stream, usando cámara local...")
        cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        print("Cámara conectada!")
        procesar_video(cap)
    else:
        print("Error: No se pudo abrir ninguna fuente de video")

if __name__ == "__main__":
    main()
