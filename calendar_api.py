#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Calendar API 整合工具
用於 Hange 髮廊的預約管理系統
"""

import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 如果修改這些範圍，請刪除 token.json 檔案
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarAPI:
    """Google Calendar API 管理類別"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.calendar_id = os.getenv('CALENDAR_ID', 'primary')
        self.timezone = os.getenv('TIMEZONE', 'Asia/Taipei')
        self._authenticate()
    
    def _authenticate(self):
        """驗證 Google Calendar API"""
        # token.json 儲存使用者的存取和更新 token
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # 如果沒有有效的憑證，讓使用者登入
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # 儲存憑證供下次使用
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def create_event(self, summary, start_time, end_time, description='', 
                     attendees=None, location=''):
        """建立行事曆事件
        
        Args:
            summary (str): 事件標題
            start_time (datetime): 開始時間
            end_time (datetime): 結束時間
            description (str): 事件描述
            attendees (list): 參與者 email 列表
            location (str): 地點
        
        Returns:
            dict: 建立的事件資訊
        """
        try:
            event = {
                'summary': summary,
                'location': location,
                'description': description,
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
                        {'method': 'popup', 'minutes': 24 * 60},  # 1天前
                        {'method': 'popup', 'minutes': 60},        # 1小時前
                    ],
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendUpdates='all'  # 發送通知給所有參與者
            ).execute()
            
            print(f'事件已建立: {event.get("htmlLink")}')
            return event
            
        except HttpError as error:
            print(f'發生錯誤: {error}')
            return None
    
    def list_upcoming_events(self, max_results=10):
        """列出即將到來的事件
        
        Args:
            max_results (int): 最多顯示幾個事件
        
        Returns:
            list: 事件列表
        """
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            print(f'\n即將到來的 {max_results} 個預約:')
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                print('沒有即將到來的預約。')
                return []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"{start} - {event['summary']}")
            
            return events
            
        except HttpError as error:
            print(f'發生錯誤: {error}')
            return []
    
    def update_event(self, event_id, **kwargs):
        """更新事件
        
        Args:
            event_id (str): 事件 ID
            **kwargs: 要更新的欄位
        
        Returns:
            dict: 更新後的事件
        """
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # 更新提供的欄位
            for key, value in kwargs.items():
                if key in ['summary', 'location', 'description']:
                    event[key] = value
                elif key in ['start_time', 'end_time']:
                    time_key = 'start' if key == 'start_time' else 'end'
                    event[time_key]['dateTime'] = value.isoformat()
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            print(f'事件已更新: {updated_event.get("htmlLink")}')
            return updated_event
            
        except HttpError as error:
            print(f'發生錯誤: {error}')
            return None
    
    def delete_event(self, event_id):
        """刪除事件
        
        Args:
            event_id (str): 事件 ID
        
        Returns:
            bool: 是否成功刪除
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            print('事件已刪除')
            return True
            
        except HttpError as error:
            print(f'發生錯誤: {error}')
            return False

def main():
    """主程式 - 示範如何使用"""
    # 初始化 Calendar API
    calendar = GoogleCalendarAPI()
    
    # 列出即將到來的預約
    calendar.list_upcoming_events()
    
    # 建立新預約範例
    # start = datetime.datetime.now() + datetime.timedelta(days=1)
    # end = start + datetime.timedelta(hours=2)
    # 
    # calendar.create_event(
    #     summary='接髮諮詢 - 王小姐',
    #     start_time=start,
    #     end_time=end,
    #     description='圭環珠珠接點，100束',
    #     location='台北市萬華區西門町',
    #     attendees=['customer@example.com']
    # )

if __name__ == '__main__':
    main()
