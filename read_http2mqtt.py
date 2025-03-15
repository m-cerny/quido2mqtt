import paho.mqtt.client as pah_mqtt
from flask import Flask, request
import json, os

app = Flask(__name__)

script_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(script_dir, "config.json")

with open(conf_path, "r") as conf:
    data = json.load(conf)

MQTT_BROKER = data["mqtt_broker_ip"]
MQTT_PORT = data["mqtt_port"]
MQTT_TOPIC = data["mqtt_topic"]
MQTT_SUBTOPIC = data["mqtt_subtopics"]

QUIDO_IP = data["quido_ip"]
QUIDO_HTTP_PORT = data["quido_http_port"]


# Set up MQTT client
mqtt_client = pah_mqtt.Client(pah_mqtt.CallbackAPIVersion.VERSION2)

# Connect to the MQTT broker
def connect_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Callback to handle connection
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"'read_http' connected to MQTT Broker with result code {reason_code}")

# Set the callback function for the MQTT client
mqtt_client.on_connect = on_connect

# Start the MQTT loop in the background
mqtt_client.loop_start()

@app.route('/script', methods=['GET'])
def read_request():
    # Retrieve GET parameters
    mac = request.args.get('mac')
    name = request.args.get('name')
    ins = request.args.get('ins')
    outs = request.args.get('outs')
    tempS = request.args.get('tempS')
    tempV = request.args.get('tempV')
    cnt2 = request.args.get('cnt2')
    cnt6 = request.args.get('cnt6')

    # Create the response as a string
    response = f'''
    Received GET request with parameters:
    MAC Address: {mac}
    Name: {name}
    Inputs: {ins}
    Outputs: {outs}
    TempS: {tempS}
    TempV: {tempV}
    Counter 2: {cnt2}
    Counter 6: {cnt6}
    '''

    # Prepare the payload for MQTT
    def transform(value: int) -> list:
        """
        Transform binary code to list
        Value should be ins or outs
        """
        value = list(value)
        output = [1 if x == "1" else 0 for x in value]
        return output
        
    payload_dict = {
    "coils": transform(outs),
    "inputs": transform(ins),
    "temp": float(tempV)
    }  
    
    payload_json = json.dumps(payload_dict)

    # Send the data to the MQTT broker
    mqtt_client.publish(f"{MQTT_TOPIC}/{MQTT_SUBTOPIC[0]}", payload_json, retain=True)

    # Return the response to the client
    return response

if __name__ == '__main__':
    # Connect to the MQTT broker before starting the Flask app
    connect_mqtt()
    
    # Run the Flask app on port 8083
    app.run(debug=False, port=8083, host="0.0.0.0")
