from flask import Flask, send_from_directory
from flask_cors import CORS
from services.mqtt_client import mqtt_saver
import atexit
import os

from routes.devices import devices_bp
from routes.charts import charts_bp
from routes.tables import tables_bp

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

app.register_blueprint(devices_bp)
app.register_blueprint(charts_bp)
app.register_blueprint(tables_bp)

@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'main.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

def start_mqtt_client():
    """Запуск MQTT клиента при старте приложения"""
    mqtt_saver.start()
    print("MQTT client started")

def stop_mqtt_client():
    """Остановка MQTT клиента при завершении приложения"""
    mqtt_saver.stop()
    print("MQTT client stopped")

# Запуск MQTT клиента при старте Flask
start_mqtt_client()

# Регистрация функции остановки при завершении
atexit.register(stop_mqtt_client)

if __name__ == "__main__":
    os.makedirs("static/images", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)