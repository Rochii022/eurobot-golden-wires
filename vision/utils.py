import numpy as np
import os

def obtener_fuente_video():
    nombre_archivo = "config_camara.txt"
    
    # Verificamos si existe el archivo
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, "r") as f:
                # Leemos la linea y usamos .strip() para quitar espacios y saltos de linea (\n)
                url = f.read().strip()
                
            print(f"--> Cargando cámara desde URL: {url}")
            return url
        except Exception as e:
            print(f"Error leyendo el archivo: {e}")
            return 0 # Retorna 0 (webcam por defecto) si falla
    else:
        print("--> No se encontró 'config_camara.txt'. Usando webcam 0 por defecto.")
        return 0

def cargar_colores_calibrados(archivo="colores_calibrados.npz"):
    """
    Carga los rangos HSV de un archivo .npz único.
    Devuelve un diccionario con las claves: 
    'amarillo_min', 'amarillo_max', 'azul_min', 'azul_max'.
    """
    defaults = {
        'amarillo_min': np.array([20, 100, 100]),
        'amarillo_max': np.array([30, 255, 255]),
        'azul_min': np.array([100, 150, 0]),
        'azul_max': np.array([140, 255, 255])
    }

    if not os.path.exists(archivo):
        print(f"[AVISO] No se encontró '{archivo}'. Usando valores por defecto.")
        return defaults

    try:
        # Cargamos el archivo npz
        datos = np.load(archivo)
        
        # Construimos el diccionario de retorno
        calibracion = {
            'amarillo_min': datos['amarillo_min'],
            'amarillo_max': datos['amarillo_max'],
            'azul_min': datos['azul_min'],
            'azul_max': datos['azul_max']
        }
        print(f"--> Colores cargados correctamente desde {archivo}")
        return calibracion

    except Exception as e:
        print(f"[ERROR] Fallo al leer {archivo}: {e}. Usando defaults.")
        return defaults
