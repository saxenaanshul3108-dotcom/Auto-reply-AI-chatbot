"""
WhatsApp AI Auto-Reply Bot
--------------------------
Uses Selenium to drive WhatsApp Web and Gemini API to generate replies.

Run:
    python whatsapp_bot.py

First run will open a Chrome window showing a QR code. Scan it with your
phone's WhatsApp (Settings > Linked Devices > Link a Device). After that,
your login session is saved locally, so you won't need to scan again.

NOTE: WhatsApp Web's page structure changes from time to time, which can
break the CSS/XPath selectors below. If the bot stops detecting messages,
the selectors in get_unread_chats / get_last_incoming_message / send_reply
are the first place to check and update.
"""

import time
import json
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    CHROME_PROFILE_DIR,
    POLL_INTERVAL_SECONDS,
    MAX_UNREAD_CHATS_PER_CYCLE,
    IGNORE_LIST,
)
from gemini_client import get_ai_reply

REPLIED_LOG_FILE = "replied_messages.json"


# ---------- persistence: avoid replying to the same message twice ----------

def load_replied_log():
    if os.path.exists(REPLIED_LOG_FILE):
        with open(REPLIED_LOG_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_replied_log(replied_set):
    with open(REPLIED_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(list(replied_set), f)


# ---------- browser setup ----------

def start_driver():
    options = webdriver.ChromeOptions()
    profile_path = Path(CHROME_PROFILE_DIR).resolve()
    profile_path.mkdir(parents=True, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")
    # Keep headless OFF for the very first run so you can scan the QR code.
    # Once logged in, you can uncomment the next line for a background bot.
    # options.add_argument("--headless=new")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://web.whatsapp.com")
    return driver


def wait_for_login(driver):
    print("Waiting for WhatsApp Web... scan the QR code on screen if prompted.")
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Chat list"]'))
    )
    print("Logged in. Bot is now watching for messages.")


# ---------- chat interaction ----------
def get_unread_chats(driver, limit):
    chat_list = driver.find_element(
        By.XPATH,
        '//div[@aria-label="Chat list"]'
    )

    chats = chat_list.find_elements(
        By.XPATH,
        './/div[@data-testid="cell-frame-container"]'
    )

    unread_chats = []

    for chat in chats:
        unread_badge = chat.find_elements(
            By.XPATH,
            './/*[@data-testid="icon-unread-count"]'
        )

        if unread_badge:
            unread_chats.append(chat)

    print(
        f"DEBUG: Found {len(chats)} total chats, "
        f"{len(unread_chats)} unread chats"
    )

    return unread_chats[:limit]

def open_chat(driver, chat_element):
    chat_element.click()
    time.sleep(1.5)


def get_chat_name(driver):
    header = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//header//span[@dir="auto"]'))
    )
    return header.text


def get_last_incoming_message(driver):
    containers = driver.find_elements(
        By.XPATH,
        '//div[@data-testid="msg-container"]'
    )

    # Start from the newest message and work backwards
    for container in reversed(containers):
        # If tail-out exists, this is a message sent by us
        outgoing = container.find_elements(
            By.XPATH,
            './/*[@data-icon="tail-out"]'
        )

        if outgoing:
            continue

        # Get selectable message text
        text_elements = container.find_elements(
            By.XPATH,
            './/span[contains(@class, "selectable-text")]'
        )

        texts = [
            element.text.strip()
            for element in text_elements
            if element.text.strip()
        ]

        if texts:
            return " ".join(texts)

    return None


def send_reply(driver, text):
    box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//footer//div[@contenteditable="true"]'))
    )
    box.click()
    for i, line in enumerate(text.split("\n")):
        if i > 0:
            box.send_keys(Keys.SHIFT, Keys.ENTER)
        box.send_keys(line)
    box.send_keys(Keys.ENTER)


# ---------- main loop ----------

def main():
    replied = load_replied_log()
    driver = start_driver()
    wait_for_login(driver)

    print("Auto-reply bot is running. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                # -------------------------------------------------
                # 1. Process chats that have unread messages
                # -------------------------------------------------
                unread_chats = get_unread_chats(
                    driver,
                    MAX_UNREAD_CHATS_PER_CYCLE
                )

                for chat in unread_chats:
                    try:
                        open_chat(driver, chat)

                        name = get_chat_name(driver)

                        if name in IGNORE_LIST:
                            continue

                        message = get_last_incoming_message(driver)

                        if not message:
                            continue

                        msg_id = f"{name}:{message}"

                        if msg_id in replied:
                            continue

                        print(f"[{name}] -> {message}")

                        reply = get_ai_reply(name, message)

                        print(f"[{name}] <- {reply}")

                        send_reply(driver, reply)

                        replied.add(msg_id)
                        save_replied_log(replied)

                        time.sleep(2)

                    except (NoSuchElementException, TimeoutException) as e:
                        print(
                            f"Skipped a chat due to a page-structure error: {e}"
                        )
                        continue

                # -------------------------------------------------
                # 2. Check the currently open chat
                # -------------------------------------------------
                try:
                    name = get_chat_name(driver)

                    if name not in IGNORE_LIST:
                        message = get_last_incoming_message(driver)

                        if message:
                            msg_id = f"{name}:{message}"

                            if msg_id not in replied:
                                print(f"[{name}] -> {message}")

                                reply = get_ai_reply(name, message)

                                print(f"[{name}] <- {reply}")

                                send_reply(driver, reply)

                                replied.add(msg_id)
                                save_replied_log(replied)

                                time.sleep(2)

                except (NoSuchElementException, TimeoutException):
                    # No chat is currently open — that's okay.
                    pass

            except Exception as loop_error:
                print(
                    f"Loop error (bot will keep running): {loop_error}"
                )

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStopping bot...")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()