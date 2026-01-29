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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)
        
        if path == '/api/available_slots':
            # 可用時段查詢
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
            time_min
