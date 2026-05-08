#!/usr/bin/env python3
"""
🤖 Amazon Cookie Generator - Telegram Bot
🍪 Genera cookies de sesión de Amazon desde Telegram
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from cookie_generator import CookieGenerator

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
MAX_DAILY = int(os.getenv("MAX_DAILY_GENERATIONS", "10"))

# Estados de conversación
(WAIT_EMAIL, WAIT_PASSWORD, WAIT_CONFIRM) = range(3)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("TelegramBot")

# Rate limiting simple
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

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍪 Generar Cookie", callback_data="generate")],
        [
            InlineKeyboardButton("📊 Mi Uso Hoy", callback_data="stats"),
            InlineKeyboardButton("ℹ️ Ayuda", callback_data="help"),
        ],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Volver", callback_data="back")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    remaining = rate_limiter.remaining(user.id)
    mensaje = f"""
<b>🍪 Amazon Cookie Generator</b>
<i>Elite Edition • Bot Oficial</i>

👋 ¡Hola {user.first_name}!

Con este bot puedes generar cookies de sesión 
de Amazon automáticamente.

📊 <b>Tus estadísticas:</b>
• Generaciones hoy: {MAX_DAILY - remaining}/{MAX_DAILY}
• Disponibles: {remaining}

⚠️ <i>Usa responsablemente. Solo cuentas propias.</i>

Selecciona una opción:
"""
    await update.message.reply_text(mensaje, parse_mode="HTML", reply_markup=main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if query.data == "generate":
        remaining = rate_limiter.remaining(user.id)
        if remaining <= 0:
            await query.edit_message_text(
                "❌ <b>Límite diario alcanzado</b>\n\n"
                f"Has usado tus {MAX_DAILY} generaciones de hoy.\n"
                "Vuelve mañana o contacta a un admin.",
                parse_mode="HTML",
                reply_markup=back_keyboard()
            )
            return ConversationHandler.END
        
        await query.edit_message_text(
            "📧 <b>Paso 1/2: Email</b>\n\n"
            "Envía el email para crear la cuenta:\n"
            "<i>Ejemplo: micorreo@gmail.com</i>\n\n"
            "✖️ /cancel para cancelar",
            parse_mode="HTML"
        )
        return WAIT_EMAIL
    
    elif query.data == "stats":
        remaining = rate_limiter.remaining(user.id)
        await query.edit_message_text(
            f"📊 <b>Tus estadísticas</b>\n\n"
            f"👤 Usuario: <code>{user.id}</code>\n"
            f"🍪 Generaciones hoy: {MAX_DAILY - remaining}/{MAX_DAILY}\n"
            f"🟢 Disponibles: {remaining}\n"
            f"⏰ Límite se reinicia: Medianoche UTC",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
        return ConversationHandler.END
    
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ <b>Ayuda del Bot</b>\n\n"
            "<b>¿Cómo funciona?</b>\n"
            "1. Pulsa 'Generar Cookie'\n"
            "2. Envía un email y contraseña\n"
            "3. El bot crea la cuenta en Amazon\n"
            "4. Recibes la cookie de sesión\n\n"
            "<b>⚠️ Importante:</b>\n"
            "• Usa solo cuentas propias\n"
            "• Límite: 10 cookies/día\n"
            "• Tiempo aprox: 30-60 segundos\n\n"
            "<b>📝 Comandos:</b>\n"
            "/start - Menú principal\n"
            "/stats - Ver estadísticas\n"
            "/help - Esta ayuda\n"
            "/cancel - Cancelar operación",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
        return ConversationHandler.END
    
    elif query.data == "admin":
        if user.id not in ADMIN_IDS:
            await query.edit_message_text("🔒 Panel de administración restringido.", reply_markup=back_keyboard())
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("📊 Estadísticas globales", callback_data="admin_global")],
            [InlineKeyboardButton("🔙 Volver", callback_data="back")],
        ]
        await query.edit_message_text(
            "👑 <b>Panel de Administración</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    elif query.data == "admin_global" and user.id in ADMIN_IDS:
        total_users = len(rate_limiter.users)
        total_generations = sum(len(v) for v in rate_limiter.users.values())
        await query.edit_message_text(
            f"📊 <b>Estadísticas Globales</b>\n\n"
            f"👥 Usuarios activos hoy: {total_users}\n"
            f"🍪 Total generaciones hoy: {total_generations}\n"
            f"📐 Límite por usuario: {MAX_DAILY}/día",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
        return ConversationHandler.END
    
    elif query.data == "back":
        await query.edit_message_text(
            "🍪 <b>Menú Principal</b>\nSelecciona una opción:",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END

async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if '@' not in email or '.' not in email:
        await update.message.reply_text("❌ Email inválido. Intenta de nuevo o /cancel", parse_mode="HTML")
        return WAIT_EMAIL
    
    context.user_data['email'] = email
    await update.message.reply_text(
        f"📧 Email: <code>{email}</code>\n\n"
        "🔑 <b>Paso 2/2: Contraseña</b>\n\n"
        "Envía la contraseña (mínimo 6 caracteres):\n"
        "<i>No uses contraseñas reales importantes</i>\n\n"
        "✖️ /cancel para cancelar",
        parse_mode="HTML"
    )
    return WAIT_PASSWORD

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    if len(password) < 6:
        await update.message.reply_text("❌ Contraseña muy corta. Intenta de nuevo o /cancel", parse_mode="HTML")
        return WAIT_PASSWORD
    
    email = context.user_data.get('email', '')
    context.user_data['password'] = password
    await update.message.reply_text(
        "📋 <b>Confirma los datos:</b>\n\n"
        f"📧 Email: <code>{email}</code>\n"
        f"🔑 Password: <code>{'*' * len(password)}</code>\n\n"
        "¿Proceder con la generación?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Sí, generar", callback_data="confirm_yes"),
             InlineKeyboardButton("❌ Cancelar", callback_data="confirm_no")]
        ])
    )
    return WAIT_CONFIRM

async def confirm_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_no":
        context.user_data.clear()
        await query.edit_message_text("❌ Generación cancelada.", reply_markup=main_keyboard())
        return ConversationHandler.END
    
    user = query.from_user
    email = context.user_data.get('email', '')
    password = context.user_data.get('password', '')
    
    if not rate_limiter.is_allowed(user.id):
        await query.edit_message_text("❌ Límite diario alcanzado.", reply_markup=main_keyboard())
        return ConversationHandler.END
    
    await query.edit_message_text(
        "🔄 <b>Generando cookie...</b>\n\n"
        f"📧 {email}\n"
        "⏳ Esto puede tardar 30-60 segundos\n"
        "<i>El bot está creando la cuenta en Amazon...</i>",
        parse_mode="HTML"
    )
    
    success, result, error = generator.generate(email, password)
    
    if not success:
        await query.edit_message_text(
            f"❌ <b>Error al generar cookie</b>\n\n"
            f"📧 {email}\n"
            f"🔴 Error: {error}\n\n"
            "Posibles causas:\n"
            "• Amazon detectó automatización\n"
            "• CAPTCHA requerido\n"
            "• Email ya registrado\n\n"
            "Intenta con otro email.",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    cookie_preview = result.cookie_string[:500] + "..." if len(result.cookie_string) > 500 else result.cookie_string
    response = f"""
<b>🍪 ¡Cookie Generada Exitosamente!</b>

👤 <b>Email:</b> <code>{result.email}</code>
🔑 <b>Password:</b> <code>{result.password}</code>
🇺🇸 <b>Sitio:</b> Amazon.com
⏱ <b>Tiempo:</b> {result.time_elapsed}s
📅 <b>Fecha:</b> {result.timestamp}

<b>🍪 Cookie:</b>
<pre><code class="language-text">{cookie_preview}</code></pre>

📊 Te quedan {rate_limiter.remaining(user.id)} generaciones hoy.
"""
    if len(result.cookie_string) > 3000:
        await query.edit_message_text(
            f"🍪 <b>¡Cookie Generada!</b>\n\n👤 {result.email}\n⏱ {result.time_elapsed}s\n\n"
            "📎 <i>La cookie es muy larga, se envía como archivo...</i>",
            parse_mode="HTML"
        )
        cookie_file = f"cookie_{result.email.replace('@', '_')}.txt"
        with open(cookie_file, 'w') as f:
            f.write(f"Cookie generada para: {result.email}\n")
            f.write(f"Password: {result.password}\n")
            f.write(f"Fecha: {result.timestamp}\n")
            f.write(f"Tiempo: {result.time_elapsed}s\n")
            f.write("=" * 50 + "\n")
            f.write(result.cookie_string)
        with open(cookie_file, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=f"amazon_cookie_{result.email.split('@')[0]}.txt",
                caption="🍪 Cookie de sesión de Amazon"
            )
        os.remove(cookie_file)
        await query.message.reply_text("✅ Usa /start para volver al menú", reply_markup=main_keyboard())
    else:
        await query.edit_message_text(response, parse_mode="HTML", reply_markup=main_keyboard())
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operación cancelada.\nUsa /start para comenzar.", reply_markup=main_keyboard())
    return ConversationHandler.END

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    remaining = rate_limiter.remaining(user.id)
    await update.message.reply_text(
        f"📊 <b>Tus estadísticas</b>\n\n"
        f"🍪 Generaciones hoy: {MAX_DAILY - remaining}/{MAX_DAILY}\n"
        f"🟢 Disponibles: {remaining}",
        parse_mode="HTML"
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("🔒 No tienes acceso al panel admin.")
        return
    total_users = len(rate_limiter.users)
    total_gens = sum(len(v) for v in rate_limiter.users.values())
    await update.message.reply_text(
        f"👑 <b>Panel Admin</b>\n\n"
        f"👥 Usuarios activos hoy: {total_users}\n"
        f"🍪 Generaciones hoy: {total_gens}\n"
        f"📐 Límite: {MAX_DAILY}/día/usuario",
        parse_mode="HTML"
    )

def main():
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN no configurado")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^generate$")],
        states={
            WAIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            WAIT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            WAIT_CONFIRM: [CallbackQueryHandler(confirm_generation, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(stats|help|admin|back|admin_global)$"))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("cancel", cancel))
    
    logger.info("🤖 Bot iniciado...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
