#!/usr/bin/env python3
"""
Motor de generación de cookies de Amazon - Edición Sigilo
Optimizado para evadir detección de bots
"""

import os
import time
import random
import logging
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

# ---------------------------------------------------------------------------
# Configuración anti-detección
# ---------------------------------------------------------------------------
REALISTIC_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
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
    """Generador de cookies con técnicas avanzadas anti-detección"""

    AMAZON_REGISTER_URL = "https://www.amazon.com/ap/register"
    AMAZON_HOME = "https://www.amazon.com"
    TIMEOUT = 30

    def __init__(self):
        self.user_data_dir = "/tmp/chrome_profile"
        self._setup_env()

    def _setup_env(self):
        """Detecta el binario de Chrome/Chromium y lo exporta"""
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
        # Si no existe, asumimos la ruta instalada por build command (chromium)
        os.environ['CHROME_BIN'] = '/usr/bin/chromium'
        logger.warning("Navegador no detectado, usando ruta predeterminada /usr/bin/chromium")

    def _build_driver(self) -> uc.Chrome:
        """Construye un navegador sigiloso"""

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
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless=new")
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
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # --- CORRECCIÓN: Pasar la ruta del binario explícitamente ---
        chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        driver = uc.Chrome(options=options, browser_executable_path=chrome_bin, version_main=None)

        # Aplicar stealth mejorado (UNA SOLA VEZ)
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
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({state: 'prompt'}) :
                originalQuery(parameters)
            );
        """)

        driver.set_page_load_timeout(45)
        return driver

    def _human_type(self, element, text: str):
        """Tecleo humano con errores"""
        for i, char in enumerate(text):
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.25))
            if random.random() < 0.02 and i > 0:
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.3))
                element.send_keys(char)

    def _random_mouse_movements(self, driver):
        """Movimientos de ratón realistas"""
        try:
            driver.execute_script(f"window.scrollTo(0, {random.randint(50, 400)});")
            time.sleep(random.uniform(0.2, 0.8))
            actions = ActionChains(driver)
            try:
                links = driver.find_elements(By.TAG_NAME, "a")[:5]
                if links:
                    random_link = random.choice(links)
                    actions.move_to_element(random_link)
                    actions.pause(random.uniform(0.3, 0.7))
                    actions.perform()
            except:
                pass
        except:
            pass

    def generate(self, email: str, password: str, name: str = None) -> Tuple[bool, any, str]:
        driver = None
        start = time.time()

        if not name:
            first_names = ["Michael", "Emma", "David", "Sophia", "James", "Mia", "William", "Olivia"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
            name = f"{random.choice(first_names)} {random.choice(last_names)}"

        logger.info(f"🎯 Generando cookie sigilosa para {email}")

        try:
            driver = self._build_driver()

            # Paso 0: visita la homepage
            driver.get(self.AMAZON_HOME)
            time.sleep(random.uniform(2.5, 4.0))
            self._random_mouse_movements(driver)

            # Cerrar popups
            try:
                driver.find_element(By.ID, "sp-cc-accept").click()
                time.sleep(0.5)
            except:
                pass

            # Paso 1: registro
            driver.get(self.AMAZON_REGISTER_URL)
            time.sleep(random.uniform(3.0, 5.0))
            self._random_mouse_movements(driver)

            # Rellenar formulario
            name_input = WebDriverWait(driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "ap_customer_name"))
            )
            name_input.clear()
            self._human_type(name_input, name)
            time.sleep(random.uniform(1.0, 2.0))

            driver.find_element(By.ID, "ap_email").send_keys(email)
            time.sleep(random.uniform(0.8, 1.5))
            driver.find_element(By.ID, "ap_password").send_keys(password)
            time.sleep(random.uniform(0.8, 1.5))
            driver.find_element(By.ID, "ap_password_check").send_keys(password)
            time.sleep(random.uniform(1.0, 2.0))

            self._random_mouse_movements(driver)

            continue_btn = driver.find_element(By.ID, "continue")
            ActionChains(driver).move_to_element(continue_btn).pause(0.5).click().perform()

            time.sleep(random.uniform(7, 11))

            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()

            # Verificar errores
            try:
                error_box = driver.find_element(By.ID, "auth-error-message-box")
                if error_box.is_displayed():
                    return False, None, error_box.text[:150]
            except:
                pass

            success_indicators = ["your-account", "register-complete", "nav-link-accountList"]
            if not any(ind in current_url for ind in success_indicators):
                if "captcha" in page_source:
                    return False, None, "CAPTCHA detectado"
                return False, None, "Registro fallido"

            logger.info("✅ Cuenta creada")

            # Calentar sesión
            for page in ["/gp/your-account/order-history", "/gp/css/homepage.html"]:
                try:
                    driver.get(self.AMAZON_HOME + page)
                    time.sleep(random.uniform(2.0, 3.5))
                except:
                    pass

            cookies = driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            elapsed = round(time.time() - start, 2)

            return True, GeneratedCookie(
                cookie_string=cookie_str,
                email=email,
                password=password,
                user_agent=driver.execute_script("return navigator.userAgent"),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                time_elapsed=elapsed,
            ), None

        except TimeoutException:
            return False, None, "Timeout: Amazon no respondió"
        except WebDriverException as e:
            return False, None, f"Error navegador: {str(e)[:80]}"
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return False, None, f"Error: {str(e)[:80]}"
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
