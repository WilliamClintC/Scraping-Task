import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
from datetime import datetime
import time
import traceback

# Set up Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Commented out to see what's happening
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Create a dataframe to store our results
results = pd.DataFrame(columns=['Link', 'Month', 'Year'])

# Define the base URL and the max pages to try (will stop if no new content)
base_url = "https://www.jdpowervalues.com/commercial-truck-market"
max_pages_to_try = 10  # Maximum number of pages to check

try:
    page_num = 0
    all_processed_links = set()  # Track all links we've seen across pages
    no_new_content = False
    
    while page_num < max_pages_to_try and not no_new_content:
        # Construct the page URL (first page has no parameter)
        if page_num == 0:
            page_url = base_url
        else:
            page_url = f"{base_url}?page={page_num}"
            
        # Load the page
        driver.get(page_url)
        print(f"\nLoaded page {page_num}: {page_url}")
        
        # Wait for the page to load and make sure content is visible
        time.sleep(5)  # Add more time to ensure page is fully loaded
        
        # DEBUG: Print page title to verify we're on the right page
        print(f"Page title: {driver.title}")
        
        # Get all links from the page
        all_links = driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(all_links)} total links on page {page_num}")
        
        # Identify article links (using /article/ in the URL)
        article_links = []
        for link in all_links:
            href = link.get_attribute('href')
            if href and href.startswith('http'):
                if '/article/' in href and href != base_url:
                    article_links.append(href)
        
        # Remove duplicates
        article_links = list(set(article_links))
        
        # Check if we found any new links on this page
        new_links = [link for link in article_links if link not in all_processed_links]
        
        if not new_links:
            print(f"No new links found on page {page_num}. Stopping pagination.")
            no_new_content = True
            break
            
        print(f"Found {len(article_links)} article links on page {page_num} ({len(new_links)} new)")
        
        # Update all processed links
        all_processed_links.update(article_links)
        
        # Print them for debugging
        for i, link in enumerate(new_links):
            print(f"New article link {i+1}: {link}")
        
        # Process each article link
        for url in new_links:
            try:
                # Skip if we've already processed this URL
                if url in results['Link'].values:
                    print(f"Skipping already processed URL: {url}")
                    continue
                
                # Navigate to the page
                driver.get(url)
                print(f"Processing: {url}")
                
                # Wait for the page to load
                time.sleep(3)
                
                # Get the page source
                page_source = driver.page_source
                
                # Look for dates in format like "March 15, 2023"
                date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+(\d{4})'
                matches = re.findall(date_pattern, page_source)
                
                # If dates found, extract month and year and add to the dataframe
                if matches:
                    # Use the first match
                    month = matches[0][0]  # First match, first group (month)
                    year = matches[0][1]   # First match, second group (year)
                    
                    # Add to results
                    new_row = pd.DataFrame({'Link': [url], 'Month': [month], 'Year': [year]})
                    results = pd.concat([results, new_row], ignore_index=True)
                    
                    print(f"Found date: {month} {year} on {url}")
                else:
                    print(f"No date found on {url}")
                    
                    # Try a more specific approach to find the date
                    try:
                        # Look for date elements using common class names
                        date_elements = driver.find_elements(By.CSS_SELECTOR, ".date, .post-date, .article-date, .meta-date, time")
                        for date_el in date_elements:
                            date_text = date_el.text.strip()
                            print(f"Found potential date element: '{date_text}'")
                            
                            # Check if it contains a month name
                            month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)'
                            month_match = re.search(month_pattern, date_text)
                            
                            if month_match:
                                # Try to extract year
                                year_pattern = r'\b(20\d{2})\b'
                                year_match = re.search(year_pattern, date_text)
                                
                                if year_match:
                                    month = month_match.group(1)
                                    year = year_match.group(1)
                                    
                                    # Add to results
                                    new_row = pd.DataFrame({'Link': [url], 'Month': [month], 'Year': [year]})
                                    results = pd.concat([results, new_row], ignore_index=True)
                                    
                                    print(f"Found date from element: {month} {year} on {url}")
                                    break
                    except Exception as e:
                        print(f"Error finding date elements: {e}")
                    
            except Exception as e:
                print(f"Error processing {url}: {e}")
                traceback.print_exc()
                continue
        
        # Save progress after each page
        results.to_csv('truck_market_dates_progress.csv', index=False)
        print(f"Progress saved after page {page_num}")
        
        # Move to next page
        page_num += 1
    
    # Display the results
    print("\nFinal Results:")
    print(results)
    
    # Save to CSV
    results.to_csv('truck_market_dates.csv', index=False)
    print("Results saved to truck_market_dates.csv")
    
except Exception as e:
    print(f"An error occurred: {e}")
    traceback.print_exc()
    
finally:
    # Clean up
    driver.quit()
    print("Browser closed")