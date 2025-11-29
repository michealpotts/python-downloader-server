from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import subprocess
import sys
import os

def setup_driver():
    try:
        chrome_options = Options()
        
        # Essential options for Render.com
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        
        # Additional stability options for Render
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Render.com specific paths
        chrome_binary = None
        
        # Check for Chrome in common Render locations
        possible_chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome-stable'
        ]
        
        for path in possible_chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                print(f"Found Chrome at: {path}")
                break
        
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        
        # ChromeDriver setup for Render
        chromedriver_path = None
        possible_driver_paths = [
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
            '/opt/homebrew/bin/chromedriver',
            '/app/.chromedriver/bin/chromedriver'  # Common in buildpacks
        ]
        
        for path in possible_driver_paths:
            if os.path.exists(path):
                chromedriver_path = path
                print(f"Found ChromeDriver at: {path}")
                break
        
        if chromedriver_path:
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Fallback - let Selenium find it in PATH
            print("Using ChromeDriver from PATH")
            driver = webdriver.Chrome(options=chrome_options)
        
        # Anti-detection scripts
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        return driver
        
    except Exception as e:
        print(f"Failed to initialize Chrome WebDriver: {str(e)}")
        
        # Debug information
        print("Debug info:")
        print(f"Python version: {sys.version}")
        print("Chrome check:")
        try:
            result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
            print(f"which google-chrome: {result.stdout}")
        except Exception as ex:
            print(f"which check failed: {ex}")
            
        print("ChromeDriver check:")
        try:
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            print(f"which chromedriver: {result.stdout}")
        except Exception as ex:
            print(f"which check failed: {ex}")
            
        sys.exit(1)

def find_sign_link(link):
    driver = setup_driver()
    try:
        print(f"Navigating to: {link}")
        driver.get(link)
        
        # Wait for page to load completely
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Try multiple strategies to find video
        video_src = None
        
        # Strategy 1: Direct video tag
        try:
            video_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "video"))
            )
            if video_elements:
                video_src = video_elements[0].get_attribute("src")
                print(f"Found video via tag: {video_src}")
        except Exception as e:
            print(f"Video tag strategy failed: {e}")
        
        # Strategy 2: Source tags inside video
        if not video_src:
            try:
                source_elements = driver.find_elements(By.TAG_NAME, "source")
                for source in source_elements:
                    src = source.get_attribute("src")
                    if src and any(ext in src.lower() for ext in ['.mp4', '.webm', '.ogg']):
                        video_src = src
                        print(f"Found video via source tag: {video_src}")
                        break
            except Exception as e:
                print(f"Source tag strategy failed: {e}")
        
        # Strategy 3: Iframe content
        if not video_src:
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        iframe_videos = driver.find_elements(By.TAG_NAME, "video")
                        if iframe_videos:
                            video_src = iframe_videos[0].get_attribute("src")
                            print(f"Found video in iframe: {video_src}")
                            break
                    except Exception as e:
                        print(f"iframe check failed: {e}")
                    finally:
                        driver.switch_to.default_content()
            except Exception as e:
                print(f"Iframe strategy failed: {e}")
        
        return video_src
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return None
    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"Warning: driver.quit() failed: {e}")