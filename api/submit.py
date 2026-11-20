from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
import os
import psycopg2

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data)
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            date_val = data.get('date', '').strip()
            time_val = data.get('time', '').strip()

            if not all([name, phone, date_val, time_val]):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Заполните все поля"}).encode('utf-8'))
                return

            # 1. Сохраняем в Neon
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO appointments (name, phone, appointment_date, appointment_time)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (name, phone, date_val, time_val)
                )
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                cur.close()
                conn.close()
                self.send_response(409)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Это время уже занято"}).encode('utf-8'))
                return
            finally:
                if not cur.closed:
                    cur.close()
                if not conn.closed:
                    conn.close()

            # 2. Отправляем уведомление в Telegram
            text = (
                f"🚨 Новая запись в Оптику!\n\n"
                f"👤 Имя: {name}\n"
                f"📞 Телефон: {phone}\n"
                f"📅 Дата: {date_val}\n"
                f"⏰ Время: {time_val}"
            )
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