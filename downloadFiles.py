import os
from dotenv import load_dotenv
from sec_api import QueryApi
from sec_api import ExtractorApi
import json

load_dotenv()

api_key = os.getenv("SEC_API_KEY")
query_api = QueryApi(api_key=api_key)

companies = {
    "Apple": "320193",
    "Microsoft": "789019",
    "Alphabet": "1652044",
    "Nvidia": "1045810"
}

def get_latest_10k(company_name, cik):

    query = {
        "query": f"cik:{cik} AND formType:\"10-K\"",
        "from": "0",
        "size": "1",  
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    response = query_api.get_filings(query)
    filings = response.get('filings', [])
    
    if filings:
        latest_filing = filings[0]
        return {
            "name": company_name,
            "filedAt": latest_filing['filedAt'],
            "url": latest_filing['linkToFilingDetails']
        }
    return None

metadatas = []
for name, cik in companies.items():
    metadata = get_latest_10k(name, cik)
    if metadata:
        metadatas.append(metadata)


with open("Extracted/filings_metadata.json", "w") as file:
    json.dump(metadatas, file)

extractor = ExtractorApi(api_key)
data = []

for metadata in metadatas:
    a = {"name": metadata["name"], "filedAt": metadata["filedAt"]}
    a['item_1a_text'] = extractor.get_section(metadata['url'], "1A", "text")
    a['item_1_text'] = extractor.get_section(metadata['url'], "1", "text")
    data.append(a)

with open("Extracted/filings_data.json", "w") as file:
    json.dump(data, file)

