
import re
import os
from datetime import datetime, timedelta
from ah_grinder import AhGrinder
from item import ItemStat
from utils import read_json_from_file, read_json_from_file_compressed

header_format = "{:<25} {:<15} {:<20} {:<20} {:<20} {:<20} {:<20}"

def get_data_file_names(data_dir: str) -> list[str]:

    files = os.listdir(data_dir)

    files = filter_files(files)

    files.sort()

    return files

def filter_files(files: list[str]) -> list[str]:
    filtered_files = []
    date_time_obj_x_days_ago = datetime.now() - timedelta(days=14)
    for file in files:

        # get the date time from the file name
        # and check if it is within the last x day
        match = re.search(r'(\d{4}_\d{2}_\d{2}_18_\d{2}_\d{2})', file)
        if match:
            date_time_str = match.group(1)
            date_time_obj = datetime.strptime(date_time_str, '%Y_%m_%d_%H_%M_%S')
            if date_time_obj >= date_time_obj_x_days_ago:
                filtered_files.append(file)

    return filtered_files

class AhAnalyzer:
    item_stats = {} # item_id -> ItemStat

    def __init__(self):
        self.read_historic_responses()
        self.get_latest_response()
        self.create_item_statistics()

    def read_historic_responses(self):
        data_directory = os.path.abspath('./data')
        json_gz_files = get_data_file_names(data_directory)
        # it is important that json_gz_files is sorted

        for file_name in json_gz_files:
            print("Reading file: ", file_name)
            dt = datetime.strptime(file_name, "auctions_%Y_%m_%d_%H_%M_%S.json.gz")
            time_stamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            file_path = os.path.join(data_directory, file_name)
            response = read_json_from_file_compressed(file_path)
            auctions = response['auctions']
            self.add_auction_info(time_stamp, auctions)

    def get_latest_response(self):
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("getting latest auctions: ", time_stamp)
        ah_grinder = AhGrinder()
        connected_realm_id = 5220 # stitches eu hardcore realm id
        auction_house_id = 2 # alliance auction house id
        response = ah_grinder.get_auctions(connected_realm_id=connected_realm_id, auction_house_id=auction_house_id, save_response=False)
        response_json = response.json()
        latest_auctions = response_json['auctions']
        print("last modified: ", response.headers['last-modified'])
        self.add_auction_info(time_stamp, latest_auctions)


    def add_auction_info(self, time_stamp: str, auctions: dict):
        for auction in auctions:
            item_id = auction['item']['id']

            # we need this for some reason because else some statistics, like min_price,
            # can become zero. why do auctions exist with 0 buyout?
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

        # read the sell price from the json file
        item_info = read_json_from_file("item_info.json")

        for item_id, item in self.item_stats.items():

            # try to get the sell price and item name from the json file
            try:
                item.sell_price = item_info[str(item_id)]['sell_price']
                item.name = item_info[str(item_id)]['name']
            except KeyError:
                #print(f"item_id {item_id} not found")
                item.sell_price = 0
                item.name = "unknown" + str(item_id)

            item.calculate_statistics()

            self.item_stats[item_id] = item


    def print_items_with_highest_score(self):
        items = []

        for item_id, item in self.item_stats.items():
            if item.min_quantity > 10:
                items.append(item)

        # sort the items ids by the largest score, largest comes first
        sorted_items = sorted(items, key=lambda x: x.score, reverse=True)

        # get the item names of those item ids and their median avg median price
        num_items_to_show = 10
        #header_format = "{:<25} {:<15} {:<20} {:<20} {:<20} {:<20}"
        #header_format = "{:<25} {:<15} {:<20} {:<50} {:<25}"

        print(header_format.format("item_name", "score", "latest_min_price", "min_min_price", "median_min_price", "max_min_price", "min/median/max_quantity"))
        for item in sorted_items[:num_items_to_show]:
            item.print_statistics()

    def print_item_statistics(self, item_name: str):
        for item in self.item_stats.values():
            if item.name.lower() == item_name:
                item.print_statistics()
                break



if __name__ == '__main__':

    ah_analyzer = AhAnalyzer()
    ah_analyzer.print_items_with_highest_score()
    ah_analyzer.print_item_statistics("devilsaur leather")

        # TODO

        # min quantity is always at least one. make sure that each item has at least None auctions at every day.

        # fetch all the auction data again but this time save everything. you want to know if an item is grey or not
        # and in the future you probably want to look at even more info

        # auctions seems to be updated at xx:16 to xx:17 every hour.

        # the command for copying from the pi is
        #  scp -n pi@raspberrypi.local:~/auctions* data/.
        # the -n flag does so that existing files are not overwritten
        # rsync -av --ignore-existing pi@raspberrypi.local:~/auctions* data/

#         Explanation:

# -av: Archive mode with verbose output.
# --ignore-existing: Skip files that already exist at the destination.
# pi@raspberrypi.local:~/auctions*: Source path on the remote server. This assumes you are copying files matching the pattern auctions* from the home directory of the pi user on the Raspberry Pi.
# data/: Destination directory on your local machine.
# This rsync command will only copy files that don't already exist in the destination directory (data/), similar to the -n option in scp.






