const express = require("express");
const axios = require("axios");
const morgan = require("morgan");
const rateLimit = require("express-rate-limit");
const multer = require("multer");
const FormData = require("form-data");
const cors = require("cors");

const aplicacion = express();
const PUERTO = process.env.PORT || 3000;
// Si se ejecuta con Docker Compose, cogerá la variable de entorno. Localmente, usará localhost.
const URL_SERVICIO_IA = process.env.URL_SERVICIO_IA || "http://127.0.0.1:8000";

console.log("URL_SERVICIO_IA es:", URL_SERVICIO_IA);

// Configuración de multer para la subida de archivos (límite de 10MB)
const subida_archivos = multer({ limits: { fileSize: 10 * 1024 * 1024 } });

// Middlewares
aplicacion.use(cors()); // Permite peticiones desde el frontend externo
aplicacion.use(morgan("dev")); // Registro de peticiones HTTP
aplicacion.use(express.json()); // Parseo del cuerpo en formato JSON

// Mejora adicional: Limitador de peticiones para evitar saturación (Rate Limiting)
const limitador = rateLimit({
  windowMs: 60 * 1000, // 1 minuto
  max: 100, // Límite de 100 peticiones por minuto por IP
  message: { error: "Demasiadas peticiones. Inténtalo más tarde." },
});
aplicacion.use(limitador);

/**
 * Endpoint de Predicción - Soporta múltiples imágenes
 * Actúa como intermediario recibiendo la petición y enviándola al servicio de IA
 */
aplicacion.post("/predecir", subida_archivos.array("archivos", 10), async (peticion, respuesta) => {
  if (!peticion.files || peticion.files.length === 0) {
    return respuesta.status(400).json({ error: "No se han subido archivos" });
  }

  console.log(`[INTERMEDIARIO] Procesando ${peticion.files.length} archivos`);

  try {
    // Procesar cada archivo de forma concurrente
    const resultados = await Promise.all(
      peticion.files.map(async (elemento) => {
        const formulario = new FormData();
        formulario.append("archivo", elemento.buffer, {
          filename: elemento.originalname,
          contentType: elemento.mimetype,
        });

        // Enviar la imagen al servicio de IA interno
        const respuesta_ia = await axios.post(`${URL_SERVICIO_IA}/predecir`, formulario, {
          headers: { ...formulario.getHeaders() },
          timeout: 15000, // Tiempo de espera máximo de 15 segundos para dar tiempo a YOLO
        });

        return respuesta_ia.data;
      })
    );

    // Devolver los resultados agrupados al cliente
    respuesta.json(resultados);
  } catch (error) {
    if (error.response) {
      console.error(`[ERROR] Fallo en la comunicación con IA: ${error.response.status}`, error.response.data);
    } else {
      console.error(`[ERROR] Fallo en la comunicación con IA: ${error.message}`);
    }
    respuesta.status(502).json({ error: "Error de comunicación con el servicio de IA" });
  }
});

/**
 * Endpoint para comprobar el estado de salud de toda la arquitectura
 */
aplicacion.get("/salud", async (peticion, respuesta) => {
  try {
    // Hace ping al servicio de IA para comprobar que todo está operativo
    const salud_ia = await axios.get(`${URL_SERVICIO_IA}/salud`, { timeout: 3000 });
    respuesta.json({ intermediario: "operativo", servicio_ia: salud_ia.data });
  } catch (error) {
    respuesta.json({ intermediario: "operativo", servicio_ia: "fuera_de_linea" });
  }
});

// Iniciar el servidor
aplicacion.listen(PUERTO, () => {
  console.log(`[OK] Servicio Intermediario corriendo y escuchando en http://localhost:${PUERTO}`);
});
