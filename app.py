import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from pytz import timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)
CORS(app)

# MongoDB Atlas URI desde variable de entorno
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["Sensor_ESP32_Mongo"] # Nombre de tu base de datos
collection = db["Datos"] # Nombre de la collecion

# Ruta para recibir datos del ESP32
@app.route("/api/data", methods=["POST"])
def recibir_dato():
    try:
        data = request.get_json()
        # Campos obligatorios
        required_keys = ["dispositivo", "temperatura", "humedad"]
        if not all(k in data for k in required_keys):
            return jsonify({"error": "Faltan campos obligatorios en el JSON"}), 400

        # Validar tipos de datos
        try:
            temperatura = float(data["temperatura"])
            humedad = float(data["humedad"])
        except (ValueError, TypeError):
            return jsonify({"error": "Temperatura o humedad no son valores numéricos válidos"}), 400

        # Crear documento con campos obligatorios
        documento = {
            "dispositivo": str(data["dispositivo"]),
            "temperatura": temperatura,
            "humedad": humedad,
            "timestamp": datetime.utcnow() - timedelta(hours=6)
        }

        # Agregar campos opcionales si están presentes
        if "luz" in data:
            try:
                documento["luz"] = int(data["luz"])
            except (ValueError, TypeError):
                return jsonify({"error": "El campo luz debe ser un valor numérico"}), 400

        if "intensidad_luz" in data:
            documento["intensidad_luz"] = str(data["intensidad_luz"])

        if "movimiento" in data:
            documento["movimiento"] = str(data["movimiento"])

        # Insertar en MongoDB
        collection.insert_one(documento)
        return jsonify({"message": "Datos guardados correctamente"}), 200

    except Exception as e:
        print("Error al guardar en MongoDB:", str(e))  # Aparecerá en los logs de Render
        return jsonify({"error": "Error al guardar en la base de datos"}), 500

# Ruta para ver los últimos 50 datos
@app.route("/api/datos", methods=["GET"])
def ver_datos():
    datos = list(collection.find().sort("timestamp", -1).limit(50))
    for d in datos:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].isoformat()

    return jsonify(datos), 200

@app.route("/", methods=["GET"])
def index():
    return "API Flask con MongoDB funcionando en Render", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
