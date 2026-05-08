#!/usr/bin/env python3
"""
🤖 Amazon Cookie Generator - Telegram Bot (Elite Edition)
🍪 Genera cookies de sesión de un solo clic
"""

import os
import secrets
import string
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from cookie_generator import CookieGenerator

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Reemplaza esto con tu ID de Telegram si no usas .env
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip() != "0"]
MAX_DAILY = int(os.getenv("MAX_DAILY_GENERATIONS", "10"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("TelegramBot")

# Generador de contraseñas seguras al azar
def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

class RateLimiter:
    def __init__(self, max_per_day: int):
        self.max_per_day = max_per_day
        self.users = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        now = datetime.now()
        self.users[user_id] = [t for t in self.users[user_id] if now - t < timedelta(days=1)]
        if len(self.users[user_id]) >= self.max_per_day:
            return False
        self.users[user_id].append(now)
        return True
    
    def remaining(self, user_id: int) -> int:
        now = datetime.now()
        self.users[user_id] = [t for t in self.users[user_id] if now - t < timedelta(days=1)]
        return max(0, self.max_per_day - len(self.users[user_id]))

rate_limiter = RateLimiter(MAX_DAILY)
generator = CookieGenerator()

# --- TECLADOS ---
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 GENERAR COOKIE (Auto)", callback_data="fast_gen")],
        [
            InlineKeyboardButton("📊 Mi Uso", callback_data="stats"),
            InlineKeyboardButton("ℹ️ Info", callback_data="help"),
        ]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back")]])

# --- MANEJADORES ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    remaining = rate_limiter.remaining(user.id)
    mensaje = f"""
<b>🍪 Amazon Cookie Generator</b>
<i>Versión "Kevin Preso" • San Miguel Ed.</i> 🇸🇻

👋 ¡Qué onda, {user.first_name}!

Ya no tenés que escribir nada. Solo dale al botón de abajo y el bot usará tu Gmail configurado para crear la cuenta y darte la cookie automáticamente.

📊 <b>Disponibles hoy:</b> <code>{remaining}</code>
"""
    await update.message.reply_text(mensaje, parse_mode="HTML", reply_markup=main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if query.data == "fast_gen":
        remaining = rate_limiter.remaining(user.id)
        if remaining <= 0:
            await query.edit_message_text("❌ <b>Límite alcanzado.</b> Vuelve mañana, chele.", parse_mode="HTML", reply_markup=back_keyboard())
            return

        # Generar password al azar para la nueva cuenta
        random_pass = generate_random_password()
        
        await query.edit_message_text(
            "🔄 <b>GENERANDO COOKIE...</b>\n\n"
            "🕵️ <i>Usando alias de Gmail sigiloso...</i>\n"
            "🔑 <i>Password inventado:</i> <code>" + random_pass + "</code>\n"
            "⏳ Esperá unos 40-60 segundos, estoy leyendo el OTP...",
            parse_mode="HTML"
        )

        # LLAMADA AL GENERADOR VERGÓN
        # Le pasamos cualquier cosa como email porque el CookieGenerator ya usa el de "Kevin Preso" internamente
        success, result, error = generator.generate("base@gmail.com", random_pass)

        if not success:
            await query.edit_message_text(
                f"💥 <b>Error en la misión</b>\n\n🔴 <code>{error}</code>\n\n"
                "Probá de nuevo en un ratito o revisá los logs de tu compu.",
                parse_mode="HTML",
                reply_markup=back_keyboard()
            )
            return

        # Si todo salió bien
        response = f"""
<b>✅ ¡COOKIE GENERADA!</b>

📧 <b>Email usado:</b> <code>{result.email}</code>
🔑 <b>Password:</b> <code>{result.password}</code>
⏱ <b>Tiempo:</b> <code>{result.time_elapsed}s</code>

<b>🍪 Cookie (Copiá y pegá):</b>
<pre><code class="language-text">{result.cookie_string}</code></pre>

📊 Te quedan {rate_limiter.remaining(user.id)} intentos hoy.
"""
        # Si la cookie es muy larga, mandarla como archivo
        if len(result.cookie_string) > 3500:
            filename = f"cookie_{result.email.split('@')[0]}.txt"
            with open(filename, "w") as f: f.write(result.cookie_string)
            await query.message.reply_document(document=open(filename, "rb"), caption="🍪 Cookie larga detectada.")
            os.remove(filename)
            await query.message.reply_text("✅ Listo. ¿Querés otra?", reply_markup=main_keyboard())
        else:
            await query.edit_message_text(response, parse_mode="HTML", reply_markup=main_keyboard())

    elif query.data == "stats":
        remaining = rate_limiter.remaining(user.id)
        await query.edit_message_text(
            f"📊 <b>Estado de tu cuenta</b>\n\n"
            f"👤 ID: <code>{user.id}</code>\n"
            f"🟢 Disponibles hoy: <b>{remaining}</b>\n"
            f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}",
            parse_mode="HTML", reply_markup=back_keyboard()
        )

    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ <b>¿Cómo se usa esta onda?</b>\n\n"
            "1. Dale a <b>Generar Cookie</b>.\n"
            "2. El bot usa tu Gmail base y le mete puntos al azar.\n"
            "3. Entra a Amazon, crea la cuenta.\n"
            "4. Si pide código, el bot lo lee de tu Gmail solo.\n"
            "5. Te manda la cookie lista.\n\n"
            "¡Fácil y rápido!", parse_mode="HTML", reply_markup=back_keyboard()
        )

    elif query.data == "back":
        await start(update, context)

def main():
    if not TOKEN:
        print("❌ Error: No hay TOKEN de Telegram.")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Bot local encendido y listo.")
    app.run_polling()

if __name__ == "__main__":
    main()
