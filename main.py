import json
import logging
from datetime import datetime
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN, CLAUDE_API_KEY, CLAUDE_API_URL, DEFAULT_MODE
from pdf_generator import text_to_pdf

logging.basicConfig(level=logging.INFO)
user_modes = {}

def is_paid_user(user_id):
    try:
        with open("paid_users.json", "r") as f:
            paid = json.load(f)
            return str(user_id) in paid
    except:
        return False

def load_data():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f)

def can_use_bot(user_id):
    data = load_data()
    now = datetime.now()
    if str(user_id) not in data:
        data[str(user_id)] = {"count": 1, "last": now.isoformat()}
    else:
        last = datetime.fromisoformat(data[str(user_id)]["last"])
        if (now - last).days >= 7:
            data[str(user_id)] = {"count": 1, "last": now.isoformat()}
        elif data[str(user_id)]["count"] < 10:
            data[str(user_id)]["count"] += 1
        else:
            save_data(data)
            return False
    save_data(data)
    return True

def set_user_mode(user_id, mode):
    user_modes[user_id] = mode

def get_user_mode(user_id):
    return user_modes.get(user_id, DEFAULT_MODE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام! من ربات هوش مصنوعی برنامه‌نویسی هستم.\n\n"
        "✅ تا ۱۰ بار در هفته رایگان استفاده کن.\n"
        "💳 برای دسترسی نامحدود، ۱۰۰ هزار تومان به کارت زیر واریز کن:\n"
        "`6219 8619 6313 6964` (محمد قدیانی)\n"
        "و رسید پرداخت رو بفرست تا فعال بشی.\n\n"
        "🔧 با دستور زیر حالت استفاده رو مشخص کن:\n"
        "/mode fix - بررسی و اصلاح کد\n"
        "/mode generate - ساخت کد از توضیح\n\n"
        "حالا کدت رو بفرست! 📤"
    )

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = update.message.from_user.id
    if not args:
        await update.message.reply_text("🔧 لطفاً یکی از حالت‌ها رو انتخاب کن:\n/mode fix - اصلاح\n/mode generate - ساخت")
        return
    mode = args[0].lower()
    if mode not in ["fix", "generate"]:
        await update.message.reply_text("❌ فقط fix یا generate مجازه.")
        return
    set_user_mode(user_id, mode)
    await update.message.reply_text(f"✅ حالت شما تنظیم شد به: {mode.upper()}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_input = update.message.text

    if not is_paid_user(user_id):
        if not can_use_bot(user_id):
            await update.message.reply_text(
                "📛 سقف استفاده رایگان شما تموم شده.\n\n"
                "💳 لطفاً ۱۰۰ هزار تومان به شماره کارت زیر واریز کن:\n"
                "`6219 8619 6313 6964` (محمد قدیانی)\n"
                "و رسید پرداخت رو برای تأیید ارسال کن."
            )
            return

    mode = get_user_mode(user_id)
    if mode == "fix":
        prompt = f"""کد زیر را بررسی کن و اگر خطایی داشت بگو:\n\n{user_input}\n\nپاسخ را با توضیح فارسی بده و سپس همان را به انگلیسی هم بنویس."""
    else:
        prompt = f"""طبق توضیح زیر یک برنامه کامل بنویس:\n\n{user_input}\n\nپاسخ را با توضیح فارسی بده و سپس همان را به انگلیسی هم بنویس."""

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(CLAUDE_API_URL, headers=headers, json=data)
    reply = response.json().get("content")[0]["text"]

    pdf_file = text_to_pdf(reply)
    await update.message.reply_document(document=open(pdf_file, "rb"), filename="response.pdf")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
