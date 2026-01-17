import asyncio
import json
import csv
import random
import time
from typing import List, Dict, Optional
# You need to install duckduckgo-search: pip install duckduckgo-search

try:
    from duckduckgo_search import DDGS
except ImportError:
    print("Please install the library first: pip install duckduckgo-search")
    exit(1)

async def find_website(company_name: str, address: str) -> Optional[str]:
    """
    Searches DuckDuckGo for the company website.
    """
    query = f"{company_name} {address} official website"
    print(f"Searching for: {query}")
    
    try:
        results = DDGS().text(query, max_results=3)
        if results:
            # Simple heuristic: return the first result that looks like a main domain
            # In a real script, you'd want better filtering to avoid Yelp/YellowPages links
            return results[0]['href']
    except Exception as e:
        print(f"Error searching for {company_name}: {e}")
        return None
    return None

def process_places(places: List[Dict]):
    """
    Iterates through places and enriches them.
    """
    enriched_places = []
    
    for place in places:
        name = place.get('name', 'Unknown')
        address = place.get('address', '')
        
        # Artificial delay to respect rate limits (approx 20-30 req/min for free tier)
        time.sleep(random.uniform(2, 4)) 
        
        website = asyncio.run(find_website(name, address))
        
        if website:
            print(f"Found: {website}")
            place['website'] = website
        else:
            print(f"Could not find website for {name}")
            
        enriched_places.append(place)
        
    return enriched_places

if __name__ == "__main__":
    # Example data (Replace this with reading your actual file)
    sample_data = [
        {"name": "Joe's Pizza", "address": "123 Main St, New York, NY"},
        {"name": "Tech Corp", "address": "456 Innovation Dr, San Francisco, CA"}
    ]
    
    print("Starting enrichment...")
    enriched = process_places(sample_data)
    print("\nEnriched Results:")
    print(json.dumps(enriched, indent=2))
