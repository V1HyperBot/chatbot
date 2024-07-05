import logging
import os
import sys
from io import BytesIO

import requests
import telebot
from dotenv import load_dotenv

telebot.logger.setLevel(logging.INFO)

load_dotenv(sys.argv[1])

AI_GOOGLE_API = os.getenv("AI_GOOGLE_API")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

text = """
user_id: {}
name: {}

msg: {}
"""


def get_text(message):
    reply_text = (
        message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message
        else ""
    )
    user_text = message.text
    return (
        f"{user_text}\n\n{reply_text}"
        if reply_text and user_text
        else reply_text + user_text
    )


def google_ai(question):
    if not AI_GOOGLE_API:
        return "Silakan periksa AI_GOOGLE_API Anda di file env"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={AI_GOOGLE_API}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": question}]}],
        "generationConfig": {
            "temperature": 1,
            "topK": 0,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "stopSequences": [],
        },
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Failed to generate content. Status code: {response.status_code}"


def mention(user):
    name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    link = f"tg://user?id={user.id}"
    return f"[{name}]({link})"


def send_large_output(message, output, msg):
    if len(output) <= 4000:
        bot.send_message(message.chat.id, output, parse_mode=None)
    else:
        with BytesIO(str.encode(str(output))) as out_file:
            out_file.name = "result.txt"
            bot.send_document(message.chat.id, out_file)
    bot.delete_message(message.chat.id, msg.message_id)


def owner_notif(func):
    def function(message):
        if message.from_user.id != OWNER_ID:
            link = (
                f"https://t.me/{message.from_user.username}"
                if message.from_user.username
                else f"tg://openmessage?user_id={message.from_user.id}"
            )
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("link profil", url=link))
            bot.send_message(OWNER_ID, message.text, reply_markup=markup)
        return func(message)

    return function


@bot.message_handler(func=lambda message: True)
@owner_notif
def google(message):
    if message.text.startswith("/start"):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Repository", url="https://github.com/V1HyperBot/chatbot"
            ),
            telebot.types.InlineKeyboardButton("Credit", url="https://t.me/NorSodikin"),
        )
        bot.send_message(
            message.chat.id,
            f"**👋 Hai {mention(message.from_user)} Perkenalkan saya ai google telegram bot. Dan saya adalah robot kecerdasan buatan dari ai.google.dev, dan saya siap menjawab pertanyaan yang Anda berikan**",
            parse_mode="MARKDOWN",
            reply_markup=markup,
        )
    else:
        msg = bot.reply_to(message, "Silahkan tunggu...")
        try:
            result = google_ai(get_text(message))
            send_large_output(message, result, msg)
        except Exception as error:
            bot.edit_message_text(str(error), message.chat.id, msg.message_id)


bot.infinity_polling()
