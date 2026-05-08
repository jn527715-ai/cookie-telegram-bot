#!/usr/bin/env python3
"""
Motor de generación de cookies para el Bot de Telegram
"""

import os
import time
import random
import hashlib
import logging
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass, asdict

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium_stealth import stealth
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CookieGen")

@dataclass
class GeneratedCookie:
    cookie_string: str
    email: str
    password: str
    user_agent: str
    timestamp: str
    time_elapsed: float
    site: str = "Amazon.com"

class CookieGenerator:
    """Generador de cookies optimizado para bot de Telegram"""
    
    AMAZON_REGISTER_URL = "https://www.amazon.com/ap/register"
    AMAZON_HOME = "https://www.amazon.com"
    TIMEOUT = 25
    
    def __init__(self):
        self.ua = UserAgent()
        self._setup_env()
    
    def _setup_env(self):
        """Configura entorno headless"""
        for browser in ['/usr/bin/chromium-browser', '/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable']:
            if os.path.exists(browser):
                os.environ['CHROME_BIN'] = browser
                break
        if 'CHROME_BIN' not in os.environ:
            os.system('apt-get update && apt-get install -y chromium-browser')
            os.environ['CHROME_BIN'] = '/usr/bin/chromium-browser'
    
    def _build_driver(self):
        options = uc.ChromeOptions()
        options.add_argument(f"--window-size={random.randint(1280,1920)},{random.randint(720,1080)}")
        options.add_argument(f"--user-agent={self.ua.random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless=new")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--single-process")
        
        driver = uc.Chrome(options=options, version_main=None)
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        driver.set_page_load_timeout(40)
        return driver
    
    def _human_type(self, element, text: str):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.03, 0.15))
            if random.random() < 0.02:
                element.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
                element.send_keys(char)
    
    def generate(self, email: str, password: str, name: str = None) -> Tuple[bool, any, str]:
        driver = None
        start = time.time()
        if not name:
            names = ["Michael Smith", "Emma Johnson", "David Brown", "Olivia Davis"]
            name = random.choice(names)
        logger.info(f"🎯 Generando: {email}")
        try:
            driver = self._build_driver()
            driver.get(self.AMAZON_REGISTER_URL)
            time.sleep(random.uniform(2, 4))
            WebDriverWait(driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "ap_customer_name"))
            ).send_keys(name)
            time.sleep(0.3)
            driver.find_element(By.ID, "ap_email").send_keys(email)
            time.sleep(0.3)
            driver.find_element(By.ID, "ap_password").send_keys(password)
            time.sleep(0.3)
            driver.find_element(By.ID, "ap_password_check").send_keys(password)
            time.sleep(0.5)
            driver.find_element(By.ID, "continue").click()
            time.sleep(random.uniform(5, 8))
            current_url = driver.current_url.lower()
            try:
                error = driver.find_element(By.ID, "auth-error-message-box")
                if error.is_displayed():
                    return False, None, error.text[:100]
            except:
                pass
            success_indicators = ["your-account", "register-complete", "nav-link-accountList"]
            if not any(ind in current_url for ind in success_indicators):
                return False, None, "Registro fallido (posible CAPTCHA)"
            warmup_pages = ["/gp/your-account/order-history", "/gp/css/homepage.html"]
            for page in warmup_pages:
                try:
                    driver.get(f"{self.AMAZON_HOME}{page}")
                    time.sleep(1.5)
                except:
                    pass
            cookies = driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            result = GeneratedCookie(
                cookie_string=cookie_str,
                email=email,
                password=password,
                user_agent=driver.execute_script("return navigator.userAgent"),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                time_elapsed=round(time.time() - start, 2)
            )
            logger.info(f"✅ Cookie generada en {result.time_elapsed}s")
            return True, result, None
        except TimeoutException:
            return False, None, "Timeout - Amazon tardó mucho"
        except WebDriverException as e:
            return False, None, f"Error navegador: {str(e)[:80]}"
        except Exception as e:
            logger.error(f"Error: {e}")
            return False, None, f"Error: {str(e)[:80]}"
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
