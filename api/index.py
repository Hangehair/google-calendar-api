from flask import Flask, request, jsonify
import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pytz

app = Flask(__name__)

# Google Calendar API 設定
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('CALENDAR_ID', 'primary')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Taipei')

def get_calendar_service():
    """建立 Google Calendar 服務"""
    creds = None
    
    # 從環境變數讀取憑證
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not credentials_json:
        return None, "Missing GOOGLE_CREDENTIALS_JSON environment variable"
    
    try:
        credentials_info = json.loads(credentials_json)
        creds = Credentials.from_authorized_user_info(credentials_info, SCOPES)
    except Exception as e:
        return None, f"Error loading credentials: {str(e)}"
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service, None
    except Exception as e:
        return None, f"Error building calendar service: {str(e)}"

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    service, error = get_calendar_service()
    
    if error:
        return jsonify({
            'status': 'unhealthy',
            'error': error,
            'timestamp': datetime.now(pytz.timezone(TIMEZONE)).isoformat()
        }), 500
    
    return jsonify({
        'status': 'healthy',
        'calendar_connected': True,
        'calendar_id': CALENDAR_ID,
        'timezone': TIMEZONE,
        'timestamp': datetime.now(pytz.timezone(TIMEZONE)).isoformat()
    })

@app.route('/api/booking', methods=['POST'])
def create_booking():
    """建立預約"""
    service, error = get_calendar_service()
    
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    try:
        data = request.get_json()
        
        # 驗證必要欄位
        required_fields = ['name', 'phone', 'date', 'time', 'services']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 解析日期時間
        tz = pytz.timezone(TIMEZONE)
        date_str = f"{data['date']} {data['time']}"
        start_time = tz.localize(datetime.strptime(date_str, '%Y-%m-%d %H:%M'))
        end_time = start_time + timedelta(hours=2)  # 預設2小時
        
        # 建立事件
        event = {
            'summary': f"{', '.join(data['services'])} - {data['name']}",
            'description': f"客戶：{data['name']}\n電話：{data['phone']}\n服務：{', '.join(data['services'])}",
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': TIMEZONE,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 24 * 60},  # 前一天
                    {'method': 'popup', 'minutes': 60},  # 1小時前
                ],
            },
        }
        
        # 新增到 Google Calendar
        created_event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event
        ).execute()
        
        return jsonify({
            'success': True,
            'message': f"預約建立成功！{data['name']} 的 {', '.join(data['services'])} 預約已安排在 {data['date']} {data['time']}",
            'event_id': created_event['id'],
            'calendar_link': created_event.get('htmlLink', '')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    """檢查時段可用性"""
    service, error = get_calendar_service()
    
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    try:
        data = request.get_json()
        
        if 'date' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: date'
            }), 400
        
        # 解析日期
        tz = pytz.timezone(TIMEZONE)
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        start_of_day = tz.localize(datetime.combine(date_obj, datetime.min.time()))
        end_of_day = tz.localize(datetime.combine(date_obj, datetime.max.time()))
        
        # 查詢當天的預約
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # 整理已預約時段
        booked_slots = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            booked_slots.append({
                'time': start,
                'summary': event.get('summary', '未命名')
            })
        
        return jsonify({
            'success': True,
            'date': data['date'],
            'booked_slots': booked_slots,
            'available': len(booked_slots) < 6  # 假設一天最多6個時段
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Vercel 需要這個
app = app
