'''
Este código es para correr en WINDOWS. Detección de ArUcos en el campo, pero detección de colores SOLO dentro de las áreas definidas.
'''

import cv2
import numpy as np
import os
from utils import obtener_fuente_video, cargar_colores_calibrados

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

# Definición de áreas
AREAS_AMARILLO = [
    [(599, 138), (595, 166), (681, 166), (682, 138)],   # Área 1
    [(943, 137), (967, 165), (1053, 166), (1026, 137)], # Área 2
    [(579, 268), (570, 326), (696, 325), (690, 269)],   # Área 3
    [(998, 268), (1041, 325), (1164, 325), (1110, 268)],# Área 4
    [(250, 649), (305, 536), (477, 535), (452, 652)],   # Área 5
    [(786, 652), (771, 539), (954, 539), (999, 656)],   # Área 6
]

AREAS_AZUL = [
    [(620, 132), (617, 159), (706, 160), (701, 131)],   # Área 1
    [(279, 130), (250, 157), (334, 159), (359, 131)],   # Área 2
    [(610, 262), (605, 315), (731, 316), (723, 261)],   # Área 3
    [(192, 260), (140, 314), (263, 317), (304, 259)],   # Área 4
    [(304, 636), (353, 524), (531, 526), (513, 637)],   # Área 5
    [(858, 638), (829, 525), (1007, 524), (1063, 640)], # Área 6
]

AREAS = {
    "amarillo": AREAS_AMARILLO,
    "azul": AREAS_AZUL
}

def punto_en_poligono(punto, poligono):
    """ Determina si un punto está dentro de un polígono """
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
    """ Retorna el índice del área (1-6) o None si no está en ninguna """
    for i, area in enumerate(areas):
        if punto_en_poligono(centro, area):
            return i + 1
    return None

def procesar_color(frame, mask, nombre_color, color_bgr, areas):
    """
    Busca contornos de color, pero SOLO los dibuja si están DENTRO de un área.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        area_pixel = cv2.contourArea(cnt)
        
        if area_pixel > 500: # Filtro de ruido
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                # 1. Comprobamos dónde está el objeto
                area_id = detectar_area((cX, cY), areas)
                
                # 2. FILTRO CLAVE: Solo procesamos si area_id NO es None
                if area_id is not None:
                    # Dibujar contorno y centro
                    cv2.drawContours(frame, [cnt], -1, color_bgr, 2)
                    cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)
                    
                    # Etiqueta (Ya sabemos que está dentro)
                    texto = f"{nombre_color} - A{area_id}"
                    
                    cv2.putText(frame, texto, (cX - 20, cY - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

def detection(color_equipo, url):
    """Detecta ArUcos en todo el campo y Colores SOLO en las áreas"""
    
    colores_hsv = cargar_colores_calibrados()
    
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("Error: No se puede abrir la cámara")
        return
    
    # ========== OPTIMIZACIONES CRÍTICAS ==========
    # 1. Reduce el buffer de la cámara (elimina lag acumulado)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # 2. Opcional: reduce resolución si no necesitas máxima calidad
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    
    print("\n=== Detector Iniciado ===")
    
    mostrar_areas = False  # Desactivado por defecto para mejor rendimiento
    
    # Pre-convertir áreas a numpy para dibujo más rápido
    areas = AREAS[color_equipo]
    areas_np = [np.array(area, np.int32).reshape((-1, 1, 2)) for area in areas]
    
    # Pre-crear overlay una sola vez (reutilizable)
    overlay = None
    
    while True:
        ret, frame = cap.read()
        if not ret: 
            break
        
        if (color_equipo == "azul"):
            frame = cv2.flip(frame, -1)

        # --- DIBUJAR ÁREAS VISUALMENTE (OPTIMIZADO) ---
        if mostrar_areas:
            # Crear overlay solo cuando cambia el estado
            if overlay is None:
                overlay = frame.copy()
                for i, pts in enumerate(areas_np):
                    # 1. Dibujar borde verde
                    cv2.polylines(overlay, [pts], True, (0, 255, 0), 2)
                    
                    # 2. Rellenar de verde
                    cv2.fillPoly(overlay, [pts], (0, 255, 0))
                    
                    # Texto de área
                    area = areas[i]
                    cx_a = int(np.mean([p[0] for p in area]))
                    cy_a = int(np.mean([p[1] for p in area]))
                    cv2.putText(overlay, f"A{i+1}", (cx_a-20, cy_a), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Mezclar con transparencia
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
        else:
            overlay = None  # Resetear cuando se desactiva

        # --- PROCESAMIENTO DE COLOR (solo si es necesario) ---
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Aplicar un blur ligero para reducir ruido (mejora rendimiento de findContours)
        hsv = cv2.GaussianBlur(hsv, (5, 5), 0)
        
        mask_amarillo = cv2.inRange(hsv, colores_hsv['amarillo_min'], colores_hsv['amarillo_max'])
        procesar_color(frame, mask_amarillo, "Muestra Am.", (0, 255, 255), areas)
        
        mask_azul = cv2.inRange(hsv, colores_hsv['azul_min'], colores_hsv['azul_max'])
        procesar_color(frame, mask_azul, "Muestra Az.", (255, 100, 0), areas)

        # --- DETECTAR ARUCOS (En todo el frame) ---
        corners, ids, rejected = detector.detectMarkers(frame)
        
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            for i, marker_id in enumerate(ids):
                marker_id = marker_id[0]
                if marker_id in MARKERS_CONFIG:
                    config = MARKERS_CONFIG[marker_id]
                    
                    # Calcular centro
                    c = corners[i][0]
                    cx = int(np.mean(c[:, 0]))
                    cy = int(np.mean(c[:, 1]))
                    
                    # Ver dónde está (solo para informar)
                    area_id = detectar_area((cx, cy), areas)
                    
                    # Colores de dibujo
                    if config["color"] == "Azul": color = (255, 0, 0)
                    elif config["color"] == "Amarillo": color = (0, 255, 255)
                    elif config["color"] == "Negro": color = (50, 50, 50)
                    elif "Robot Azul" in config["color"]: color = (255, 100, 0)
                    else: color = (0, 200, 255)
                    
                    pts = c.reshape((-1, 1, 2)).astype(np.int32)
                    cv2.polylines(frame, [pts], True, color, 3)
                    
                    if area_id: label = f"{config['color']} (ID:{marker_id}) - A{area_id}"
                    else: label = f"{config['color']} (ID:{marker_id}) - Fuera"
                    
                    cv2.putText(frame, label, (cx - 40, cy - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        cv2.putText(frame, "Q: Salir | A: Ver Areas", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Eurobot Vision System', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27: 
            break
        elif key == ord('a'): 
            mostrar_areas = not mostrar_areas
            overlay = None  # Forzar recreación
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    print("=== Sistema de Detección ArUco para Competición de Robótica ===\n")
    print("Elige el color de tu equipo:")
    print("1. Equipo AMARILLO")
    print("2. Equipo AZUL")
    
    opcion = input("\nSelecciona una opción (1/2): ").strip()
    while opcion != "1" and opcion != "2":
        opcion = input("\nOpción no válida, elige otra vez (1/2): ")

    if opcion == "1":
        color_equipo = "amarillo"
    elif opcion == "2":
        color_equipo = "azul"
    
    print("Has elegido el color ", color_equipo)
    
    # ========== FIX CRÍTICO: Solo llama a obtener_fuente_video() UNA VEZ ==========
    url = obtener_fuente_video()
    detection(color_equipo, url)  # <-- Usar la misma URL

if __name__ == "__main__":
    main()