import time
import csv
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse

def setup_driver():
    """Set up and return a Chrome webdriver."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    # Add these options to reduce logging noise
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("--log-level=3")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def google_search(driver, query):
    """Perform a Google search with the given query and handle verification."""
    print("Opening Google...")
    driver.get("https://www.google.com")
    
    # Accept cookies if the dialog appears
    try:
        accept_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
        accept_button.click()
        time.sleep(1)
        print("Accepted cookies dialog")
    except Exception as e:
        print("No cookies dialog found or couldn't interact with it")
    
    # Find the search box and enter the query
    try:
        print(f"Searching for: {query}")
        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        print("Search query submitted")
    except Exception as e:
        print(f"Error during search: {str(e)}")
    
    # Explicit wait for user verification
    print("\n" + "="*50)
    print("IMPORTANT: If you see a CAPTCHA or verification prompt, please complete it now.")
    confirmation = input("Press Enter when you're ready to continue with link extraction...")
    print("Continuing with extraction...")
    print("="*50 + "\n")
    
    return True

def navigate_to_page(driver, query, page_num):
    """Navigate directly to a specific search results page."""
    encoded_query = urllib.parse.quote(query)
    start_index = 0 if page_num == 1 else (page_num - 1) * 10
    
    url = f"https://www.google.com/search?q={encoded_query}"
    if start_index > 0:
        url += f"&start={start_index}"
        
    print(f"Navigating to page {page_num} with URL: {url}")
    driver.get(url)
    time.sleep(3)  # Allow time for the page to load
    
    if page_num > 1:
        # Give additional time for the second page and validate we're actually on page 2
        current_url = driver.current_url
        if "start=" not in current_url:
            print(f"Warning: URL doesn't contain 'start=' parameter: {current_url}")
            print("Taking a screenshot for debugging...")
            driver.save_screenshot(f"page{page_num}_debug.png")
    
    return True

def extract_date_from_link(link):
    """Extract month and year from link if available."""
    month = None
    year = None
    
    # Try to find patterns like MM.YYYY or MM/YYYY or similar in the URL or filename
    date_patterns = [
        r'(\d{1,2})\.(\d{4})',  # MM.YYYY
        r'(\d{1,2})/(\d{4})',   # MM/YYYY
        r'(\d{1,2})-(\d{4})',   # MM-YYYY
        r'(\d{1,2})_(\d{4})',   # MM_YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.search(pattern, link)
        if matches:
            try:
                month_num = int(matches.group(1))
                year = matches.group(2)
                
                # Convert month number to name
                if 1 <= month_num <= 12:
                    month = datetime(2000, month_num, 1).strftime('%b')
                    return month, year
            except:
                continue
    
    # Try to find month names in the URL
    month_patterns = [
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[^a-z].*?(\d{4})',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)[^a-z].*?(\d{4})'
    ]
    
    for pattern in month_patterns:
        matches = re.search(pattern, link.lower())
        if matches:
            try:
                month_str = matches.group(1)
                year = matches.group(2)
                
                # Convert full month name to abbreviated version if needed
                if len(month_str) > 3:
                    month_map = {
                        'january': 'Jan', 'february': 'Feb', 'march': 'Mar', 'april': 'Apr',
                        'may': 'May', 'june': 'Jun', 'july': 'Jul', 'august': 'Aug',
                        'september': 'Sep', 'october': 'Oct', 'november': 'Nov', 'december': 'Dec'
                    }
                    month = month_map.get(month_str)
                else:
                    month = month_str.capitalize()
                
                return month, year
            except:
                continue
    
    return month, year

def extract_links(driver, page_number=1):
    """Extract links from Google search results."""
    print(f"Extracting links from web search, page {page_number}...")
    
    # Get the page source and parse with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    
    # Find all search result links - trying multiple selectors
    search_results = []
    
    # Try the first selector pattern
    results = soup.select("div.yuRUbf > a")
    if not results:
        # Try an alternative selector pattern
        results = soup.select("div.g div.tF2Cxc > div.yuRUbf > a")
    if not results:
        # Try yet another pattern
        results = soup.select("h3.LC20lb")
        if results:
            # If we found h3 elements, try to get their parent links
            results = [h3.find_parent('a') for h3 in results if h3.find_parent('a')]
    
    # Process results if any were found
    for result in results:
        if result:
            link = result.get("href")
            title = result.select_one("h3")
            title_text = title.text if title else "No title"
            
            if link:  # Only add if we have a valid link
                month, year = extract_date_from_link(link)
                
                search_results.append({
                    "title": title_text,
                    "link": link,
                    "page": page_number,
                    "month": month if month else "",
                    "year": year if year else ""
                })
                    
    # For debugging, save the HTML to a file if no results were found
    if not search_results:
        with open(f"debug_web_page_{page_number}.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print(f"No results found for web search, page {page_number}. Page source saved for inspection")
    
    return search_results

def save_to_file(results, filename="2.csv"):
    """Save search results to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "page", "month", "year"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Results saved to {filename}")
    return filename

def main():
    query = input("Enter your search query: ")
    driver = setup_driver()
    all_results = []
    
    try:
        # Initial search and verification
        google_search(driver, query)
        time.sleep(2)
        
        # Loop through pages 1 to 4
        for page_num in range(1, 5):
            # Navigate to the specific page (page 1 is already loaded after initial search)
            if page_num > 1:
                navigate_to_page(driver, query, page_num)
            
            # Take a screenshot for verification
            driver.save_screenshot(f"page{page_num}_results.png")
            print(f"Saved screenshot of page {page_num} results")
            
            # Extract links from current page
            page_results = extract_links(driver, page_number=page_num)
            all_results.extend(page_results)
            print(f"Found {len(page_results)} results on web search page {page_num}.")
            
            # Short delay between page navigations
            time.sleep(2)
        
        # Print a preview of the results with month and year information
        print(f"\nTotal results found: {len(all_results)}")
        preview_count = min(5, len(all_results))
        for i, result in enumerate(all_results[:preview_count], 1):
            date_info = ""
            if result['month'] or result['year']:
                date_info = f" ({result['month']} {result['year']})"
            print(f"{i}. [Page {result['page']}] {result['title']}{date_info} - {result['link']}")
        
        if all_results:
            # Save results and automatically open the file
            filename = save_to_file(all_results)
            print(f"Opening {filename}...")
            os.system(f"start {filename}")
    except Exception as e:
        import traceback
        print(f"An error occurred: {str(e)}")
        print(traceback.format_exc())
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    main()