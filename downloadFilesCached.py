import json
from sec_api import ExtractorApi
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SEC_API_KEY")

with open("Extracted/filings_metadata.json", "r") as file:
    metadatas = json.load(file)

extractor = ExtractorApi(api_key)
data = []

for metadata in metadatas:
    a = {"name": metadata["name"], "filedAt": metadata["filedAt"]}
    a['item_1a_text'] = extractor.get_section(metadata['url'], "1A", "text")
    a['item_1_text'] = extractor.get_section(metadata['url'], "1", "text")
    data.append(a)

with open("Extracted/filings_data.json", "w") as file:
    json.dump(data, file)
    
