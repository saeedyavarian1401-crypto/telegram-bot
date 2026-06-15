from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"
DEEPSEEK_KEY = "sk-5ce288a4c6ed4c10ba125d1cfa981b06"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"خطا در ارسال: {e}")

def ask_deepseek(question):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": question}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=15)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"خطا در هوش مصنوعی: {e}"

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
                send_message(chat_id, "🤔 در حال فکر کردن...")
                answer = ask_deepseek(text)
                send_message(chat_id, answer)
        return "ok", 200
    except Exception as e:
        return "error", 500

@app.route('/')
def home():
    return "ربات هوشمند فعال است", 200
