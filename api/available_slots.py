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
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            date_str = query.get('date', [None])[0]
            
            if not date_str:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Missing date'}).encode())
                return
            
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if not credentials_json:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': 'Missing credentials'}).encode())
                return
            
            if not CALENDAR_ID:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': 'Missing CALENDAR_ID'}).encode())
                return
            
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=SCOPES
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            time_min = date_obj.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            time_max = date_obj.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            all_slots = ['13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
            busy_slots = set()
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                if 'T' not in start:
                    continue
                
                start_parts = start.split('T')
                end_parts = end.split('T')
                start_clean = start_parts[0] + 'T' + start_parts[1].split('+')[0].split('-')[0].split('Z')[0]
                end_clean = end_parts[0] + 'T' + end_parts[1].split('+')[0].split('-')[0].split('Z')[0]
                
                try:
                    start_dt = datetime.fromisoformat(start_clean)
                    end_dt = datetime.fromisoformat(end_clean)
                except:
                    continue
                
                for slot in all_slots:
                    slot_hour = int(slot.split(':')[0])
                    slot_start = date_obj.replace(hour=slot_hour, minute=0, second=0)
                    slot_end = slot_start + timedelta(hours=2)
                    
                    if not (slot_end <= start_dt or slot_start >= end_dt):
                        busy_slots.add(slot)
            
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
                'error': str(e),
                'error_type': type(e).__name__
            }).encode())
