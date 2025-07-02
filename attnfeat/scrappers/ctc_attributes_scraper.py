# ctc_attributes_scraper.py

import requests
import csv
import json
import sys
from datetime import datetime
from typing import List, Dict, Any

BASE_URL = "https://staging.bi-rite.knaps.io/ctc/get-attributes/"

# Set up cookies with the session ID
cookies = {
    "sessionid": "9rgikhk0531epejjh5i20hdtj5qki77h"
}

headers = {
    "Accept": "application/json",
}

output_file = "ctc_attributes.csv"
json_output_file = "ctc_attributes.json"

def load_category_ids(json_file: str = "category_ids.json") -> List[int]:
    """
    Load category IDs from the extracted JSON file
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            category_ids = json.load(f)
        print(f"Loaded {len(category_ids)} category IDs from {json_file}")
        return category_ids
    except FileNotFoundError:
        print(f"Category IDs file {json_file} not found. Please run extract_category_ids.py first.")
        return []

def fetch_attributes_for_category(category_id: int) -> Dict[str, Any]:
    """
    Fetch attributes for a specific product category using GET request
    """
    message = {"product_category_id": category_id}
    try:
        resp = requests.get(BASE_URL, json=message, headers=headers, cookies=cookies, timeout=30)
        if resp.status_code == 419:
            print(f"Session expired at category_id={category_id}")
            return None
        elif resp.status_code != 200:
            print(f"[{resp.status_code}] Error for category_id={category_id}: {resp.text[:100]}...")
            return None
        try:
            data = resp.json()
            return data
        except json.JSONDecodeError as e:
            print(f"JSON decode error for category_id={category_id}: {e}")
            print(f"Response text: {resp.text[:200]}...")  # Show first 200 chars
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for category_id={category_id}: {e}")
        return None

def fetch_all_attributes(category_ids: List[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch attributes for all product categories using the provided category IDs
    """
    if category_ids is None:
        category_ids = load_category_ids()
        if not category_ids:
            return []
    
    all_attributes = []
    
    print(f"Fetching attributes for {len(category_ids)} categories...")
    
    for i, category_id in enumerate(category_ids, 1):
        print(f"Fetching attributes for category_id={category_id} ({i}/{len(category_ids)})...")
        
        data = fetch_attributes_for_category(category_id)
        
        if data is None:
            print(f"[no response] at category_id={category_id}")
            continue
            
        if not data:
            print(f"[empty] at category_id={category_id}")
            continue
        
        # Add metadata to the response
        # The API returns a list of attributes directly, so we need to wrap it
        record = {
            "category_id": category_id,
            "scraped_at": datetime.utcnow().isoformat(),
            "attributes": data  # data is already a list of attributes
        }
        all_attributes.append(record)
        
        print(f"Fetched attributes for category_id={category_id}")
        
        # Add a small delay to be respectful to the server
        import time
        time.sleep(0.1)
    
    return all_attributes

def write_csv(rows: List[Dict[str, Any]], filename: str):
    """
    Write data to CSV file
    """
    if not rows:
        print(f"no data to write for {filename}")
        return

    # For attributes, we'll flatten the structure
    flattened_rows = []
    for row in rows:
        category_id = row.get("category_id")
        scraped_at = row.get("scraped_at")
        
        # Extract attributes from the response
        attributes = row.get("attributes", []) if isinstance(row.get("attributes"), list) else []
        
        for attr in attributes:
            flat_row = {
                "category_id": category_id,
                "scraped_at": scraped_at,
                **attr  # Flatten the attribute data
            }
            flattened_rows.append(flat_row)
    
    if not flattened_rows:
        print(f"no flattened data to write for {filename}")
        return

    # Get all unique fieldnames from all rows
    fieldnames = set()
    for row in flattened_rows:
        fieldnames.update(row.keys())
    fieldnames = sorted(list(fieldnames))

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_rows)

    print(f"wrote {len(flattened_rows)} rows to {filename}")

def write_json(rows: List[Dict[str, Any]], filename: str):
    """
    Write data to JSON file for easier inspection
    """
    if not rows:
        print(f"no data to write for {filename}")
        return

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"wrote {len(rows)} records to {filename}")

def analyze_data_structure(data: List[Dict[str, Any]]):
    """
    Analyze the structure of the fetched data to help with database design
    """
    print(f"\n{'='*50}")
    print("ATTRIBUTES DATA STRUCTURE ANALYSIS")
    print(f"{'='*50}")
    
    if not data:
        print("No data to analyze")
        return
    
    print(f"Total category records: {len(data)}")
    
    # Analyze first few records
    sample = data[:3]
    print(f"Sample records: {len(sample)}")
    
    for i, record in enumerate(sample):
        print(f"\nRecord {i+1} (Category ID: {record.get('category_id')}):")
        
        # Show the overall structure
        for key, value in record.items():
            if key in ['category_id', 'scraped_at']:
                print(f"  {key}: {value}")
            elif key == 'attributes':
                if isinstance(value, list):
                    print(f"  attributes: {len(value)} items")
                    for j, attr in enumerate(value[:3]):  # Show first 3 attributes
                        print(f"    Attribute {j+1}: {attr}")
                    if len(value) > 3:
                        print(f"    ... and {len(value) - 3} more attributes")
                else:
                    print(f"  attributes: {value}")
            else:
                print(f"  {key}: {value}")

def test_single_category():
    """
    Test the API with a single category to understand the response structure
    """
    print("Testing single category (ID: 276)...")
    
    data = fetch_attributes_for_category(276)
    
    if data:
        print("Response structure:")
        print(json.dumps(data, indent=2))
    else:
        print("No response received")

if __name__ == "__main__":
    print("CTC Attributes Scraper")
    print("=" * 50)
    
    # Test with a single category first
    test_single_category()
    
    print(f"\n{'='*50}")
    print("Starting full scrape...")
    print(f"{'='*50}")
    
    # Fetch all data using extracted category IDs
    all_data = fetch_all_attributes()
    
    # Write to files
    write_csv(all_data, output_file)
    write_json(all_data, json_output_file)
    
    # Analyze the data structure
    analyze_data_structure(all_data)
    
    print(f"\n{'='*50}")
    print("SCRAPING COMPLETE")
    print(f"{'='*50}")
    print(f"Files created:")
    print(f"  {output_file}")
    print(f"  {json_output_file}") 