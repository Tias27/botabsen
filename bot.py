from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import threading
import asyncio
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ambil token dari Railway ENV
TOKEN = os.getenv("TOKEN")

user_sessions = {}



def create_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"
    
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    
options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
options.add_argument("--window-size=1920,1080")
    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    driver.set_page_load_timeout(30)

    return driver


# ================= POPUP =================
def klik_popup(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swal2-popup"))
        )

        popup = driver.find_element(By.CLASS_NAME, "swal2-popup")

        if "swal2-icon-success" in popup.get_attribute("class"):
            status = "success"
        elif "swal2-icon-error" in popup.get_attribute("class"):
            status = "error"
        else:
            status = "info"

        ok_btn = driver.find_element(By.XPATH, "//button[text()='OK']")
        driver.execute_script("arguments[0].click();", ok_btn)

        return status

    except:
        return None


# ================= AMBIL NAMA =================
def ambil_nama_matkul(card, index):
    try:
        text = card.text.split("\n")
        for t in text:
            t = t.strip()
            if t and "absen" not in t.lower() and "sks" not in t.lower():
                return t
        return f"Matkul ke-{index+1}"
    except:
        return f"Matkul ke-{index+1}"


# ================= MAIN ABSEN =================
def jalankan_absen_otomatis(nim_target, chat_id):
    driver = create_driver()

    try:
        driver.get("https://absen.zatest11.my.id/")

        input_nim = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "nim"))
        )
        input_nim.clear()
        input_nim.send_keys(nim_target)

        driver.find_element(By.XPATH, "//button[contains(text(),'Ambil Jadwal')]").click()

        klik_popup(driver)
        time.sleep(5)

        hasil = []
        index = 0

        while True:
            # ⛔ stop kalau user cancel
            if user_sessions.get(chat_id) != "running":
                break

            try:
                cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[.//button[contains(text(),'Absen')]]")
                    )
                )

                if index >= len(cards):
                    break

                card = cards[index]
                nama = ambil_nama_matkul(card, index)

                tombol = card.find_element(By.XPATH, ".//button[contains(text(),'Absen')]")

                driver.execute_script("arguments[0].scrollIntoView();", tombol)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", tombol)

                status = klik_popup(driver)

                if status == "success":
                    hasil.append(f"✅ {nama}\n   ↳ Absen berhasil")
                else:
                    hasil.append(f"⏰ {nama}\n   ↳ Belum dibuka / sudah absen")

                time.sleep(2)
                index += 1

            except:
                hasil.append(f"⚠️ Matkul ke-{index+1} error")
                index += 1

        return hasil

    finally:
        driver.quit()


# ================= TELEGRAM =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot siap!\n\nGunakan:\n/absen NIM\n\nContoh:\n/absen 1223150000"
    )


async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if user_sessions.get(chat_id) == "running":
        await update.message.reply_text(
            "⚠️ Masih proses sebelumnya bro...\nTunggu atau /end"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "❗ Format salah\nGunakan:\n/absen NIM"
        )
        return

    nim = context.args[0]
    user_sessions[chat_id] = "running"

    await update.message.reply_text(f"⏳ Proses absen untuk NIM: {nim}")
    await update.message.reply_text("🚀 Lagi di absenin sabar ya...")

    threading.Thread(
        target=run_absen,
        args=(chat_id, context.application, nim),
        daemon=True
    ).start()


def run_absen(chat_id, app, nim):
    try:
        hasil = jalankan_absen_otomatis(nim, chat_id)

        teks = "📊 *Hasil Absen:*\n\n" + "\n\n".join(hasil)

        asyncio.run(
            app.bot.send_message(
                chat_id=chat_id,
                text=teks,
                parse_mode="Markdown"
            )
        )

    except Exception as e:
        asyncio.run(
            app.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error:\n{str(e)}"
            )
        )

    finally:
        # 🔥 penting: reset session
        user_sessions.pop(chat_id, None)


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    user_sessions.pop(chat_id, None)

    await update.message.reply_text(
        "🔄 Session di-reset. Silakan /absen lagi."
    )


# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("absen", absen))
app.add_handler(CommandHandler("end", end))

print("BOT JALAN (HEADLESS - FIXED)...")
app.run_polling()
