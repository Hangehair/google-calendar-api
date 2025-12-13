#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Calendar API 整合工具 (服務帳戶版本)
用於 Hange 髮廊的預約管理系統
無需每次手動授權，適合自動化使用
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 服務帳戶憑證檔案路徑
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']

class HangeCalendarAPI:
    """Hange 髮廊專用 Google Calendar API 管理類別"""
    
    def __init__(self, calendar_id=None):
        """
        初始化 Calendar API
        
        Args:
            calendar_id (str): Google Calendar ID (通常是 Gmail 地址)
                              如果不提供，會從 .env 讀取
        """
        self.calendar_id = calendar_id or os.getenv('CALENDAR_ID', 'primary')
        self.timezone = os.getenv('TIMEZONE', 'Asia/Taipei')
        self.service = self._authenticate()
    
    def _authenticate(self):
        """使用服務帳戶驗證 Google Calendar API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            print(f'❌ 驗證失敗: {e}')
            print('\n請確認：')
            print('1. credentials.json 檔案存在')
            print('2. 已將行事曆分享給服務帳戶 email')
            print(f'   服務帳戶 email: {self._get_service_account_email()}')
            raise
    
    def _get_service_account_email(self):
        """取得服務帳戶 email"""
        try:
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                data = json.load(f)
                return data.get('client_email', '未知')
        except:
            return '無法讀取'
    
    def create_appointment(self, customer_name, phone, service_type, 
                          start_time, duration_hours=2, notes='', 
                          customer_email=None):
        """
        建立 Hange 髮廊預約
        
        Args:
            customer_name (str): 客戶姓名
            phone (str): 客戶電話
            service_type (str): 服務類型（接髮/縮毛矯正/染髮等）
            start_time (datetime): 預約時間
            duration_hours (float): 預約時長（小時）
            notes (str): 額外備註
            customer_email (str): 客戶 email（可選，用於發送通知）
        
        Returns:
            dict: 建立的事件資訊
        """
        end_time = start_time + timedelta(hours=duration_hours)
        
        # 建構事件描述
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
        
        # 如果有客戶 email，加入參與者
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
        """
        列出即將到來的預約
        
        Args:
            days (int): 查詢未來幾天的預約
            max_results (int): 最多顯示幾個預約
        
        Returns:
            list: 預約事件列表
        """
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
                # 將 ISO 格式轉換為易讀格式
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
        """
        建立 2 個月後的接髮調整回訪提醒
        
        Args:
            customer_name (str): 客戶姓名
            phone (str): 客戶電話
            original_appointment_date (datetime): 原始預約日期
            notes (str): 額外備註
        
        Returns:
            dict: 建立的提醒事件
        """
        # 2個月後的同一時間
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
    
    def update_appointment(self, event_id, **kwargs):
        """
        更新預約資訊
        
        Args:
            event_id (str): 事件 ID
            **kwargs: 要更新的欄位（summary, description, start_time, end_time）
        
        Returns:
            dict: 更新後的事件
        """
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # 更新欄位
            if 'summary' in kwargs:
                event['summary'] = kwargs['summary']
            if 'description' in kwargs:
                event['description'] = kwargs['description']
            if 'start_time' in kwargs:
                event['start']['dateTime'] = kwargs['start_time'].isoformat()
            if 'end_time' in kwargs:
                event['end']['dateTime'] = kwargs['end_time'].isoformat()
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            print(f'✅ 預約已更新')
            return updated_event
            
        except HttpError as error:
            print(f'❌ 更新預約失敗: {error}')
            return None
    
    def cancel_appointment(self, event_id):
        """
        取消預約
        
        Args:
            event_id (str): 事件 ID
        
        Returns:
            bool: 是否成功取消
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            print('✅ 預約已取消')
            return True
            
        except HttpError as error:
            print(f'❌ 取消預約失敗: {error}')
            return False


def main():
    """示範如何使用 Hange Calendar API"""
    
    print('🎯 Hange 髮廊 Google Calendar 整合系統')
    print('=' * 60)
    
    # 初始化 API
    calendar = HangeCalendarAPI()
    
    # 顯示服務帳戶資訊
    print(f'\n📧 服務帳戶: {calendar._get_service_account_email()}')
    print(f'📅 行事曆 ID: {calendar.calendar_id}')
    print('\n⚠️  請確認已將行事曆分享給上述服務帳戶 email！\n')
    
    # 示範：查詢未來 7 天的預約
    print('\n【查詢預約】')
    calendar.list_upcoming_appointments(days=7)
    
    # 示範：建立新預約（已註解，取消註解即可使用）
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
    # 
    # # 同時建立 2 個月後的回訪提醒
    # if event:
    #     calendar.create_adjustment_reminder(
    #         customer_name='測試客戶',
    #         phone='0912-345-678',
    #         original_appointment_date=appointment_time
    #     )

if __name__ == '__main__':
    main()
