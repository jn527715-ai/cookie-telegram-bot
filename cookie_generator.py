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
# Lista de User-Agents realistas (Windows + Mac) con versiones recientes de Chrome
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
        self.user_data_dir = "/tmp/chrome_profile"  # Perfil persistente
        self._setup_env()

    def _setup_env(self):
        """Configura el binario de Chrome en el entorno"""
        posibles = [
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium'
        ]
        for browser in posibles:
            if os.path.exists(browser):
                os.environ['CHROME_BIN'] = browser
                logger.info(f"Usando Chrome: {browser}")
                break
        else:
            logger.warning("No se encontró Chrome instalado")

    def _build_driver(self) -> uc.Chrome:
        """Construye un navegador con configuración de sigilo"""

        # Crear carpeta de perfil si no existe
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

        options = uc.ChromeOptions()

        # Seleccionar un User-Agent realista
        ua = random.choice(REALISTIC_USER_AGENTS)

        # Configuración de ventana (tamaños comunes)
        width = random.choice([1366, 1440, 1536, 1920])
        height = random.choice([768, 900, 864, 1080])
        options.add_argument(f"--window-size={width},{height}")
        options.add_argument(f"--user-agent={ua}")

        # Configuraciones de perfil y caché (parece un usuario real que ya usaba Chrome)
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument("--profile-directory=Default")

        # Deshabilitar características que delatan automatización
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--disable-extensions")
        # El modo headless=new oculta mejor la automatización
        options.add_argument("--headless=new")
        # Opciones de rendimiento
        options.add_argument("--single-process")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")

        # Preferencias de perfil
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_settings.popups": 0,
            "download.prompt_for_download": False,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True,
            "profile.managed_default_content_settings.images": 1,  # Cargar imágenes
            "profile.default_content_setting_values.notifications": 2,  # Bloquear notificaciones
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Crear driver
        driver = uc.Chrome(options=options, version_main=None)

        # Aplicar stealth mejorado
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32" if "Windows" in ua else "MacIntel",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine" if "Windows" in ua else "Apple M1",
            fix_hairline=True,
        )

        # Inyectar scripts para ocultar automatización
        driver.execute_script("""
            // Eliminar webdriver
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            // Falsificar plugins
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            // Falsificar languages
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            // Falsificar permisos
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({state: 'prompt'}) :
                originalQuery(parameters)
            );
            // Falsificar conexiones de red
            if (navigator.connection) {
                navigator.connection = { effectiveType: '4g', rtt: 50, downlink: 10 };
            }
            // Falsificar battery status
            navigator.getBattery = () => Promise.resolve({ charging: true, level: 1 });
        """)

        driver.set_page_load_timeout(45)
        driver.set_script_timeout(30)

        return driver

    def _human_type(self, element, text: str):
        """Simula escritura humana con errores y ritmo variable"""
        for i, char in enumerate(text):
            element.send_keys(char)
            # Pausa variable entre teclas (más realista)
            time.sleep(random.uniform(0.05, 0.25))
            # Error tipográfico ocasional (2% probabilidad)
            if random.random() < 0.02 and i > 0:
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.3))
                element.send_keys(char)
                time.sleep(random.uniform(0.02, 0.1))

    def _random_mouse_movements(self, driver):
        """Movimientos de mouse complejos (scroll, hover, pausas)"""
        try:
            actions = ActionChains(driver)
            screen_width = driver.execute_script("return window.innerWidth")
            screen_height = driver.execute_script("return window.innerHeight")

            # Scroll aleatorio hacia abajo/arriba
            driver.execute_script(f"window.scrollTo(0, {random.randint(50, 400)});")
            time.sleep(random.uniform(0.2, 0.8))

            # Mover mouse a un elemento aleatorio (si hay)
            try:
                links = driver.find_elements(By.TAG_NAME, "a")[:10]
                if links:
                    random_link = random.choice(links)
                    actions.move_to_element(random_link)
                    actions.pause(random.uniform(0.3, 0.7))
                    actions.perform()
            except:
                pass

            # Movimiento aleatorio a otro punto
            x = random.randint(100, screen_width - 100)
            y = random.randint(100, screen_height - 100)
            actions.move_by_offset(x, y)
            actions.pause(random.uniform(0.1, 0.4))
            actions.perform()

        except Exception:
            pass

    def generate(self, email: str, password: str, name: str = None) -> Tuple[bool, any, str]:
        """Genera cookie para una cuenta nueva de Amazon con evasión de detección"""
        driver = None
        start = time.time()

        if not name:
            first_names = ["Michael", "Emma", "David", "Sophia", "James", "Mia", "William", "Olivia"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
            name = f"{random.choice(first_names)} {random.choice(last_names)}"

        logger.info(f"🎯 Iniciando generación sigilosa para: {email}")

        try:
            driver = self._build_driver()

            # --- PASO 0: Visitar página principal (parecer un usuario normal) ---
            logger.info("🌐 Visitando página principal de Amazon...")
            driver.get(self.AMAZON_HOME)
            time.sleep(random.uniform(2.5, 4.0))
            self._random_mouse_movements(driver)

            # Aceptar cookies si aparece (opcional)
            try:
                accept_btn = driver.find_element(By.ID, "sp-cc-accept")
                accept_btn.click()
                time.sleep(random.uniform(0.5, 1.0))
            except:
                pass

            # Cerrar posible popup de país
            try:
                popup = driver.find_element(By.CSS_SELECTOR, "[data-action-type='DISMISS']")
                popup.click()
                time.sleep(random.uniform(0.3, 0.7))
            except:
                pass

            # --- PASO 1: Ir al registro ---
            logger.info("📝 Navegando a registro...")
            driver.get(self.AMAZON_REGISTER_URL)
            time.sleep(random.uniform(3.0, 5.0))
            self._random_mouse_movements(driver)

            # --- PASO 2: Llenar formulario (con pausas humanas) ---
            logger.info("⌨️ Rellenando formulario con delays humanos...")

            name_input = WebDriverWait(driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "ap_customer_name"))
            )
            name_input.clear()
            self._human_type(name_input, name)
            time.sleep(random.uniform(0.8, 2.0))

            email_input = driver.find_element(By.ID, "ap_email")
            email_input.clear()
            self._human_type(email_input, email)
            time.sleep(random.uniform(0.8, 2.0))

            password_input = driver.find_element(By.ID, "ap_password")
            password_input.clear()
            self._human_type(password_input, password)
            time.sleep(random.uniform(0.8, 2.0))

            password_check = driver.find_element(By.ID, "ap_password_check")
            password_check.clear()
            self._human_type(password_check, password)
            time.sleep(random.uniform(1.0, 2.5))

            # Movimiento de mouse antes de hacer clic
            self._random_mouse_movements(driver)

            # --- PASO 3: Enviar ---
            logger.info("🚀 Enviando formulario...")
            continue_btn = driver.find_element(By.ID, "continue")
            actions = ActionChains(driver)
            actions.move_to_element(continue_btn)
            actions.pause(random.uniform(0.3, 0.7))
            actions.click()
            actions.perform()

            # --- PASO 4: Esperar respuesta y verificar ---
            time.sleep(random.uniform(6, 10))  # Espera más larga

            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()

            # Verificar errores visibles
            try:
                error_box = driver.find_element(By.ID, "auth-error-message-box")
                if error_box.is_displayed():
                    error_text = error_box.text[:150]
                    logger.error(f"Error de Amazon: {error_text}")
                    return False, None, error_text
            except:
                pass

            # Verificar éxito (redirigido a cuenta o página de confirmación)
            success_indicators = [
                "your-account",
                "register-complete",
                "nav-link-accountList",
                "ap/register-complete",
                "confirmation",
            ]
            if not any(ind in current_url for ind in success_indicators):
                # Posible CAPTCHA o bloqueo
                if "captcha" in page_source:
                    return False, None, "CAPTCHA detectado, intenta con otro email o usa una IP diferente"
                return False, None, "Registro fallido (posible verificación adicional o bloqueo de IP)"

            logger.info("✅ Cuenta creada exitosamente")

            # --- PASO 5: Calentar sesión (navegar) ---
            logger.info("🔥 Calentando sesión...")
            warmup_pages = [
                "/gp/your-account/order-history",
                "/gp/css/homepage.html",
                "/gp/your-account/address-list",
            ]
            for page in warmup_pages:
                try:
                    driver.get(self.AMAZON_HOME + page)
                    time.sleep(random.uniform(2.0, 4.0))
                    self._random_mouse_movements(driver)
                except:
                    pass

            # --- PASO 6: Extraer cookies ---
            cookies = driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            elapsed = round(time.time() - start, 2)
            user_agent_used = driver.execute_script("return navigator.userAgent")

            result = GeneratedCookie(
                cookie_string=cookie_str,
                email=email,
                password=password,
                user_agent=user_agent_used,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                time_elapsed=elapsed,
            )

            logger.info(f"🍪 Cookie generada en {elapsed}s | Longitud: {len(cookie_str)} chars")
            return True, result, None

        except TimeoutException:
            return False, None, "Timeout: Amazon no respondió a tiempo (posible bloqueo)"
        except WebDriverException as e:
            return False, None, f"Error del navegador: {str(e)[:80]}"
        except Exception as e:
            logger.error(f"Error inesperado: {e}", exc_info=True)
            return False, None, f"Error interno: {str(e)[:80]}"
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
