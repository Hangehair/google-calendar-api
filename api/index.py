from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('CALENDAR_ID')

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/booking':
            self._handle_booking()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'success': False, 'message': '路徑不存在'}).encode())

    def _handle_booking(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')), scopes=SCOPES)
            service = build('calendar', 'v3', credentials=credentials)
            
            start_datetime = datetime.strptime(f"{data['date']}T{data['time']}:00", '%Y-%m-%dT%H:%M:%S')
            end_datetime = start_datetime + timedelta(hours=2)  # 接髮2小時
            
            event = {
                'summary': f"預約：{data['name']} - {', '.join(data['services'])}",
                'description': f"姓名：{data['name']}\n電話：{data['phone']}\n服務：{', '.join(data['services'])}",
                'location': '台北市萬華區西門町 Hange韓哥接髮',
                'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'Asia/Taipei'},
                'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'Asia/Taipei'},
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 1440},  # 前1天提醒
                        {'method': 'popup', 'minutes': 60}     # 前1小時提醒
                    ]
                }
            }
            
            created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            
            self._set_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'message': '預約成功，已自動加入韓哥行事曆',
                'event_id': created_event['id']
            }).encode())
            
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({
                'success': False,
                'message': str(e)
            }).encode())

def main():
    pass

if __name__ == '__main__':
    main()
