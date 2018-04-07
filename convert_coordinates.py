import os
import requests
import re
import json
import sqlite3

connection = sqlite3.connect('enderecos.db')
c = connection.cursor()

data_dir = "/Users/mauricio.karas/PycharmProjects/coordinates/data_points"
key = "AIzaSyBYMwq_MqG3aNIjbZvGU4-eBnDu7wD69Xo"


# latitude	longitude	rua	numero	bairro	cidade	cep	estado	pais endereço
def create_table():
    c.execute(
        """CREATE TABLE IF NOT EXISTS enderecos
        (latitude TEXT, longitude TEXT, rua TEXT, numero TEXT, 
        bairro TEXT, cidade TEXT, cep TEXT, estado TEXT, pais TEXT, endereco_completo TEXT)""")


def sql_insert_address(lat, long, numero, rua, bairro, cidade, cep, estado, pais, endereco):
    try:
        sql = """UPDATE enderecos SET 
        latitude = ?, longitude = ?, rua = ?, numero = ?, bairro = ?, cidade = ?, cep = ?,  estado = ?, pais = ?, 
        endereco_completo = ?;""".format(lat, long, rua, numero, bairro, cidade, cep, estado, pais, endereco)

        c.execute(sql)
        connection.commit()

    except Exception as e:
        print('Erro insert: ', str(e))


def call_api(lat, long):
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&key={2}".format(lat, long, key)
    response = requests.get(url)
    #print(url)
    content = response.content.decode("utf-8")
    return get_json(content)


def get_json(content):
    js = json.loads(content)
    return js


def get_json_api_exceeded(file):
    js = json.load(open(file))
    return js


def get_address(jason_data):
    address_dict = {"rua":"", "numero":"", "bairro":"", "cidade":"", "estado":"", "pais":"", "cep":"", "endereco_completo":""}

    for i in jason_data["results"][0]["address_components"]:
        if i["types"] == ["route"]:
            address_dict["rua"] = i["long_name"]
        elif i["types"] == ["street_number"]:
            address_dict["numero"] = i["long_name"]
        elif i["types"] == ['political', 'sublocality', 'sublocality_level_1']:
            address_dict["bairro"] = i["long_name"]
        elif i["types"] == ['administrative_area_level_2', 'political']:
            address_dict["cidade"] = i["long_name"]
        elif i["types"] == ['administrative_area_level_1', 'political']:
            address_dict["estado"] = i["long_name"]
        elif i["types"] == ['country', 'political']:
            address_dict["pais"] = i["long_name"]
        elif i["types"] == ['postal_code', 'postal_code_prefix']:
            address_dict["cep"] = i["long_name"]

    address_dict["endereco_completo"] = jason_data["results"][0]["formatted_address"]

    return address_dict


coordinates_regex = re.compile(r'^(?:Latitude|Longitude).+(?:S|W)\s\s\s([0-9\.\-]+)$')
def get_latlong_from_line(coor):
    match = coordinates_regex.match(coor)
    if match:
        coordinates_number = match.group(1)
        return coordinates_number
    else:
        return "Not valid"  # CHANGE THIS


def get_coordinates(directory):
    lat_list, long_list = [], []

    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename)) as file:
            for line in file:
                if line.startswith("Latitude"):
                    lat_list.append(get_latlong_from_line(line))
        with open(os.path.join(directory, filename)) as file:
            for line in file:
                if line.startswith("Longitude"):
                    long_list.append(get_latlong_from_line(line))

    coordinates_list = [coor for coor in zip(lat_list, long_list)]

    return coordinates_list


def main():

    create_table()
    '''
    coordinates_list = get_coordinates(data_dir)
    
    for coor in coordinates_list:
        result = call_api(coor[0], coor[1])
        address = get_address(result)
        print(address)

        #sql_insert_address(coor[0])
    '''
    result = get_json_api_exceeded("test.json")

    address = get_address(result)



if __name__ == '__main__':
    main()
