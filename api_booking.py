#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hange 髮廊預約 API
整合 HAN.BOT (LINE LIFF) 與 Google Calendar
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from calendar_secure import HangeCalendarSecure
import os

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# Hange 髮廊營業設定
CLOSED_DAYS = [0, 1]  # 0=星期一, 1=星期二
OPEN_HOURS = {'start': 12, 'end': 18}  # 12:30-18:00

# 初始化 Google Calendar
calendar = HangeCalendarSecure()

def is_closed_day(date):
    """檢查是否為公休日"""
    return date.weekday() in CLOSED_DAYS

def check_time_slot_available(date_str, time_str):
    """
    檢查時段是否可用（避免重複預約）
    
    Args:
        date_str: 日期 YYYY-MM-DD
        time_str: 時間 HH:MM
    
    Returns:
        bool: True=可用, False=已滿
    """
    try:
        # 解析預約時間
        appointment_datetime = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        
        # 查詢當天的所有預約
        day_start = appointment_datetime.replace(hour=0, minute=0, second=0)
        day_end = appointment_datetime.replace(hour=23, minute=59, second=59)
        
        events = calendar.service.events().list(
            calendarId=calendar.calendar_id,
            timeMin=day_start.isoformat() + 'Z',
            timeMax=day_end.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute().get('items', [])
        
        # 檢查是否有時間衝突
        for event in events:
            event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
            
            # 預約時間在現有預約範圍內
            if event_start <= appointment_datetime < event_end:
                return False
        
        return True
        
    except Exception as e:
        print(f'檢查時段錯誤: {e}')
        return False

@app.route('/api/booking', methods=['POST'])
def create_booking():
    """
    建立預約並同步到 Google Calendar
    
    Request Body:
    {
        "name": "王小姐",
        "phone": "0912-345-678",
        "date": "2025-12-20",
        "time": "14:00",
        "services": ["接髮", "染髮"]
    }
    
    Response:
    {
        "success": true,
        "message": "預約建立成功！",
        "event_id": "xxx123",
        "calendar_link": "https://..."
    }
    """
    try:
        data = request.get_json()
        
        # 驗證必填欄位
        required_fields = ['name', 'phone', 'date', 'time', 'services']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填欄位: {field}'
                }), 400
        
        name = data['name']
        phone = data['phone']
        date_str = data['date']
        time_str = data['time']
        services = data['services'] if isinstance(data['services'], list) else [data['services']]
        services_str = ', '.join(services)
        
        # 解析時間
        appointment_datetime = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        
        # 檢查公休日
        if is_closed_day(appointment_datetime):
            return jsonify({
                'success': False,
                'message': '該日為公休日（星期一、二），無法預約！'
            }), 400
        
        # 檢查時段是否可用
        if not check_time_slot_available(date_str, time_str):
            return jsonify({
                'success': False,
                'message': '該時段已有預約，請選擇其他時間！'
            }), 400
        
        # 計算服務時長（根據服務類型）
        service_duration = {
            '接髮': 3,
            '染髮': 2.5,
            '燙髮': 2.5,
            '剪髮': 1,
            '洗髮': 0.5,
            '頭髮護理': 1,
            '頭皮護理': 1
        }
        
        total_hours = sum([service_duration.get(s, 2) for s in services])
        
        # 建立 Google Calendar 預約
        event = calendar.create_appointment(
            customer_name=name,
            phone=phone,
            service_type=services_str,
            start_time=appointment_datetime,
            duration_hours=total_hours,
            notes=f'LINE LIFF 線上預約 - {services_str}'
        )
        
        if not event:
            return jsonify({
                'success': False,
                'message': '建立預約失敗，請聯繫店家！'
            }), 500
        
        # 如果是接髮，自動建立 2 個月後的回訪提醒
        if '接髮' in services:
            calendar.create_adjustment_reminder(
                customer_name=name,
                phone=phone,
                original_appointment_date=appointment_datetime,
                notes=f'首次接髮 - {services_str}'
            )
        
        return jsonify({
            'success': True,
            'message': '預約建立成功！韓哥會再與您確認。',
            'event_id': event['id'],
            'calendar_link': event.get('htmlLink'),
            'appointment_time': f'{date_str} {time_str}',
            'services': services_str,
            'duration_hours': total_hours
        }), 200
        
    except Exception as e:
        print(f'API 錯誤: {e}')
        return jsonify({
            'success': False,
            'message': f'系統錯誤: {str(e)}'
        }), 500

@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    """
    檢查時段是否可用
    
    Request Body:
    {
        "date": "2025-12-20",
        "time": "14:00"
    }
    
    Response:
    {
        "available": true/false,
        "message": "..."
    }
    """
    try:
        data = request.get_json()
        date_str = data.get('date')
        time_str = data.get('time')
        
        if not date_str or not time_str:
            return jsonify({
                'available': False,
                'message': '缺少日期或時間參數'
            }), 400
        
        appointment_datetime = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        
        # 檢查公休日
        if is_closed_day(appointment_datetime):
            return jsonify({
                'available': False,
                'message': '該日為公休日（星期一、二）'
            }), 200
        
        # 檢查時段
        is_available = check_time_slot_available(date_str, time_str)
        
        return jsonify({
            'available': is_available,
            'message': '可預約' if is_available else '該時段已滿'
        }), 200
        
    except Exception as e:
        return jsonify({
            'available': False,
            'message': f'錯誤: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """API 健康檢查"""
    return jsonify({
        'status': 'healthy',
        'calendar_connected': True,
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
