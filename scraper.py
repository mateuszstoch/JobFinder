import requests
from bs4 import BeautifulSoup

def build_olx_url(city, query, category="praca", filters=None):
    # OLX URL structure: https://www.olx.pl/{category}/{city}/q-{query}/
    # Simple sanitization
    city = city.lower().replace(" ", "-")
    query = query.lower().replace(" ", "-")
    base_url = "https://www.olx.pl/"
    
    url = f"{base_url}/{category}/{city}/q-{query}/"
    
    if filters:
        params = []
        for key, value in filters.items():
            # Assuming key is the enum name e.g. 'contract_type' and value is the specific value
            # search[filter_enum_KEY][0]=VALUE
            # Handling lists if multiple values selected? For now assuming single.
            if isinstance(value, list):
                 for i, v in enumerate(value):
                      params.append(f"search[filter_enum_{key}][{i}]={v}")
            else:
                 params.append(f"search[filter_enum_{key}][0]={value}")
        
        if params:
            url += "?" + "&".join(params)
    if url[-1]=="/":
        url+="?"
    else:
        url+="&"
    url+="search%5Border%5D=created_at:desc"
    
    return url

def fetch_offers(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        offers = []
        
        # This selector needs to be verified against live OLX
        # Looking for listing grid. 
        # Usually offers are in div with data-cy="l-card" or similar.
        
        # Trying a generic approach for listings
        # NOTE: This is a best-guess and will likely need refinement after testing structure.
        listing_grid = soup.find('div', {'data-testid': 'listing-grid'})
        
        if not listing_grid:
            # Fallback or empty
            return []
            
        cards = listing_grid.find_all('div', {'data-cy': 'l-card'})
        
        for card in cards:
            try:
                title_tag = card.find('h4')
                if not title_tag: 
                     # Fallback to h6 just in case
                     title_tag = card.find('h6')
                if not title_tag: continue
                title = title_tag.text.strip()
                
                link_tag = card.find('a', href=True)
                if not link_tag: continue
                link = link_tag['href']
                if link.startswith('/'):
                    link = "https://www.olx.pl" + link
                
                # New extraction logic based on SVG proximity
                details = {
                    "price": None,
                    "location": None,
                    "contract": None,
                    "work_load": None
                }
                
                # Find all potential detail items.
                # Structure: A container div holding an SVG (icon) and a P tag (text).
                # We iterate all divs in the card.
                for div in card.find_all('div'):
                    if div.find('svg') and div.find('p'):
                         text = div.find('p').get_text(strip=True)
                         if not text: continue
                         
                         # Naive classification based on keywords
                         if "zł" in text:
                             details["price"] = text
                         elif any(x in text for x in ["Umowa", "B2B", "Kontrakt", "Samozatrudnienie"]):
                             details["contract"] = text
                         elif "etat" in text or "Praca" in text: # Praca dodatkowa / Pełny etat
                             details["work_load"] = text
                         elif not details["location"] and ("," in text or (text[0].isupper() and len(text) < 40 and "dzisiaj" not in text.lower())):
                             # Location heuristic: "Kraków, Stare Miasto"
                             details["location"] = text
                
                # Cleanup / Fallbacks
                price = details["price"] if details["price"] else "N/A"
                location = details["location"] if details["location"] else "N/A"
                contract = details["contract"] if details["contract"] else "N/A"
                work_load = details["work_load"] if details["work_load"] else "N/A"
                
                # ID extraction
                offer_id = link
                
                offers.append({
                    'id': offer_id,
                    'title': title,
                    'price': price,
                    'location': location,
                    'contract': contract,
                    'work_load': work_load,
                    'url': link
                })
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue
                
        return offers

    except Exception as e:
        print(f"Error fetching offers: {e}")
        return []
