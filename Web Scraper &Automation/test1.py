# Command-Line Job Scraper
# A tool to scrape job listings from Indeed.com and save them to a CSV file.
#
# Author: Your Name
# Version: 1.0.0
#
# How to Run:
# 1. Install required libraries: pip install requests beautifulsoup4 pandas
# 2. Run from the terminal:
#    python job_scraper.py "Python Developer" "Remote"
#    python job_scraper.py "Cybersecurity Analyst" "Washington DC"

import requests
from bs4 import BeautifulSoup
import pandas as pd
import argparse
import time
from datetime import datetime

def get_jobs(job_title, location):
    """
    Scrapes job listings for a given title and location from Indeed.
    """
    print(f"Scraping jobs for '{job_title}' in '{location}'...")

    # Construct the URL for the search query
    # We use '+' to join words in the query parameters
    url = f"https://www.indeed.com/jobs?q={job_title.replace(' ', '+')}&l={location.replace(' ', '+')}"

    # --- Ethical Scraping Best Practice: Set a User-Agent ---
    # This header identifies our script to the web server, making our requests transparent.
    headers = {
        'User-Agent': 'JobScraper/1.0 (YourName; your.email@example.com; +https://github.com/your-repo)'
    }

    try:
        # Fetch the webpage content
        response = requests.get(url, headers=headers)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

    # --- Parse the HTML with BeautifulSoup ---
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the main container holding the job listings
    # Indeed uses a 'div' with the id 'mosaic-provider-jobcards'
    job_cards_container = soup.find('div', id='mosaic-provider-jobcards')
    if not job_cards_container:
        print("Could not find the main job cards container. The website structure may have changed.")
        return None
    
    # Find all individual job cards. These are 'a' tags with a specific class.
    job_cards = job_cards_container.find_all('a', class_='tapItem')
    if not job_cards:
        print("No job cards found. Try a different search term or check the class names.")
        return None

    # --- Extract Data from Each Job Card ---
    jobs_data = []
    for card in job_cards:
        # Using .text.strip() to get clean text content
        title_element = card.find('span', title=True)
        job_title_text = title_element.text.strip() if title_element else 'N/A'

        company_element = card.find('span', class_='companyName')
        company_name = company_element.text.strip() if company_element else 'N/A'

        location_element = card.find('div', class_='companyLocation')
        job_location = location_element.text.strip() if location_element else 'N/A'

        # Construct the full link to the job posting
        job_link = "https://www.indeed.com" + card['href']

        jobs_data.append({
            'Job Title': job_title_text,
            'Company': company_name,
            'Location': job_location,
            'Link': job_link
        })
        
        # --- Ethical Scraping Best Practice: Be Respectful ---
        # Add a small delay to avoid overwhelming the server with requests.
        time.sleep(0.1)

    print(f"Found {len(jobs_data)} jobs.")
    return jobs_data

def save_to_csv(jobs_data, job_title, location):
    """
    Saves the scraped job data to a timestamped CSV file.
    """
    if not jobs_data:
        print("No data to save.")
        return

    # Create a pandas DataFrame
    df = pd.DataFrame(jobs_data)

    # Generate a clean, timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d")
    clean_job_title = job_title.replace(' ', '-').lower()
    clean_location = location.replace(' ', '-').lower()
    filename = f"{clean_job_title}_{clean_location}_jobs_{timestamp}.csv"

    # Save the DataFrame to a CSV file
    df.to_csv(filename, index=False)
    print(f"Successfully saved data to {filename}")


if __name__ == "__main__":
    # --- Set up Command-Line Argument Parsing ---
    # This makes the script a reusable and professional tool.
    parser = argparse.ArgumentParser(description="Scrape job listings from Indeed.com.")
    parser.add_argument("job_title", type=str, help="The job title to search for (e.g., 'Python Developer').")
    parser.add_argument("location", type=str, help="The location to search in (e.g., 'Remote').")
    
    args = parser.parse_args()

    # --- Run the Scraper ---
    scraped_data = get_jobs(args.job_title, args.location)
    if scraped_data:
        save_to_csv(scraped_data, args.job_title, args.location)

