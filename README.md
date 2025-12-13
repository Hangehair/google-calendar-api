# Google Calendar API 整合專案

這是專為 **Hange 髮廊**設計的 Google Calendar API 預約管理工具，支援手機操作設定！

## ✨ 功能特色

- ✅ 建立髮廊預約事件（接髮、縮毛矯正、染髮）
- ✅ 查詢即將到來的預約
- ✅ 自動提醒（前一天 + 1小時前）
- ✅ 2個月接髮調整回訪提醒
- ✅ 生日問候自動排程
- ✅ **手機也能輕鬆設定**

---

## 📱 手機設定步驟（超簡單！）

### 步驟 1：啟用 Google Calendar API

**在手機瀏覽器操作：**

1. 開啟 [Google Cloud Console](https://console.cloud.google.com/) （建議用 Chrome）
2. 點選左上角 **≡** 選單
3. 找到「**API 和服務**」→ 點選「**已啟用的 API 和服務**」
4. 點擊上方藍色按鈕「**+ 啟用 API 和服務**」
5. 搜尋「**Google Calendar API**」
6. 點擊進入後，按「**啟用**」按鈕

---

### 步驟 2：建立 OAuth 憑證（重要！）

**繼續在手機操作：**

1. 在 Google Cloud Console，點選左上角 **≡** 選單
2. 找到「**API 和服務**」→ 點選「**憑證**」
3. 點擊上方「**+ 建立憑證**」→ 選擇「**OAuth 用戶端 ID**」

#### ⚠️ 如果出現「需要設定 OAuth 同意畫面」：

4. 點擊「**設定同意畫面**」
5. 選擇「**外部**」→ 點擊「**建立**」
6. 填寫以下資訊：
   - **應用程式名稱**：Hange預約系統
   - **使用者支援電子郵件**：選擇你的 Gmail
   - **開發者聯絡資訊**：填入你的 Gmail
7. 點擊「**儲存並繼續**」（其他可跳過）
8. 一直點「**儲存並繼續**」直到完成

#### 繼續建立憑證：

9. 回到「**憑證**」頁面，再次點擊「**+ 建立憑證**」→「**OAuth 用戶端 ID**」
10. **應用程式類型**選擇「**電腦應用程式**」
11. **名稱**輸入：Hange Calendar App
12. 點擊「**建立**」

---

### 步驟 3：下載憑證檔案（手機版）

**📲 下載 credentials.json 的方法：**

建立完成後，畫面會跳出視窗顯示「已建立 OAuth 用戶端」：

#### 方法 A：直接下載（推薦）
1. 在彈出視窗中，點擊「**下載 JSON**」按鈕
2. 檔案會下載到你的手機（通常在「下載」資料夾）
3. 將檔案重新命名為 `credentials.json`

#### 方法 B：從憑證清單下載
1. 如果關閉了彈出視窗，回到「**憑證**」頁面
2. 在「OAuth 2.0 用戶端 ID」區塊，找到你剛建立的「Hange Calendar App」
3. 點擊右側的「**⋮**」（三個點）或「下載」圖示（向下箭頭）
4. 選擇「**下載 OAuth 用戶端**」或直接點擊下載圖示
5. 檔案會儲存為類似 `client_secret_xxx.json` 的名稱
6. 將檔案重新命名為 `credentials.json`

#### 方法 C：用電腦操作（最簡單）
如果手機操作困難，可以：
1. 用電腦開啟 [Google Cloud Console](https://console.cloud.google.com/)
2. 進入「API 和服務」→「憑證」
3. 找到你的 OAuth 用戶端 ID
4. 點擊右側的 **⬇️ 下載圖示**
5. 重新命名為 `credentials.json`
6. 上傳到你的專案資料夾

---

## 💻 安裝與使用

### 1. 克隆專案

```bash
git clone https://github.com/Hangehair/google-calendar-api.git
cd google-calendar-api
```

### 2. 安裝套件

```bash
pip install -r requirements.txt
```

### 3. 放置憑證檔案

將你下載的 `credentials.json` 放在專案根目錄。

### 4. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env` 檔案：

```env
CALENDAR_ID=你的Gmail帳號@gmail.com
TIMEZONE=Asia/Taipei
```

### 5. 第一次執行（授權）

```bash
python calendar_api.py
```

**第一次執行時：**
- 會自動開啟瀏覽器要求授權
- 選擇你的 Google 帳號
- 點擊「允許」
- 授權完成後會生成 `token.json`（之後不需再授權）

---

## 🎯 Hange 髮廊專用功能

### 範例 1：建立接髮預約

```python
from calendar_api import GoogleCalendarAPI
import datetime

calendar = GoogleCalendarAPI()

# 接髮諮詢預約
start = datetime.datetime(2025, 12, 20, 14, 0)  # 2025/12/20 下午2點
end = start + datetime.timedelta(hours=2)

calendar.create_event(
    summary='接髮諮詢 - 王小姐',
    start_time=start,
    end_time=end,
    description='服務：圭環珠珠接點\n髮量：100束\n價格：$15,000\n備註：專屬解決方案',
    location='Hange韓哥接髮｜台北西門町',
    attendees=['customer@example.com']  # 可選：客戶email
)
```

### 範例 2：查詢本週預約

```python
# 列出未來7天的預約
events = calendar.list_upcoming_events(max_results=10)

for event in events:
    print(f"預約：{event['summary']}")
    print(f"時間：{event['start']['dateTime']}")
```

### 範例 3：2個月接髮調整提醒

```python
# 在建立接髮預約時，同時建立2個月後的調整提醒
adjustment_date = start + datetime.timedelta(days=60)

calendar.create_event(
    summary='【回訪提醒】王小姐 - 接髮調整',
    start_time=adjustment_date,
    end_time=adjustment_date + datetime.timedelta(hours=2),
    description='接髮調整課程買4送1優惠\n單次 $5,000\n提醒客戶預約調整'
)
```

---

## 🔧 API 功能說明

### `create_event()` - 建立預約

```python
event = calendar.create_event(
    summary='預約標題',        # 必填
    start_time=開始時間,       # datetime 物件
    end_time=結束時間,         # datetime 物件
    description='預約詳情',    # 可選
    location='地點',           # 可選
    attendees=['email@xxx.com'] # 可選：參與者email列表
)
```

### `list_upcoming_events()` - 查詢預約

```python
events = calendar.list_upcoming_events(max_results=10)
# 回傳即將到來的預約列表
```

### `update_event()` - 修改預約

```python
calendar.update_event(
    event_id='事件ID',
    summary='新標題',
    description='新內容'
)
```

### `delete_event()` - 取消預約

```python
calendar.delete_event(event_id='事件ID')
```

---

## 💡 與 LINE 整合建議

### 1. 自動預約流程

```
客戶在 LINE 預約 
    ↓
觸發 calendar_api.py
    ↓
Google Calendar 建立事件
    ↓
LINE 回傳預約確認
```

### 2. 2個月回訪提醒

使用 Google Apps Script 或排程工具：
- 每天檢查2個月前的接髮預約
- 自動發送 LINE Flex Message 提醒調整
- 附上「買4送1」優惠資訊

### 3. 生日問候

將客戶生日存入 Calendar：
- 生日當天自動發送 LINE 祝福
- 附上專屬生日優惠

---

## ❓ 常見問題

### Q1: 手機下載的憑證檔名不是 credentials.json？

**A:** 下載的檔案通常叫 `client_secret_xxxxx.json`，請手動重新命名為 `credentials.json`。

### Q2: 第一次執行出現「檔案不存在」錯誤？

**A:** 確認 `credentials.json` 是否放在與 `calendar_api.py` 同一個資料夾。

### Q3: 授權後出現「Access denied」？

**A:** 回到 Google Cloud Console → API 和服務 → OAuth 同意畫面 → 新增測試使用者（輸入你的 Gmail）。

### Q4: token.json 過期怎麼辦？

**A:** 刪除 `token.json` 檔案，重新執行程式即可重新授權。

### Q5: 如何在多台電腦使用？

**A:** 複製 `credentials.json` 和 `token.json` 到新電腦即可。

---

## 🔒 安全注意事項

1. **不要公開分享**：
   - `credentials.json` - OAuth 憑證
   - `token.json` - 授權 token
   - `.env` - 環境變數

2. **已加入 .gitignore**：
   這些敏感檔案不會被上傳到 GitHub

3. **備份建議**：
   將 `credentials.json` 存放在安全的地方（如雲端硬碟私人資料夾）

---

## 📞 技術支援

遇到問題？歡迎聯絡：

- GitHub Issues: [提交問題](https://github.com/Hangehair/google-calendar-api/issues)
- LINE: @hangehair
- Email: hangehair@example.com

---

## 📄 授權

MIT License

---

💇‍♀️ **Hange韓哥接髮 | 台北西門町 | 接髮專家 | 專屬解決方案**

🌟 圭環珠珠接點 | 極致線綁 | 頭皮養護 | 質感染髮
