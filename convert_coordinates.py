import os
import requests
import re
import json
import sqlite3

connection = sqlite3.connect('enderecos2.db')
c = connection.cursor()
sql_transaction = []


key = "AIzaSyCO0FMQRjoiN1z0Xkoo3gPoq1iQyFKx3aE"


def create_table():
    c.execute(
        """CREATE TABLE IF NOT EXISTS enderecos
        (latitude TEXT, longitude TEXT, rua TEXT, numero TEXT, 
        bairro TEXT, cidade TEXT, cep TEXT, estado TEXT, pais TEXT, endereco_completo TEXT)""")


def sql_insert_address(lat, long, numero, rua, bairro, cidade, cep, estado, pais, endereco):
    try:
        sql = """INSERT INTO enderecos
                (latitude, longitude, rua, numero, bairro, cidade, cep, estado, pais, endereco_completo) 
                VALUES ("{}", "{}", "{}", "{}", "{}", 
                "{}", "{}", "{}", "{}", "{}");""".format(lat, long, rua, numero, bairro, cidade, cep, estado, pais, endereco)

        #transaction_builder(sql)
        c.execute(sql)
        connection.commit()

    except Exception as e:
        print('Erro insert: ', str(e))


def transaction_builder(sql):
    global sql_transaction
    sql_transaction.append(sql)
    if len(sql_transaction) > 200:
        c.execute('BEGIN TRANSACTION')
        for s in sql_transaction:
            try:
                c.execute(s)
            except:
                pass
        connection.commit()
        sql_transaction = []


def call_api(lat, long):
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&key={2}".format(lat, long, key)
    response = requests.get(url)
    content = response.content.decode("utf-8")
    return get_json(content)


def get_json(content):
    js = json.loads(content)
    return js


def get_json_api_exceeded(file):
    js = json.load(open(file))
    return js


def get_address(jason_data):
    address_dict = {"rua": "", "numero": "", "bairro": "", "cidade": "", "estado": "",
                    "pais": "", "cep": "", "endereco_completo": ""}
    try:
        #  This is the API json result mapping:
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
            elif i["types"] == ['postal_code', 'postal_code_prefix'] or i["types"] == ['postal_code']:
                address_dict["cep"] = i["long_name"]

        address_dict["endereco_completo"] = jason_data["results"][0]["formatted_address"]
    except Exception as e:
        print("Error in the following JSON result:")
        print(jason_data)
        print("Error: ", e)

    return address_dict


coordinates_regex = re.compile(r'^(?:Latitude|Longitude).+(?:S|W)\s\s\s([0-9\.\-]+)$')
def get_latlong_from_line(coor):
    match = coordinates_regex.match(coor)
    if match:
        coordinates_number = match.group(1)
        return coordinates_number


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


data_dir = "/Users/mauricio.karas/PycharmProjects/coordinates/data_points"


def main():

    create_table()

    coordinates_list = get_coordinates(data_dir)
    total = len(coordinates_list)+1
    
    for index, coordinate in enumerate(coordinates_list):

        result = call_api(coordinate[0], coordinate[1])

        if list(result.keys())[0] == "error_message":
            print(result["error_message"])
            break

        address = get_address(result)
        sql_insert_address(coordinate[0], coordinate[1], address["numero"], address["rua"], address["bairro"],
                       address["cidade"], address["cep"], address["estado"], address["pais"],
                       address["endereco_completo"])
        
        print(str(index+1)+"/"+str(total), str(round(((index+1)/(total)*100), 2)) + "%", end='\r')

if __name__ == '__main__':
    main()
