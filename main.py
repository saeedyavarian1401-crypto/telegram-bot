from flask import Flask, request
import requests
import json
import time

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

def get_channel_messages(limit=100):
    """گرفتن آخرین پیام‌های کانال"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"limit": limit}, timeout=10)
        if r.status_code == 200:
            return r.json().get("result", [])
        return []
    except Exception as e:
        print(f"خطا در دریافت پیام‌ها: {e}")
        return []

def search_in_channel(keyword):
    """جستجو در کانال کتابخونه"""
    try:
        messages = get_channel_messages(limit=200)
        results = []
        
        for item in messages:
            msg = item.get("message", {})
            # چک کردن اینکه پیام از کانال ماست
            if str(msg.get("chat", {}).get("id")) == CHANNEL_ID:
                msg_text = msg.get("text", "")
                if keyword.lower() in msg_text.lower():
                    results.append(msg_text[:300])
        
        if results:
            return "\n\n📄 ---\n\n".join(results[:3])
        return None
    except Exception as e:
        print(f"خطا در جستجو: {e}")
        return None

def ask_groq(question, context=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    if context:
        prompt = f"""بر اساس اطلاعات زیر از کتابخانه پاسخ بده:

📚 اطلاعات کتابخانه:
{context}

❓ سوال کاربر: {question}

لطفاً پاسخ مناسب و مفید بده:"""
    else:
        prompt = question
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
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
                send_message(chat_id, "سلام! من ربات هوشمند کتابخونه‌ات هستم.\n\nهر سوالی بپرسی، اول توی کتابخونه می‌گردم، اگه چیزی پیدا نکردم از هوش مصنوعی جواب می‌گیرم.")
            
            elif text.startswith('/search '):
                keyword = text[8:]
                send_message(chat_id, f"🔍 در حال جستجوی «{keyword}» در کتابخونه...")
                result = search_in_channel(keyword)
                if result:
                    send_message(chat_id, f"📚 **نتایج پیدا شده در کتابخونه:**\n\n{result}")
                else:
                    send_message(chat_id, f"❌ هیچ نتیجه‌ای برای «{keyword}» در کتابخونه پیدا نشد.")
            
            else:
                send_message(chat_id, "🔍 در حال جستجو در کتابخونه...")
                result = search_in_channel(text)
                
                if result:
                    send_message(chat_id, "📚 **مطلبی در کتابخونه پیدا شد. دارم تحلیل می‌کنم...**")
                    answer = ask_groq(text, result)
                    send_message(chat_id, f"📖 **پاسخ بر اساس کتابخونه:**\n\n{answer}")
                else:
                    send_message(chat_id, "📭 توی کتابخونه چیزی پیدا نکردم. از هوش مصنوعی می‌پرسم...")
                    answer = ask_groq(text)
                    send_message(chat_id, f"🤖 **پاسخ هوش مصنوعی:**\n\n{answer}")
        
        return "ok", 200
    except Exception as e:
        print(f"خطا در وب هوک: {e}")
        return "error", 500

@app.route('/')
def home():
    return "ربات کتابخانه هوشمند فعال است", 200
