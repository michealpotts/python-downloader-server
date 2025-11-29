from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import sys
import os

def setup_driver():
    try:
        chrome_options = Options()
        
        # Essential options for Render.com
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Use webdriver-manager to handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Anti-detection scripts
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
        
    except Exception as e:
        print(f"Failed to initialize Chrome WebDriver: {str(e)}")
        sys.exit(1)

# Keep your existing find_sign_link function the same
def find_sign_link(link):
    driver = setup_driver()
    try:
        print(f"Navigating to: {link}")
        driver.get(link)
        
        # Wait for page to load and find video elements
        video_elements = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "video"))
        )
        print(f"Found {len(video_elements)} video elements.")
        
        if video_elements:
            video_src = video_elements[0].get_attribute("src")
            print(f"Video source: {video_src}")
            return video_src
        else:
            print("No video elements found")
            return None
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return None
    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"Warning: driver.quit() failed: {e}")