# Apollo Web Scraper

This repository contains a Python-based web scraper designed to automate the extraction of business and professional data from Apollo. The scraper utilizes `Selenium` for dynamic web interaction and `BeautifulSoup` for parsing HTML, making it ideal for gathering information across multiple pages efficiently. The code is organized into a class structure for ease of use, scalability, and maintainability.

## Features

- **Login Automation**: Automatically logs in to Apollo with your credentials.
- **Data Extraction**: Scrapes essential information such as:
  - Business Name
  - Website
  - Industry (Niche)
  - Country
  - First and Last Names
  - Job Title
  - Phone Number
  - Personal and Company LinkedIn URLs
  - Personal Email
- **Multiple Pages Scraping**: Configurable to scrape data from multiple pages.
- **Data Export**: Saves the scraped data to an Excel file (`.xlsx` format).
- **Duplicate Removal**: Automatically removes duplicate entries from the final Excel file.
- **Randomized User Agents**: Uses a random user-agent header to prevent blocking and simulate human browsing behavior.

## Setup & Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/apollo-web-scraper.git
   cd apollo-web-scraper
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download and set up the Chrome WebDriver that matches your Chrome version.

4. Update the following in the code:

    - Your Apollo login credentials (email and password).
  
    - The Apollo saved list URL you want to scrape.

    - The number of pages you want to scrape.

## How to Use

1. Modify the `scraper.py` file with your Apollo credentials and target URL.

2. Run the script:

   ```bash
   python main.py
   ```
   
The script will log in to Apollo, scrape the data, and save it to an Excel file (`complete_data.xlsx`). It will also generate a cleaned file with duplicates removed (`output_file.xlsx`).
