from datetime import datetime
import gzip
import json
import csv

def read_json_from_file_compressed(file_name: str) -> dict:
    with gzip.open(file_name, 'rb') as f:
        json_str = f.read().decode('utf-8')

    data = json.loads(json_str)
    return data

def read_json_from_file(file_name: str) -> dict:
    with open(file_name) as json_file:
        data = json.load(json_file)
    return data

def save_json_to_file_compressed(json_data, file_name=None):
    if not file_name:
        file_name = 'auctions_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.json.gz'
    json_str = json.dumps(json_data)
    with gzip.open(file_name, 'wb') as f:
        f.write(json_str.encode('utf-8'))

def save_json_to_file(json_data, file_name=None):
    if not file_name:
        file_name = 'auctions_' + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.json'
    with open(file_name, 'w') as outfile:
        json.dump(json_data, outfile, indent=4)

def read_first_column(file_path):
    result_list = []
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            # Assuming you want to ignore the header row
            # If your CSV file doesn't have a header, you can remove this condition
            if csv_reader.line_num == 1:
                continue
            # Append the first column (index 0) to the result list
            result_list.append(row[0])
    return result_list