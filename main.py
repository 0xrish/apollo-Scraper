from seleniumbase import SB
from bs4 import BeautifulSoup
import time
import json
import os
import pandas as pd


def load_config(config_path='config.json'):
    """Load configuration from config.json file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


# Load configuration from config.json
config = load_config()
EMAIL = config['credentials']['email']
PASSWORD = config['credentials']['password']
TARGET_URL = config['urls']['saved_link_list']
LOGIN_URL = config['urls']['login_url']
HOMEPAGE_CLASS = config['selectors']['homepage_class']
CONTACT_NAME_CELL = config['selectors']['contact_name_cell']['value']
TABLE_XPATH = config['selectors']['table_xpath']
TIMEOUT = config['timeouts']['page_load']
MAX_PAGES = config.get('scraping', {}).get('max_pages', 10)  # Default to 10 if not specified

def save_data_to_file(data, output_file="apollo_data.json"):
    """Appends scraped data to a JSON file incrementally."""
    # Read existing data if file exists
    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            # If file is corrupted or empty, start fresh
            existing_data = []
    
    # Merge existing data with new data
    all_data = existing_data + data
    
    # Write all data back to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print(f"Data saved: {len(data)} new contacts added. Total contacts in {output_file}: {len(all_data)}")

def convert_json_to_csv(json_file="apollo_data.json", csv_file="apollo_data.csv"):
    """Convert JSON file to CSV format."""
    try:
        # Read JSON file
        if not os.path.exists(json_file):
            print(f"JSON file {json_file} not found. Skipping CSV conversion.")
            return
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("No data found in JSON file. Skipping CSV conversion.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Handle nested fields (like social_media which might be a list)
        # Flatten social_media list to comma-separated string
        if 'social_media' in df.columns:
            df['social_media'] = df['social_media'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else str(x)
            )
        
        # Save to CSV
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"\nCSV file created: {csv_file}")
        print(f"Total records in CSV: {len(df)}")
        
    except Exception as e:
        print(f"Error converting JSON to CSV: {e}")

def capture_api_response(sb, api_url, timeout=30):
    """Capture API response from network logs."""
    print(f"Waiting for API call to {api_url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Get performance logs
            logs = sb.driver.get_log('performance')
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    method = message.get('message', {}).get('method', '')
                    
                    if method == 'Network.responseReceived':
                        response_params = message.get('message', {}).get('params', {})
                        response_url = response_params.get('response', {}).get('url', '')
                        
                        if api_url in response_url:
                            request_id = response_params.get('requestId')
                            if request_id:
                                try:
                                    # Get response body using CDP
                                    response_body = sb.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                    body_text = response_body.get('body', '{}')
                                    api_data = json.loads(body_text)
                                    print(f"API response captured successfully!")
                                    return api_data
                                except Exception as e:
                                    print(f"Error reading response body: {e}")
                                    continue
                except (json.JSONDecodeError, KeyError) as e:
                    continue
            
            time.sleep(1)  # Check every second
        except Exception as e:
            print(f"Error checking for API response: {e}")
            time.sleep(1)
    
    print(f"Timeout: API response not captured after {timeout} seconds")
    return None

def scrape_apollo(email, password, login_url, list_url, output_file="apollo_data.json"):
    all_data = []
    total_contacts_scraped = 0
    current_page = 1
    API_URL = "https://app.apollo.io/api/v1/mixed_people/search"

    # Clear the output file at the start of a new scrape
    if os.path.exists(output_file):
        os.remove(output_file)

    with SB(uc=True, headless=False) as sb:
        sb.open(login_url)
        time.sleep(2)  # Wait for page to load
        
        # Login
        print("Entering email...")
        sb.type('input[name="email"]', email)
        time.sleep(1)
        
        print("Entering password...")
        sb.type('input[name="password"]', password)
        time.sleep(1)
        
        print("Clicking login button...")
        sb.click('form button[type="submit"]')
        time.sleep(2)  # Wait after clicking login
        
        # Handle captcha if present
        try:
            print("Checking for captcha...")
            sb.uc_gui_click_captcha()  # UC bypasses Turnstile
            time.sleep(2)
        except Exception as e:
            print(f"Captcha handling: {e}")

        # Wait for dashboard with better error handling
        print("Waiting for homepage to load...")
        try:
            sb.wait_for_element_visible(f'.{HOMEPAGE_CLASS}', timeout=TIMEOUT)
            print("Homepage loaded successfully")
        except Exception as e:
            print(f"Homepage element not found: {e}")
            print("Checking current URL...")
            current_url = sb.get_current_url()
            print(f"Current URL: {current_url}")
            
            # Check if we're on a captcha page
            if "challenges.cloudflare.com" in current_url or "cf-browser-check" in current_url:
                print("Cloudflare captcha detected. Please solve it manually...")
                print("Waiting for captcha to be solved...")
                # Wait for user to solve captcha
                max_wait = 300  # 5 minutes
                start_time = time.time()
                while time.time() - start_time < max_wait:
                    time.sleep(2)
                    current_url = sb.get_current_url()
                    if "challenges.cloudflare.com" not in current_url and "cf-browser-check" not in current_url:
                        print("Captcha appears to be solved!")
                        break
                # Try waiting for homepage again
                try:
                    sb.wait_for_element_visible(f'.{HOMEPAGE_CLASS}', timeout=TIMEOUT)
                except:
                    print("Continuing anyway...")
            else:
                print("Continuing to saved link list...")
        
        # Enable network domain for API interception
        try:
            sb.driver.execute_cdp_cmd('Network.enable', {})
            sb.driver.execute_cdp_cmd('Runtime.enable', {})
            print("Network monitoring enabled")
        except Exception as e:
            print(f"Warning: Could not enable network monitoring: {e}")
        
        # Set up JavaScript interception for API calls
        sb.execute_script("""
            window.__apollo_api_responses = [];
            
            // Intercept fetch
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                if (typeof url === 'string' && url.includes('mixed_people/search')) {
                    return originalFetch.apply(this, args).then(response => {
                        const clonedResponse = response.clone();
                        clonedResponse.json().then(data => {
                            window.__apollo_api_responses.push(data);
                            console.log('API response intercepted:', data);
                        }).catch(err => console.error('Error parsing API response:', err));
                        return response;
                    });
                }
                return originalFetch.apply(this, args);
            };
            
            // Intercept XMLHttpRequest
            const originalXHROpen = XMLHttpRequest.prototype.open;
            const originalXHRSend = XMLHttpRequest.prototype.send;
            
            XMLHttpRequest.prototype.open = function(method, url) {
                this._url = url;
                return originalXHROpen.apply(this, arguments);
            };
            
            XMLHttpRequest.prototype.send = function() {
                if (this._url && this._url.includes('mixed_people/search')) {
                    this.addEventListener('load', function() {
                        try {
                            const data = JSON.parse(this.responseText);
                            window.__apollo_api_responses.push(data);
                            console.log('API response intercepted via XHR:', data);
                        } catch(e) {
                            console.error('Error parsing XHR response:', e);
                        }
                    });
                }
                return originalXHRSend.apply(this, arguments);
            };
        """)
        
        # Navigate to saved link list
        print(f"Navigating to saved link list: {list_url}")
        sb.open(list_url)
        time.sleep(3)  # Wait after navigation
        
        while current_page <= MAX_PAGES:
            print(f"\n--- Scraping Page {current_page} ---")
            
            # Wait for table to be available using the provided selector
            print("Waiting for contact list table to load...")
            try:
                sb.wait_for_element_visible(TABLE_XPATH, timeout=TIMEOUT)
                print("Contact list table loaded successfully")
            except Exception as e:
                print(f"Contact list table element not found: {e}")
                print("Waiting additional time...")
                time.sleep(5)
            
            # Wait for API response instead of scraping HTML
            print("Waiting for API response...")
            api_response = None
            
            # Method 1: Try to get from JavaScript interception
            start_time = time.time()
            while time.time() - start_time < 30:
                try:
                    responses = sb.execute_script("return window.__apollo_api_responses || [];")
                    if responses and len(responses) > 0:
                        # Get the most recent response
                        api_response = responses[-1]
                        print("API response captured via JavaScript interception!")
                        break
                except Exception as e:
                    pass
                time.sleep(1)
            
            # Method 2: Fallback to network logs if JS interception didn't work
            if not api_response:
                print("Trying network logs method...")
                api_response = capture_api_response(sb, API_URL, timeout=10)
            
            # Extract data from API response
            page_data = []
            if api_response and 'people' in api_response:
                people = api_response.get('people', [])
                print(f"Found {len(people)} people in API response")
                
                for person in people:
                    person_data = {
                        "name": person.get('name', 'NA'),
                        "first_name": person.get('first_name', 'NA'),
                        "last_name": person.get('last_name', 'NA'),
                        "email": person.get('email', 'NA'),
                        "company": person.get('organization', {}).get('name', 'NA') if person.get('organization') else 'NA',
                        "job_title": person.get('title', 'NA'),
                        "location": person.get('city', 'NA') + ', ' + person.get('state', 'NA') if person.get('city') else 'NA',
                        "linkedin_url": person.get('linkedin_url', 'NA'),
                        "twitter_url": person.get('twitter_url', 'NA'),
                        "github_url": person.get('github_url', 'NA'),
                        "phone_number": person.get('phone_numbers', [{}])[0].get('raw_number', 'NA') if person.get('phone_numbers') else 'NA',
                        "page": current_page
                    }
                    page_data.append(person_data)
            elif api_response:
                # If response structure is different, save raw data
                print("API response structure different than expected. Saving raw data...")
                page_data = [api_response]
            else:
                print("No API response captured. Skipping this page.")
                # Try to continue to next page anyway
                if current_page >= MAX_PAGES:
                    break
                try:
                    btn = sb.find_element('button[aria-label="Next"]')
                    if btn.get_attribute("disabled") is None:
                        sb.click('button[aria-label="Next"]')
                        time.sleep(2)
                        current_page += 1
                        continue
                    else:
                        break
                except:
                    break
            
            all_data.extend(page_data)
            total_contacts_scraped += len(page_data)
            print(f"Extracted {len(page_data)} contacts from Page {current_page}. Total contacts: {total_contacts_scraped}")
            
            # Save data incrementally after each page
            if page_data:
                save_data_to_file(page_data, output_file)
            
            # Clear intercepted responses for next page
            try:
                sb.execute_script("window.__apollo_api_responses = [];")
            except:
                pass

            if current_page >= MAX_PAGES:
                print(f"Reached maximum number of pages ({MAX_PAGES}). Ending scraping.")
                break
            
            # Try to go to next page
            try:
                btn = sb.find_element('button[aria-label="Next"]')

                # If the button is disabled exit the loop
                if btn.get_attribute("disabled") is not None:
                    print("Next button is disabled. No more pages.")
                    break
                else:
                    print("Clicking next page button...")
                    sb.click('button[aria-label="Next"]')
                    time.sleep(2)  # Wait after clicking
                    sb.wait_for_element_visible(CONTACT_NAME_CELL, timeout=TIMEOUT)
                    current_page += 1

            except Exception as e:
                print(f"Could not find or click next button: {e}")
                print("No more pages or button not available. Ending scraping.")
                break

    print(f"\nScraping finished. Total pages scraped: {current_page-1}. Total contacts saved to {output_file}: {total_contacts_scraped}")
    
    # Convert JSON to CSV after scraping is complete
    csv_file = output_file.replace('.json', '.csv')
    print(f"\nConverting JSON to CSV...")
    convert_json_to_csv(output_file, csv_file)

# Run scraper
scrape_apollo(EMAIL, PASSWORD, LOGIN_URL, TARGET_URL)
