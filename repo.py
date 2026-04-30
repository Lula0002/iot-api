import os
import smtplib
from email.mime.text import MIMEText
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
        self.alerts = self.db.alerts  # <-- NY: Vi tilføjer alerts samlingen

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

    # --- ALERT METODER (NYT) ---
    def create_alert(self, alert_data):
        result = self.alerts.insert_one(alert_data)
        return str(result.inserted_id)

    def get_all_alerts(self):
        alerts = list(self.alerts.find())
        for alert in alerts:
            alert['_id'] = str(alert['_id'])
        return alerts

    # --- EMAIL NOTIFIKATION (NYT) ---
    def send_email_notification(self, alert_data):
        # Vi henter email-oplysninger fra miljøvariabler (så vi ikke hardcoder dem!)
        sender_email = os.environ.get("SENDER_EMAIL")
        sender_password = os.environ.get("SENDER_PASSWORD")
        receiver_email = os.environ.get("RECEIVER_EMAIL", "lukas@test.com") # Default hvis ikke sat (matchar .env filen)

        if not sender_email or not sender_password:
            print("Advarsel: Email variabler ikke sat. Kan ikke sende email.")
            return

        # Lav selve beskeden (brevet)
        msg = MIMEText(f"ALARM! {alert_data['message']}\nVærdi: {alert_data['value']}\nTid: {alert_data['timestamp']}")
        msg['Subject'] = f"IoT Alert: {alert_data['type']}"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        try:
            # Opret forbindelse til Gmail (eller anden SMTP server)
            # Vi bruger Gmail her som eksempel. Host: smtp.gmail.com, Port: 587
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()  # Start krypteret forbindelse
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print("Email sendt succesfuldt!")
        except Exception as e:
            print(f"Fejl ved afsendelse af email: {e}")