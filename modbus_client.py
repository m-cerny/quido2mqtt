from pymodbus.client import ModbusTcpClient
import ast, time, os, json
import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
    ModbusException,
    
 )

script_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(script_dir, "config.json")

with open(conf_path, "r") as conf:
    data = json.load(conf)

QUIDO_IP = data["quido_ip"]
MODBUS_PORT = data["modbus_port"]

async def read(comm, host, port, framer=FramerType.SOCKET):
    """Run async client."""

    client: ModbusClient.ModbusBaseClient
    if comm == "tcp":
        client = ModbusClient.AsyncModbusTcpClient(
            host,
            port=port,
            framer=framer,
            # timeout=10,
            # retries=3,
            # source_address=("localhost", 0),
        )
    elif comm == "udp":
        client = ModbusClient.AsyncModbusUdpClient(
            host,
            port=port,
            framer=framer,
            # timeout=10,
            # retries=3,
            # source_address=None,
        )
    elif comm == "serial":
        client = ModbusClient.AsyncModbusSerialClient(
            port,
            framer=framer,
            # timeout=10,
            # retries=3,
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            # handle_local_echo=False,
        )
    else:
        print(f"Unknown client {comm} selected")
        return

    await client.connect()
    # test client is connected
    assert client.connected

    #print("get and verify data")
    ### Outputs
    try:
        # See all calls in client_calls.py
        rr = await client.read_coils(0, count=8, slave=49)
        #print(f"Read coils: {rr}")
        
        coils = str(rr).split("bits=")[1].split(", registers")[0]
        coils = coils.replace("False", "0").replace("True", "1")
        coils = ast.literal_eval(coils) # transform str to list
        coils = {"coils" : coils}
        #print(coils)
     
            
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
        client.close()
        return
    if  rr.isError():
        print(f"Received exception from device ({rr})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        client.close()
        return
    
    ### temperature

    try:
        # See all calls in client_calls.py
        rr = await client.read_input_registers(1, count=2, slave=49)
        #print(f"Read input registers: {rr}")
        #print(rr)
        temp = str(rr).split("registers=")[1].split(", status")[0]
        #print(temp)
        temp = ast.literal_eval(temp)
        temp = {"temp" : temp[0]/10}
        #print(temp)
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
        client.close()
        return
    if rr.isError():
        print(f"Received exception from device ({rr})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        client.close()
        return
    ### inputs
    try:
        # See all calls in client_calls.py
        rr = await client.read_discrete_inputs(0, count=8, slave=49)
        #print(f"Read discrete inputs: {rr}")
        inputs = str(rr).split("bits=")[1].split(", registers")[0]
        #print(inputs)
        inputs = inputs.replace("False", "0").replace("True", "1")
        inputs = ast.literal_eval(inputs)
        inputs = {"inputs" : inputs}
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
        client.close()
        return
    if rr.isError():
        print(f"Received exception from device ({rr})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        client.close()
        return   
    client.close()
    response = {}
    response.update(temp)
    response.update(coils)
    response.update(inputs)

    return response

def control_coils(coil_number: int, coil_state: bool):
    try:
        client = ModbusTcpClient(QUIDO_IP, port=MODBUS_PORT)  # Replace with your Modbus server's IP address
        if client.connect():
            print("Connection successful")

        # Attempt to write a coil (turn coil on or off)
            #response = client.write_coils(coil_number, [True, True, True, True, True, True, True, True])  # Starting from address 0
            response = client.write_coils(coil_number, [coil_state])
        # Check if there is an exception response
            if response.isError():
                print(f"Modbus error: {response}")
            else:
                print("Coil written successfully")
        # Sleep for a while to ensure the operation is processed (optional)
            time.sleep(1)

        else:
            print("Failed to connect to Modbus server")

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        client.close()  # Close connection after usage
        print("Connection closed")

#asyncio.run(read("tcp", "192.168.0.99", 502))
