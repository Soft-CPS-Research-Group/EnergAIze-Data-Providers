import requests

def get_device_info(device_id):
    # Faz o pedido para obter as informações da tag
    token = "CW eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOiI3MzgiLCJVc2VyS2V5IjoiNTk1ZDJjNDctZTVlMi00ZDA5LTg0NzYtODI5NjJlZWYyZmYyIiwiUHJvZmlsZVR5cGUiOiI2IiwiQ3VycmVuY3lTeW1ib2wiOiLigqwiLCJSYW5kb21CeXRlcyI6ImRoNzRVVHFNYjZjPSIsIm5iZiI6MTcxMzc4OTQwNywiZXhwIjoxNzEzNzkzMDA3LCJpc3MiOiJodHRwOi8vY2xlYW53YXR0cy5lbmVyZ3kiLCJhdWQiOiJodHRwOi8vYXBpLmNsZWFud2F0dHMuZW5lcmd5In0.5GgscXI2JmtZs_Fc8aGv1NqchkuF7yqYZ4xF248e1IA"
    headers = {
        "Authorization": token
    }

    # Faz a solicitação inicial para obter informações sobre as tags
    url = f"https://ks.innov.cleanwatts.energy/api/2.0/tags?deviceId={device_id}"
    response = requests.get(url, headers=headers)
    print(response.status_code)
    data = response.json()

    tag_instances = data["List"]

    for tag_instance in tag_instances:
        tag_type_id = tag_instance["TagTypeId"]
        # Faz a solicitação para obter informações sobre o tipo de tag
        tag_type_url = f"https://ks.innov.cleanwatts.energy/api/2.0/tagtype/{tag_type_id}"
        tag_type_response = requests.get(tag_type_url, headers=headers)
        tag_type_info = tag_type_response.json()

        # Extrai as informações relevantes
        tag_id = tag_instance["Id"]
        tag_name = tag_instance["Name"]
        description = tag_type_info["Description"]
        partial = tag_type_info["Partial"]
        measurement_unit = tag_type_info["MeasurementUnit"]
        accumulate = tag_type_info["Accumulate"]
        visible = tag_type_info["Visible"]
        actuator = tag_type_info["Actuator"]

        # Imprime as informações no formato especificado
        print(f"ID {tag_id}")
        print(f"Nome {tag_name}")
        print(f"TagTypeId {tag_type_id}")
        print(f"Description {description}")
        print(f"Partial {partial}")
        print(f"MeasurementUnit {measurement_unit}")
        print(f"Accumulate {accumulate}")
        print(f"Visible {visible}")
        print(f"Actuator {actuator}")
        print()

# Chama a função com o ID da tag passado como parâmetro
get_device_info(5441)
