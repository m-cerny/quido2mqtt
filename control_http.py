import requests, json, os

script_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(script_dir, "config.json")

with open(conf_path, "r") as conf:
    data = json.load(conf)

QUIDO_IP = data["quido_ip"]
QUIDO_HTTP_PORT = data["quido_http_port"]

BASE_URL = f"http://{QUIDO_IP}:{QUIDO_HTTP_PORT}"

def write_coils(output_number: int, function:str) -> None:
    """
    Function to control an output
    modes: r,s,i,p
    """
    function_list = {"on": "s",
                "off": "r",
                "i": "i",
                "r": "r"
                }
    
    url = f"{BASE_URL}/set.xml?type={function_list[function]}&id={output_number}"
    response = requests.get(url)
    
    if response.status_code == 200:
        fce_to_print = function
        print("controlOutput")
        print(f"Output {output_number} set to {fce_to_print}")
    else:
        print("controlOutput")
        print(f"Failed to control output {output_number}. Status code: {response.status_code}")
    
