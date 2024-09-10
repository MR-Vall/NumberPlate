from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def find_ejer_brugerskift(vin):
    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome()
    
    try:
        driver.get("https://www.altombilen.dk/")
        
        # Find the search input element and enter the VIN
        search_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "text-searchvehicle"))
        )
        search_input.send_keys(vin)
        search_input.send_keys(Keys.RETURN)  # Simulate hitting Enter
        
        print("Search submitted. Waiting for the timeline to load...")
        
        # Wait for the timeline-wrapper to ensure the page is fully loaded
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "timeline-wrapper"))
        )
        
        # Additional wait to allow all dynamic content to load
        time.sleep(5)
        
        # Save page source for debugging
        page_source = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as file:
            file.write(page_source)
        print("Page source saved to 'page_source.html'.")
        
        # Find all divs with data-tabname="Ejer-/brugerskift"
        ejer_brugerskift_rows = driver.find_elements(By.XPATH, "//div[@data-tabname='Ejer-/brugerskift']")
        print(f"Found {len(ejer_brugerskift_rows)} 'Ejer-/brugerskift' rows.")
        
        if ejer_brugerskift_rows:
            for idx, row in enumerate(ejer_brugerskift_rows, start=1):
                print(f"\nProcessing 'Ejer-/brugerskift' event #{idx}:")
                
                # Extract the date
                try:
                    date_element = row.find_element(By.CLASS_NAME, "timeline-date")
                    date_str = date_element.text.strip()
                    print(f"  Date: {date_str}")
                except:
                    date_str = "Date not found"
                    print(f"  Date: {date_str}")
                
                # Extract the registration number(s)
                try:
                    regnr_elements = row.find_elements(By.XPATH, ".//table//td")
                    regnr_str = ", ".join([td.text.strip() for td in regnr_elements]) if regnr_elements else "Reg.nr. not found"
                    print(f"  Reg.nr.: {regnr_str}")
                except:
                    regnr_str = "Reg.nr. not found"
                    print(f"  Reg.nr.: {regnr_str}")
        else:
            print("No 'Ejer-/brugerskift' rows found.")
    
    except Exception as e:
        print("An error occurred during processing:", e)
    
    finally:
        driver.quit()  # Ensure the driver is closed

def main():
    vin = "WDB2110221B363566"  # Example VIN to search
    find_ejer_brugerskift(vin)

if __name__ == "__main__":
    main()
