import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import re

# Function to ensure the user profile directory exists
def create_profile_dir(profile_name):
    profile_dir = f"C:/Users/mr/Code/Nummerplade tjekker Script/Chrome user dir/{profile_name}"
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    return profile_dir

# Function to search and find 'Ejer-/brugerskift'
def find_ejer_brugerskift(vin, profile_name):
    driver = None
    ownership_changes = defaultdict(list)

    try:
        options = Options()
        options.add_argument("--headless")
        profile_path = create_profile_dir(profile_name)
        options.add_argument(f"user-data-dir={profile_path}")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        print("Starting Chrome with custom profile...")
        driver = webdriver.Chrome(options=options)
        print("Chrome started successfully.")
        
        driver.get("https://www.altombilen.dk/")
        print("Navigating to altombilen.dk...")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "text-searchvehicle"))
        )
        print("Page loaded successfully.")
        
        search_input = driver.find_element(By.ID, "text-searchvehicle")
        search_input.send_keys(vin)
        search_input.send_keys(Keys.RETURN)
        
        print(f"Searching for VIN {vin} on altombilen.dk")

        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.CLASS_NAME, "timeline-wrapper"))
        )
        
        time.sleep(10)
        
        # Find all divs with data-tabname="Ejer-/brugerskift"
        ejer_brugerskift_rows = driver.find_elements(By.XPATH, "//div[@data-tabname='Ejer-/brugerskift']")
        print(f"Found {len(ejer_brugerskift_rows)} 'Ejer-/brugerskift' rows for VIN {vin}.")

        if ejer_brugerskift_rows:
            for idx, row in enumerate(ejer_brugerskift_rows, start=1):
                print(f"\nProcessing 'Ejer-/brugerskift' event #{idx}:")
                
                # Extract the date
                try:
                    date_element = row.find_element(By.CLASS_NAME, "timeline-date")
                    date_str = date_element.text.strip()
                    
                    # Extract year from the date string
                    match = re.search(r"\b(2022|2023|2024)\b", date_str)
                    year = match.group(0) if match else "Unknown Year"
                    
                    print(f"  Date: {date_str} (Year: {year})")
                except:
                    date_str = "Date not found"
                    year = "Unknown Year"
                    print(f"  Date: {date_str}")
                
                # Extract the registration number(s)
                try:
                    regnr_elements = row.find_elements(By.XPATH, ".//table//td")
                    regnr_str = ", ".join([td.text.strip() for td in regnr_elements]) if regnr_elements else "Reg.nr. not found"
                    print(f"  Reg.nr.: {regnr_str}")
                except:
                    regnr_str = "Reg.nr. not found"
                    print(f"  Reg.nr.: {regnr_str}")

                # Add to the ownership_changes dictionary by year
                if year != "Unknown Year":
                    ownership_changes[year].append(f"VIN: {vin}, Reg.nr.: {regnr_str}, Date: {date_str}")

        else:
            print(f"No ownership changes found for VIN {vin}.")
    
    except Exception as e:
        print(f"An error occurred during processing VIN {vin}: {e}")
    
    finally:
        if driver:
            driver.quit()
            print("Closed Chrome.")

    return ownership_changes

# Function to get the VIN (Stelnummer) from nummerpladeregister.dk
def get_vin_from_numberplate(numberplate_url):
    response = requests.get(numberplate_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        vin_row = soup.find('td', string='Stelnummer')
        if vin_row:
            vin = vin_row.find_next_sibling('td', class_='dd').text.strip()
            print(f"Extracted VIN: {vin}")
            return vin
    return None

# Function to scrape VINs and check ownership changes
def process_vin(vin, profile_name):
    ownership_changes = find_ejer_brugerskift(vin, profile_name)
    return ownership_changes

# Main function to manage the workflow
def main():
    base_url = "https://nummerpladeregister.dk/mercedes-benz/e-320-cdi"
    
    # Example of hardcoded numberplate URLs, replace with real scraping logic
    numberplate_urls = ["https://nummerpladeregister.dk/example"]  # Replace this with real URLs
    
    summary = defaultdict(list)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for numberplate_url in numberplate_urls:
            vin = get_vin_from_numberplate(numberplate_url)
            if vin:
                profile_name = f"Profile-{vin}"
                futures.append(executor.submit(process_vin, vin, profile_name))
        
        for future in as_completed(futures):
            ownership_changes = future.result()
            for year, changes in ownership_changes.items():
                summary[year].extend(changes)

    # Print the results categorized by year
    for year in ["2022", "2023", "2024"]:
        if summary[year]:
            print(f"\nCars which changed owners in {year}:")
            for change in summary[year]:
                print(f"- {change}")
        else:
            print(f"\nNo cars found with ownership changes in {year}.")

if __name__ == "__main__":
    main()
