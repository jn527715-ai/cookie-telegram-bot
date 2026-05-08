#!/usr/bin/env python3
"""
Motor de generación de cookies de Amazon - Edición "Kevin Preso" 🇸🇻
Totalmente automatizado: Bypass de detección, Dot Trick y Lector de OTP.
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
from selenium.common.exceptions import TimeoutException, WebDriverException
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
    TIMEOUT = 40

    def __init__(self):
        self.user_data_dir = "/tmp/chrome_profile"
        
        # --- TUS DATOS CONFIGURADOS ---
        self.GMAIL_USER = "chancucakevinpresocecotelsalva@gmail.com" 
        self.GMAIL_PASS = "voll gdwi kevv ohbm" 
        # -----------------------------
        
        self._setup_env()

    def _setup_env(self):
        """Detecta el navegador en el sistema"""
        posibles = ['/usr/bin/google-chrome-stable', '/usr/bin/google-chrome']
        for browser in posibles:
            if os.path.exists(browser):
                os.environ['CHROME_BIN'] = browser
                return
        os.environ['CHROME_BIN'] = '/usr/bin/google-chrome-stable'

    def _generate_dot_alias(self, base_email: str) -> str:
        """Aplica el truco de los puntos para crear infinitas cuentas"""
        username, domain = base_email.split('@')
        # Si el username es corto, no hacemos mucho, pero el tuyo es largo así que perfecto
        chars = list(username)
        for i in range(1, len(chars) * 2, 2):
            if random.random() > 0.5:
                chars.insert(i, '.')
        # Limpiar puntos dobles o finales que Amazon rechaza
        res = "".join(chars).replace("..", ".").strip(".")
        return f"{res}@{domain}"

    def _get_amazon_otp(self) -> str:
        """Se conecta a tu Gmail y roba el código de 6 dígitos de Amazon"""
        logger.info("📩 Entrando a Gmail para buscar el código OTP...")
        try:
            # Esperamos un poco a que el correo llegue físicamente a los servidores de Google
            time.sleep(5)
            for intento in range(10):
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(self.GMAIL_USER, self.GMAIL_PASS)
                mail.select("inbox")
                
                # Buscamos correos de Amazon que no hayamos leído
                status, data = mail.search(None, '(UNSEEN FROM "account-update@amazon.com")')
                mail_ids = data[0].split()
                
                if mail_ids:
                    latest_id = mail_ids[-1]
                    status, data = mail.fetch(latest_id, '(RFC822)')
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extraer el texto del cuerpo del correo
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                    else:
                        body = msg.get_payload(decode=True).decode()
                    
                    # Buscar el patrón de 6 números (OTP)
                    otp_match = re.search(r'\b\d{6}\b', body)
                    if otp_match:
                        otp = otp_match.group(0)
                        logger.info(f"🔑 ¡Código encontrado!: {otp}")
                        mail.logout()
                        return otp
                
                mail.logout()
                logger.info(f"⏳ Intento {intento+1}: Correo no ha llegado aún, esperando...")
                time.sleep(6)
            return None
        except Exception as e:
            logger.error(f"❌ Error en el módulo de Gmail: {e}")
            return None

    def _build_driver(self) -> uc.Chrome:
        """Configura el navegador con sigilo máximo"""
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        options = uc.ChromeOptions()
        
        # Carga rápida (no espera a que carguen imágenes/publicidad)
        options.page_load_strategy = 'eager'
        
        # Modo oculto de nueva generación
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-zygote")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        chrome_bin = os.environ.get('CHROME_BIN')
        
        driver = uc.Chrome(options=options, browser_executable_path=chrome_bin)
        
        # Camuflaje para que Amazon no sepa que es un bot
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        return driver

    def generate(self, base_email: str, password: str, name: str = None) -> Tuple[bool, any, str]:
        driver = None
        start_time = time.time()
        
        # Generamos el alias con puntos
        target_email = self._generate_dot_alias(self.GMAIL_USER)
        
        if not name:
            name = f"User {random.randint(1000, 9999)}"

        try:
            logger.info(f"🚀 Iniciando misión: Crear cuenta para {target_email}")
            driver = self._build_driver()
            
            # 1. Abrir página de registro
            driver.get(self.AMAZON_REGISTER_URL)
            
            # 2. Llenar el formulario
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "ap_customer_name"))).send_keys(name)
            driver.find_element(By.ID, "ap_email").send_keys(target_email)
            driver.find_element(By.ID, "ap_password").send_keys(password)
            driver.find_element(By.ID, "ap_password_check").send_keys(password)
            
            time.sleep(1)
            driver.find_element(By.ID, "continue").click()
            logger.info("📡 Formulario enviado, esperando respuesta de Amazon...")
            
            time.sleep(5)
            
            # 3. ¿Pidió código OTP?
            if "verify" in driver.current_url or len(driver.find_elements(By.NAME, "code")) > 0:
                logger.warning("⚠️ Amazon pidió verificación. Consultando a 'Kevin Preso'...")
                otp = self._get_amazon_otp()
                
                if otp:
                    input_otp = driver.find_element(By.NAME, "code")
                    input_otp.send_keys(otp)
                    time.sleep(1)
                    # Intentar dar clic al botón de enviar OTP
                    for btn_id in ["cvf-submit-otp-button", "continue"]:
                        try:
                            driver.find_element(By.ID, btn_id).click()
                            break
                        except: continue
                    time.sleep(6)
                else:
                    return False, None, "No se encontró el OTP en Gmail (revisa si llegó el correo)"

            # 4. Finalizar y extraer cookies
            if "ap/register" in driver.current_url:
                return False, None, "Bloqueado por Amazon (Captcha o IP sospechosa)"
                
            logger.info("✅ ¡Cuenta creada con éxito! Extrayendo tesoro (cookies)...")
            cookies = driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            return True, GeneratedCookie(
                cookie_string=cookie_str,
                email=target_email,
                password=password,
                user_agent=driver.execute_script("return navigator.userAgent"),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                time_elapsed=round(time.time() - start_time, 2)
            ), None
            
        except Exception as e:
            logger.error(f"💥 Error durante la generación: {e}")
            return False, None, str(e)[:100]
        finally:
            if driver:
                driver.quit()
