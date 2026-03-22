import logging
import base64
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from ultralytics import YOLO

# ---------- Configuración de Registros ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
registrador = logging.getLogger("servicio-ia")

aplicacion = FastAPI(title="Servicio de IA — Híbrido RIFLE vs PARAGUAS")

# Diccionario para traducir las clases por defecto de COCO (YOLO) al español
TRADUCCIONES = {
    "person": "Persona",
    "umbrella": "Paraguas",
    "kite": "Rifle",   # YOLO COCO suele confundir rifles largos con cometas ('kite') por su forma
    "weapon": "Arma",
    "knife": "Cuchillo"
}

# ---------- Carga de Modelos ----------
try:
    modelo_yolo = YOLO("yolov8n.pt") 
    
    # Inyectar traducciones directamente en el modelo YOLO para que las pinte en español
    for key, val in modelo_yolo.names.items():
        if val in TRADUCCIONES:
            modelo_yolo.names[key] = TRADUCCIONES[val]
            
    registrador.info("Modelo YOLOv8 cargado correctamente con traducciones.")
except Exception as error:
    registrador.error("Error cargando YOLOv8: %s", error)
    modelo_yolo = None

@aplicacion.get("/salud")
def estado_salud():
    return {"estado": "ok", "yolo": modelo_yolo is not None}

@aplicacion.post("/predecir")
async def predecir(archivo: UploadFile = File(...)):
    if modelo_yolo is None:
        raise HTTPException(status_code=503, detail="Modelos no disponibles")

    # Leer el contenido de la imagen
    contenido = await archivo.read()
    arreglo_numpy = np.frombuffer(contenido, np.uint8)
    imagen = cv2.imdecode(arreglo_numpy, cv2.IMREAD_COLOR)

    if imagen is None:
        raise HTTPException(status_code=400, detail="Imagen inválida")

    # Inferencia YOLO
    resultados_yolo = modelo_yolo(imagen)
    imagen_dibujada = resultados_yolo[0].plot() # Guarda la imagen con las cajas de YOLO

    # Compilar detecciones
    detecciones = []
    
    for caja in resultados_yolo[0].boxes:
        id_clase = int(caja.cls[0])
        confianza = float(caja.conf[0])
        etiqueta_original = modelo_yolo.names[id_clase]
        
        # Traducir al español, o dejar la etiqueta original si no está en el diccionario
        etiqueta_es = TRADUCCIONES.get(etiqueta_original, etiqueta_original)
        
        detecciones.append({
            "etiqueta": etiqueta_es,
            "confianza": round(confianza, 4),
            "caja": caja.xyxy[0].tolist() # Coordenadas [x1, y1, x2, y2]
        })

    registrador.info("Detectados %d objetos en %s", len(detecciones), archivo.filename)

    # Convertir salida a base64
    _, buffer_imagen = cv2.imencode(".jpg", imagen_dibujada)
    imagen_base64 = base64.b64encode(buffer_imagen).decode("utf-8")

    return {
        "nombre_archivo": archivo.filename,
        "detecciones": detecciones,
        "imagen_base64": imagen_base64
    }
