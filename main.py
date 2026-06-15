from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"
GROQ_KEY = "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"
CHANNEL_ID = "-1004274256213"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"خطا در ارسال: {e}")

def get_files_list():
    """دریافت لیست فایل‌های کانال"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"limit": 100}, timeout=10)
        if r.status_code == 200:
            updates = r.json().get("result", [])
            files = []
            for item in updates:
                msg = item.get("message", {})
                if str(msg.get("chat", {}).get("id")) == CHANNEL_ID:
                    if msg.get("document"):
                        file_name = msg["document"].get("file_name", "بدون نام")
                        files.append(file_name)
            return files
        return []
    except Exception as e:
        print(f"خطا در دریافت فایل‌ها: {e}")
        return []

def ask_groq(question):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": question}]
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
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
                send_message(chat_id, "سلام! من ربات کتابخونه هستم.\n📚 دستورات:\n/files - لیست کتاب‌ها\n/start - راهنما")
            
            elif text == '/files':
                files = get_files_list()
                if files:
                    result = "📚 **لیست کتاب‌های کتابخونه:**\n\n"
                    for f in files:
                        result += f"• {f}\n"
                    send_message(chat_id, result)
                else:
                    send_message(chat_id, "📭 هیچ فایلی در کتابخونه پیدا نشد.\n\n💡 راهنما: کتاب‌ها باید به صورت فایل (PDF، عکس، و...) در کانال آپلود شده باشند.")
            
            elif text == '/search':
                send_message(chat_id, "🔍 لطفاً بعد از /search کلمه مورد نظر را بنویسید.\nمثال: /search کتاب")
            
            elif text.startswith('/search '):
                keyword = text[8:]
                files = get_files_list()
                if files:
                    result = f"🔍 **نتایج جستجوی «{keyword}» در کتابخونه:**\n\n"
                    found = [f for f in files if keyword.lower() in f.lower()]
                    if found:
                        for f in found:
                            result += f"• {f}\n"
                        send_message(chat_id, result)
                    else:
                        send_message(chat_id, f"❌ هیچ کتابی با کلمه «{keyword}» پیدا نشد.")
                else:
                    send_message(chat_id, "📭 کتابخونه خالی است. ابتدا کتاب‌ها را آپلود کنید.")
            
            else:
                send_message(chat_id, "🤔 در حال فکر کردن...")
                answer = ask_groq(text)
                send_message(chat_id, answer)
        
        return "ok", 200
    except Exception as e:
        print(f"خطا در وب هوک: {e}")
        return "error", 500

@app.route('/')
def home():
    return "ربات کتابخانه فعال است", 200
