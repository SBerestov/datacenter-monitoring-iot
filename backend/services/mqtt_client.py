import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
from db.connection import execute, fetch_all
from config import MQTT_CONFIG

class MQTTSaver:
    def __init__(self):
        self.host = MQTT_CONFIG['host']
        self.port = MQTT_CONFIG['port']
        self.topic = MQTT_CONFIG['topic']
        self.client = mqtt.Client()
        
        # Настройка обработчиков
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Словарь для преобразования имени устройства в type_id
        self.device_mapping = {
            "AqaraSensor": 1,
            "SonoffSensor": 2,
            "SmartPlug": 3,
            "AqaraWaterLeakSensor": 4
        }
        
        # Кэш property_id для каждого устройства и параметра
        self.property_cache = {}
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"MQTT: Connected with result code {rc}")
        if rc == 0:
            # Подписываемся на топик
            client.subscribe(self.topic)
            print(f"MQTT: Subscribed to {self.topic}")
        else:
            print(f"MQTT: Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"MQTT: Disconnected with result code {rc}")
        while True:
            try:
                print("MQTT: Attempting to reconnect...")
                client.reconnect()
                break
            except:
                time.sleep(5)
    
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            if "bridge" in topic:
                return
                
            device_name = topic.split('/')[-1]
            
            if device_name in self.device_mapping:
                print(f"MQTT: Received data from {device_name}")
                self.save_device_data(device_name, payload)
                
        except Exception as e:
            print(f"MQTT: Error processing message: {e}")
    
    def get_property_id(self, type_id, property_name):
        """Получает property_id из кэша или БД"""
        cache_key = f"{type_id}_{property_name}"
        
        if cache_key in self.property_cache:
            return self.property_cache[cache_key]
        
        query = """
        SELECT properties_id 
        FROM properties 
        WHERE type_id = %s AND property_name = %s
        LIMIT 1
        """
        
        result = fetch_all(query, (type_id, property_name))
        
        if result:
            prop_id = result[0]['properties_id']
            self.property_cache[cache_key] = prop_id
            return prop_id
        else:
            print(f"Warning: Property '{property_name}' not found for type_id {type_id}")
            return None
    
    def save_device_data(self, device_name, payload):
        """Сохраняет данные устройства в БД"""
        try:
            data = json.loads(payload)
            type_id = self.device_mapping[device_name]
            timestamp = datetime.now()
            
            for property_name, value in data.items():
                property_id = self.get_property_id(type_id, property_name)
                
                if property_id is not None:
                    query = """
                    INSERT INTO data_sources 
                    (type_id, datetime, data_source_name, properties_id, value)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    
                    execute(query, (type_id, timestamp, device_name, property_id, str(value)))
                    print(f"Saved: {device_name}.{property_name} = {value}")
            
        except json.JSONDecodeError:
            print(f"MQTT: Invalid JSON payload: {payload}")
        except Exception as e:
            print(f"MQTT: Error saving data: {e}")
    
    def start(self):
        """Запускает MQTT клиент"""
        try:
            self.client.connect(self.host, self.port, MQTT_CONFIG["keepalive"])
            print(f"MQTT: Connecting to {self.host}:{self.port}")
            
            self.client.loop_start()
            
        except Exception as e:
            print(f"MQTT: Connection error: {e}")
    
    def stop(self):
        """Останавливает MQTT клиент"""
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT: Client stopped")

mqtt_saver = MQTTSaver()