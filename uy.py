from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import threading
import asyncio
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN belum diset di Railway")

user_sessions = {}

# ======================
# DRIVER (HEADLESS VPS)
# ======================
def create_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    return driver

# ======================
# UTIL
# ======================
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


def ambil_nama_matkul(card, index):
    try:
        text = card.text.split("\n")
        for t in text:
            t = t.strip()
            if t and "abs
