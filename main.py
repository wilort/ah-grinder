import gzip
import requests
from datetime import datetime

import json

client_id = "242c003436074d628bae15af629bce2f"
client_secret = "VivOf0TQYxZ1NrjUTogJYNaEyEx2wwuj"

def create_access_token():
    data = {
        'grant_type': 'client_credentials',
    }

    response = requests.post('https://oauth.battle.net/token', data=data, auth=(client_id, client_secret))

    access_token = response.json()['access_token']

    return access_token

def get_auctions(connected_realm_id, auction_house_id, save_to_file=False):
    region = 'eu'
    namespace = 'dynamic-classic1x-eu'
    locale = 'en_US'
    access_token = create_access_token()

    url = f"https://{region}.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/{auction_house_id}?namespace={namespace}&locale={locale}&access_token={access_token}"

    print(url)
    response = requests.get(url)
    #print(response.json())

    auctions = response.json()#['auctions']
    nr_of_auctions = len(auctions)
    print(nr_of_auctions)

    if save_to_file:
        save_json_to_file_compressed(auctions)
        #save_json_to_file(auctions)

    return auctions


def get_auction_house_ids(connected_realm_id: int):
    region = 'eu'
    namespace = 'dynamic-classic1x-eu'
    locale = 'en_US'
    access_token = create_access_token()

    url = f"https://{region}.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/index?namespace={namespace}&locale={locale}&access_token={access_token}"

    print(url)
    response = requests.get(url)
    auction_house_ids_respons = response.json()
    #print(response.json())
    return auction_house_ids_respons

def get_item_name(item_id):
    region = 'eu'
    namespace = 'static-classic-eu'
    locale = 'en_US'
    access_token = create_access_token()
    url = f"https://{region}.api.blizzard.com/data/wow/item/{item_id}?namespace={namespace}&locale={locale}&access_token={access_token}"
    response = requests.get(url)
    item_name= response.json()['name']
    #print(response.json())
    return item_name

def get_server_id(server_name):
    region = 'eu'
    namespace = 'dynamic-classic1x-eu'
    locale = 'en_US'
    url = f"https://{region}.api.blizzard.com/data/wow/search/connected-realm?namespace={namespace}&realms.name.en_US={server_name}&access_token="
    access_token = create_access_token()
    response = requests.get(url + access_token)
    server_id = response.json()['results'][0]['data']['id']
    print(response.json())
    print(server_id)
    return server_id

def analyze_auctions(auctions):
    analyzed_auctions = {}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for auction in auctions:
        item_id = auction['item']['id']
        #item_name = get_item_name(item_id)
        quantity = auction['quantity']
        buyout_price = auction['buyout']
        unit_price = buyout_price / quantity
        #print(item_id, item_name, quantity, unit_price)

        if item_id in analyzed_auctions:
            current_buyout_price = analyzed_auctions[item_id]['unit_price']
            analyzed_auctions[item_id]['quantity'] += quantity
            analyzed_auctions[item_id]['unit_price'] = min(buyout_price, current_buyout_price)
        else:
            analyzed_auctions[item_id] = {'quantity': quantity, 'unit_price': unit_price}

    return analyzed_auctions

def save_json_to_file_compressed(json_data):
    file_name = 'auctions_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.json.gz'
    json_str = json.dumps(json_data)
    with gzip.open(file_name, 'wb') as f:
        f.write(json_str.encode('utf-8'))

def read_json_from_file_compressed(file_name):
    with gzip.open(file_name, 'rb') as f:
        json_str = f.read().decode('utf-8')

    data = json.loads(json_str)
    return data

def save_json_to_file(json_data):
    file_name = 'auctions_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.json'
    with open(file_name, 'w') as outfile:
        json.dump(json_data, outfile)

def read_json_from_file(file_name):
    with open(file_name) as json_file:
        data = json.load(json_file)
    return data

if __name__ == '__main__':
    #connected_realm_id = get_server_id("stitches")
    #auction_house_ids_respons = get_auction_house_ids(connected_realm_id)
    connected_realm_id = 5220 # stitches eu hardcore realm id
    auction_house_id = 2 # alliance auction house id
    get_auctions(connected_realm_id, auction_house_id, save_to_file=True)

    #auctions = read_json_from_file_compressed('auctions_2023_10_27_17_39_01.json.gz')
    #item_name = get_item_name(10548)
    #analyze_auctions = analyze_auctions(auctions)
    #print(analyze_auctions)
