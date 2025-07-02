# ctc_features_benefits_scraper.py

import requests
import csv
import json
import sys
from datetime import datetime
from typing import List, Dict, Any

BASE_URL = "https://staging.bi-rite.knaps.io/ctc/features-benefits/"

# Set up cookies with the session ID
cookies = {
    "sessionid": "9rgikhk0531epejjh5i20hdtj5qki77h"
}

headers = {
    "Accept": "application/json",
}

# Output files for each level
output_files = {
    "class": "features_benefits_class.csv",
    "type": "features_benefits_type.csv", 
    "category": "features_benefits_category.csv"
}

def fetch_features_benefits(level: str, max_id: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch features and benefits for a specific level (class, type, category)
    """
    all_rows = []
    
    print(f"Fetching {level} level features and benefits...")
    
    for item_id in range(1, max_id + 1):
        # Build URL with parameters in the line
        url = f"{BASE_URL}?id={item_id}&level={level}"
        
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            
            if resp.status_code == 419:
                print(f"Session expired at {level} id={item_id}")
                break
            elif resp.status_code != 200:
                print(f"[{resp.status_code}] stopping at {level} id={item_id}")
                break
                
            data = resp.json()
            # Handle API response with 'data' key
            items = data.get('data') if isinstance(data, dict) and 'data' in data else data
            if not items:
                print(f"[empty] at {level} id={item_id}")
                continue
            
            for item in items:
                item["level"] = level
                item["level_id"] = item_id
                item["scraped_at"] = datetime.utcnow().isoformat()
                all_rows.append(item)
            
            print(f"Fetched {len(items)} items for {level} id={item_id}")
            
        except requests.exceptions.RequestException as e:
            print(f"Request error for {level} id={item_id}: {e}")
            continue
            
    return all_rows

def write_csv(rows: List[Dict[str, Any]], filename: str):
    """
    Write data to CSV file
    """
    if not rows:
        print(f"no data to write for {filename}")
        return

    # Get all unique fieldnames from all rows
    fieldnames = set()
    for row in rows:
        fieldnames.update(row.keys())
    fieldnames = sorted(list(fieldnames))

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {filename}")

def write_json(rows: List[Dict[str, Any]], filename: str):
    """
    Write data to JSON file for easier inspection
    """
    if not rows:
        print(f"no data to write for {filename}")
        return

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"wrote {len(rows)} rows to {filename}")

def fetch_all_levels():
    """
    Fetch features and benefits for all three levels
    """
    all_data = {}
    
    for level in ["class", "type", "category"]:
        print(f"\n{'='*50}")
        print(f"Processing {level.upper()} level")
        print(f"{'='*50}")
        
        rows = fetch_features_benefits(level)
        all_data[level] = rows
        
        # Write to CSV
        csv_filename = output_files[level]
        write_csv(rows, csv_filename)
        
        # Write to JSON for inspection
        json_filename = csv_filename.replace('.csv', '.json')
        write_json(rows, json_filename)
        
    return all_data

def analyze_data_structure(data: Dict[str, List[Dict[str, Any]]]):
    """
    Analyze the structure of the fetched data to help with database design
    """
    print(f"\n{'='*50}")
    print("DATA STRUCTURE ANALYSIS")
    print(f"{'='*50}")
    
    for level, rows in data.items():
        if not rows:
            print(f"\n{level.upper()} level: No data")
            continue
            
        print(f"\n{level.upper()} level:")
        print(f"  Total records: {len(rows)}")
        
        # Analyze first few records
        sample = rows[:3]
        print(f"  Sample records: {len(sample)}")
        
        # Show all unique fields
        all_fields = set()
        for row in sample:
            all_fields.update(row.keys())
        
        print(f"  All fields: {sorted(all_fields)}")
        
        # Show sample data
        for i, row in enumerate(sample):
            print(f"  Record {i+1}:")
            for key, value in row.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"    {key}: {value}")

if __name__ == "__main__":
    print("CTC Features and Benefits Scraper")
    print("=" * 50)
    
    # Fetch all data
    all_data = fetch_all_levels()
    
    # Analyze the data structure
    analyze_data_structure(all_data)
    
    print(f"\n{'='*50}")
    print("SCRAPING COMPLETE")
    print(f"{'='*50}")
    print("Files created:")
    for level, filename in output_files.items():
        print(f"  {filename}")
        print(f"  {filename.replace('.csv', '.json')}") 