import requests
from datetime import datetime



client_id = "242c003436074d628bae15af629bce2f"
client_secret = "VivOf0TQYxZ1NrjUTogJYNaEyEx2wwuj"

def create_access_token():
    data = {
        'grant_type': 'client_credentials',
    }

    response = requests.post('https://oauth.battle.net/token', data=data, auth=(client_id, client_secret))

    access_token = response.json()['access_token']

    return access_token

def get_auction_house_index_working(connected_realm_id):
    connected_realm_id = 1587
    #namespace = 'dynamic-classic1x-eu'
    #namespace = 'dynamic-classic-eu'
    namespace = 'dynamic-eu'
    locale = 'en_GB'
    access_token = create_access_token()

    #url = f'https://eu.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/index&access_token='
    #url = "https://eu.api.blizzard.com/data/wow/connected-realm/1587/auctions?namespace=dynamic-eu&locale=en_GB&access_token="
    url = f"https://eu.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions?namespace={namespace}&locale={locale}&access_token={access_token}"
    #url = f"https://eu.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions?access_token="
    print(url)
    response = requests.get(url)
    #print(response.json())
    nr_of_auctions = len(response.json()['auctions'])
    #print(len(response.json()))
    print(nr_of_auctions)

def get_auction_house_auctions():
    region = 'eu'
    namespace = 'dynamic-classic1x-eu'
    locale = 'en_US'
    auction_house_id = 2 # alliance auction house
    access_token = create_access_token()

    url = f"https://{region}.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/{auction_house_id}?namespace={namespace}&locale={locale}&access_token={access_token}"

    print(url)
    response = requests.get(url)
    #print(response.json())

    auctions = response.json()['auctions']
    nr_of_auctions = len(auctions)
    print(nr_of_auctions)
    return auctions


def get_auction_house_id(connected_realm_id):
    region = 'eu'
    namespace = 'dynamic-classic1x-eu'
    locale = 'en_GB'
    access_token = create_access_token()

    url = f"https://{region}.api.blizzard.com/data/wow/connected-realm/{connected_realm_id}/auctions/index?namespace={namespace}&locale={locale}&access_token={access_token}"

    print(url)
    response = requests.get(url)
    auction_house_id = response.json()
    #print(response.json())
    return auction_house_id

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
    #https://eu.api.blizzard.com/data/wow/search/connected-realm?namespace=dynamic-eu&realms.name.en_US=kazzak&access_token=YOUR_TOKEN

    url = f"https://eu.api.blizzard.com/data/wow/search/connected-realm?namespace=dynamic-classic1x-eu&realms.name.en_US={server_name}&access_token="
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


if __name__ == '__main__':
    connected_realm_id = get_server_id("stitches")
    auction_house_id = get_auction_house_id(connected_realm_id)
    auctions = get_auction_house_auctions()
    #item_name = get_item_name(10548)
    analyze_auctions = analyze_auctions(auctions)
    print(analyze_auctions)
    # {time: xx:xx, auctions: [{item_id: {item_name: name, quantity: 0, price: 0}, ...}, ...]}
