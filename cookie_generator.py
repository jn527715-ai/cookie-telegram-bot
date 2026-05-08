#!/usr/bin/env python3
"""
Motor de generación de cookies de Amazon - Versión CECOT
Configurado con Truco de Puntos y Lector de OTP automático
"""

import os
import time
import random
import logging
import subprocess
import imaplib
import email
import re
from datetime import datetime
from typing import Tuple
from dataclasses import dataclass
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    AMAZON_REGISTER_URL = "https://www.amazon.com/ap/register"
    AMAZON_HOME = "https://www.amazon.com"
    TIMEOUT = 30

    def __init__(self):
        self.user_data_dir = "/tmp/chrome_profile"
        
        # --- CONFIGURACIÓN DE TU CUENTA GMAIL ---
        self.GMAIL_USER = "chancucakevinpresocecotelsalva@gmail.com" 
        self.GMAIL_PASS = "fqph zfzn fotq rilz" # Tu contraseña de aplicación
        # ----------------------------------------
        
        self._setup_env()

    def _setup_env(self):
        """Busca el ejecutable de Chrome en el sistema"""
        posibles = ['/usr/bin/google-chrome-stable', '/usr/bin/google-chrome', 'C:/Program Files/Google/Chrome/Application/chrome.exe']
        for browser in posibles:
            if os.path.exists(browser):
                os.environ['CHROME_BIN'] = browser
                logger.info(f"✅ Navegador encontrado: {browser}")
                return
        os.environ['CHROME_BIN'] = '/usr/bin/google-chrome-stable'

    def _generate_dot_alias(self, base_email: str) -> str:
        """Genera variaciones de Gmail usando el truco de los puntos"""
        if "@gmail.com" not in base_email.lower(): return base_email
        username, domain = base_email.split('@')
        alias = username[0]
        for char in username[1:]:
            # 60% de probabilidad de poner un punto entre letras
            if random.random() > 0.6 and alias[-1] != '.':
                alias += '.'
            alias += char
        return f"{alias}@{domain}"

    def _get_amazon_otp(self) -> str:
        """Se conecta a Gmail y extrae el código OTP de 6 dígitos enviado por Amazon"""
        logger.info("📩 Entrando a Gmail para leer el código de Amazon...")
        try:
            # Reintentar durante 60 segundos (Amazon a veces tarda en enviar el correo)
            for _ in range(10):
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(self.GMAIL_USER, self.GMAIL_PASS)
                mail.select("inbox")
                
                # Buscar correos no leídos de Amazon (del remitente oficial de cuentas)
                status, data = mail.search(None, '(UNSEEN FROM "account-update@amazon.com")')
                mail_ids = data[0].split()
                
                if mail_ids:
                    latest_id = mail_ids[-1]
                    status, data = mail.fetch(latest_id, '(RFC822)')
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extraer el cuerpo del mensaje
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = str(part.get_payload(decode=True))
                    else:
                        body = str(msg.get_payload(decode=True))
                    
                    # Buscar patrón de 6 números (el código de Amazon)
                    otp_match = re.search(r'\b\d{6}\b', body)
                    if otp_match:
                        otp = otp_match.group(0)
                        logger.info(f"🔑 ¡Código OTP robado con éxito! -> {otp}")
                        mail.logout()
                        return otp
                
                mail.logout()
                time.sleep(6)
            return None
        except Exception as e:
            logger.error(f"❌ Error crítico leyendo Gmail: {e}")
            return None

    def _get_chrome_main_version(self, binary_path):
        """Detecta la versión de Chrome instalada"""
        try:
            version_str = subprocess.check_output([binary_path, '--version']).decode('utf-8').strip()
            return int(version_str.split(' ')[-1].split('.')[0])
        except: return None

    def _build_driver(self) -> uc.Chrome:
        """Configura el navegador con sigilo máximo"""
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        options = uc.ChromeOptions()
        options.page_load_strategy = 'eager'
        
        # Modo invisible nativo
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-zygote")
        options.add_argument("--log-level=3")
        
        chrome_bin = os.environ.get('CHROME_BIN')
        v_main = self._get_chrome_main_version(chrome_bin)
        
        driver = uc.Chrome(options=options, browser_executable_path=chrome_bin, version_main=v_main)
        
        # Camuflaje Stealth
        stealth(driver, 
                languages=["en-US", "en"], 
                vendor="Google Inc.", 
                platform="Win32", 
                webgl_vendor="Intel Inc.", 
                renderer="Intel Iris OpenGL Engine", 
                fix_hairline=True)
        
        return driver

    def generate(self, base_email: str, password: str, name: str = None) -> Tuple[bool, any, str]:
        driver = None
        start = time.time()
        
        # SIEMPRE usamos tu correo base mutado para que todo caiga a tu bandeja
        target_email = self._generate_dot_alias(self.GMAIL_USER)
        
        if not name:
            name = f"{random.choice(['John', 'Emma', 'David', 'Sophia'])} {random.choice(['Smith', 'Brown', 'Davis', 'Wilson'])}"

        try:
            logger.info(f"🚀 Iniciando operación para: {target_email}")
            driver = self._build_driver()
            driver.get(self.AMAZON_REGISTER_URL)
            
            # ⌨️ Paso 1: Llenar el formulario de Amazon
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "ap_customer_name"))).send_keys(name)
            driver.find_element(By.ID, "ap_email").send_keys(target_email)
            driver.find_element(By.ID, "ap_password").send_keys(password)
            driver.find_element(By.ID, "ap_password_check").send_keys(password)
            driver.find_element(By.ID, "continue").click()
            
            time.sleep(5)
            
            # 🕵️ Paso 2: Detectar si Amazon pide el código OTP
            if "verify" in driver.current_url or len(driver.find_elements(By.NAME, "code")) > 0:
                logger.info("⚠️ Amazon pide código de verificación. Activando lector de Gmail...")
                otp = self._get_amazon_otp()
                
                if otp:
                    # Pegar el código encontrado
                    code_field = driver.find_element(By.NAME, "code")
                    code_field.send_keys(otp)
                    try:
                        driver.find_element(By.ID, "cvf-submit-otp-button").click()
                    except:
                        # Si el ID del botón es diferente en algunas regiones
                        driver.find_element(By.CSS_SELECTOR, "input.a-button-input").click()
                    time.sleep(5)
                else:
                    return False, None, "No se halló el código OTP en Gmail (Tiempo agotado)"

            # 🏁 Paso 3: Validar éxito y extraer cookies
            if "ap/register" in driver.current_url:
                return False, None, "Bloqueo de Amazon (Captcha o IP sospechosa)"
                
            cookies = driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            logger.info("✅ ¡Cookie generada exitosamente!")
            return True, GeneratedCookie(
                cookie_string=cookie_str, email=target_email, password=password,
                user_agent=driver.execute_script("return navigator.userAgent"),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                time_elapsed=round(time.time() - start, 2)
            ), None
            
        except TimeoutException:
            return False, None, "Error: La página de Amazon tardó demasiado en cargar"
        except Exception as e:
            return False, None, f"Error inesperado: {str(e)[:100]}"
        finally:
            if driver:
                driver.quit()
