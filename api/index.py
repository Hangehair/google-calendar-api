from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz

app = Flask(__name__)

# ✅ 啟用 CORS 支援，允許所有來源（產品環境建議限制特定域名）
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Google Calendar API 設定
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('CALENDAR_ID', 'primary')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Taipei')

def get_calendar_service():
    """建立 Google Calendar 服務（使用 Service Account）"""
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not credentials_json:
        return None, "Missing GOOGLE_CREDENTIALS_JSON environment variable"
    
    try:
        credentials_info = json.loads(credentials_json)
        creds = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        return service, None
    except Exception as e:
        return None, f"Error: {str(e)}"

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """健康檢查端點"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    service, error = get_calendar_service()
    
    if error:
        return jsonify({
            'status': 'unhealthy',
            'error': error,
            'timestamp': datetime.now(pytz.timezone(TIMEZONE)).isoformat()
        }), 500
    
    response = jsonify({
        'status': 'healthy',
        'calendar_connected': True,
        'calendar_id': CALENDAR_ID,
        'timezone': TIMEZONE,
        'timestamp': datetime.now(pytz.timezone(TIMEZONE)).isoformat()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/booking', methods=['POST', 'OPTIONS'])
def create_booking():
    """建立預約"""
    # 處理 OPTIONS 預檢請求
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    service, error = get_calendar_service()
    
    if error:
        response = jsonify({'success': False, 'error': error})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
    
    try:
        data = request.get_json()
        
        # 驗證必要欄位
        required_fields = ['name', 'phone', 'date', 'time', 'services']
        for field in required_fields:
            if field not in data:
                response = jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
        
        # 解析日期時間
        tz = pytz.timezone(TIMEZONE)
        date_str = f"{data['date']} {data['time']}"
        start_time = tz.localize(datetime.strptime(date_str, '%Y-%m-%d %H:%M'))
        end_time = start_time + timedelta(hours=2)
        
        # 處理 services （可能是 list 或 string）
        services = data['services']
        if isinstance(services, list):
            services_str = ', '.join(services)
        else:
            services_str = services
        
        # 建立事件
        event = {
            'summary': f"{services_str} - {data['name']}",
            'description': f"客戶：{data['name']}\n電話：{data['phone']}\n服務：{services_str}",
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
                    {'method': 'popup', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }
        
        # 新增到 Google Calendar
        created_event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event
        ).execute()
        
        response = jsonify({
            'success': True,
            'message': f"預約建立成功！{data['name']} 的 {services_str} 預約已安排在 {data['date']} {data['time']}",
            'event_id': created_event['id'],
            'calendar_link': created_event.get('htmlLink', '')
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/check-availability', methods=['POST', 'OPTIONS'])
def check_availability():
    """檢查時段可用性"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    service, error = get_calendar_service()
    
    if error:
        response = jsonify({'success': False, 'error': error})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
    
    try:
        data = request.get_json()
        
        if 'date' not in data:
            response = jsonify({
                'success': False,
                'error': 'Missing required field: date'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
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
        
        response = jsonify({
            'success': True,
            'date': data['date'],
            'booked_slots': booked_slots,
            'available': len(booked_slots) < 6
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Vercel 需要這個
app = app
