from flask import Flask, request
import requests
import json

app = Flask(__name__)

TOKEN = "8624726972:AAHa89X4pWrLaD7c-GI3OUjmx7FuSL-5pQQ"
GROQ_KEY = "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"
CHANNEL_ID = "-1004274256213"  # آیدی کانال کتابخونه

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"خطا در ارسال: {e}")

def search_in_channel(keyword):
    """جستجو در کانال کتابخونه و پیدا کردن فایل‌های مرتبط"""
    url = f"https://api.telegram.org/bot{TOKEN}/searchMessages"
    params = {
        "chat_id": CHANNEL_ID,
        "query": keyword,
        "limit": 5
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            messages = r.json().get("result", [])
            if messages:
                result_text = f"📚 **نتایج جستجو در کتابخونه برای «{keyword}»:**\n\n"
                for msg in messages:
                    text = msg.get("text", "")
                    if text:
                        result_text += f"• {text[:100]}...\n"
                return result_text
            else:
                return f"❌ هیچ نتیجه‌ای برای «{keyword}» در کتابخونه پیدا نشد."
        else:
            return f"❌ خطا در جستجو: {r.status_code}"
    except Exception as e:
        print(f"خطا در جستجو: {e}")
        return f"❌ خطا در ارتباط با کتابخونه: {e}"

def ask_groq(question, context=""):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    if context:
        prompt = f"بر اساس اطلاعات کتابخونه: {context}\n\nسوال کاربر: {question}\n\nلطفاً پاسخ مناسب بده:"
    else:
        prompt = question
    
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ خطا در هوش مصنوعی: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if update and 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '')
            
            if text == '/start':
                send_message(chat_id, "سلام! من ربات هوشمند کتابخونه‌ات هستم.\n\nبرای جستجو در کتابخونه، سوالت رو بپرس.")
            
            elif text.startswith('/search '):
                keyword = text[8:]
                send_message(chat_id, f"🔍 در حال جستجوی «{keyword}» در کتابخونه...")
                result = search_in_channel(keyword)
                send_message(chat_id, result)
            
            else:
                send_message(chat_id, "🔍 در حال جستجو در کتابخونه...")
                search_result = search_in_channel(text)
                
                if "❌ هیچ نتیجه‌ای" in search_result:
                    send_message(chat_id, "📭 توی کتابخونه چیزی پیدا نکردم. از هوش مصنوعی می‌پرسم...")
                    answer = ask_groq(text)
                    send_message(chat_id, answer)
                else:
                    send_message(chat_id, search_result)
                    send_message(chat_id, "🤔 در حال پردازش اطلاعات کتابخونه...")
                    answer = ask_groq(text, search_result)
                    send_message(chat_id, f"📚 **پاسخ بر اساس کتابخونه:**\n\n{answer}")
        
        return "ok", 200
    except Exception as e:
        print(f"خطا در وب هوک: {e}")
        return "error", 500

@app.route('/')
def home():
    return "ربات کتابخانه هوشمند فعال است", 200
