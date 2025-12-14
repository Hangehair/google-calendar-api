#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hange 髮廊智能預約系統
自動避開公休日（星期一、星期二）
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# Hange 髮廊營業設定
CLOSED_DAYS = [0, 1]  # 0=星期一, 1=星期二
OPEN_HOURS = {
    'start': 10,  # 早上10點
    'end': 20     # 晚上8點
}

def is_closed_day(date):
    """檢查是否為公休日"""
    return date.weekday() in CLOSED_DAYS

def get_day_name(weekday):
    """取得星期名稱"""
    days = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    return days[weekday]

def find_next_available_day(start_date=None, preferred_hour=14):
    """
    尋找下一個可用的預約時間（避開公休日）
    
    Args:
        start_date: 開始日期，預設為今天
        preferred_hour: 希望的時間（小時），預設下午2點
    
    Returns:
        datetime: 下一個可用的預約時間
    """
    if start_date is None:
        start_date = datetime.now()
    
    # 從明天開始找
    current_date = start_date + timedelta(days=1)
    
    # 最多找14天
    for _ in range(14):
        if not is_closed_day(current_date):
            # 找到了！設定時間
            available_time = current_date.replace(
                hour=preferred_hour, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            
            # 檢查是否在營業時間內
            if OPEN_HOURS['start'] <= preferred_hour < OPEN_HOURS['end']:
                return available_time
        
        current_date += timedelta(days=1)
    
    return None

def display_schedule_info():
    """顯示營業資訊"""
    print('📍 Hange韓哥接髮 | 台北西門町')
    print('=' * 60)
    print('\n📅 營業資訊：')
    print(f'   營業時間：{OPEN_HOURS["start"]}:00 - {OPEN_HOURS["end"]}:00')
    print(f'   公休日：星期一、星期二')
    print(f'   營業日：星期三至星期日')
    print('\n' + '=' * 60)

print('🎯 Hange 髮廊智能預約系統')
print('=' * 60)

# 顯示營業資訊
display_schedule_info()

# 檢查設定
print('\n🔍 檢查環境設定...')
calendar_id = os.getenv('CALENDAR_ID', 'winter81943@yahoo.com.tw')
print(f'✅ CALENDAR_ID: {calendar_id}')

if not os.path.exists('credentials.json'):
    print('\n❌ 找不到 credentials.json！')
    print('\n請先完成：')
    print('1. 將 credentials.json 放在專案根目錄')
    print('2. 在 Google Calendar 分享給：')
    print('   hangeapi@calendar-38de3.iam.gserviceaccount.com')
    exit(1)

print('\n🧮 智能選擇預約時間...')

# 尋找下一個可用時間
available_time = find_next_available_day(preferred_hour=14)  # 下午2點

if available_time:
    weekday = available_time.weekday()
    day_name = get_day_name(weekday)
    
    print(f'\n✅ 找到可用時間！')
    print('\n📅 預約資訊：')
    print(f'   日期：{available_time.strftime("%Y年%m月%d號")} ({day_name})')
    print(f'   時間：{available_time.strftime("%p %I:%M")} (下午2:00)')
    print(f'   服務：接髮諮詢')
    print(f'   時長：2小時')
    
    # 顯示未來7天的狀態
    print('\n📆 未來7天狀態：')
    print('-' * 60)
    for i in range(7):
        check_date = datetime.now() + timedelta(days=i+1)
        day_name = get_day_name(check_date.weekday())
        status = '❌ 公休' if is_closed_day(check_date) else '✅ 可預約'
        marker = ' ⭐ (建議選擇)' if check_date.date() == available_time.date() else ''
        print(f'   {check_date.strftime("%m/%d")} ({day_name})  {status}{marker}')
    print('-' * 60)
    
    print('\n🔗 連線 Google Calendar API...')
    
    try:
        from calendar_secure import HangeCalendarSecure
        
        # 初始化
        calendar = HangeCalendarSecure(calendar_id=calendar_id)
        
        print('✅ API 連線成功！')
        
        # 先查詢現有預約
        print('\n📅 查詢現有預約...')
        existing_events = calendar.list_upcoming_appointments(days=14)
        
        # 建立測試預約
        print('\n' + '=' * 60)
        print('📦 建立測試預約...')
        print('=' * 60)
        
        event = calendar.create_appointment(
            customer_name='測試客戶 - Hange韓哥',
            phone='0912-345-678',
            service_type='圭環珠珠接點諮詢',
            start_time=available_time,
            duration_hours=2,
            notes=f'智能預約測評 - 自動避開公休日 ({day_name})'
        )
        
        if event:
            print('\n🎉 預約建立成功！')
            print('\n✅ Google Calendar 預約資訊：')
            print(f'   • 標題：{event["summary"]}')
            print(f'   • 時間：{available_time.strftime("%Y/%m/%d (%a) %H:%M")}')
            print(f'   • 事件 ID：{event["id"]}')
            print(f'   • 連結：{event.get("htmlLink")}')
            
            # 建立 2 個月回訪提醒（也會避開公休日）
            print('\n🔔 建立 2 個月後的回訪提醒...')
            
            # 2個月後
            reminder_base = available_time + timedelta(days=60)
            # 如果是公休日，找下一個可用日
            if is_closed_day(reminder_base):
                reminder_time = find_next_available_day(reminder_base, preferred_hour=14)
            else:
                reminder_time = reminder_base
            
            reminder = calendar.create_adjustment_reminder(
                customer_name='測試客戶 - Hange韓哥',
                phone='0912-345-678',
                original_appointment_date=available_time,
                notes=f'首次接髮 2個月後調整 - 買4送1優惠'
            )
            
            if reminder:
                reminder_day = get_day_name(reminder_time.weekday())
                print(f'\n✅ 回訪提醒已設定！')
                print(f'   提醒日期：{reminder_time.strftime("%Y年%m月%d號")} ({reminder_day})')
            
            print('\n' + '=' * 60)
            print('\n✅ 所有測評都完成了！')
            print('\n【接下來請到 Google Calendar 查看】')
            print(f'   🔗 https://calendar.google.com')
            print('\n你會看到：')
            print(f'   1. {available_time.strftime("%m/%d")} ({day_name}) 14:00 - 【Hange預約】測試客戶')
            print(f'   2. {reminder_time.strftime("%m/%d")} ({get_day_name(reminder_time.weekday())}) 14:00 - 【回訪提醒】測試客戶')
            
            print('\n📧 如需刪除測誕預約：')
            print(f'   calendar.cancel_appointment("{event["id"]}")')
            
            print('\n【功能特點】')
            print('   ✅ 自動避開星期一、星期二公休日')
            print('   ✅ 自動尋找下一個可用時間')
            print('   ✅ 2個月回訪提醒也會避開公休日')
            print('   ✅ 適用於 LINE Bot 自動預約系統')
            
        else:
            print('\n❌ 預約建立失敗！')
            
    except ImportError as e:
        print(f'\n❌ 無法載入模組: {e}')
        print('\n請先安裝：')
        print('pip install -r requirements.txt')
        
    except Exception as e:
        print(f'\n❌ 發生錯誤: {e}')
        print('\n請檢查：')
        print('1. Google Calendar 已分享給：hangeapi@calendar-38de3.iam.gserviceaccount.com')
        print('2. CALENDAR_ID 正確: winter81943@yahoo.com.tw')
        print('3. credentials.json 檔案存在')
        
else:
    print('\n❌ 無法找到可用時間！')
    
print('\n' + '=' * 60)
