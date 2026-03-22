# Instrucciones de Despliegue y Ejecución

El presente documento detalla el procedimiento oficial para inicializar y ejecutar el proyecto **"Despliegue de un modelo de IA como servicio mediante microservicios"**. 

El sistema consta de una arquitectura balanceada de tres capas independientes:
1. **Frontend Público** (Vanilla JS / NGINX, Puerto 8080)
2. **API Gateway Intermediario** (Node.js / Express, Puerto 3000)
3. **Servicio Central de Inferencia de IA** (Python / FastAPI, Puerto 8000)

Existen dos vías para ejecutar el entorno de desarrollo: mediante contenerización integral (recomendado) o en formato bare-metal (manual).

---

## Opción 1: Ejecución Automatizada mediante Docker (Recomendada)

La forma más estandarizada de probar la plataforma aislando todas sus dependencias es mediante Docker y su orquestador de bajo nivel Docker Compose.

1. Se requiere tener instalado el motor de Docker. En sistemas Windows o Mac, asegúrese de tener en ejecución **Docker Desktop**.
2. Abra un terminal y sitúese en la raíz principal del proyecto.
3. Ejecute el siguiente comando para construir y orquestar las imágenes simultáneamente:
   ```bash
   docker-compose up --build
   ```
4. El sistema aprovisionará los tres contenedores y los comunicará a través de una red virtual en modo puente (`red-app`).
5. Cuando los logs de terminal confirmen que el API Gateway está en el puerto 3000 y FastAPI en el 8000, acceda a nivel usuario desde cualquier navegador:
   👉 **http://localhost:8080**

---

## Opción 2: Ejecución Manual en Entorno Local

Si la máquina anfitriona no dispone de permisos o instalación de Docker, el ecosistema puede inicializarse de forma manual en tres terminales separados instalando previamentes sus dependencias (vía `pip` y `npm`).

### A) Despliegue del Servicio de Inferencia (Python)
1. Abra un terminal y navegue hasta el directorio: `cd servicio_ia`
2. Instale los requerimientos mediante `pip install -r requirements.txt`.
3. Inicie el servicio web asíncrono en localhost puerto 8000:
   ```bash
   python -m uvicorn main:aplicacion --host 127.0.0.1 --port 8000
   ```

### B) Despliegue del API Gateway (Node.js)
1. Abra un **segundo terminal** y navegue hasta: `cd servicio_intermediario`
2. Resuelva los paquetes de dependencias con `npm install`.
3. Defina la variable de entorno que enruta al backend de Python e inicie el proxy sobre el puerto 3000:
   - *En Windows PowerShell:*
     ```powershell
     $env:URL_SERVICIO_IA="http://127.0.0.1:8000"
     node servidor.js
     ```
   - *En Linux/Mac:*
     ```bash
     export URL_SERVICIO_IA="http://127.0.0.1:8000" && node servidor.js
     ```

### C) Despliegue del Servidor Web Frontend
1. Abra un **tercer terminal** y navegue hasta la nueva capa pública: `cd frontend`
2. Inicialice un servidor web nativo sobre el puerto 8080 para servir los ficheros estáticos en red:
   ```bash
   python -m http.server 8080
   ```
3. Abra su navegador y visite **http://localhost:8080**.

---

## Ejecución de Pruebas Automatizadas del Sistema (cURL)

La rúbrica técnica exige probar la correcta delegación de recursos a cada capa por separado probando los endpoints `POST /predecir`. Con los servicios levantados, se pueden utilizar utilidades de consola como `curl` para demostrar respuestas validadas JSON.

**1. Interacción a través del API Gateway (Punto de entrada oficial Node.js):**
*Invocación simulando Frontend a puerto 3000 recibiendo array multiparte ('archivos')*
```bash
curl.exe -X POST "http://localhost:3000/predecir" -F "archivos=@ruta_foto\foto.jpg"
```

**2. Interacción privada saltando el Gateway (Solo para depuración de Python):**
*Invocación simulando API Gateway internamente a puerto 8000 ('archivo' singular)*
```bash
curl.exe -X POST "http://127.0.0.1:8000/predecir" -F "archivo=@ruta_foto\foto.jpg"
```

El log del proxy registrará la llegada de los Bytes, la delegación interior asíncrona mediante Axios y retornará al cliente el Base64 codificado renderizable y un array asociativo con cada objeto detectado y ponderado.
