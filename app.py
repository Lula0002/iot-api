from flask import Flask, jsonify, request
from flasgger import Swagger
from pymongo import MongoClient

# 1. Start restauranten (Flask)
app = Flask(__name__)
swagger = Swagger(app)

# 2. Forbind til pengeskabet (MongoDB)
# HUSK AT SÆTTE DIN EGEN CONNECTION STRING IND HERUNDER!
MONGO_URI = "mongodb+srv://lula0002:Niptyalalyel2026!@lula0002.zhc8sou.mongodb.net/?appName=lula0002"


# Vi beder tolken (MongoClient) om at låse pengeskabet op
client = MongoClient(MONGO_URI)

# Vi vælger den specifikke skuffe i pengeskabet, vi vil bruge (vi kalder den 'iot_db')
db = client.iot_db

# Vi laver to mapper nede i skuffen: én til sensorer og én til målinger
sensors_collection = db.sensors
readings_collection = db.readings

# En lille test-dør for at se, om restauranten er åben
@app.route('/', methods=['GET'])
def home():
    """
    Velkomst-dør
    ---
    responses:
      200:
        description: En velkomstbesked
    """
    return jsonify({"message": "Velkommen til Intelligent IoT Solutions API!"})


# --- DØR 1: Opret en ny sensor ---
@app.route('/sensors', methods=['POST'])
def create_sensor():
    """
    Opret en ny sensor
    ---
    tags:
      - Sensors
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - location
            - type
          properties:
            name:
              type: string
              example: "Termometer Hal A"
            location:
              type: string
              example: "Maskinhal A"
            type:
              type: string
              example: "temperature"
    responses:
      201:
        description: Sensoren blev oprettet
    """
    # 1. Læs den seddel (JSON), som teknikeren har sendt med
    data = request.json
    
    # 2. Tjek om han har husket at skrive navn, placering og type
    if not data or 'name' not in data or 'location' not in data or 'type' not in data:
        return jsonify({"error": "Du mangler at udfylde name, location eller type!"}), 400
    
    # 3. Lav en ny mappe til sensoren
    ny_sensor = {
        "name": data['name'],
        "location": data['location'],
        "type": data['type'],
        "status": "active" # Vi siger automatisk, at den er aktiv fra start
    }
    
    # 4. Læg mappen ned i pengeskabet (MongoDB)
    resultat = sensors_collection.insert_one(ny_sensor)
    
    # 5. Fortæl teknikeren, at det gik godt (og giv ham det ID, pengeskabet fandt på)
    return jsonify({
        "message": "Sensor oprettet!", 
        "sensor_id": str(resultat.inserted_id)
    }), 201

# --- DØR 2: Hent alle sensorer ---
@app.route('/sensors', methods=['GET'])
def get_sensors():
    """
    Hent en liste over alle sensorer
    ---
    tags:
      - Sensors
    responses:
      200:
        description: En liste af sensorer
    """
    # 1. Bed tjeneren om at hente alt indholdet fra skuffen 'sensors_collection'
    alle_sensorer = list(sensors_collection.find())
    
    # 2. MongoDB's unikke ID'er er lidt specielle, så vi skal lige oversætte dem til almindelig tekst
    for sensor in alle_sensorer:
        sensor['_id'] = str(sensor['_id'])
        
    # 3. Send listen tilbage til brugeren
    return jsonify(alle_sensorer), 200

# --- DØR 3: Modtag en ny måling fra en sensor ---
@app.route('/readings', methods=['POST'])
def create_reading():
    """
    Modtag en ny måling
    ---
    tags:
      - Readings
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - sensor_id
            - value
            - unit
          properties:
            sensor_id:
              type: string
              example: "SÆT_DIT_LANGE_SENSOR_ID_IND_HER"
            value:
              type: number
              example: 25.5
            unit:
              type: string
              example: "Celsius"
    responses:
      201:
        description: Målingen blev gemt
    """
    data = request.json
    
    if not data or 'sensor_id' not in data or 'value' not in data or 'unit' not in data:
        return jsonify({"error": "Du mangler at udfylde sensor_id, value eller unit!"}), 400
    
    import datetime # Vi skal bruge dette til at stemple tidspunktet
    
    ny_maaling = {
        "sensor_id": data['sensor_id'],
        "value": data['value'],
        "unit": data['unit'],
        "timestamp": datetime.datetime.now().isoformat() # Vi stempler automatisk, hvornår målingen kom ind
    }
    
    resultat = readings_collection.insert_one(ny_maaling)
    
    return jsonify({
        "message": "Måling gemt!", 
        "reading_id": str(resultat.inserted_id)
    }), 201

# --- DØR 4: Hent alle målinger ---
@app.route('/readings', methods=['GET'])
def get_readings():
    """
    Hent en liste over alle målinger
    ---
    tags:
      - Readings
    responses:
      200:
        description: En liste af målinger
    """
    alle_maalinger = list(readings_collection.find())
    
    for maaling in alle_maalinger:
        maaling['_id'] = str(maaling['_id'])
        
    return jsonify(alle_maalinger), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)