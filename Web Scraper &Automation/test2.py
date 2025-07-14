# Advanced Command-Line Job Scraper using Selenium
# A tool to scrape job listings from Google Careers and save them to a CSV file.
# This version is more robust as it uses Selenium to control a real browser.
#
# Author: ujjwal rautela in colloboration with gemini
# Version: 2.0.0
#
# --- SETUP (IMPORTANT!) ---
# 1. Install required libraries:
#    pip install selenium pandas webdriver-manager
#
# 2. This script uses webdriver-manager to automatically download the correct
#    ChromeDriver. No manual download is needed.
#
# --- HOW TO RUN ---
# Run from the terminal with a job title and the number of pages to scrape:
# Example: python google_jobs_scraper.py "Software Engineer" 2
# This will scrape the first 2 pages of results for "Software Engineer".

import time
import pandas as pd
from datetime import datetime
import argparse

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Initializes and returns a Selenium WebDriver instance."""
    print("Setting up the Chrome WebDriver...")
    # Automatically downloads and manages the driver
    service = ChromeService(ChromeDriverManager().install())
    
    # Set up Chrome options for a cleaner run
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no browser window)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument('log-level=3') # Suppress console logs
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_google_jobs(driver, job_title, pages_to_scrape):
    """
    Scrapes job listings from Google Careers.
    """
    # Construct the search URL
    query = job_title.replace(' ', '%20')
    search_url = f"https://www.google.com/about/careers/applications/jobs/results/?q={query}"
    
    print(f"Navigating to: {search_url}")
    driver.get(search_url)

    jobs_data = []
    
    for page_num in range(pages_to_scrape):
        print(f"\n--- Scraping Page {page_num + 1} ---")
        
        try:
            # --- INTELLIGENT WAIT ---
            # Wait for the main job container to be present on the page
            # This is crucial for dynamic websites.
            wait = WebDriverWait(driver, 20)
            job_list_container = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "sp2RC"))
            )
            
            # Find all job posting elements within the container
            # These are divs with a specific class name
            job_cards = job_list_container.find_elements(By.CLASS_NAME, "sMn82b")
            
            if not job_cards:
                print("No job cards found on this page. The website structure might have changed.")
                break

            print(f"Found {len(job_cards)} jobs on this page.")

            # Extract data from each job card
            for card in job_cards:
                try:
                    title = card.find_element(By.CLASS_NAME, "hprKdb").text
                    # Google Careers often lists multiple locations in spans
                    locations = card.find_elements(By.CLASS_NAME, "r0wTof")
                    location_text = ", ".join([loc.text for loc in locations])
                    link = card.find_element(By.TAG_NAME, "a").get_attribute('href')

                    jobs_data.append({
                        'Job Title': title,
                        'Company': 'Google', # It's always Google on this site
                        'Location': location_text,
                        'Link': link
                    })
                except NoSuchElementException:
                    # Skip a card if it's missing expected info (e.g., an ad or malformed card)
                    print("Skipping a card with missing information.")
                    continue
            
        except TimeoutException:
            print("Timed out waiting for page content to load. Exiting.")
            break
            
        # --- PAGINATION ---
        # Try to find and click the 'Next' page button
        try:
            # The 'Next' button is identified by its aria-label
            next_button = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Go to next page']")
            if next_button.is_displayed() and next_button.is_enabled():
                print("Navigating to the next page...")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5) # Wait for the next page to load
            else:
                print("Next button is not interactable. Reached the last page.")
                break
        except NoSuchElementException:
            print("No 'Next' button found. Reached the last page.")
            break # Exit loop if no next page

    return jobs_data

def save_to_csv(jobs_data, job_title):
    """Saves the scraped job data to a timestamped CSV file."""
    if not jobs_data:
        print("No data was scraped. CSV file will not be created.")
        return

    df = pd.DataFrame(jobs_data)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"google-jobs_{job_title.replace(' ', '-')}_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    print(f"\n✅ Success! Scraped {len(df)} jobs and saved to '{filename}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape job listings from Google Careers using Selenium.")
    parser.add_argument("job_title", type=str, help="The job title to search for.")
    parser.add_argument("pages", type=int, help="The number of pages to scrape.")
    
    args = parser.parse_args()
    
    driver = None # Initialize driver to None
    try:
        driver = setup_driver()
        scraped_data = scrape_google_jobs(driver, args.job_title, args.pages)
        save_to_csv(scraped_data, args.job_title)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # --- IMPORTANT: Always close the browser ---
        if driver:
            print("Closing the WebDriver.")
            driver.quit()
