from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timedelta
import sys

# 添加父目錄到路徑，以便導入 calendar_secure
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from calendar_secure import HangeCalendarSecure
    CALENDAR_AVAILABLE = True
except Exception as e:
    CALENDAR_AVAILABLE = False
    CALENDAR_ERROR = str(e)

# 營業設定
CLOSED_DAYS = [0, 1]  # 0=星期一, 1=星期二

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
        if self.path == '/api/health' or self.path == '/api/':
            self._set_headers()
            response = {
                'status': 'healthy',
                'calendar_available': CALENDAR_AVAILABLE,
                'timestamp': datetime.now().isoformat()
            }
            if not CALENDAR_AVAILABLE:
                response['error'] = CALENDAR_ERROR
            self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not Found'}).encode())
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self._set_headers(400)
            self.wfile.write(json.dumps({'success': False, 'message': '無效的 JSON 格式'}).encode())
            return
        
        if self.path == '/api/booking':
            self.handle_booking(data)
        elif self.path == '/api/check-availability':
            self.handle_check_availability(data)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not Found'}).encode())
    
    def handle_booking(self, data):
        """處理預約請求"""
        if not CALENDAR_AVAILABLE:
            self._set_headers(500)
            self.wfile.write(json.dumps({
                'success': False,
                'message': 'Calendar 服務暫時無法使用'
            }).encode())
            return
        
        # 驗證必填欄位
        required_fields = ['name', 'phone', 'date', 'time', 'services']
        for field in required_fields:
            if field not in data:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f'缺少必填欄位: {field}'
                }).encode())
                return
        
        try:
            name = data['name']
            phone = data['phone']
            date_str = data['date']
            time_str = data['time']
            services = data['services'] if isinstance(data['services'], list) else [data['services']]
            services_str = ', '.join(services)
            
            # 解析時間
            appointment_datetime = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
            
            # 檢查公休日
            if appointment_datetime.weekday() in CLOSED_DAYS:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': '該日為公休日（星期一、二），無法預約！'
                }).encode())
                return
            
            # 計算服務時長
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
            calendar = HangeCalendarSecure()
            event = calendar.create_appointment(
                customer_name=name,
                phone=phone,
                service_type=services_str,
                start_time=appointment_datetime,
                duration_hours=total_hours,
                notes=f'LINE LIFF 線上預約 - {services_str}'
            )
            
            if not event:
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': '建立預約失敗，請聯絡店家！'
                }).encode())
                return
            
            # 如果是接髮，建立回訪提醒
            if '接髮' in services:
                calendar.create_adjustment_reminder(
                    customer_name=name,
                    phone=phone,
                    original_appointment_date=appointment_datetime,
                    notes=f'首次接髮 - {services_str}'
                )
            
            self._set_headers(200)
            self.wfile.write(json.dumps({
                'success': True,
                'message': '預約建立成功！韓哥會再與您確認。',
                'event_id': event['id'],
                'calendar_link': event.get('htmlLink'),
                'appointment_time': f'{date_str} {time_str}',
                'services': services_str,
                'duration_hours': total_hours
            }).encode())
            
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({
                'success': False,
                'message': f'系統錯誤: {str(e)}'
            }).encode())
    
    def handle_check_availability(self, data):
        """檢查時段可用性"""
        if not CALENDAR_AVAILABLE:
            self._set_headers(500)
            self.wfile.write(json.dumps({
                'available': False,
                'message': 'Calendar 服務暫時無法使用'
            }).encode())
            return
        
        date_str = data.get('date')
        time_str = data.get('time')
        
        if not date_str or not time_str:
            self._set_headers(400)
            self.wfile.write(json.dumps({
                'available': False,
                'message': '缺少日期或時間參數'
            }).encode())
            return
        
        try:
            appointment_datetime = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
            
            # 檢查公休日
            if appointment_datetime.weekday() in CLOSED_DAYS:
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    'available': False,
                    'message': '該日為公休日（星期一、二）'
                }).encode())
                return
            
            self._set_headers(200)
            self.wfile.write(json.dumps({
                'available': True,
                'message': '可預約'
            }).encode())
            
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({
                'available': False,
                'message': f'錯誤: {str(e)}'
            }).encode())
