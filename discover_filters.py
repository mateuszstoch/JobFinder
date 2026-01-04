import requests
from bs4 import BeautifulSoup

def discover_filters():
    url = "https://www.olx.pl/praca/warszawa/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for form inputs that might be filters
    # Usually they are inputs with names starting with search[
    
    import json
    
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
    if script_tag:
        print("Found __NEXT_DATA__ script!")
        try:
            data = json.loads(script_tag.string)
            # Traverse to find filter configuration
            # Usually in props -> pageProps -> state -> adListing -> filters or similar
            # Or data -> ...
            
            # Let's verify keys first to guess path
            print("Keys in data:", data.keys())
            if 'props' in data:
                print("Keys in props:", data['props'].keys())
                if 'pageProps' in data['props']:
                    pp = data['props']['pageProps']
                    print("Keys in pageProps:", pp.keys())
                    
                    # Try to locate filters
                    # Often in 'listing' or 'search'
                    # Let's serialize specific parts to file to read
                    with open("next_data_dump.json", "w", encoding="utf-8") as f:
                        json.dump(pp, f, indent=2)
                    print("Dumped pageProps to next_data_dump.json")
                    
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    else:
        print("__NEXT_DATA__ not found.")

    # Also checking if there are any 'a' tags with hrefs containing filter patterns as a fallback
    links = soup.find_all('a', href=True)
    potential_filters = set()
    for link in links:
        href = link['href']
        if 'search[' in href:
            potential_filters.add(href)
            
    if potential_filters:
        print(f"Found {len(potential_filters)} links with search parameters.")
        for p in list(potential_filters)[:5]:
            print(f"Sample: {p}")


if __name__ == "__main__":
    discover_filters()
