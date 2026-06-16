import json
import os



with open("Extracted/filings_data.json", "r") as file:
    data = json.load(file)

for a in data:
    with open(f'Extracted/{a["name"]}_filing.txt', 'w') as file:
        file.write(a['item_1a_text'])
        file.write(a['item_1_text'])
