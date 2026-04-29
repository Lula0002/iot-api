from pymongo import MongoClient

class IoTRepository:
    def __init__(self):
        # HUSK AT SÆTTE DIN EGEN CONNECTION STRING IND HER!
        self.client = MongoClient("mongodb+srv://lula0002:Niptyalalyel2026%21@lula0002.zhc8sou.mongodb.net/?appName=lula0002")
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