import gzip
import requests
from datetime import datetime
import json
from client_secrets import client_id, client_secret

def create_access_token() -> str:

    data = {
        'grant_type': 'client_credentials',
    }

    response = requests.post('https://oauth.battle.net/token', data=data, auth=(client_id, client_secret))

    access_token = response.json()['access_token']

    return access_token


class AhGrinder:
    region = 'eu'
    locale = 'en_US'

    def __init__(self):
        self.access_token = create_access_token()

    def get_auctions(self, connected_realm_id: int, auction_house_id: int, save_response: bool=False) -> list[dict]:

        namespace = 'dynamic-classic1x-eu'

        url = f"https://{self.region}.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/{auction_house_id}?namespace={namespace}&locale={self.locale}&access_token={self.access_token}"

        print(url)
        response = requests.get(url)
        #print(response.json())

        response_json = response.json()
        auctions = response_json['auctions']
        #nr_of_auctions = len(auctions)
        #print(nr_of_auctions)

        if save_response:
            save_json_to_file_compressed(response_json)
            #save_json_to_file(auctions)

        return auctions


    def get_auction_house_ids(self, connected_realm_id: int) -> dict:
        namespace = 'dynamic-classic1x-eu'

        url = f"https://{self.region}.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/index?namespace={namespace}&locale={self.locale}&access_token={self.access_token}"

        print(url)
        response = requests.get(url)
        auction_house_ids_respons = response.json()
        #print(response.json())
        return auction_house_ids_respons

    def get_server_id(self, server_name: str) -> int:
        namespace = 'dynamic-classic1x-eu'
        url = f"https://{self.region}.api.blizzard.com/data/wow/search/connected-realm?namespace={namespace}&realms.name.en_US={server_name}&access_token={self.access_token}"
        response = requests.get(url)
        server_id = response.json()['results'][0]['data']['id']
        print(response.json())
        print(server_id)
        return server_id

def save_json_to_file_compressed(json_data):
    file_name = 'auctions_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.json.gz'
    json_str = json.dumps(json_data)
    with gzip.open(file_name, 'wb') as f:
        f.write(json_str.encode('utf-8'))

def save_json_to_file(json_data):
    file_name = 'auctions_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.json'
    with open(file_name, 'w') as outfile:
        json.dump(json_data, outfile)

def get_item_name(item_id: int) -> str:
    region = 'eu'
    namespace = 'static-classic-eu'
    locale = 'en_US'
    access_token = create_access_token()
    url = f"https://{region}.api.blizzard.com/data/wow/item/{item_id}?namespace={namespace}&locale={locale}&access_token={access_token}"
    response = requests.get(url)
    item_name= response.json()['name']
    #print(response.json())
    return item_name

if __name__ == '__main__':
    ah_grinder = AhGrinder()
    #connected_realm_id = ah_grinder.get_server_id("stitches")
    #auction_house_ids_respons = ah_grinder.get_auction_house_ids(connected_realm_id)
    connected_realm_id = 5220 # stitches eu hardcore realm id
    auction_house_id = 2 # alliance auction house id
    auctions = ah_grinder.get_auctions(connected_realm_id, auction_house_id, save_response=True)
