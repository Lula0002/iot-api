import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Fortæl Python at den skal kigge i .env filen og indlæse variablerne
load_dotenv()

class IoTRepository:
    def __init__(self):
        # Vi henter nøglen fra en hemmelig miljøvariabel i stedet for at skrive den direkte i koden
        mongo_uri = os.environ.get("MONGO_URI")
        
        # Hvis vi tester lokalt og glemmer at sætte variablen, giver vi en pæn fejlbesked
        if not mongo_uri:
            raise ValueError("Fejl: MONGO_URI miljøvariablen mangler!")
            
        self.client = MongoClient(mongo_uri)
        self.db = self.client.iot_db
        self.sensors = self.db.sensors
        self.readings = self.db.readings

    # --- SENSOR METODER ---
    def create_sensor(self, sensor_data):
        result = self.sensors.insert_one(sensor_data)
        return str(result.inserted_id)

    def get_all_sensors(self):
        sensors = list(self.sensors.find())
        for sensor in sensors:
            sensor['_id'] = str(sensor['_id'])
        return sensors

    # --- READING METODER ---
    def create_reading(self, reading_data):
        result = self.readings.insert_one(reading_data) 
        return str(result.inserted_id)

    def get_all_readings(self):
        readings = list(self.readings.find())
        for reading in readings:
            reading['_id'] = str(reading['_id'])
        return readings