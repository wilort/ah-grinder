import re
import os
from datetime import datetime
from ah_grinder import AhGrinder
from item import ItemStat
from utils import get_data_file_names, read_json_from_file_compressed

header_format = "{:<25} {:<15} {:<20} {:<20} {:<20} {:<20} {:<20}"


class AhAnalyzer:
    item_stats: dict[int, ItemStat] = {} # item_id -> ItemStat
    time_stamps: list[str] = []

    def __init__(self):
        # first read information about all items and create the item_stats dictionary
        # then read all the auctions and add the auction info.
        # then calculate the item statistics


        self.read_historic_auctions()
        self.get_latest_auctions()
        self.create_item_statistics()

    def read_item_info(self):
        item_responses = read_json_from_file_compressed("item_responses.json.gz")
        for item_id, item_response in item_responses.items():
            item = ItemStat()
            item.item_id = item_id
            item.sell_price = item_response['sell_price']
            item.name = item_response['name']
            item.quality = item_response['quality']['type']
            item.class_name = item_response['item_class']['name']
            self.item_stats[item_id] = item

    def read_historic_auctions(self):
        data_directory = os.path.abspath('./data')
        json_gz_files = get_data_file_names(data_directory)
        # it is important that json_gz_files is sorted, last date at the end

        for file_name in json_gz_files:
            print("Reading file: ", file_name)
            dt = datetime.strptime(file_name, "auctions_%Y_%m_%d_%H_%M_%S.json.gz")
            time_stamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.time_stamps.append(time_stamp)
            file_path = os.path.join(data_directory, file_name)
            response = read_json_from_file_compressed(file_path)
            auctions = response['auctions']
            self.add_auction_info(time_stamp, auctions)

    def get_latest_auctions(self):
        ah_grinder = AhGrinder()
        connected_realm_id = 5220 # stitches eu hardcore realm id
        auction_house_id = 2 # alliance auction house id
        response = ah_grinder.get_auctions(connected_realm_id=connected_realm_id, auction_house_id=auction_house_id, save_response=False)
        response_json = response.json()
        latest_auctions = response_json['auctions']

        dt_now = datetime.utcnow()
        time_stamp = dt_now.strftime("%Y-%m-%d %H:%M:%S")
        self.time_stamps.append(time_stamp)
        self.add_auction_info(time_stamp, latest_auctions)

        # print some information about the response
        last_modified = response.headers['last-modified']
        dt_last_modified = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
        time_since_last_modified = dt_now - dt_last_modified
        minutes_since_last_modified, remaining_seconds = divmod(time_since_last_modified.seconds, 60)
        print("latest auctions request: ", time_stamp)
        print(f"last modified: {last_modified}")
        print(f"time since last modified: {minutes_since_last_modified} minutes and {remaining_seconds} seconds")

    def add_auction_info(self, time_stamp: str, auctions: dict):
        for auction in auctions:
            item_id = auction['item']['id']

            # auctions with zero buyout price exist but never appear in raelity.
            # ignore them.
            buyout = auction['buyout']
            if buyout == 0:
                continue

            # if the item does not exist, create it.
            item = self.item_stats.get(item_id)
            if item is None:
                item = ItemStat()
                item.item_id = item_id

            quantity = auction['quantity']
            unit_price = buyout / quantity

            if time_stamp not in item.auctions:
                item.auctions[time_stamp] = {'unit_prices': [], 'quantities': []}

            item.auctions[time_stamp]['unit_prices'].append(unit_price)
            item.auctions[time_stamp]['quantities'].append(quantity)
            self.item_stats[item_id] = item


    def create_item_statistics(self):
        """
        Read preprocessed api calls for each item and set and calculate the item statistics.
        """
        item_responses = read_json_from_file_compressed("item_responses.json.gz")

        # TODO: make sure we get item statistics for each time stamp even tho the item was not seen
        # at that timestamp. This is important for the score calculation.ge fdaf
        for item_id, item in self.item_stats.items():
            item_id_str = str(item_id)
            # try to get the sell price and item name from the json file
            try:
                item_response = item_responses[item_id_str]
                item.sell_price = item_response['sell_price']
                item.name = item_response['name']
                item.quality = item_response['quality']['type']
                item.class_name = item_response['item_class']['name']
            except KeyError:
                #print(f"item_id {item_id} not found")
                item.name = "unknown" + item_id_str

            item.calculate_statistics()

            self.item_stats[item_id] = item


    def print_items_with_highest_score(self):
        items = []

        for item_id, item in self.item_stats.items():
            if item.min_quantity > 100:
                items.append(item)

        # sort the items ids by the largest score, largest comes first
        sorted_items = sorted(items, key=lambda x: x.score, reverse=True)

        num_items_to_show = 10

        print(header_format.format("item_name", "score", "latest_min_price", "min_min_price", "median_min_price", "max_min_price", "min/median/max_quantity"))
        for item in sorted_items[:num_items_to_show]:
            item.print_statistics()

    def print_item_statistics(self, item_name: str):
        for item in self.item_stats.values():
            if item.name.lower() == item_name.lower():
                item.print_statistics()
                return
        print(f"no item found with the name: {item_name}")


if __name__ == '__main__':
    ah_analyzer = AhAnalyzer()
    ah_analyzer.print_items_with_highest_score()
    ah_analyzer.print_item_statistics("Savory deviate delight")
