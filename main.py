

from seleniumbase import SB
from bs4 import BeautifulSoup
import time
import json
import os
import csv


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
OUTPUT_FORMAT = config.get('scraping', {}).get('output_format', 'both').lower()  # Default to 'both' if not specified
# Validate output_format
if OUTPUT_FORMAT not in ['json', 'csv', 'both']:
    print(f"Warning: Invalid output_format '{OUTPUT_FORMAT}'. Using 'both' instead.")
    OUTPUT_FORMAT = 'both'

def save_data_to_file(data, output_file="apollo_data.json", output_format="both"):
    """Appends scraped data to a JSON file incrementally (if JSON or both format is selected)."""
    if output_format not in ['json', 'both']:
        return  # Skip JSON saving if only CSV is requested
    
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
        
        # Get all unique keys from all records to create CSV headers
        all_keys = set()
        for record in data:
            all_keys.update(record.keys())
        
        # Sort keys for consistent column order
        fieldnames = sorted(all_keys)
        
        # Write to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in data:
                # Flatten nested structures
                row = {}
                for key in fieldnames:
                    value = record.get(key, '')
                    # Handle lists (like social_media)
                    if isinstance(value, list):
                        value = ', '.join(str(item) for item in value) if value else 'NA'
                    # Handle dictionaries (like organization)
                    elif isinstance(value, dict):
                        value = ', '.join(f"{k}: {v}" for k, v in value.items()) if value else 'NA'
                    # Handle None values
                    elif value is None:
                        value = 'NA'
                    else:
                        value = str(value)
                    row[key] = value
                
                writer.writerow(row)
        
        print(f"\nCSV file created: {csv_file}")
        print(f"Total records in CSV: {len(data)}")
        
    except Exception as e:
        print(f"Error converting JSON to CSV: {e}")

def save_data_to_csv(data, csv_file="apollo_data.csv"):
    """Appends scraped data to a CSV file incrementally."""
    try:
        # Read existing data if file exists
        existing_data = []
        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    existing_data = list(reader)
            except Exception as e:
                print(f"Warning: Could not read existing CSV file: {e}")
                existing_data = []
        
        # Merge existing data with new data
        all_data = existing_data + data
        
        if not all_data:
            return
        
        # Get all unique keys from all records to create CSV headers
        all_keys = set()
        for record in all_data:
            all_keys.update(record.keys())
        
        # Sort keys for consistent column order
        fieldnames = sorted(all_keys)
        
        # Write to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in all_data:
                # Flatten nested structures
                row = {}
                for key in fieldnames:
                    value = record.get(key, '')
                    # Handle lists (like social_media)
                    if isinstance(value, list):
                        value = ', '.join(str(item) for item in value) if value else 'NA'
                    # Handle dictionaries (like organization)
                    elif isinstance(value, dict):
                        value = ', '.join(f"{k}: {v}" for k, v in value.items()) if value else 'NA'
                    # Handle None values
                    elif value is None:
                        value = 'NA'
                    else:
                        value = str(value)
                    row[key] = value
                
                writer.writerow(row)
        
        print(f"Data saved to CSV: {len(data)} new contacts added. Total contacts in {csv_file}: {len(all_data)}")
        
    except Exception as e:
        print(f"Error saving data to CSV: {e}")

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

def unlock_contact_details(sb, person_id):
    """Unlock email and phone number for a contact by calling Apollo APIs."""
    try:
        # Generate cache key (timestamp)
        cache_key = int(time.time() * 1000)
        
        # Payload for both APIs
        payload = {
            "entity_ids": [person_id],
            "analytics_context": "Searcher: Individual Add Button",
            "skip_fetching_people": True,
            "cta_name": "Access email",
            "cacheKey": cache_key
        }
        
        # Clear previous unlock responses
        sb.execute_script("window.__apollo_unlock_responses = [];")
        
        # Step 1: Call safety_check API
        safety_check_url = "https://app.apollo.io/api/v1/mixed_people/safety_check"
        print(f"  Calling safety_check for person {person_id}...")
        
        # Make the API call via JavaScript
        sb.execute_script(f"""
            fetch('{safety_check_url}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({json.dumps(payload)})
            }}).catch(err => console.error('Safety check error:', err));
        """)
        
        time.sleep(1)  # Small delay between API calls
        
        # Step 2: Call add_to_my_prospects API and wait for response
        add_prospects_url = "https://app.apollo.io/api/v1/mixed_people/add_to_my_prospects"
        print(f"  Calling add_to_my_prospects for person {person_id}...")
        
        # Update cache key for second call
        payload['cacheKey'] = int(time.time() * 1000)
        
        # Make the API call
        sb.execute_script(f"""
            fetch('{add_prospects_url}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({json.dumps(payload)})
            }}).catch(err => console.error('Add prospects error:', err));
        """)
        
        # Wait for the response to appear in intercepted responses
        prospects_response = None
        start_time = time.time()
        timeout = 10  # 10 seconds timeout
        initial_response_count = 0
        
        # Get initial count of responses
        try:
            initial_responses = sb.execute_script("return window.__apollo_unlock_responses || [];")
            initial_response_count = len(initial_responses) if initial_responses else 0
        except:
            pass
        
        while time.time() - start_time < timeout:
            try:
                responses = sb.execute_script("return window.__apollo_unlock_responses || [];")
                if responses and len(responses) > initial_response_count:
                    # Get the most recent response (the one we just got)
                    prospects_response = responses[-1]
                    # Verify it has contacts
                    if 'contacts' in prospects_response and len(prospects_response['contacts']) > 0:
                        print(f"  Response received for person {person_id}")
                        break
            except Exception as e:
                pass
            time.sleep(0.5)
        
        # Fallback: Try to capture from network logs if JS interception didn't work
        if not prospects_response:
            print(f"  Trying network logs method for unlock response...")
            prospects_response = capture_api_response(sb, add_prospects_url, timeout=5)
        
        if not prospects_response:
            print(f"  Timeout waiting for unlock response for person {person_id}")
            return None, None
        
        # Extract email and phone from response
        email = None
        phone = None
        
        if 'contacts' in prospects_response and len(prospects_response['contacts']) > 0:
            contact = prospects_response['contacts'][0]
            
            # Get email
            email = contact.get('email', None)
            if not email and 'contact_emails' in contact and len(contact['contact_emails']) > 0:
                email = contact['contact_emails'][0].get('email', None)
            
            # Get phone number
            if 'phone_numbers' in contact and len(contact['phone_numbers']) > 0:
                phone = contact['phone_numbers'][0].get('raw_number', None)
                if not phone:
                    phone = contact['phone_numbers'][0].get('sanitized_number', None)
        
        return email, phone
        
    except Exception as e:
        print(f"  Error unlocking contact details for {person_id}: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def scrape_apollo(email, password, login_url, list_url, output_file="apollo_data.json", output_format="both"):
    all_data = []
    total_contacts_scraped = 0
    current_page = 1
    API_URL = "https://app.apollo.io/api/v1/mixed_people/search"
    
    # Determine file names based on output format
    json_file = output_file if output_file.endswith('.json') else "apollo_data.json"
    csv_file = json_file.replace('.json', '.csv')

    # Clear the output files at the start of a new scrape
    if output_format in ['json', 'both']:
        if os.path.exists(json_file):
            os.remove(json_file)
    if output_format in ['csv', 'both']:
        if os.path.exists(csv_file):
            os.remove(csv_file)

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
            window.__apollo_unlock_responses = [];
            
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
                if (typeof url === 'string' && url.includes('mixed_people/add_to_my_prospects')) {
                    return originalFetch.apply(this, args).then(response => {
                        const clonedResponse = response.clone();
                        clonedResponse.json().then(data => {
                            window.__apollo_unlock_responses.push(data);
                            console.log('Unlock API response intercepted:', data);
                        }).catch(err => console.error('Error parsing unlock API response:', err));
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
                if (this._url && this._url.includes('mixed_people/add_to_my_prospects')) {
                    this.addEventListener('load', function() {
                        try {
                            const data = JSON.parse(this.responseText);
                            window.__apollo_unlock_responses.push(data);
                            console.log('Unlock API response intercepted via XHR:', data);
                        } catch(e) {
                            console.error('Error parsing unlock XHR response:', e);
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
                
                for idx, person in enumerate(people, 1):
                    person_id = person.get('id')
                    person_name = person.get('name', 'Unknown')
                    
                    print(f"\n  Processing person {idx}/{len(people)}: {person_name} (ID: {person_id})")
                    
                    # Initialize person data with basic info
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
                    
                    # Unlock email and phone if person_id is available and email/phone are locked
                    if person_id:
                        # Check if email/phone need unlocking
                        current_email = person.get('email', '')
                        current_phone = person.get('phone_numbers', [{}])[0].get('raw_number', '') if person.get('phone_numbers') else ''
                        
                        needs_unlock = (
                            not current_email or 
                            current_email == 'email_not_unlocked@domain.com' or
                            not current_phone or
                            len(person.get('phone_numbers', [])) == 0
                        )
                        
                        if needs_unlock:
                            print(f"  Unlocking contact details for {person_name}...")
                            unlocked_email, unlocked_phone = unlock_contact_details(sb, person_id)
                            
                            if unlocked_email and unlocked_email != 'email_not_unlocked@domain.com':
                                person_data['email'] = unlocked_email
                                print(f"  ✓ Email unlocked: {unlocked_email}")
                            else:
                                print(f"  ✗ Email not available or still locked")
                            
                            if unlocked_phone:
                                person_data['phone_number'] = unlocked_phone
                                print(f"  ✓ Phone unlocked: {unlocked_phone}")
                            else:
                                print(f"  ✗ Phone not available")
                            
                            # Small delay between unlocking contacts to avoid rate limiting
                            time.sleep(1)
                        else:
                            print(f"  Email and phone already available")
                    
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
                # Always save to JSON (needed for JSON mode, both mode, and as temp storage for CSV mode)
                if output_format in ['json', 'both', 'csv']:
                    save_data_to_file(page_data, json_file, 'json')  # Always save as JSON for now
            
            # Clear intercepted responses for next page
            try:
                sb.execute_script("window.__apollo_api_responses = []; window.__apollo_unlock_responses = [];")
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

    # Final processing based on output format
    if output_format == 'json':
        print(f"\nScraping finished. Total pages scraped: {current_page-1}. Total contacts saved to {json_file}: {total_contacts_scraped}")
    elif output_format == 'csv':
        print(f"\nScraping finished. Total pages scraped: {current_page-1}. Converting to CSV...")
        # Convert JSON to CSV (JSON was used as temporary storage)
        convert_json_to_csv(json_file, csv_file)
        # Delete temporary JSON file if CSV-only mode
        if os.path.exists(json_file):
            os.remove(json_file)
            print(f"Temporary JSON file removed. CSV file saved: {csv_file}")
        print(f"Total contacts saved to {csv_file}: {total_contacts_scraped}")
    else:  # both
        print(f"\nScraping finished. Total pages scraped: {current_page-1}. Total contacts saved to {json_file}: {total_contacts_scraped}")
        # Convert JSON to CSV after scraping is complete
        print(f"\nConverting JSON to CSV...")
        convert_json_to_csv(json_file, csv_file)

# Run scraper
scrape_apollo(EMAIL, PASSWORD, LOGIN_URL, TARGET_URL, output_format=OUTPUT_FORMAT)
