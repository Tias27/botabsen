import os
import asyncio
import time

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

# ================= DRIVER =================
def create_driver():
    options = Options()
    options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")

    # ================= options.add_argument("--headless=new") =================
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))

    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


# ================= LOGIC =================
def run_absen(nim: str):
    try:
        driver = create_driver()
        wait = WebDriverWait(driver, 15)

        driver.get(URL)
        time.sleep(5)

        if "cloudflare" in driver.page_source.lower():
            driver.quit()
            return "⚠️ Kena Cloudflare, coba lagi"

        # input nim
        try:
            input_nim = wait.until(
                EC.presence_of_element_located((By.NAME, "nim"))
            )
        except:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            input_nim = inputs[0] if inputs else None

        if not input_nim:
            driver.quit()
            return "❌ Input NIM tidak ditemukan"

        input_nim.send_keys(nim)

        # klik login
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for b in buttons:
            if "login" in b.text.lower():
                b.click()
                break

        time.sleep(5)

        buttons = driver.find_elements(By.TAG_NAME, "button")

        hasil = "📊 Hasil Absen:\n\n"
        count = 0

        for btn in buttons:
            if "absen" in btn.text.lower():
                count += 1
                try:
                    btn.click()
                    hasil += f"✅ Matkul {count}\n"
                except:
                    hasil += f"⚠️ Matkul {count} gagal\n"

        if count == 0:
            hasil += "⚠️ Tidak ada absen"

        driver.quit()
        return hasil

    except Exception as e:
        return f"❌ Error:\n{str(e)}"


# ================= COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot siap! Gunakan /absen NIM")


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions[update.effective_user.id] = False
    await update.message.reply_text("🔄 Reset selesai")


async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if user_sessions.get(uid):
        await update.message.reply_text("⚠️ Masih proses, pakai /end dulu")
        return

    if not context.args:
        await update.message.reply_text("Gunakan: /absen NIM")
        return

    nim = context.args[0]
    user_sessions[uid] = True

    await update.message.reply_text("⏳ Proses...")

    # 🔥 jalanin blocking selenium di thread aman
    result = await asyncio.to_thread(run_absen, nim)

    await update.message.reply_text(result)

    user_sessions[uid] = False


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("absen", absen))
    app.add_handler(CommandHandler("end", end))

    print("BOT JALAN 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
