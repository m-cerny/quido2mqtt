import asyncio, os, json
from modbus_client import read
import paho.mqtt.publish as publish

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(script_dir, "config.json")

with open(conf_path, "r") as conf:
    data = json.load(conf)

QUIDO_IP = data["quido_ip"]
QUIDO_HTTP_PORT = data["quido_http_port"]
MQTT_BROKER = data["mqtt_broker_ip"]
MQTT_PORT = data["mqtt_port"]
MQTT_TOPIC = data["mqtt_topic"]
MQTT_SUBTOPIC = data["mqtt_subtopics"]
MODBUS_PROTOCOL = data["modbus_protocol"]
MODBUS_PORT = data["modbus_port"]

async def multi_payload():
    """
    Read data from quido and publish them if there is any change to mqtt broker.
    One payload for each function
    """
    prev_response_coils = None 
    prev_response_inputs = None 
    prev_response_temp = None 

    while True:
       
        #MQTT broker config
        broker = MQTT_BROKER
        port = MQTT_PORT
        topic = f"{MQTT_TOPIC}/{MQTT_SUBTOPIC[0]}"
        # Read data from modbus
        response = await read(MODBUS_PROTOCOL, QUIDO_IP, MODBUS_PORT)
        #print(response)

        def pub(msg):
            publish.single(topic, msg, hostname=broker, retain=False)

        response_temp, response_coils, response_inputs = response.values()
        # Check if there is any change and publish if necessary
        if prev_response_coils != response_coils:
            print("coils changed")
            response_coils_msg = json.dumps({"coils": response_coils})
            pub(response_coils_msg)
            prev_response_coils = response_coils 
            
        if prev_response_inputs != response_inputs:
            print("inputs changed")
            response_inputs_msg = json.dumps({"inputs": response_inputs})
            pub(response_inputs_msg)            
            prev_response_inputs = response_inputs       
        
        if prev_response_temp != response_temp:
            print("temp changed")
            response_temp_final = response_temp[0]
            response_temp_msg = json.dumps({"temp": response_temp_final})
            pub(response_temp_msg)  
            prev_response_temp = response_temp
        
        await asyncio.sleep(0.5)

async def single_payload():
    """Read data from quido and publish them if there is any change to mqtt broker in one payload"""
    prev_response = None 

    while True:
       
        #MQTT broker config
        broker = MQTT_BROKER
        port = MQTT_PORT
        topic = f"{MQTT_TOPIC}/{MQTT_SUBTOPIC[0]}"
        # Read data from modbus
        response = await read(MODBUS_PROTOCOL, QUIDO_IP, MODBUS_PORT)

        # Check if there is any change and publish if necessary
        if prev_response != response:
            print("payload changed")
            response_msg = json.dumps(response)
            publish.single(topic, response_msg, hostname=broker, retain=True)
            prev_response = response

        await asyncio.sleep(0.5)
asyncio.run(single_payload())
