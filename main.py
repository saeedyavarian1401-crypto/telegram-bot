from flask import Flask, request
import requests
import logging

app = Flask(__name__)

# تنظیم لاگ برای دیدن خطاها
logging.basicConfig(level=logging.INFO)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"
DEEPSEEK_KEY = "sk-5ce288a4c6ed4c10ba125d1cfa981b06"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
        logging.info(f"پیام ارسال شد به {chat_id}")
    except Exception as e:
        logging.error(f"خطا در ارسال: {e}")

def ask_deepseek(question):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": question}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=15)
        result = r.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"خطا در دیپ سیک: {e}")
        return "خطا در ارتباط با هوش مصنوعی"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if update and 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '')
            logging.info(f"پیام دریافت شد: {text} از {chat_id}")
            
            if text == '/start':
                send_message(chat_id, "سلام! ربات فعال است.")
            elif text:
                send_message(chat_id, "در حال فکر کردن...")
                answer = ask_deepseek(text)
                send_message(chat_id, answer)
        return "ok", 200
    except Exception as e:
        logging.error(f"خطا در وب هوک: {e}")
        return "error", 500

@app.route('/')
def home():
    return "ربات فعال است"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
