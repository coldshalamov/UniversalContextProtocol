import csv
import time
import random
import os
import argparse
from typing import Optional
from datetime import datetime, timedelta

# Try importing duckduckgo_search
try:
    from duckduckgo_search import DDGS
except ImportError:
    print("Please install duckduckgo-search: pip install duckduckgo-search")
    exit(1)

def find_website_ddg(query: str) -> Optional[str]:
    """
    Searches DuckDuckGo and returns the first result URL.
    """
    try:
        # random delay to simulate human behavior and respect rough rate limits
        # Free tier limit is roughly 20-30 req/min => 2-3 seconds per req
        time.sleep(random.uniform(2.0, 4.0))
        
        results = DDGS().text(query, max_results=1)
        if results:
            return results[0]['href']
    except Exception as e:
        print(f"  [!] Error searching '{query}': {e}")
        # If we hit a rate limit error, sleep longer
        if "Ratelimit" in str(e):
            print("  [!] Rate limit hit. Sleeping for 30 seconds...")
            time.sleep(30)
        return None
    return None

def main():
    parser = argparse.ArgumentParser(description="Mass enrich places with websites using DuckDuckGo (Free).")
    parser.add_argument("--input", required=True, help="Input CSV file path (must have 'name' and 'address' columns)")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--limit", type=int, help="Limit number of records to process (for testing)")
    
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    # Check for existing progress
    processed_counts = 0
    existing_data = {}
    
    if os.path.exists(output_path):
        print(f"Found existing output file '{output_path}'. Resuming...")
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create a unique key to identify rows (e.g., name+address)
                key = f"{row.get('name', '')}|{row.get('address', '')}"
                existing_data[key] = row
                processed_counts += 1
        print(f"Loaded {processed_counts} valid enriched records.")

    # Read Input
    rows_to_process = []
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if 'website' not in fieldnames:
            fieldnames.append('website')
            
        for row in reader:
             rows_to_process.append(row)

    print(f"Total rows in input: {len(rows_to_process)}")
    
    # Open Output for Appending/Writing
    # If resuming, we rewriting everything? Safer to append, but CSV structural integrity is hard with append if headers change.
    # For simplicity in this script: Read all, process missing, write all periodically.
    # actually, purely appending is safer for crashes.
    
    # Better approach for massive files:
    # 1. Read Input
    # 2. Open Output in 'a' (append) mode if exists, else 'w'.
    
    # We will iterate and write immediately.
    
    # existing keys set for fast lookup
    processed_keys = set(existing_data.keys())
    
    write_header = not os.path.exists(output_path)
    
    with open(output_path, 'a', encoding='utf-8', newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
            
        count = 0
        skipped = 0
        total_limit = args.limit if args.limit else len(rows_to_process)
        
        start_time = datetime.now()
        
        for i, row in enumerate(rows_to_process):
            if count >= total_limit:
                break
                
            name = row.get('name', '').strip()
            address = row.get('address', '').strip()
            key = f"{name}|{address}"
            
            if key in processed_keys:
                skipped += 1
                continue
            
            # Enrich
            query = f"{name} {address} official website"
            print(f"[{i+1}/{len(rows_to_process)}] Searching: {name}...", end='', flush=True)
            
            website = find_website_ddg(query)
            
            if website:
                row['website'] = website
                print(f" Found: {website}")
            else:
                row['website'] = ""
                print(" Not found.")
                
            # Write immediately
            writer.writerow(row)
            f_out.flush() # Ensure it's saved
            
            count += 1
            
            # Simple ETA calc
            if count % 10 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_secd = elapsed / count
                remaining = len(rows_to_process) - (i + 1)
                eta_seconds = remaining * avg_secd
                eta_str = str(timedelta(seconds=int(eta_seconds)))
                print(f"   >>> Progress: {count} enriched. Avg: {avg_secd:.2f}s/row. ETA: {eta_str}")

    print("Done.")

if __name__ == "__main__":
    main()
