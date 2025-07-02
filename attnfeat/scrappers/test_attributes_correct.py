# test_attributes_correct.py

import requests
import json
from datetime import datetime

BASE_URL = "https://staging.bi-rite.knaps.io/ctc/get-attributes/"

# Set up cookies with the session ID
cookies = {
    "sessionid": "9rgikhk0531epejjh5i20hdtj5qki77h"
}

headers = {
    "Accept": "application/json",
}

def test_category_ids():
    """
    Test a few category IDs using GET requests
    """
    # Test with a few category IDs from the extracted list
    test_ids = [52, 133, 134, 135, 628, 629, 630]  # First few IDs from the extracted list
    
    for category_id in test_ids:
        print(f"\nTesting category_id={category_id}...")
        message = {"product_category_id": category_id}
        try:
            resp = requests.get(BASE_URL, json=message, headers=headers, cookies=cookies, timeout=30)
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"Success! Response: {json.dumps(data, indent=2)[:500]}...")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Response text: {resp.text[:200]}...")
            else:
                print(f"Error: {resp.text[:200]}...")
                
        except Exception as e:
            print(f"Request error: {e}")

if __name__ == "__main__":
    print("Testing Attributes Endpoint with GET Requests")
    print("=" * 50)
    test_category_ids() 