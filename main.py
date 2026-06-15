from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"

GEMINI_KEY = "AIzaSyBmsVlC2CjYvKZ6OqbFLO5yOtQN_JRgiQ"  # ✅ این کلید منهای توست

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"خطا در ارسال: {e}")

def ask_gemini(question):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    data = {"contents": [{"parts": [{"text": question}]}]}
    try:
        r = requests.post(url, json=data, timeout=20)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ خطا: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if update and 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '')
            if text == '/start':
                send_message(chat_id, "سلام! من ربات هوشمند با گوگل جمینای هستم.")
            elif text:
                send_message(chat_id, "🤔 در حال فکر کردن...")
                answer = ask_gemini(text)
                send_message(chat_id, answer)
        return "ok", 200
    except Exception as e:
        return "error", 500

@app.route('/')
def home():
    return "ربات هوشمند با جمینای فعال است", 200
