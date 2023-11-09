import gzip
from dataclasses import dataclass
import re
import statistics
import os
from datetime import datetime
import json
from ah_grinder import get_item_name, AhGrinder

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




class AhAnalyzer:

    auctions_info = dict() # {item_idx: {time_stamp: {unit_prices:[x,y,z], quantities:[x,y,z], min_unit_price:x, median_unit_price:y, max_unit_price:z }}
    time_stamps = []
    def __init__(self):
        self.read_responses()
        self.calculate_item_statistics()

    def read_responses(self):
        data_directory = os.path.abspath('./data2')
        json_gz_files = get_data_file_names(data_directory)

        # read historic auction data
        for file_name in json_gz_files:
            print("Processing file: ", file_name)
            dt = datetime.strptime(file_name, "auctions_%Y_%m_%d_%H_%M_%S.json.gz")
            time_stamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.time_stamps.append(time_stamp)
            file_path = os.path.join(data_directory, file_name)
            response = read_json_from_file_compressed(file_path)
            auctions = response['auctions']
            self.add_auction_info(time_stamp, auctions)

        # get latest auction data
        ah_grinder = AhGrinder()
        connected_realm_id = 5220 # stitches eu hardcore realm id
        auction_house_id = 2 # alliance auction house id
        latest_auctions = ah_grinder.get_auctions(connected_realm_id=connected_realm_id, auction_house_id=auction_house_id, save_response=False)
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_stamps.append(time_stamp)
        print("getting latest auctions: ", time_stamp)
        self.add_auction_info(time_stamp, latest_auctions)

    def add_auction_info(self, time_stamp, auctions):
        for auction in auctions:
            item_id = auction['item']['id']
            buyout = auction['buyout']
            quantity = auction['quantity']
            unit_price = buyout / quantity

            # we need this for some reason because else the min price is 0 some times
            if unit_price == 0:
                continue

            if item_id not in self.auctions_info:
                self.auctions_info[item_id] = {}

            if time_stamp not in self.auctions_info[item_id]:
                self.auctions_info[item_id][time_stamp] = {'unit_prices':[], 'quantities':[]}

            self.auctions_info[item_id][time_stamp]['unit_prices'].append(unit_price)
            self.auctions_info[item_id][time_stamp]['quantities'].append(quantity)

    def calculate_item_statistics(self):

        # calculate the min, median and max unit price for each item and time stamp
        for item_id in self.auctions_info:
            for time_stamp in self.auctions_info[item_id]:
                unit_prices = self.auctions_info[item_id][time_stamp]['unit_prices']
                quantities = self.auctions_info[item_id][time_stamp]['quantities']
                min_unit_price = min(unit_prices)
                max_unit_price = max(unit_prices)
                median_unit_price = statistics.median(unit_prices)
                quantity = sum(quantities)
                self.auctions_info[item_id][time_stamp]['min_unit_price'] = min_unit_price
                self.auctions_info[item_id][time_stamp]['median_unit_price'] = median_unit_price
                self.auctions_info[item_id][time_stamp]['max_unit_price'] = max_unit_price
                self.auctions_info[item_id][time_stamp]['quantity'] = quantity

    def analyze_auctions(self):
        item_ids = []

        # select the item ids that have consistent quantity above min_quantity
        min_quantity = 100
        for item_id in self.auctions_info:
            item_quantities = []
            for time_stamp in self.auctions_info[item_id]:
                # we have an issue here because the time stamp will be latest_min_unit_price. which does not ahve a quantity
                quantity = self.auctions_info[item_id][time_stamp]['quantity']
                item_quantities.append(quantity)

            if min(item_quantities) > min_quantity:
                item_ids.append(item_id)

        # get items statistics
        items_score = []
        for item_id in item_ids:

            min_prices = []
            for time_stamp in self.auctions_info[item_id]:
                min_price = self.auctions_info[item_id][time_stamp]['min_unit_price']
                min_prices.append(min_price)

            max_min_price = max(min_prices)
            min_min_price = min(min_prices)
            median_min_price = statistics.median(min_prices)

            # latest price
            latest_time_stamp = max(self.auctions_info[item_id].keys())
            self.auctions_info[item_id]['latest_time_stamp'] = latest_time_stamp
            latest_min_price = self.auctions_info[item_id][latest_time_stamp]['min_unit_price']

            score = median_min_price - latest_min_price
            items_score.append((item_id, score))

            self.auctions_info[item_id]['median_min_unit_price'] = median_min_price
            self.auctions_info[item_id]['min_min_unit_price'] = min_min_price
            self.auctions_info[item_id]['max_min_unit_price'] = max_min_price


        # sort the items ids by the largest score, largest comes first
        sorted_items_score = sorted(items_score, key=lambda x: x[1], reverse=True)

        # get the item names of those item ids and their median avg median price
        num_items_to_show = 10
        header_format = "{:<25} {:<15} {:<20} {:<20} {:<20}"
        print(header_format.format("item_name", "score", "latest_min_price", "median_min_price", "max_min_price"))
        for item_id, score in sorted_items_score[:num_items_to_show]:
            item_name = get_item_name(item_id)
            min_min_price = str(Money(self.auctions_info[item_id]['min_min_unit_price']))
            median_min_price = str(Money(self.auctions_info[item_id]['median_min_unit_price']))
            max_min_price = str(Money(self.auctions_info[item_id]['max_min_unit_price']))

            # get the latest time stamp in the specified format
            latest_time_stamp = self.auctions_info[item_id]['latest_time_stamp']
            latest_min_price = str(Money(self.auctions_info[item_id][latest_time_stamp]['min_unit_price']))
            score = str(Money(score))
            print(header_format.format(item_name, score, latest_min_price, median_min_price, max_min_price))

        shit = 1



if __name__ == '__main__':

    ah_analyzer = AhAnalyzer()
    ah_analyzer.analyze_auctions()

        # TODO
        # use pandas to store auction info instead of a dict.
        # each line in the pandas dataframe is an auction with columns as info
        # then we can create 
        # implement a function to get the item id from an item name and get its statistics
        # make the raspberry pi able to pull from your git repo
        # the command for copying from the pi is
        #  scp -n pi@raspberrypi.local:~/auctions* data2/.
        # the -n flag does so that existing files are not overwritten