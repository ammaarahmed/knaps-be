# fetch_features_benefits.py

import requests
import csv
import sys

BASE_URL = "https://staging.bi-rite.knaps.io/ctc/features-benefits/"
SESSION_ID = "9rgikhk0531epejjh5i20hdtj5qki77h"  # ← replace with your real session ID

headers = {
    "Session-ID": SESSION_ID,
    "Accept": "application/json",
}

output_file = "features_benefits.csv"

def fetch_all():
    all_rows = []
    for class_id in range(1, 1000):
        params = {"id": class_id, "level": "class"}
        resp = requests.get(BASE_URL, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"[{resp.status_code}] stopping at class_id={class_id}")

        data = resp.json()
        if not data:
            print(f"[empty] stopping at class_id={class_id}")

        for item in data:
            item["class_id"] = class_id
            all_rows.append(item)

    return all_rows

def write_csv(rows):
    if not rows:
        print("no data to write")
        return

    # take fieldnames from first row
    fieldnames = list(rows[0].keys())

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {output_file}")

if __name__ == "__main__":
    rows = fetch_all()
    write_csv(rows)
