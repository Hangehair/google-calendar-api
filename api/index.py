from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('winter81943@yahoo.com.tw')

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)
        
        # 處理 /api/index 和 /api/available_slots 兩個路徑
        if path in ['/api/index', '/api/available_slots']:
            date_str = query.get('date', [None])[0]
            if not date_str:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Missing date parameter'}).encode())
                return
            
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if not credentials_json:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': 'Missing GOOGLE_APPLICATION_CREDENTIALS_JSON'}).encode())
                return
            
            if not CALENDAR_ID:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': 'Missing CALENDAR_ID env var'}).encode())
                return
            
            try:
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=SCOPES
                )
                service = build('calendar', 'v3', credentials=credentials)
                
                # 解析日期
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                time_min = date_obj.replace(hour=9, minute=0, second=0, microsecond=0).isoformat() + 'Z'
                time_max = date_obj.replace(hour=21, minute=0, second=0, microsecond=0).isoformat() + 'Z'
                
                # 取得當日事件
                events_result = service.events().list(
                    calendarId=CALENDAR_ID,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                # 定義時段 (30分鐘一格，9:00-21:00)
                slots = []
                current_time = date_obj.replace(hour=9, minute=0)
                end_time = date_obj.replace(hour=21, minute=0)
                
                while current_time < end_time:
                    slot_end = current_time + timedelta(minutes=30)
                    slot_str = current_time.strftime('%H:%M')
                    
                    # 檢查是否有重疊事件
                    is_available = True
                    for event in events:
                        event_start = datetime.fromisoformat(event['start']['dateTime'])
                        event_end = datetime.fromisoformat(event['end']['dateTime'])
                        
                        if (current_time < event_end and slot_end > event_start):
                            is_available = False
                            break
                    
                    slots.append({
                        'time': slot_str,
                        'available': is_available
                    })
                    
                    current_time = slot_end
                
                self._set_headers()
                response = {
                    'success': True,
                    'date': date_str,
                    'available_slots': slots
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())

def main():
    handler()

if __name__ == '__main__':
    main()
