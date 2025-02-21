import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Replace these with your credentials
USERNAME = "username"
PASSWORD = "password"

def scrape_page(url, driver):
    try:
        # Set up Selenium WebDriver
        options = Options()
        options.add_experimental_option("detach", True)  
        
        # Initialize driver if it's None
        if driver is None:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)

            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "username")) 
            )
            password_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "password")) 
            )
  
            username_input.send_keys(USERNAME)
            password_input.send_keys(PASSWORD)
            password_input.send_keys(Keys.RETURN)

            # Wait for manual 2FA approval
            input("Please approve 2FA in your app, then press Enter to continue...\n")

        else:
            driver.get(url)

        # Wait for the "Live" link to be visible using its ID
        live_link_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'live-link-')]"))
        )
        live_link = live_link_element.get_attribute("href")

        live_link_status = "No"
        if live_link:
            try:
                response = requests.get(live_link, allow_redirects=False)  # Don't follow redirects
                if response.status_code == 200:
                    live_link_status = "Yes"
                elif response.status_code in [301, 302] and response.headers.get('Location') == "https://library.tamu.edu/404":  # Handle redirects
                    live_link_status = "No"
                else:
                    live_link_status = f"No"
            except requests.RequestException as e:
                live_link_status = f"No"

        file_name = "Unknown"
        file_type = "Unknown"
        file_element = driver.find_element(By.TAG_NAME, 'h1') 
        if file_element:
            file_name = file_element.text.strip().replace('File: ', '')
        
        # Set file type based on extension
        if file_name.lower().endswith(('.jpg', '.png')):
            file_type = "image"
        elif file_name.lower().endswith('.pdf'):
            file_type = "pdf"
        else:
            file_type = "page"
        
        # Keep browser open for debugging
        print("\nScraping complete. Close the browser manually when done.")
        
        result = {
            "File Name": file_name,
            "File Type": file_type,
            "CMS URL": url,
            "URL": live_link,
            "Published?": live_link_status
        }
        
        save_to_csv(result)
        return result
    
    except Exception as e:
        return {"Error": str(e)}

def save_to_csv(data, filename="scraped_data.csv"):
    # Define the CSV column headers (without Link Status)
    headers = ["File Name", "CMS URL", "File Type", "Published?", "URL"]
    
    # Open CSV file in append mode and write data
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        
        # Write header only if the file is empty
        if file.tell() == 0:
            writer.writeheader()
        
        writer.writerow(data)
    print(f"Data saved to {filename}")

# Example usage
urls = [
    "https://tamu.cascadecms.com/entity/open.act?id=0f8fe8ab0a000094392877edb4d80e0b&type=page",
    # Add more URLs here
]

driver = None

for url in urls:
    data = scrape_page(url, driver)

if driver:
    driver.quit()
