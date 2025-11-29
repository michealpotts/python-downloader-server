from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import sys
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    try:
        chrome_options = Options()
        
        # Essential options for headless environment
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--headless')
        
        # Enhanced stability options for cloud environments
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        
        # Performance optimizations
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--disable-images')  # Consider enabling if you need images
        chrome_options.add_argument('--disable-javascript')  # Remove if you need JS
        
        # Set user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Configure service with timeouts
        service_kwargs = {}
        
        # Render.com specific path
        if os.path.exists('/usr/bin/chromedriver'):
            service_kwargs['service'] = Service('/usr/bin/chromedriver')
        
        # Set page load strategy to 'eager' for faster loading
        chrome_options.page_load_strategy = 'eager'
        
        driver = webdriver.Chrome(**service_kwargs, options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        # Additional anti-detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        return driver
        
    except Exception as e:
        logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
        raise

def find_sign_link(link):
    driver = None
    try:
        driver = setup_driver()
        logger.info(f"Navigating to: {link}")
        
        # Navigate with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(link)
                logger.info("Page loaded successfully")
                break
            except TimeoutException:
                logger.warning(f"Page load timeout, attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
        
        # Wait for the page to be ready
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        
        # Additional wait for video elements with multiple selectors
        logger.info("Looking for video elements...")
        
        # Try multiple strategies to find video
        video_selectors = [
            (By.TAG_NAME, "video"),
            (By.CSS_SELECTOR, "video source"),
            (By.CSS_SELECTOR, "video[src]"),
            (By.CSS_SELECTOR, "[data-video-src]"),
        ]
        
        video_src = None
        for by, selector in video_selectors:
            try:
                elements = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((by, selector))
                )
                if elements:
                    logger.info(f"Found {len(elements)} elements with {by}={selector}")
                    
                    # Try to get src from different attributes
                    for element in elements:
                        video_src = (element.get_attribute("src") or 
                                   element.get_attribute("data-src") or
                                   element.get_attribute("data-video-src"))
                        
                        if video_src:
                            logger.info(f"Found video source: {video_src}")
                            return video_src
                            
            except TimeoutException:
                logger.info(f"No elements found with {by}={selector}")
                continue
        
        if not video_src:
            logger.warning("No video source found with any selector")
            
            # Debug: Save page source for inspection
            page_source = driver.page_source
            logger.info(f"Page source length: {len(page_source)}")
            
            # Look for any media elements
            media_elements = driver.find_elements(By.CSS_SELECTOR, "[src*='video'], [src*='mp4'], [src*='webm']")
            logger.info(f"Found {len(media_elements)} media elements")
            
        return video_src
        
    except TimeoutException as e:
        logger.error(f"Timeout while waiting for elements: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver quit successfully")
            except Exception as e:
                logger.warning(f"Driver quit failed: {e}")