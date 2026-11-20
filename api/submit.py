from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
import os

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            name = data.get('name', 'Не указано')
            phone = data.get('phone', 'Не указан')
            datetime_val = data.get('datetime', 'Не указано')
            
            # Приводим дату к более читаемому виду (заменяем 'T' на пробел)
            datetime_clean = datetime_val.replace('T', ' ') if datetime_val != 'Не указано' else datetime_val
            
            # Формируем сообщение для Оптики
            text = f"🚨 Новая запись в Оптику!\n\n👤 Имя: {name}\n📞 Телефон: {phone}\n📅 Желаемая дата: {datetime_clean}"
            encoded_text = urllib.parse.quote(text)
            
            bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            chat_id = os.environ.get('TELEGRAM_CHAT_ID')
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={encoded_text}"
            urllib.request.urlopen(url)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))