from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"
GROQ_KEY = "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"
CHANNEL_ID = -1004274256213  # آیدی کانالی که بهت دادم

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"خطا در ارسال: {e}")

def ask_groq(question):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": question}]
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        return r.json()["choices"][0]["message"]["content"]
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
                send_message(chat_id, "سلام! من ربات هوشمند کتابخونه‌ات هستم.")
            elif text:
                send_message(chat_id, "🤔 در حال جستجو در کتابخانه و فکر کردن...")
                # اینجا بعداً کد جستجو در کانال رو اضافه می‌کنیم
                answer = ask_groq(text)
                send_message(chat_id, answer)
        return "ok", 200
    except Exception as e:
        return "error", 500

@app.route('/')
def home():
    return "ربات کتابخانه هوشمند فعال است", 200
