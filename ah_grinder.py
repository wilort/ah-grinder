import requests
from client_secrets import client_id, client_secret
from utils import save_json_to_file, save_json_to_file_compressed, read_first_column

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

        response_json = response.json()
        # auctions = response_json['auctions']

        if save_response:
            save_json_to_file_compressed(response_json)

        return response


    def get_auction_house_ids(self, connected_realm_id: int) -> dict:
        namespace = 'dynamic-classic1x-eu'

        url = f"https://{self.region}.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/index?namespace={namespace}&locale={self.locale}&access_token={self.access_token}"

        print(url)
        response = requests.get(url)
        auction_house_ids_respons = response.json()
        return auction_house_ids_respons

    def get_server_id(self, server_name: str) -> int:
        namespace = 'dynamic-classic1x-eu'
        url = f"https://{self.region}.api.blizzard.com/data/wow/search/connected-realm?namespace={namespace}&realms.name.en_US={server_name}&access_token={self.access_token}"
        response = requests.get(url)
        server_id = response.json()['results'][0]['data']['id']
        print(response.json())
        print(server_id)
        return server_id

    def get_item_name(self, item_id: int) -> str:
        namespace = 'static-classic-eu'
        locale = 'en_US'
        url = f"https://{self.region}.api.blizzard.com/data/wow/item/{item_id}?namespace={namespace}&locale={locale}&access_token={self.access_token}"
        response = requests.get(url)
        item_name= response.json()['name']
        return item_name

    def get_item_id(self, name: str) -> int:
        namespace = 'static-classic-eu'
        url = f"https://{self.region}.api.blizzard.com/data/wow/search/item?namespace={namespace}&name.en_US={name}&access_token={self.access_token}"
        response = requests.get(url)
        # there may be several results, but we just take the first one
        item_id = response.json()['results'][0]['data']['id']
        return item_id

    def get_item_info(self, item_id: int) -> dict:
        namespace = 'static-classic-eu'
        locale = 'en_US'
        url = f"https://{self.region}.api.blizzard.com/data/wow/item/{item_id}?namespace={namespace}&locale={locale}&access_token={self.access_token}"
        response = requests.get(url)
        #item_info = response.json()
        #name = item_info['name']
        #sell_price = item_info['sell_price']
        #return item_info
        return response

    def get_all_item_info(self):
        item_jsons = {}
        strange_item_jsons = {}
        item_ids = set(read_first_column('items_id_and_name.csv'))
        #item_ids = range(5205,5206)
        for i, item_id in enumerate(item_ids):
            print(i, item_id)
            item_response = self.get_item_info(item_id)
            if item_response.status_code == 200:
                item_jsons[item_id] = item_response.json()
            elif item_response.status_code == 404:
                continue # there is no item with this item_id
            else:
                strange_item_jsons[item_id] = item_response

        print("problematic responses:")
        print(strange_item_jsons.keys())
        print("saving to file: item_responses.json.gz")
        save_json_to_file_compressed(item_jsons, file_name='item_jsons.json.gz')
        pass


def get_all_item_info():

# these item ids were shit for some reason.
# i.e. i coulld get a response from the blizzard api
# ['7748', '2441', '17968', '14479', '1024', '11556', '6987', '14477', '16999', '18000', '14505', '18005', '12400', '17733', '14478', '11555', '14473', '14504', '18401', '11554', '18001', '14472', '4111', '1167', '1166', '2133', '14500', '1193', '14491', '8964', '18566', '2444', '4851', '9602', '7678', '11546', '11553', '18513', '14480', '16057', '14485', '2443', '1255', '9186', '17782', '4110', '2377', '14484', '11558', '11559', '14495', '1027', '18489', '2442', '18565', '11545', '7809', '128', '14498', '11548', '5140', '14481', '11549', '11547', '19760', '11550', '3034', '0', '2499', '11364', '11551', '997', '11552', '5105', '11557', '14469']

    ah_grinder = AhGrinder()
    # read all the item ids from the file in items_id_and_name.csv
    # make a set out of this list
    item_ids = set(read_first_column('items_id_and_name.csv'))
    item_info = {}
    shitty_item_ids = []
    for i, item_id in enumerate(item_ids):
        item = ah_grinder.get_item_info(item_id)
        try:
            item_info[item_id] = {}
            item_info[item_id]['name'] = item['name']
            item_info[item_id]['sell_price'] = item['sell_price']
        except:
            print(f"shitty item_id: {item_id}")
            shitty_item_ids.append(item_id)

        #time.sleep(1/1000)
        print(i)
        # if i > 100:
        #     break
    # save the item info to a file as json
    print(shitty_item_ids)
    save_json_to_file(item_info, file_name='item_info.json')




    save_json_to_file(item_responses, file_name='item_responses.json')

if __name__ == '__main__':
    ah_grinder = AhGrinder()
    #connected_realm_id = ah_grinder.get_server_id("stitches")
    #auction_house_ids_respons = ah_grinder.get_auction_house_ids(connected_realm_id)
    # connected_realm_id = 5220 # stitches eu hardcore realm id
    # auction_house_id = 2 # alliance auction house id
    # response = ah_grinder.get_auctions(connected_realm_id, auction_house_id, save_response=True)
    # response_json = response.json()
    # auctions = response_json['auctions']
    #item_id = ah_grinder.get_item_id("Thunderfury")

    #get_all_item_info()
    ah_grinder.get_all_item_info()
