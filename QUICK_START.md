# 🚀 Hange 髮廊 Google Calendar 快速上手

恭喜你！你已經下載了**服務帳戶憑證** `credentials.json`。  
這個版本**不需要每次手動授權**，非常適合自動化使用！

---

## ✅ 你已完成的步驟

- [x] 建立 Google Cloud 專案
- [x] 啟用 Google Calendar API
- [x] 建立服務帳戶
- [x] 下載 `credentials.json`

---

## 📝 最後一步：分享行事曆給服務帳戶

### 重要！必須執行這一步：

你的服務帳戶 email 是：
```
hangeapi@calendar-38de3.iam.gserviceaccount.com
```

### 在手機上操作：

1. 開啟 **Google Calendar** App
2. 點擊左上角 **≡** 選單
3. 點選你要使用的行事曆（通常是主要行事曆）
4. 點擊行事曆名稱右側的 **⋮** （三個點）
5. 選擇「**設定和分享**」
6. 點擊「**與特定人員分享**」
7. 輸入 email：`hangeapi@calendar-38de3.iam.gserviceaccount.com`
8. 權限選擇「**管理變更事件**」或「**建立事件**」
9. 點擊「**傳送**」

### 在電腦上操作：

1. 開啟 [Google Calendar](https://calendar.google.com/)
2. 在左側找到你要使用的行事曆
3. 點擊行事曆名稱旁的 **⋮** → 選擇「**設定和分享**」
4. 在「與特定人員分享」區塊，點擊「**+ 新增人員**」
5. 輸入：`hangeapi@calendar-38de3.iam.gserviceaccount.com`
6. 權限選擇「**管理變更事件**」
7. 點擊「**傳送**」

---

## 💻 安裝與使用

### 1. 下載專案

```bash
git clone https://github.com/Hangehair/google-calendar-api.git
cd google-calendar-api
```

### 2. 放置 credentials.json

將你上傳的 `credentials.json` 放在專案根目錄：

```
google-calendar-api/
├── credentials.json  ← 放這裡！
├── service_account_calendar.py
├── requirements.txt
└── .env.example
```

### 3. 安裝 Python 套件

```bash
pip install -r requirements.txt
```

### 4. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env` 檔案：

```env
# 你的 Gmail 地址（行事曆 ID）
CALENDAR_ID=你的Gmail@gmail.com

# 時區
TIMEZONE=Asia/Taipei
```

---

## 🎯 立即測試！

### 第一次執行

```bash
python service_account_calendar.py
```

**成功的話會看到：**
```
🎯 Hange 髮廊 Google Calendar 整合系統
============================================================

📧 服務帳戶: hangeapi@calendar-38de3.iam.gserviceaccount.com
📅 行事曆 ID: 你的Gmail@gmail.com

⚠️  請確認已將行事曆分享給上述服務帳戶 email！

【查詢預約】
📅 未來 7 天的預約（共 0 個）：
============================================================
```

---

## 📝 實用範例

### 範例 1：建立接髮預約

```python
from service_account_calendar import HangeCalendarAPI
from datetime import datetime, timedelta

# 初始化
calendar = HangeCalendarAPI()

# 建立明天下午2點的預約
tomorrow = datetime.now() + timedelta(days=1)
appointment_time = tomorrow.replace(hour=14, minute=0, second=0)

# 建立預約
event = calendar.create_appointment(
    customer_name='陳小姐',
    phone='0912-345-678',
    service_type='圭環珠珠接點',
    start_time=appointment_time,
    duration_hours=2,
    notes='100束，首次諮詢',
    customer_email='customer@example.com'  # 可選
)

print(f'✅ 預約 ID: {event["id"]}')
```

### 範例 2：同時建立 2 個月回訪提醒

```python
# 建立預約
event = calendar.create_appointment(
    customer_name='王小姐',
    phone='0912-345-678',
    service_type='圭環珠珠接點',
    start_time=appointment_time,
    duration_hours=3
)

# 同時建立 2 個月後的調整提醒
if event:
    calendar.create_adjustment_reminder(
        customer_name='王小姐',
        phone='0912-345-678',
        original_appointment_date=appointment_time,
        notes='首次接髮 100 束'
    )
```

### 範例 3：查詢本週預約

```python
# 查詢未來 7 天的預約
events = calendar.list_upcoming_appointments(days=7)

# 查詢未來 30 天的預約
events = calendar.list_upcoming_appointments(days=30, max_results=100)
```

### 範例 4：修改預約

```python
# 假設你有事件 ID
event_id = 'abc123xyz'

calendar.update_appointment(
    event_id=event_id,
    summary='【Hange預約】陳小姐 - 接髮調整',
    description='更改為調整服務'
)
```

### 範例 5：取消預約

```python
calendar.cancel_appointment(event_id='abc123xyz')
```

---

## 🔧 与 LINE Bot 整合

### LINE 預約流程範例

```python
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from service_account_calendar import HangeCalendarAPI
from datetime import datetime

# 初始化
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
calendar = HangeCalendarAPI()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 假設用戶輸入：預約 陳小姐 0912345678 接髮 2025/12/20 14:00
    text = event.message.text
    
    if text.startswith('預約'):
        # 解析預約資訊
        parts = text.split()
        customer_name = parts[1]
        phone = parts[2]
        service_type = parts[3]
        date_str = parts[4]
        time_str = parts[5]
        
        # 建立預約
        appointment_time = datetime.strptime(f'{date_str} {time_str}', '%Y/%m/%d %H:%M')
        event = calendar.create_appointment(
            customer_name=customer_name,
            phone=phone,
            service_type=service_type,
            start_time=appointment_time,
            duration_hours=2
        )
        
        # 回傳確認訊息
        if event:
            reply_text = f"""✅ 預約完成！

👤 客戶：{customer_name}
📱 電話：{phone}
💇 服務：{service_type}
📅 時間：{date_str} {time_str}
📍 地點：Hange韓哥接髮｜台北西門町

我們會在服務前一天提醒您！❤️
"""
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
```

---

## ❓ 常見問題

### Q1: 出現 "Access denied" 錯誤？

**A:** 表示你還沒有分享行事曆給服務帳戶。  
請回到上方「分享行事曆」段落，將行事曆分享給：
```
hangeapi@calendar-38de3.iam.gserviceaccount.com
```

### Q2: 如何知道我的行事曆 ID？

**A:** 通常是你的 Gmail 地址，例如：`youremail@gmail.com`  
如果使用主要行事曆，可以在 `.env` 中設定 `CALENDAR_ID=primary`

### Q3: 可以在手機上執行嗎？

**A:** Python 程式需要在電腦或伺服器上執行。  
但你可以：
- 用電腦部署好
- 整合至 LINE Bot
- 手機就能透過 LINE 使用

### Q4: credentials.json 會過期嗎？

**A:** 不會！服務帳戶憑證沒有過期問題，只要不刪除就能一直使用。

### Q5: 安全嗎？

**A:** 服務帳戶只能存取你分享給它的行事曆，不會存取其他 Google 服務。  
但請**不要公開分享** `credentials.json` 檔案！

---

## 🎉 下一步

現在你已經可以：

1. ✅ 建立髮廊預約
2. ✅ 查詢預約清單
3. ✅ 自動 2 個月回訪提醒
4. ✅ 整合 LINE Bot 自動預約

### 進階功能建議：

- 🎂 生日問候自動化
- 📧 48小時前自動提醒
- 📊 預約統計分析
- 💰 營收記錄整合

需要協助實作任何功能，歡迎隨時聯繫！

---

💇‍♀️ **Hange韓哥接髮 | 台北西門町 | 接髮專家**
