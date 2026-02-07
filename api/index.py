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

def create_booking_events(service, name, phone, date, time, services):
    """建立兩個 Google Calendar 事件：首次預約 + 兩個月後回訪提醒"""
    
    # 解析預約時間
    tz = pytz.timezone(TIMEZONE)
    date_str = f"{date} {time}"
    booking_start = tz.localize(datetime.strptime(date_str, '%Y-%m-%d %H:%M'))
    booking_end = booking_start + timedelta(hours=2)
    
    # 計算兩個月後的提醒日期
    reminder_date = booking_start + timedelta(days=60)  # 約兩個月
    reminder_start = reminder_date.replace(hour=14, minute=0, second=0)
    reminder_end = reminder_start + timedelta(hours=2)
    
    # 處理 services
    if isinstance(services, list):
        services_str = '、'.join(services)
    else:
        services_str = services
    
    # === 事件 1：首次預約 ===
    event_booking = {
        'summary': f'【接髮服務】{name} - {services_str}',
        'description': f'👤 客戶：{name}\n📱 電話：{phone}\n💇 服務項目：{services_str}',
        'start': {
            'dateTime': booking_start.isoformat(),
            'timeZone': TIMEZONE,
        },
        'end': {
            'dateTime': booking_end.isoformat(),
            'timeZone': TIMEZONE,
        },
        'colorId': '9',  # 藍色
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 1440},  # 1天前
                {'method': 'popup', 'minutes': 60},     # 1小時前
            ],
        },
    }
    
    # === 事件 2：兩個月後回訪提醒 ===
    event_reminder = {
        'summary': f'🔔【回訪提醒】{name} - 接髮調整',
        'description': f'''🔔 接髮調整回訪提醒

👤 客戶：{name}
📱 電話：{phone}
📅 上次服務：{date}

💎 優惠方案：
- 接髮調整課程買4送1
- 單次 $5,000

💡 建議聯絡時間：提前3天主動聯繫客戶''',
        'start': {
            'dateTime': reminder_start.isoformat(),
            'timeZone': TIMEZONE,
        },
        'end': {
            'dateTime': reminder_end.isoformat(),
            'timeZone': TIMEZONE,
        },
        'colorId': '11',  # 紅色（醒目）
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 4320},  # 3天前
                {'method': 'popup', 'minutes': 1440},  # 1天前
            ],
        },
    }
    
    # 建立兩個事件
    created_booking = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event_booking
    ).execute()
    
    created_reminder = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event_reminder
    ).execute()
    
    return {
        'booking_event_id': created_booking['id'],
        'reminder_event_id': created_reminder['id'],
        'booking_link': created_booking.get('htmlLink', ''),
        'reminder_link': created_reminder.get('htmlLink', ''),
        'reminder_date': reminder_start.strftime('%Y-%m-%d')
    }

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
    """建立預約（同時建立首次服務 + 兩個月後回訪提醒）"""
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
        
        # 建立兩個事件
        result = create_booking_events(
            service,
            data['name'],
            data['phone'],
            data['date'],
            data['time'],
            data['services']
        )
        
        # 處理 services 顯示
        services = data['services']
        if isinstance(services, list):
            services_str = '、'.join(services)
        else:
            services_str = services
        
        response = jsonify({
            'success': True,
            'message': f"預約建立成功！{data['name']} 的 {services_str} 預約已安排在 {data['date']} {data['time']}",
            'booking_event_id': result['booking_event_id'],
            'reminder_event_id': result['reminder_event_id'],
            'reminder_date': result['reminder_date'],
            'booking_link': result['booking_link'],
            'reminder_link': result['reminder_link']
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
