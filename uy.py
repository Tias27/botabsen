import os
import asyncio
import threading
import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


TOKEN = os.getenv("TOKEN")
TARGET_URL = "https://absen.zatest11.my.id"  # ganti kalau perlu

user_sessions = {}


def is_site_up(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except:
        return False



def create_driver():
    options = Options()
    options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    service = Service(os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))

    driver = webdriver.Chrome(service=service, options=options)
    return driver



def run_absen(nim: str):
    try:
        # 🔥 cek dulu website hidup atau tidak
        if not is_site_up(TARGET_URL):
            return "❌ Website absen sedang DOWN / tidak bisa diakses."

        driver = create_driver()
        driver.get(TARGET_URL)

        # =======================
        # TODO: isi logic selenium lu di sini
        # =======================

        result = f"""
📊 Hasil Absen:

⏰ Matkul ke-1
↳ Sudah absen

⏰ Matkul ke-2
↳ Belum dibuka
"""

        driver.quit()
        return result.strip()

    except Exception as e:
        return f"❌ Error:\n{str(e)}"



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot siap!\n\nGunakan:\n/absen NIM\nContoh:\n/absen 1223150000"
    )


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = False
    await update.message.reply_text("🔄 Session di-reset. Silakan /absen lagi.")


async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_sessions.get(user_id):
        await update.message.reply_text("⚠️ Masih ada proses berjalan. Gunakan /end dulu.")
        return

    if not context.args:
        await update.message.reply_text("Gunakan: /absen NIM")
        return

    nim = context.args[0]

    user_sessions[user_id] = True

    await update.message.reply_text(f"⏳ Proses absen untuk NIM: {nim}")
    await update.message.reply_text("🚀 Lagi di absenin, sabar ya...")

    def worker():
        result = run_absen(nim)

        asyncio.run(send_result(update, result))

        user_sessions[user_id] = False

    threading.Thread(target=worker).start()


async def send_result(update: Update, text: str):
    await update.message.reply_text(text)



def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("absen", absen))
    app.add_handler(CommandHandler("end", end))

    print("BOT JALAN 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
