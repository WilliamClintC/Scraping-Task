import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import os

def scrape_jdpower_guidelines():
    base_url = "https://www.jdpowervalues.com"
    url = f"{base_url}/industry-guidelines"
    
    # Send request to the website
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the website: {e}")
        return []
    
    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links
    guidelines_data = []
    links = soup.find_all('a')
    
    # Define month names for pattern matching
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    
    # Month name pattern for regex
    months_pattern = "|".join(months)
    
    for link in links:
        if not link.text:
            continue
            
        link_text = link.text.strip()
        href = link.get('href')
        
        if not href:
            continue
        
        # Convert relative URLs to absolute URLs
        if href.startswith('/'):
            href = base_url + href
            
        # Check various patterns in link text
        is_guideline = False
        month = None
        year = None
        
        # Case 1: URL contains month.year pattern
        url_match = re.search(r'\/(\d{2})\.(\d{4})_Commercial\s*Truck', href)
        if url_match:
            month_num = url_match.group(1)
            year = url_match.group(2)  # This captures the actual year from URL
            try:
                month = datetime.strptime(month_num, "%m").strftime("%B")
                is_guideline = True
            except ValueError:
                pass
        
        # Also check for alternative URL patterns
        if not is_guideline:
            alt_url_match = re.search(r'(\d{2})\.(\d{4}).*(?:Commercial.*Truck|Truck.*Guidelines)', href, re.IGNORECASE)
            if alt_url_match:
                month_num = alt_url_match.group(1)
                year = alt_url_match.group(2)
                try:
                    month = datetime.strptime(month_num, "%m").strftime("%B")
                    is_guideline = True
                except ValueError:
                    pass
                
        # If not found in URL, try to extract from text
        if not is_guideline:
            # Check if "february" appears in the URL path or article title related to trucks
            if re.search(r'/article/.*(?:february|march|january|april|may|june|july|august|september|october|november|december).*(?:truck|auction)', href, re.IGNORECASE):
                # Extract month from URL
                for m in months:
                    if m.lower() in href.lower():
                        month = m
                        break
                # Use current year as default if no year in URL
                year = str(datetime.now().year)
                is_guideline = True
            
            # Various text patterns
            pattern1 = rf"(?:Download the|Read the)(?: free)?(?: monthly)? (?:({months_pattern})(?: (\d{{4}}))?) Commercial Truck Guidelines"
            pattern2 = rf"({months_pattern}) (\d{{4}}) Commercial Truck Guidelines"
            pattern3 = r"free monthly (?:commercial truck )?report"
            
            for pattern in [pattern1, pattern2]:
                match = re.search(pattern, link_text, re.IGNORECASE)
                if match:
                    month = match.group(1)
                    # Group 2 might not exist in some patterns
                    year = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                    is_guideline = True
                    break
                    
            # For generic monthly report links without specific month/year
            if not is_guideline and re.search(pattern3, link_text, re.IGNORECASE):
                is_guideline = True
                # Use current date for generic monthly reports
                current_date = datetime.now()
                month = current_date.strftime("%B")
                year = str(current_date.year)
        
        if is_guideline:
            # If we found a guideline link but couldn't extract a year, use current year
            if not year:
                year = str(datetime.now().year)
                
            # Standardize month name capitalization
            if month:
                month = month.capitalize()
                
            date_str = f"{month} {year}" if month else f"Unknown {year}"
            
            guidelines_data.append({
                "link": href,  # Now using the full URL
                "month": month if month else "Unknown",
                "year": year,
                "date_str": date_str
            })
    
    return guidelines_data

def save_to_csv(data, filename="commercial_truck_guidelines.csv"):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date_str', 'month', 'year', 'link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    print(f"Data saved to {filepath}")
    return filepath

def main():
    print("Scraping JD Power Commercial Truck Guidelines...")
    guidelines_data = scrape_jdpower_guidelines()
    
    if guidelines_data:
        print(f"Found {len(guidelines_data)} Commercial Truck Guidelines links")
        csv_path = save_to_csv(guidelines_data)
        
        # Print summary
        print("\nSummary of Guidelines found:")
        for item in guidelines_data:
            print(f"{item['date_str']}: {item['link']}")
    else:
        print("No Commercial Truck Guidelines links found")

if __name__ == "__main__":
    main()