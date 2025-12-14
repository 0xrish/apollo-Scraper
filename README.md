# Apollo Web Scraper

This repository contains a Python-based web scraper designed to automate the extraction of business and professional data from Apollo.io. The scraper utilizes **SeleniumBase** (with Undetected Chrome) for browser automation and intercepts API responses to capture data efficiently. Instead of scraping HTML, it captures data directly from Apollo's API endpoints, making it more reliable and faster.

## Features

- **Login Automation**: Automatically logs in to Apollo.io with your credentials
- **API Response Interception**: Captures data directly from `https://app.apollo.io/api/v1/mixed_people/search` API instead of scraping HTML
- **Data Extraction**: Extracts comprehensive contact information including:
  - Full Name, First Name, Last Name
  - Email Address
  - Company Name
  - Job Title
  - Location (City, State)
  - LinkedIn, Twitter, GitHub URLs
  - Phone Number
- **Multi-Page Scraping**: Configurable maximum pages to scrape via `config.json`
- **Incremental Data Saving**: Saves data after each page to prevent data loss
- **Anti-Detection**: Uses SeleniumBase's Undetected Chrome mode to avoid bot detection
- **Captcha Handling**: Automatic captcha solving with 2Captcha integration and manual fallback
- **Configuration-Based**: All settings stored in `config.json` for easy management

## Setup & Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/apollo-scraper.git
   cd apollo-scraper
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   pip install seleniumbase  # SeleniumBase is required but not in requirements.txt
   ```

4. Configure the scraper:
   - Copy `config.json.example` to `config.json` (if available) or create `config.json`
   - Update `config.json` with your credentials:
     ```json
     {
       "credentials": {
         "email": "your-email@example.com",
         "password": "your-password",
         "two_captcha_api_key": "your-2captcha-api-key"
       },
       "urls": {
         "login_url": "https://app.apollo.io/#/login?locale=en",
         "saved_link_list": "your-apollo-saved-list-url"
       },
       "scraping": {
         "max_pages": 10
       }
     }
     ```

## How to Use

1. Ensure `config.json` is properly configured with your Apollo.io credentials and target URL.

2. Run the scraper:
   ```bash
   python main.py
   ```

3. The script will:
   - Log in to Apollo.io
   - Navigate to your saved list
   - Wait for each page to load and intercept the API response
   - Extract contact data from the API response
   - Save data incrementally to `apollo_data.json` after each page
   - Continue to the next page until `max_pages` is reached or no more pages are available

## Output

The scraper saves data to `apollo_data.json` in JSON format. Each contact entry contains:
```json
{
  "name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "company": "Example Corp",
  "job_title": "Software Engineer",
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "twitter_url": "NA",
  "github_url": "NA",
  "phone_number": "+1234567890",
  "page": 1
}
```

## Configuration

All configuration is managed through `config.json`:
- **Credentials**: Email, password, and 2Captcha API key
- **URLs**: Login URL and target saved list URL
- **Selectors**: CSS selectors and XPaths for page elements
- **Timeouts**: Page load and default timeouts
- **Scraping**: Maximum pages to scrape

## Requirements

- Python 3.7+
- Chrome browser installed
- SeleniumBase (with Undetected Chrome support)
- BeautifulSoup4
- Valid Apollo.io account credentials

## Notes

- The scraper uses Undetected Chrome mode to avoid detection
- Data is saved incrementally to prevent loss if the script is interrupted
- If automatic captcha solving fails, the script will prompt for manual solving
- The script waits for API responses rather than scraping HTML, making it more reliable

## License

This project is for educational purposes only. Please ensure you comply with Apollo.io's Terms of Service when using this scraper.
