from flask import Flask, request
import requests
import os
import tempfile
from io import BytesIO

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

def download_file(file_id):
    """دانلود فایل از تلگرام به صورت موقت"""
    try:
        # دریافت مسیر فایل
        get_file_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
        r = requests.get(get_file_url)
        if r.status_code == 200:
            file_path = r.json()["result"]["file_path"]
            # دانلود فایل
            download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            file_data = requests.get(download_url)
            return BytesIO(file_data.content)
        return None
    except Exception as e:
        print(f"خطا در دانلود: {e}")
        return None

def extract_text_from_file(file_io, file_name):
    """استخراج متن از فایل‌های مختلف"""
    ext = file_name.split('.')[-1].lower()
    try:
        if ext == 'txt':
            return file_io.read().decode('utf-8', errors='ignore')
        
        elif ext == 'pdf':
            import PyPDF2
            reader = PyPDF2.PdfReader(file_io)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        
        elif ext in ['docx', 'doc']:
            import docx
            doc = docx.Document(file_io)
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            # برای عکس‌ها، از هوش مصنوعی بخواه توضیح بده
            return "[این یک تصویر است - از هوش مصنوعی بخواه آنالیز کند]"
        
        elif ext in ['mp3', 'wav', 'ogg', 'mp4', 'avi', 'mkv']:
            return "[فایل صوتی/تصویری - قابل استخراج متن نیست]"
        
        else:
            return f"[فرمت {ext} پشتیبانی نمی‌شود]"
    except Exception as e:
        print(f"خطا در استخراج متن: {e}")
        return f"[خطا در خواندن فایل: {e}]"

def get_channel_files_and_text():
    """دریافت فایل‌های کانال و استخراج متن آنها"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"limit": 100}, timeout=10)
        if r.status_code == 200:
            updates = r.json().get("result", [])
            files_info = []
            for item in updates:
                msg = item.get("message", {})
                if str(msg.get("chat", {}).get("id")) == CHANNEL_ID:
                    if msg.get("document"):
                        file_id = msg["document"]["file_id"]
                        file_name = msg["document"].get("file_name", "بدون نام")
                        # دانلود و استخراج متن
                        file_io = download_file(file_id)
                        if file_io:
                            text = extract_text_from_file(file_io, file_name)
                            files_info.append({
                                "name": file_name,
                                "text": text[:500]  # فقط 500 کاراکتر اول
                            })
            return files_info
        return []
    except Exception as e:
        print(f"خطا در دریافت فایل‌ها: {e}")
        return []

def search_and_ask(question):
    """جستجو در فایل‌ها و پاسخ با هوش مصنوعی"""
    files = get_channel_files_and_text()
    if not files:
        return "📭 کتابخونه خالی است. لطفاً ابتدا کتاب‌ها را آپلود کنید."
    
    # جستجو در متن فایل‌ها
    relevant_texts = []
    for f in files:
        if question.lower() in f["text"].lower() or question.lower() in f["name"].lower():
            relevant_texts.append(f"📄 **{f['name']}**:\n{f['text']}")
    
    if relevant_texts:
        context = "\n\n".join(relevant_texts[:3])
        prompt = f"""بر اساس اطلاعات زیر از کتابخونه به سوال پاسخ بده:

{context}

سوال: {question}

پاسخ:"""
    else:
        prompt = question
    
    # سوال از هوش مصنوعی
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
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
                send_message(chat_id, "سلام! من ربات کتابخونه هوشمند هستم.\n\n📚 **دستورات:**\n/files - لیست کتاب‌ها\n/search کلمه - جستجو\n/start - راهنما")
            
            elif text == '/files':
                files = get_channel_files_and_text()
                if files:
                    result = "📚 **کتاب‌های کتابخونه:**\n\n"
                    for f in files:
                        result += f"• {f['name']}\n"
                    send_message(chat_id, result)
                else:
                    send_message(chat_id, "📭 کتابخونه خالی است.")
            
            elif text.startswith('/search '):
                keyword = text[8:]
                send_message(chat_id, f"🔍 در حال جستجوی «{keyword}»...")
                answer = search_and_ask(keyword)
                send_message(chat_id, answer)
            
            else:
                send_message(chat_id, "🔍 در حال تحلیل کتابخونه...")
                answer = search_and_ask(text)
                send_message(chat_id, answer)
        
        return "ok", 200
    except Exception as e:
        print(f"خطا: {e}")
        return "error", 500

@app.route('/')
def home():
    return "ربات کتابخانه هوشمند فعال است", 200
