from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8623275372:AAFDqWsowUMrdetfZhxBGzdVhc4OJIQM1Zs"

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

user_sessions = {}

def klik_popup():
    """Klik popup + ambil status icon"""
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


def jalankan_absen_otomatis(nim_target):
    driver.get("https://absen.zatest11.my.id/")

    input_nim = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "nim"))
    )
    input_nim.clear()
    input_nim.send_keys(nim_target)

    driver.find_element(By.XPATH, "//button[contains(text(),'Ambil Jadwal')]").click()

    klik_popup()
    time.sleep(5)

    hasil = []
    index = 0

    while True:
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

            status = klik_popup()
            if status == "success":
                hasil.append(f"✅ {nama}\n   ↳ Absen berhasil")
            else:
                hasil.append(f"⏰ {nama}\n   ↳ Absen belum dibuka / sudah absen")

            time.sleep(2)
            index += 1

        except Exception as e:
            hasil.append(f"⚠️ Matkul ke-{index+1} error")
            index += 1

    return hasil

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot siap!\n\nGunakan:\n/absen NIM\n\nContoh:\n/absen 1223150000"
    )


async def absen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if user_sessions.get(chat_id) == "running":
        await update.message.reply_text(
            "⚠️ Masih ada proses berjalan.\nGunakan /end dulu."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "❗ Format salah\nGunakan:\n/absen NIM\n\nContoh:\n/absen 1223150000"
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
    hasil = jalankan_absen_otomatis(nim)

    teks = "📊 *Hasil Absen:*\n\n" + "\n\n".join(hasil)

    asyncio.run(
        app.bot.send_message(
            chat_id=chat_id,
            text=teks,
            parse_mode="Markdown"
        )
    )

    user_sessions[chat_id] = "done"


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if user_sessions.get(chat_id) == "running":
        user_sessions[chat_id] = "stopped"
        await update.message.reply_text("🛑 Proses dihentikan.")
    else:
        await update.message.reply_text("ℹ️ Tidak ada proses berjalan.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("absen", absen))
app.add_handler(CommandHandler("end", end))

print("BOT JALAN...")
app.run_polling()
