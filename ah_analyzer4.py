import gzip
from dataclasses import dataclass
import re
import statistics
import os
from datetime import datetime
import json
from ah_grinder import AhGrinder
#import pandas as pd

def read_json_from_file_compressed(file_name: str) -> dict:
    with gzip.open(file_name, 'rb') as f:
        json_str = f.read().decode('utf-8')

    data = json.loads(json_str)
    return data

def read_json_from_file(file_name: str) -> dict:
    with open(file_name) as json_file:
        data = json.load(json_file)
    return data

def get_data_file_names(data_dir: str) -> list[str]:
    # Get all compressed auction files
    files_in_directory = os.listdir(data_dir)
    json_gz_files = [file for file in files_in_directory if file.startswith('auctions') and file.endswith('.json.gz')]

    # Regular expression pattern to match desired format
    pattern = re.compile(r'auctions_2023_11_\d{2}_18_\d{2}_\d{2}.json.gz')
    json_gz_files = [file for file in files_in_directory if pattern.match(file)]
    json_gz_files.sort()

    return json_gz_files

@dataclass
class Money:
    value: int
    gold: int = 0
    silver: int = 0
    copper: int = 0

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Value must be a non-negative integer")
        self.value = int(self.value)
        self.gold, remaining_value = divmod(self.value, 10000)  # 1 gold = 10000 value
        self.silver, self.copper = divmod(remaining_value, 100)  # 1 silver = 100 value, 1 copper = 1 value

    def __str__(self):
        return f"{self.gold}g,{self.silver}s,{self.copper}c"
    # # Example usage:
    # money_obj = Money(value=12345)

#@dataclass
class ItemStats:
    def __init__(self):
        self.item_id: int = None
        self.time_stamps: list[str] = []
        self.auctions: dict = {} # time_stamp -> {unit_prices: [], quantities: []}
        self.min_unit_prices: list[int] = []
        self.median_unit_prices: list[int] = []
        self.max_unit_prices: list[int] = []
        self.quantities: list[int] = []
        self.min_min_unit_price: int = None
        self.median_min_unit_price: int = None
        self.max_min_unit_price: int = None
        self.min_quantity: int = None
        self.median_quantity: int = None
        self.max_quantity: int = None
        self.latest_min_unit_price: int = None
        self.latest_time_stamp: str = None
        self.score: int = None

        self.name: str = None
        self.sell_price: int = None # the price at which the item is sold to a vendor


        # to implement
        # self.sell_price: int = None # the price at which the item is sold to a vendor
        # self.auction_fee: int = None # the fee you pay when you sell one unit of item at the auction house.
        # this is 5% of the sell price. you get the fee back if someone buys it. else its gone.

        # to get this info you need to do an api request to blizzard.
        # make the api request once and save the response for all items in a file
        # there are roughly 16k items in wow.
        # you can make 100 requests per second
        # so do this once, save the item_id, item_name, sell_price in a csv file
        # then you read this csv file once and can get the name and sell price without doing any more requests


class AhAnalyzer:
    item_stats = {} # item_id -> ItemStats

    def __init__(self, the_item_id: int=None):
        self.read_historic_responses(the_item_id)
        self.read_latest_response(the_item_id)
        self.create_item_statistics()

    def read_historic_responses(self, the_item_id: int=None):
        data_directory = os.path.abspath('./data2')
        json_gz_files = get_data_file_names(data_directory)
        # it is important that json_gz_files is sorted

        # read historic auction data
        for file_name in json_gz_files:
            print("Processing file: ", file_name)
            dt = datetime.strptime(file_name, "auctions_%Y_%m_%d_%H_%M_%S.json.gz")
            time_stamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            file_path = os.path.join(data_directory, file_name)
            response = read_json_from_file_compressed(file_path)
            auctions = response['auctions']
            self.add_auction_info(time_stamp, auctions, the_item_id)

    def read_latest_response(self, the_item_id: int=None):
        ah_grinder = AhGrinder()
        connected_realm_id = 5220 # stitches eu hardcore realm id
        auction_house_id = 2 # alliance auction house id
        response = ah_grinder.get_auctions(connected_realm_id=connected_realm_id, auction_house_id=auction_house_id, save_response=False)
        response_json = response.json()
        latest_auctions = response_json['auctions']
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("getting latest auctions: ", time_stamp)
        print("last modified: ", response.headers['last-modified'])
        self.add_auction_info(time_stamp, latest_auctions, the_item_id)


    def add_auction_info(self, time_stamp: str, auctions: dict, the_item_id: int=None):
        for auction in auctions:
            item_id = auction['item']['id']

            # we need this for some reason because else some statistics, like min_price,
            # can become zero
            buyout = auction['buyout']
            if buyout == 0:
                continue

            # is it the item_id we are looking for?
            if the_item_id is not None and item_id != the_item_id:
                continue

            # if the item does not exist, create it.
            item = self.item_stats.get(item_id)
            if item is None:
                item = ItemStats()
                item.item_id = item_id

            quantity = auction['quantity']
            unit_price = buyout / quantity

            if time_stamp not in item.auctions:
                item.auctions[time_stamp] = {'unit_prices': [], 'quantities': []}

            item.auctions[time_stamp]['unit_prices'].append(unit_price)
            item.auctions[time_stamp]['quantities'].append(quantity)
            self.item_stats[item_id] = item


    def create_item_statistics(self):

        # read the sell price from the json file
        item_info = read_json_from_file("item_info.json")

        for item_id, item in self.item_stats.items():
            for time_stamp in item.auctions:

                unit_prices = item.auctions[time_stamp]['unit_prices']
                quantities = item.auctions[time_stamp]['quantities']
                min_unit_price = min(unit_prices)
                max_unit_price = max(unit_prices)
                median_unit_price = statistics.median(unit_prices)
                quantity = sum(quantities)

                item.time_stamps.append(time_stamp)
                item.min_unit_prices.append(min_unit_price)
                item.max_unit_prices.append(max_unit_price)
                item.median_unit_prices.append(median_unit_price)
                item.quantities.append(quantity)

            item.min_min_unit_price = min(item.min_unit_prices)
            item.median_min_unit_price = statistics.median(item.min_unit_prices)
            item.max_min_unit_price = max(item.min_unit_prices)
            item.min_quantity = min(item.quantities)
            item.median_quantity = statistics.median(item.quantities)
            item.max_quantity = max(item.quantities)
            item.latest_time_stamp = max(item.time_stamps)
            item.latest_min_unit_price = item.min_unit_prices[-1]

            # calculate the score
            potential_sell_price = item.median_min_unit_price
            auction_house_cut = potential_sell_price * 0.05
            buyout_price = item.latest_min_unit_price
            potential_profit = potential_sell_price - auction_house_cut - buyout_price
            item.score = potential_profit

            # get the sell price and item name from the json file
            try:
                item.sell_price = item_info[str(item_id)]['sell_price']
                item.name = item_info[str(item_id)]['name']
            except KeyError:
                print(f"item_id {item_id} not found")
                item.sell_price = 0
                item.name = "unknown"

            self.item_stats[item_id] = item


    def print_items_with_highest_score(self):
        items = []

        for item_id, item in self.item_stats.items():
            if item.min_quantity >= 100:
                items.append(item)

        # sort the items ids by the largest score, largest comes first
        sorted_items = sorted(items, key=lambda x: x.score, reverse=True)

        # get the item names of those item ids and their median avg median price
        num_items_to_show = 10
        header_format = "{:<25} {:<15} {:<20} {:<20} {:<20} {:<20}"

        print(header_format.format("item_name", "score", "latest_min_price", "median_min_price", "max_min_price", "min_quantity"))
        ah_grinder = AhGrinder()
        for item in sorted_items[:num_items_to_show]:
            #item_name = ah_grinder.get_item_name(item.item_id) # this is an api requests and takes some time
            item_name = item.name
            min_min_price = str(Money(item.min_min_unit_price))
            median_min_price = str(Money(item.median_min_unit_price))
            max_min_price = str(Money(item.max_min_unit_price))
            latest_min_price = str(Money(item.latest_min_unit_price))
            score = str(Money(item.score))
            min_quantity = str(item.min_quantity)
            print(header_format.format(item_name, score, latest_min_price, median_min_price, max_min_price, min_quantity))


def get_item_summary(self, item_name: str):
    ah_grinder = AhGrinder()
    item_id = ah_grinder.get_item_id(item_name)
    ah_analyzer = AhAnalyzer(item_id)
    ah_analyzer.print_items_with_highest_score()




if __name__ == '__main__':

    ah_analyzer = AhAnalyzer()
    ah_analyzer.print_items_with_highest_score()
    #ah_analyzer.get_item_summary("Greater Mana Potion")

        # TODO

        # auctions seems to be updated at xx:16 to xx:17 every hour.

        # calculate the total item quantity below the median_min_price and display it for each item listed in the top 10

        # implement a function to get the item id from an item name and get its statistics
        # make the raspberry pi able to pull from your git repo
        # the command for copying from the pi is
        #  scp -n pi@raspberrypi.local:~/auctions* data2/.
        # the -n flag does so that existing files are not overwritten
        # rsync -av --ignore-existing pi@raspberrypi.local:~/auctions* data2/

#         Explanation:

# -av: Archive mode with verbose output.
# --ignore-existing: Skip files that already exist at the destination.
# pi@raspberrypi.local:~/auctions*: Source path on the remote server. This assumes you are copying files matching the pattern auctions* from the home directory of the pi user on the Raspberry Pi.
# data2/: Destination directory on your local machine.
# This rsync command will only copy files that don't already exist in the destination directory (data2/), similar to the -n option in scp.






