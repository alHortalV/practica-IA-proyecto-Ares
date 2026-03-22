import os
import kagglehub
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
import numpy as np
import shutil

# ---------- Configuración ----------
RUTA_DATASET = "./dataset_entrenamiento"
RUTA_GUARDAR_MODELO = "modelo.h5"
TAMANO_IMAGEN = (224, 224)
TALLA_LOTE = 32
EPOCAS = 20
URL_DATASET_KAGGLE = "alexteboul/diabetes-health-indicators-dataset" # NOTA: Cambiar por el dataset real de armas/paraguas

def descargar_dataset():
    """
    Descarga el dataset desde Kaggle usando kagglehub si la carpeta no existe de antemano.
    """
    if os.path.exists(RUTA_DATASET) and len(os.listdir(RUTA_DATASET)) > 0:
        print(f"Dataset ya encontrado en {RUTA_DATASET}.")
        return RUTA_DATASET
        
    print(f"Descargando dataset desde Kaggle ({URL_DATASET_KAGGLE})...")
    # kagglehub lee automáticamente las credenciales de ~/.kaggle/kaggle.json o entorno
    try:
        ruta_descarga = kagglehub.dataset_download(URL_DATASET_KAGGLE)
        print(f"Dataset descargado temporalmente en: {ruta_descarga}")
        
        # Mover los archivos descargados a nuestra carpeta local
        shutil.copytree(ruta_descarga, RUTA_DATASET, dirs_exist_ok=True)
        print("Dataset estructurado localmente.")
        return RUTA_DATASET
    except Exception as error:
        print(f"Error descargando desde Kaggle: {error}")
        return None

def crear_modelo():
    """
    Crea un modelo basado en MobileNetV2 para la clasificación.
    """
    print("Creando arquitectura del modelo...")
    
    # Capa de entrada
    entradas = tf.keras.Input(shape=(TAMANO_IMAGEN[0], TAMANO_IMAGEN[1], 3))
    
    # Aumentación de datos (Data Augmentation) para evitar sobreajuste
    x = tf.keras.layers.RandomFlip("horizontal")(entradas)
    x = tf.keras.layers.RandomRotation(0.2)(x)
    x = tf.keras.layers.RandomZoom(0.2)(x)
    
    # Normalización (Rescaling en lugar de preprocess_input)
    x = tf.keras.layers.Rescaling(1./127.5, offset=-1)(x)

    # Cargar MobileNetV2 pre-entrenado
    modelo_base = MobileNetV2(weights='imagenet', include_top=False, input_shape=(TAMANO_IMAGEN[0], TAMANO_IMAGEN[1], 3))
    
    # Fine-Tuning: Descongelar las últimas 30 capas
    modelo_base.trainable = True
    capa_descongelar = len(modelo_base.layers) - 30
    for capa in modelo_base.layers[:capa_descongelar]:
        capa.trainable = False

    x = modelo_base(x, training=False)

    # Capas de clasificación finales
    x = GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    x = Dense(128, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.1)(x)
    
    # Capa de salida (0=Paraguas, 1=Persona, 2=Rifle)
    predicciones = Dense(3, activation='softmax')(x)

    modelo = Model(inputs=entradas, outputs=predicciones)
    modelo.compile(optimizer=tf.keras.optimizers.Adam(1e-4), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    return modelo

def generar_datos_ficticios():
    """
    Genera datos ficticios por si falla la descarga del dataset.
    """
    print("ADVERTENCIA: Generando datos ficticios para compilar modelo de prueba...")
    x_entrenamiento = np.random.rand(100, TAMANO_IMAGEN[0], TAMANO_IMAGEN[1], 3)
    y_entrenamiento = np.random.randint(0, 3, 100)
    return x_entrenamiento, y_entrenamiento

def entrenar():
    """
    Flujo principal de entrenamiento del modelo de IA.
    """
    modelo = crear_modelo()
    ruta_datos = descargar_dataset()
    
    # Asegurar que existan subcarpetas de clases (Keras requiere ImageFolder format)
    if ruta_datos and any(os.path.isdir(os.path.join(ruta_datos, d)) for d in os.listdir(ruta_datos)):
        print(f"Iniciando entrenamiento con datos de {ruta_datos}...")
        dataset_entrenamiento = tf.keras.preprocessing.image_dataset_from_directory(
            ruta_datos,
            validation_split=0.2,
            subset="training",
            seed=123,
            image_size=TAMANO_IMAGEN,
            batch_size=TALLA_LOTE
        )
        
        dataset_validacion = tf.keras.preprocessing.image_dataset_from_directory(
            ruta_datos,
            validation_split=0.2,
            subset="validation",
            seed=123,
            image_size=TAMANO_IMAGEN,
            batch_size=TALLA_LOTE
        )
        
        modelo.fit(dataset_entrenamiento, validation_data=dataset_validacion, epochs=EPOCAS)
    else:
        # Fallback si no hay carpetas válidas
        x_entrenamiento, y_entrenamiento = generar_datos_ficticios()
        print("Iniciando entrenamiento con datos sintéticos...")
        modelo.fit(x_entrenamiento, y_entrenamiento, epochs=1, batch_size=TALLA_LOTE)
        
    print(f"Guardando el modelo entrenado en: {RUTA_GUARDAR_MODELO}")
    modelo.save(RUTA_GUARDAR_MODELO)
    print("Modelo guardado correctamente.")

if __name__ == "__main__":
    entrenar()
