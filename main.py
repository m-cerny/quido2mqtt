from nicegui import ui
import paho.mqtt.client as pah_mqtt
import os, subprocess, json, time
from control_http import write_coils as control_outputs_http
from modbus_client import control_coils as control_outputs_modbus

""" 
TODO:

- pokud pouziju modbusRTU neni vytvorena funkce na zapis

"""
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
COMUNICATION_PROTOCOL = data["comunication_protocol"]
IO_PORTS = data["io_ports"]

# Check comunication protocol
if COMUNICATION_PROTOCOL == "modbus" or COMUNICATION_PROTOCOL == "http":
    comunication = COMUNICATION_PROTOCOL
    print(f"Using {comunication} for comunication with Quido")
else:
    raise ValueError("Comunication protocol has to be 'modbus' or 'http")



# Global variable to hold the elements reference

ins_value = [{'In ': str(i+1), 'state': '--'} for i in range(IO_PORTS)]

outs_value = [{'Out ': str(i+1), 'state': '--'} for i in range(IO_PORTS)]


def publish_coil_state(coil_index:int, state:int) -> None:
    """
    A helper function to publish the coil state via MQTT.

    coil index: 0-7
    state: "on", "off"
    """
    print(f"On_toggle_change: Toggle {coil_index + 1} {'ON' if state == 1 else 'OFF'}")
    payload_dict = {"coils_control": [coil_index, state]}
    payload_json = json.dumps(payload_dict)
    topic = f"{MQTT_TOPIC}/{MQTT_SUBTOPIC[1]}"
    mqtt_client.publish(topic, payload_json)


### outputs
def on_outputs(outs):
    """change state of inputs in gui"""
    global outs_table
    for i, item in enumerate(outs_value):
        if outs[i] == 1:
            item['state'] = 'On'
        else:
            item['state'] = 'Off'    

    outs_table.update_rows(rows=outs_value)
### temp
def on_temp(temp):

    global temp_value
    temp_value = temp

    temp_cir.set_value(temp_value)
    print(f"Temp update: {temp_value}")

### inputs
def on_input(ins):
    """change state of inputs in gui"""
    global ins_table
    for i, item in enumerate(ins_value):
        if ins[i] == 1:
            item['state'] = 'On'
        else:
            item['state'] = 'Off'    

    ins_table.update_rows(rows=ins_value)
   
def create_elements():

    global ins_table
    global outs_table
    global settings_ui
    global temp_cir
    
    rows_ins = ins_value
    rows_outs = outs_value
    
    with ui.header(elevated=True).style('background-color: #000000').classes('items-center justify-between'):
        ui.label("QUIDO2MQTT")
        ui.button(on_click=lambda: right_drawer.toggle(), icon='menu').props('flat color=white')
    with ui.right_drawer(fixed=False).style('background-color: #000000').props('bordered') as right_drawer:
        ui.label("SETTINGS")
        settings_ui = ui.label("--")
    
    with ui.row():
            with ui.card():
                    with ui.column():
                        ui.label("Inputs:")                                         
                        ins_table = ui.table(rows=rows_ins, row_key='inputs')
                        ins_table.add_slot('body-cell-state', '''
                                    <q-td key="state" :props="props">
                                        <q-badge :color="props.value == 'Off' ? 'red' : 'green'">
                                            {{ props.value }}
                                        </q-badge>
                                    </q-td>
                                    ''')
            with ui.card():
                    with ui.column():
                        ui.label("Outputs:")                  
                        outs_table = ui.table(title=None, rows=rows_outs, row_key='outputs',)
                        outs_table.add_slot('body-cell-state', '''
                                    <q-td key="state" :props="props">
                                        <q-badge :color="props.value == 'Off' ? 'red' : 'green'">
                                            {{ props.value }}
                                        </q-badge>
                                    </q-td>
                                    ''')

            with ui.card():
                        ui.label("Controls:")
                        ui.row()
                        ui.row()
                        for i in range(IO_PORTS):  # loop over output numbers 0 to 7
                            with ui.row():                   
                                ui.label(f"Out {i+1}:")  # display "Out 1" to "Out 8"
                                ui.button(icon="done", color="green-5", on_click=lambda i=i: publish_coil_state(i, 1))
                                ui.button(icon="close", color="red-5", on_click=lambda i=i: publish_coil_state(i, 0))
   
            with ui.card().classes('flex justify-center items-center'):
                ui.label("Temperature: ")
                temp_cir = ui.circular_progress(min=0, max=45, size="xl", color="red").tooltip("temperature [°C]")
 

def read(protocol):
    """ Starts reading of quido states. By MODBUS or HTTP """
    if protocol == "modbus":
        script_path = os.path.join(script_dir, "read_modbus2mqtt.py")
        process = subprocess.Popen(['python', script_path])
    else:
        script_path = os.path.join(script_dir, "read_http2mqtt.py")
        process = subprocess.Popen(['python', script_path])

read(COMUNICATION_PROTOCOL)

# Function to handle MQTT messages
def on_connect(client, userdata, flags, reason_code, properties):
    print("'main' connected with result code " + str(reason_code)) 
    # Subscribe to the topic
    mqtt_client.subscribe(f"{MQTT_TOPIC}/#")

def coil_control(index, state):
    """ function for controling coils via http or modbus"""
    if COMUNICATION_PROTOCOL == "http":
        control_outputs_http(index+1, "on" if state == 1 else "off") # control coils states by mqtt msg
    if COMUNICATION_PROTOCOL == "modbus":
        time.sleep(0.5)
        control_outputs_modbus(index, True if state == 1 else False)
    

def on_message(client, userdata, message):
    payload = str(message.payload.decode())
    print(f" received payload: {payload}")
    retain_msg = message.retain
    print(f"Retained msg: {retain_msg}")
    payload_dict = json.loads(payload)

    try:    
        # switch gui elements accordingly
        outs = payload_dict["coils"]
        on_outputs(outs)
    except Exception as e:
        print(f"coils is not processed")

    try:
        index, state = payload_dict["coils_control"]
        coil_control(index, state)                     
    except Exception as e:
        print(f"coils_control is not processed")  

    try:
        temp = payload_dict["temp"]
        on_temp(temp)
    except Exception as e:
        print(f"temp is not processed")   
    
    try:
        ins = payload_dict["inputs"]
        on_input(ins)                
    except Exception as e:
        print(f"inputs is not processed")
    
# MQTT client setup
mqtt_client = pah_mqtt.Client(pah_mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_message = on_message
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

create_elements()
# update settings in UI
settings_ui.set_text(str(data))

# Start the MQTT loop in a separate thread
mqtt_client.loop_start()
ui.run(title="quido2mqtt", dark=True, native=False, port=8082, show=False)




    