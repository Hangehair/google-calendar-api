#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Calendar API 整合工具 (安全版本)
使用環境變數存儲敏感資訊，無需上傳 credentials.json
適合部署到雲端或分享程式碼
"""

import os
import json
import tempfile
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']

class HangeCalendarSecure:
    """Hange 髮廊專用 Google Calendar API (安全版本)"""
    
    def __init__(self, calendar_id=None):
        """
        初始化 Calendar API
        憑證來源優先順序：
        1. 環境變數 GOOGLE_CREDENTIALS_JSON
        2. 本地 credentials.json 檔案
        """
        self.calendar_id = calendar_id or os.getenv('CALENDAR_ID', 'primary')
        self.timezone = os.getenv('TIMEZONE', 'Asia/Taipei')
        self.service = self._authenticate()
    
    def _get_credentials_dict(self):
        """從環境變數或個別變數組建憑證"""
        # 方法 1: 從完整的 JSON 環境變數
        credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if credentials_json:
            try:
                return json.loads(credentials_json)
            except json.JSONDecodeError as e:
                print(f'❌ 解析 GOOGLE_CREDENTIALS_JSON 失敗: {e}')
        
        # 方法 2: 從個別環境變數組建
        project_id = os.getenv('GOOGLE_PROJECT_ID')
        private_key = os.getenv('GOOGLE_PRIVATE_KEY')
        client_email = os.getenv('GOOGLE_CLIENT_EMAIL')
        
        if project_id and private_key and client_email:
            # 處理私鑰中的 \n (從環境變數讀取時可能被轉義)
            private_key = private_key.replace('\\n', '\n')
            
            return {
                'type': 'service_account',
                'project_id': project_id,
                'private_key': private_key,
                'client_email': client_email,
                'token_uri': 'https://oauth2.googleapis.com/token',
            }
        
        # 方法 3: 從本地檔案讀取 (本地開發用)
        if os.path.exists('credentials.json'):
            print('ℹ️  使用本地 credentials.json 檔案')
            with open('credentials.json', 'r') as f:
                return json.load(f)
        
        return None
    
    def _authenticate(self):
        """驗證 Google Calendar API"""
        try:
            credentials_dict = self._get_credentials_dict()
            
            if not credentials_dict:
                raise ValueError(
                    '找不到憑證！請設定以下任一方式：\n'
                    '1. 環境變數 GOOGLE_CREDENTIALS_JSON (完整 JSON)\n'
                    '2. 環境變數 GOOGLE_PROJECT_ID, GOOGLE_PRIVATE_KEY, GOOGLE_CLIENT_EMAIL\n'
                    '3. 本地 credentials.json 檔案'
                )
            
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict, scopes=SCOPES)
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # 測試連線
            service.calendarList().list(maxResults=1).execute()
            print('✅ Google Calendar API 連線成功')
            
            return service
            
        except Exception as e:
            print(f'❌ 驗證失敗: {e}')
            print('\n請檢查：')
            print('1. 環境變數是否正確設定')
            print('2. 服務帳戶 email 是否已分享行事曆')
            print(f'   服務帳戶: {credentials_dict.get("client_email", "未知") if credentials_dict else "無法讀取"}')
            raise
    
    def create_appointment(self, customer_name, phone, service_type, 
                          start_time, duration_hours=2, notes='', 
                          customer_email=None):
        """建立 Hange 髮廊預約"""
        end_time = start_time + timedelta(hours=duration_hours)
        
        description_parts = [
            f'👤 客戶：{customer_name}',
            f'📱 電話：{phone}',
            f'💇 服務：{service_type}',
        ]
        if notes:
            description_parts.append(f'📝 備註：{notes}')
        
        event = {
            'summary': f'【Hange預約】{customer_name} - {service_type}',
            'location': 'Hange韓哥接髮｜台北西門町',
            'description': '\n'.join(description_parts),
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': self.timezone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1440},  # 前一天
                    {'method': 'popup', 'minutes': 60},    # 1小時前
                ],
            },
        }
        
        if customer_email:
            event['attendees'] = [{'email': customer_email}]
        
        try:
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendUpdates='all' if customer_email else 'none'
            ).execute()
            
            print(f'✅ 預約建立成功！')
            print(f'   客戶：{customer_name}')
            print(f'   時間：{start_time.strftime("%Y/%m/%d %H:%M")}')
            print(f'   連結：{event.get("htmlLink")}')
            return event
            
        except HttpError as error:
            print(f'❌ 建立預約失敗: {error}')
            return None
    
    def list_upcoming_appointments(self, days=7, max_results=50):
        """列出即將到來的預約"""
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                timeMax=end,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                print(f'📅 未來 {days} 天內沒有預約')
                return []
            
            print(f'\n📅 未來 {days} 天的預約（共 {len(events)} 個）：')
            print('=' * 60)
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%m/%d %H:%M')
                except:
                    formatted_time = start
                
                print(f'{formatted_time} - {event["summary"]}')
            print('=' * 60)
            
            return events
            
        except HttpError as error:
            print(f'❌ 查詢預約失敗: {error}')
            return []
    
    def create_adjustment_reminder(self, customer_name, phone, 
                                   original_appointment_date, notes=''):
        """建立 2 個月後的接髮調整回訪提醒"""
        adjustment_date = original_appointment_date + timedelta(days=60)
        
        description = f"""🔔 接髮調整回訪提醒

👤 客戶：{customer_name}
📱 電話：{phone}
📅 上次服務：{original_appointment_date.strftime('%Y/%m/%d')}

💎 優惠方案：
- 接髮調整課程買4送1
- 單次 $5,000

📝 備註：{notes if notes else '請聯繫客戶確認預約時間'}
"""
        
        event = {
            'summary': f'【回訪提醒】{customer_name} - 接髮調整',
            'location': 'Hange韓哥接髮｜台北西門町',
            'description': description,
            'start': {
                'dateTime': adjustment_date.isoformat(),
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': (adjustment_date + timedelta(hours=2)).isoformat(),
                'timeZone': self.timezone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10080},  # 7天前
                    {'method': 'popup', 'minutes': 1440},   # 1天前
                ],
            },
        }
        
        try:
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            print(f'✅ 回訪提醒建立成功！')
            print(f'   客戶：{customer_name}')
            print(f'   提醒日期：{adjustment_date.strftime("%Y/%m/%d %H:%M")}')
            return event
            
        except HttpError as error:
            print(f'❌ 建立提醒失敗: {error}')
            return None


def main():
    """示範如何使用"""
    
    print('🎯 Hange 髮廊 Google Calendar 整合系統 (安全版本)')
    print('=' * 60)
    
    # 初始化 API
    try:
        calendar = HangeCalendarSecure()
    except Exception as e:
        print(f'\n❌ 初始化失敗: {e}')
        return
    
    # 查詢未來 7 天的預約
    print('\n【查詢預約】')
    calendar.list_upcoming_appointments(days=7)
    
    # 示範：建立新預約（已註解）
    print('\n【建立預約示範】（已註解）')
    print('取消下方註解即可建立測試預約：\n')
    
    # appointment_time = datetime.now() + timedelta(days=1)
    # appointment_time = appointment_time.replace(hour=14, minute=0, second=0, microsecond=0)
    # 
    # event = calendar.create_appointment(
    #     customer_name='測試客戶',
    #     phone='0912-345-678',
    #     service_type='圭環珠珠接點',
    #     start_time=appointment_time,
    #     duration_hours=2,
    #     notes='100束，首次諮詢'
    # )

if __name__ == '__main__':
    main()
