from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"
DEEPSEEK_KEY = "sk-5ce288a4c6ed4c10ba125d1cfa981b06"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except:
        pass

def ask_deepseek(question):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": question}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"خطا: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text == '/start':
            send_message(chat_id, "سلام! ربات فعال است.")
        elif text:
            send_message(chat_id, "در حال فکر کردن...")
            send_message(chat_id, ask_deepseek(text))
    return "ok"

@app.route('/')
def home():
    return "ربات فعال است"
