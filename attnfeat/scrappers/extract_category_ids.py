# extract_category_ids.py

import json
from typing import List, Set

def extract_category_ids(json_file: str) -> List[int]:
    """
    Extract all category IDs from the CTC categories JSON file
    """
    category_ids = set()
    
    print(f"Reading {json_file}...")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} product classes")
    
    for product_class in data:
        if 'all_product_types' in product_class:
            for product_type in product_class['all_product_types']:
                if 'all_product_categories' in product_type:
                    for category in product_type['all_product_categories']:
                        if 'id' in category:
                            category_ids.add(category['id'])
    
    # Convert to sorted list
    sorted_ids = sorted(list(category_ids))
    
    print(f"Extracted {len(sorted_ids)} unique category IDs")
    print(f"Category ID range: {min(sorted_ids)} to {max(sorted_ids)}")
    
    return sorted_ids

def save_category_ids(category_ids: List[int], output_file: str):
    """
    Save category IDs to a JSON file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(category_ids, f, indent=2)
    
    print(f"Saved category IDs to {output_file}")

def save_category_ids_csv(category_ids: List[int], output_file: str):
    """
    Save category IDs to a CSV file
    """
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category_id'])
        for category_id in category_ids:
            writer.writerow([category_id])
    
    print(f"Saved category IDs to {output_file}")

if __name__ == "__main__":
    # Extract category IDs
    category_ids = extract_category_ids('ctc_categories.json')
    
    # Save to files
    save_category_ids(category_ids, 'category_ids.json')
    save_category_ids_csv(category_ids, 'category_ids.csv')
    
    # Show first 20 IDs as sample
    print(f"\nFirst 20 category IDs: {category_ids[:20]}")
    print(f"Last 20 category IDs: {category_ids[-20:]}") 