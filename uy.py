import os
import asyncio
import threading
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TOKEN = os.getenv("TOKEN")
URL = "https://absen.zatest11.my.id"

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
    return webdriver.Chrome(service=service, options=options)

def run_absen(nim: str):
    try:
        if not is_site_up(URL):
            return "❌ Website absen lagi DOWN."

        driver = create_driver()
        wait = WebDriverWait(driver, 15)

        driver.get(URL)

        try:
            input_nim = wait.until(EC.presence_of_element_located((By.NAME, "nim")))
        except:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            input_nim = inputs[0] if inputs else None

        if not input_nim:
            return "❌ Input NIM tidak ditemukan"

        input_nim.clear()
        input_nim.send_keys(nim)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        clicked = False
        for b in buttons:
            if "login" in b.text.lower() or "masuk" in b.text.lower():
                b.click()
                clicked = True
                break
        if not clicked and buttons:
            buttons[0].click()

        wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "button")))

        buttons = driver.find_elements(By.TAG_NAME, "button")

        hasil = "📊 Hasil Absen:\n\n"
        count = 0

        for btn in buttons:
            text = btn.text.lower()

            if "absen" in text or "hadir" in text:
                count += 1

                try:

                    parent = btn.find_element(By.XPATH, "..")
                    nama = parent.text.split("\n")[0]
                except:
                    nama = f"Matkul {count}"

                try:
                    btn.click()
                    hasil += f"✅ {nama}\n↳ Absen berhasil\n\n"
                except:
                    hasil += f"⚠️ {nama}\n↳ Gagal klik\n\n"

        if count == 0:
            hasil += "⚠️ Tidak ada tombol absen ditemukan (mungkin belum dibuka)"

        driver.quit()
        return hasil.strip()

    except Exception as e:
        return f"❌ Error:\n{str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot siap!\nGunakan /absen NIM")

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions[update.effective_user.id] = False
    await update.message.reply_text("🔄 Reset selesai")

async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if user_sessions.get(uid):
        await update.message.reply_text("⚠️ Masih jalan, tunggu /end dulu")
        return

    if not context.args:
        await update.message.reply_text("Gunakan: /absen NIM")
        return

    nim = context.args[0]
    user_sessions[uid] = True

    await update.message.reply_text("⏳ Proses...")

    def worker():
        result = run_absen(nim)
        asyncio.run(update.message.reply_text(result))
        user_sessions[uid] = False

    threading.Thread(target=worker).start()

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("absen", absen))
    app.add_handler(CommandHandler("end", end))

    print("BOT JALAN 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
