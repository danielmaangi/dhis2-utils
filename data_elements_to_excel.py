'''
This code pulls data elements from a set of datasets in dhis2 and exports them into an Excel file.
'''
import requests
import pandas as pd
from openpyxl import Workbook

# load dhis2 credentials from .env file
import os
from dotenv import load_dotenv
load_dotenv()
DHIS2_BASE_URL = os.getenv('DHIS2_BASE_URL')
DHIS2_USERNAME = os.getenv('DHIS2_USERNAME')
DHIS2_PASSWORD = os.getenv('DHIS2_PASSWORD')
auth = (DHIS2_USERNAME, DHIS2_PASSWORD)


# functiomn to fetch data elements from dhis2 API fo a given dataset or datasets
def fetch_data_elements(dhis2_url, dataset_ids, auth):
    data_elements = []
    for dataset_id in dataset_ids:
        url = f"{dhis2_url}/api/dataSets/{dataset_id}.json?fields=dataSetElements[dataElement[id,displayName,code,domainType,valueType,categoryCombo[id,displayName]]]"
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        dataset = response.json()
        for element in dataset['dataSetElements']:
            de = element['dataElement']
            data_elements.append({
                'Dataset ID': dataset_id,
                'Data Element ID': de['id'],
                'Display Name': de['displayName'],
                'Code': de.get('code', ''),
                'Domain Type': de.get('domainType', ''),
                'Value Type': de.get('valueType', ''),
                'Category Combo ID': de['categoryCombo']['id'],
                'Category Combo Name': de['categoryCombo']['displayName']
            })
    return data_elements

def export_to_excel(data_elements, output_file):
    df = pd.DataFrame(data_elements)
    df.to_excel(output_file, index=False)

if __name__ == "__main__":
    # specify dataset IDs to fetch data elements from
    dataset_ids = ['Fgv05RXHfNF']  # replace with actual dataset IDs
    data_elements = fetch_data_elements(DHIS2_BASE_URL, dataset_ids, auth)
    export_to_excel(data_elements, 'data_elements.xlsx')
    print("Data elements exported to data_elements.xlsx")