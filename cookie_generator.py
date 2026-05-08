#!/usr/bin/env python3
"""
Motor de generación de cookies de Amazon - Edición Sigilo
Optimizado para evadir detección de bots
"""

import os
import time
import random
import logging
import subprocess
from datetime import datetime
from typing import Tuple
from dataclasses import dataclass
from pathlib import Path

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

REALISTIC_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

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
    AMAZON_REGISTER_URL = "https://www.amazon.com/ap/register"
    AMAZON_HOME = "https://www.amazon.com"
    TIMEOUT = 30

    def __init__(self):
        self.user_data_dir = "/tmp/chrome_profile"
        self._setup_env()

    def _setup_env(self):
        """Busca Chrome/Chromium instalado o usa la ruta por defecto de google-chrome-stable"""
        posibles = [
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium'
        ]
        for browser in posibles:
            if os.path.exists(browser):
                os.environ['CHROME_BIN'] = browser
                logger.info(f"✅ Navegador encontrado en {browser}")
                return
        os.environ['CHROME_BIN'] = '/usr/bin/google-chrome-stable'
        logger.warning("Navegador no detectado, usando ruta predeterminada /usr/bin/google-chrome-stable")

    def _get_chrome_main_version(self, binary_path):
        """Intenta extraer la versión principal de Chrome instalada (ej. 125)"""
        try:
            version_str = subprocess.check_output([binary_path, '--version']).decode('utf-8').strip()
            main_version = int(version_str.split(' ')[-1].split('.')[0])
            logger.info(f"Versión de Chrome detectada: {main_version}")
            return main_version
        except Exception as e:
            logger.warning(f"No se pudo obtener la versión exacta de Chrome: {e}")
            return None

    def _build_driver(self) -> uc.Chrome:
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

        options = uc.ChromeOptions()
        ua = random.choice(REALISTIC_USER_AGENTS)
        width = random.choice([1366, 1440, 1536, 1920])
        height = random.choice([768, 900, 864, 1080])
        
        options.add_argument(f"--window-size={width},{height}")
        options.add_argument(f"--user-agent={ua}")
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--single-process")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--log-level=3")

        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_settings.popups": 0,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True,
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)

        chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome-stable')
        v_main = self._get_chrome_main_version(chrome_bin)

        driver = uc.Chrome(
            options=options, 
            browser_executable_path=chrome_bin, 
            version_main=v_main,
            headless=True
        )

        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32" if "Windows" in ua else "MacIntel",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine" if "Windows" in ua else "Apple M1",
            fix_hairline=True,
        )

        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        driver.set_page_load_timeout(45)
        return driver

    def _human_type(self, element, text: str):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

    def _random_mouse_movements(self, driver):
        try:
            driver.execute_script(f"window.scrollTo(0, {random.randint(50, 300)});")
            time.sleep(0.5)
        except:
            pass

    def generate(self, email: str, password: str, name: str = None) -> Tuple[bool, any, str]:
        driver = None
        start = time.time()
        if not name:
            first_names = ["Michael", "Emma", "David", "Sophia"]
            last_names = ["Smith", "Johnson", "Williams", "Brown"]
            name = f"{random.choice(first_names)} {random.choice(last_names)}"

        try:
            driver = self._build_driver()
            driver.get(self.AMAZON_HOME)
            time.sleep(random.uniform(2, 3))
            
            try:
                driver.find_element(By.ID, "sp-cc-accept").click()
            except:
                pass
                
            driver.get(self.AMAZON_REGISTER_URL)
            time.sleep(random.uniform(2, 4))

            WebDriverWait(driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "ap_customer_name"))
            ).send_keys(name)
            time.sleep(0.5)
            
            driver.find_element(By.ID, "ap_email").send_keys(email)
            time.sleep(0.5)
            driver.find_element(By.ID, "ap_password").send_keys(password)
            time.sleep(0.5)
            driver.find_element(By.ID, "ap_password_check").send_keys(password)
            time.sleep(0.5)
            driver.find_element(By.ID, "continue").click()
            time.sleep(random.uniform(6, 10))

            current_url = driver.current_url.lower()
            if "register" in current_url or "ap/register" in current_url:
                return False, None, "Registro fallido o CAPTCHA"
                
            cookies = driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            return True, GeneratedCookie(
                cookie_string=cookie_str,
                email=email,
                password=password,
                user_agent=driver.execute_script("return navigator.userAgent"),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                time_elapsed=round(time.time() - start, 2)
            ), None
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return False, None, str(e)[:100]
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
