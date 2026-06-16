from flask import Flask, request
import requests
import tempfile
import os

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

def get_file_text(file_id):
    try:
        file_info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}")
        if file_info.status_code != 200:
            return None
        file_path = file_info.json()["result"]["file_path"]
        file_data = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file_path}")
        if file_data.status_code != 200:
            return None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(file_data.content)
            tmp_path = tmp.name
        with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        os.unlink(tmp_path)
        return text[:2000]
    except Exception as e:
        print(f"خطا در دریافت فایل: {e}")
        return None

def search_channel(query):
    try:
        updates = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"limit": 30}).json()
        results = []
        for item in updates.get("result", []):
            msg = item.get("message", {})
            if str(msg.get("chat", {}).get("id")) == CHANNEL_ID:
                text = msg.get("text", "")
                if query.lower() in text.lower():
                    results.append(f"📝 {text[:300]}")
                doc = msg.get("document")
                if doc:
                    file_name = doc.get("file_name", "")
                    if query.lower() in file_name.lower():
                        file_text = get_file_text(doc["file_id"])
                        if file_text:
                            results.append(f"📄 {file_name}:\n{file_text[:500]}")
        return results if results else None
    except Exception as e:
        print(f"خطا در جستجو: {e}")
        return None

def ask_groq(question, context=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    if context:
        prompt = f"بر اساس اطلاعات زیر از کتابخونه پاسخ بده:\n\n{context}\n\nسوال: {question}"
    else:
        prompt = question
    data = {"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}]}
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
                send_message(chat_id, "سلام! من ربات کتابخونه‌ات هستم. هر سوالی بپرس.")
            else:
                # بررسی کلمات کلیدی برای جستجو در کتابخونه
                keywords = ["کتاب", "کتابخونه", "فایل", "جستجو", "پیدا کن", "داری", "موضوع", "مطلب"]
                if any(kw in text for kw in keywords):
                    send_message(chat_id, "🔍 در حال جستجو در کتابخونه...")
                    results = search_channel(text)
                    if results:
                        context = "\n\n".join(results[:2])
                        send_message(chat_id, "📚 پیدا شد. دارم تحلیل می‌کنم...")
                        answer = ask_groq(text, context)
                        send_message(chat_id, f"📖 {answer}")
                    else:
                        send_message(chat_id, "📭 توی کتابخونه چیزی پیدا نشد. از هوش مصنوعی می‌پرسم...")
                        answer = ask_groq(text)
                        send_message(chat_id, f"🤖 {answer}")
                else:
                    send_message(chat_id, "🤔 در حال فکر کردن...")
                    answer = ask_groq(text)
                    send_message(chat_id, f"🤖 {answer}")
        return "ok", 200
    except Exception as e:
        print(f"خطا: {e}")
        return "error", 500

@app.route('/')
def home():
    return "ربات کتابخانه هوشمند فعال است", 200
