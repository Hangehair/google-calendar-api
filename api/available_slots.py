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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        try:
            # 從 URL 取得日期參數 (例如: ?date=2026-01-30)
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            date_str = query.get('date', [None])[0]
            
            if not date_str:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': '缺少 date 參數'}).encode())
                return
            
            # 取得 Google Calendar 憑證
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if not credentials_json:
                raise Exception('缺少 Google 憑證')
            
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=SCOPES
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # 設定查詢時間範圍（當天 00:00 ~ 23:59）
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            time_min = date_obj.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            time_max = date_obj.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
            
            # 查詢當天的所有行程
            events_result = service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # 定義所有可能的時段（12:30 - 18:00，每 30 分鐘一個時段）
            all_slots = []
            current_time = date_obj.replace(hour=12, minute=30)
            end_time = date_obj.replace(hour=18, minute=0)
            
            while current_time < end_time:
                all_slots.append(current_time.strftime('%H:%M'))
                current_time += timedelta(minutes=30)
            
            # 找出被佔用的時段
            busy_slots = set()
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # 解析時間
                if 'T' in start:  # dateTime 格式
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    
                    # 找出這個事件佔用了哪些時段
                    slot_time = date_obj.replace(hour=12, minute=30)
                    while slot_time < end_time:
                        slot_end = slot_time + timedelta(minutes=30)
                        
                        # 如果時段與事件有重疊，標記為忙碌
                        if not (slot_end <= start_dt or slot_time >= end_dt):
                            busy_slots.add(slot_time.strftime('%H:%M'))
                        
                        slot_time += timedelta(minutes=30)
            
            # 產生可用時段清單
            available_slots = [slot for slot in all_slots if slot not in busy_slots]
            
            self._set_headers(200)
            self.wfile.write(json.dumps({
                'success': True,
                'date': date_str,
                'available': available_slots,
                'busy': list(busy_slots),
                'events_count': len(events)
            }).encode())
            
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
