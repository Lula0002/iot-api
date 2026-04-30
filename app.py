from flask import Flask, jsonify, request
from flasgger import Swagger
from repo import IoTRepository

# 1. Start restauranten (Flask)
app = Flask(__name__)
swagger = Swagger(app)

# 2. Hent kokken (Repository)
repo = IoTRepository()

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
    
    try:
        # 4. Læg mappen ned i pengeskabet (MongoDB)
        sensor_id = repo.create_sensor(ny_sensor)
        
        # 5. Fortæl teknikeren, at det gik godt (og giv ham det ID, pengeskabet fandt på)
        return jsonify({
            "message": "Sensor oprettet!", 
            "sensor_id": sensor_id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    try:
        # 1. Bed tjeneren om at hente alt indholdet fra skuffen 'sensors_collection'
        alle_sensorer = repo.get_all_sensors()
            
        # 3. Send listen tilbage til brugeren
        return jsonify(alle_sensorer), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    
    try:
        # 1. Gem målingen som normalt
        reading_id = repo.create_reading(ny_maaling)
        
        # 2. Tjek temperaturen (Threshold Logic)
        # Gruppen har bestemt: > 50°C ELLER < -20°C udløser alarm!
        alert_created = False
        if data['unit'].lower() == "celsius" or data['unit'].lower() == "c":
            if data['value'] > 50 or data['value'] < -20:
                # Opret Alert objektet
                alert_data = {
                    "sensorId": data['sensor_id'],
                    "readingId": reading_id,
                    "value": data['value'],  # <-- TILFØJET: Vi skal huske at gemme værdien her!
                    "type": "threshold_breach",
                    "message": f"Temperatur alarm! Måling: {data['value']}°C (Grænse: >50 eller <-20)",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "acknowledged": False,
                    "notificationSent": False
                }
                
                # Gem alarmen i MongoDB
                alert_id = repo.create_alert(alert_data)
                
                # Send email notifikation
                repo.send_email_notification(alert_data)
                
                alert_created = True
                ny_maaling['alert_id'] = alert_id
                ny_maaling['status'] = "ALARM!"

        # 3. Returner svar
        if alert_created:
            return jsonify({
                "message": "Måling gemt! ADVARSEL: Temperatur udenfor grænser!", 
                "reading_id": reading_id,
                "alert_created": True
            }), 201
        else:
            return jsonify({
                "message": "Måling gemt!", 
                "reading_id": reading_id
            }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    try:
        alle_maalinger = repo.get_all_readings()
            
        return jsonify(alle_maalinger), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DØR 5: Hent alle alarmer ---
@app.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Hent en liste over alle alarmer
    ---
    tags:
      - Alerts
    responses:
      200:
        description: En liste af alarmer
    """
    try:
        alle_alarmer = repo.get_all_alerts()
        return jsonify(alle_alarmer), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DØR 5: Slet en sensor ---
@app.route('/sensors/<sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    """
    Slet en sensor
    ---
    tags:
      - Sensors
    parameters:
      - name: sensor_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Sensor slettet
      404:
        description: Sensor ikke fundet
    """
    try:
        deleted_count = repo.delete_sensor(sensor_id)
        if deleted_count == 0:
            return jsonify({"error": "Sensor ikke fundet"}), 404
        return jsonify({"message": "Sensor slettet!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DØR 6: Slet en måling ---
@app.route('/readings/<reading_id>', methods=['DELETE'])
def delete_reading(reading_id):
    """
    Slet en måling
    ---
    tags:
      - Readings
    parameters:
      - name: reading_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Måling slettet
      404:
        description: Måling ikke fundet
    """
    try:
        deleted_count = repo.delete_reading(reading_id)
        if deleted_count == 0:
            return jsonify({"error": "Måling ikke fundet"}), 404
        return jsonify({"message": "Måling slettet!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DØR 7: Slet en alert ---
@app.route('/alerts/<alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """
    Slet en alert
    ---
    tags:
      - Alerts
    parameters:
      - name: alert_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Alert slettet
      404:
        description: Alert ikke fundet
    """
    try:
        deleted_count = repo.delete_alert(alert_id)
        if deleted_count == 0:
            return jsonify({"error": "Alert ikke fundet"}), 404
        return jsonify({"message": "Alert slettet!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DØR 8: Opdater en sensor ---
@app.route('/sensors/<sensor_id>', methods=['PUT'])
def update_sensor(sensor_id):
    """
    Opdater en sensor
    ---
    tags:
      - Sensors
    parameters:
      - name: sensor_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            location:
              type: string
            type:
              type: string
            status:
              type: string
    responses:
      200:
        description: Sensor opdateret
      404:
        description: Sensor ikke fundet
    """
    data = request.json
    if not data:
        return jsonify({"error": "Du skal sende data med for at opdatere!"}), 400
    try:
        modified_count = repo.update_sensor(sensor_id, data)
        if modified_count == 0:
            return jsonify({"error": "Sensor ikke fundet"}), 404
        return jsonify({"message": "Sensor opdateret!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DØR 9: Opdater en alert (Acknowledge) ---
@app.route('/alerts/<alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """
    Opdater en alert (f.eks. marker som aknowledge)
    ---
    tags:
      - Alerts
    parameters:
      - name: alert_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            acknowledged:
              type: boolean
            notificationSent:
              type: boolean
    responses:
      200:
        description: Alert opdateret
      404:
        description: Alert ikke fundet
    """
    data = request.json
    if not data:
        return jsonify({"error": "Du skal sende data med for at opdatere!"}), 400
    try:
        modified_count = repo.update_alert(alert_id, data)
        if modified_count == 0:
            return jsonify({"error": "Alert ikke fundet"}), 404
        return jsonify({"message": "Alert opdateret!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Vi bruger 0.0.0.0 så Docker og andre computere kan tilgå appen udefra
    app.run(host='0.0.0.0', debug=True, port=5000)