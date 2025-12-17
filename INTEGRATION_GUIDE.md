# 🤝 HAN.BOT + Google Calendar 整合指南

這份指南教你如何將你的 **HAN.BOT** (線上預約系統) 與 **Google Calendar API** 整合，實現預約自動同步。

---

## 🎯 整合目標

### 現有功能（HAN.BOT）
- ✅ LINE LIFF 線上預約表單
- ✅ 公休日檢查（星期一、二）
- ✅ 預約時段選擇（12:30-18:00）
- ✅ Flex Message 預約確認

### 新增功能（Google Calendar）
- 🆕 **自動同步預約**到 Google Calendar
- 🆕 **檢查時段可用性**（避免重複預約）
- 🆕 **2個月自動回訪提醒**（接髮服務）
- 🆕 **韓哥可在 Google Calendar 查看所有預約**

---

## 🛠️ 整合架構

```
客戶 (LINE) 
    ↓
    點擊「立即預約」
    ↓
HAN.BOT (LIFF 頁面)
    ↓
    填寫預約表單
    ↓
    提交預約
    ↓
後端 API (api_booking.py) ←←← 你要部署這個！
    │
    ├─ 檢查公休日
    ├─ 檢查時段可用
    ├─ 建立 Google Calendar 預約
    └─ 建立 2 個月回訪提醒
    ↓
Google Calendar 
    ↓
韓哥看到預約！ 🎉
```

---

## 🚀 快速整合（5步驟）

### 步驟 1：部署 API 後端

#### 選項 A：使用 Vercel（推薦）

```bash
# 1. 安裝 Vercel CLI
npm install -g vercel

# 2. 克隆專案
git clone https://github.com/Hangehair/google-calendar-api.git
cd google-calendar-api

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 部署到 Vercel
vercel --prod

# 5. 設定環境變數
vercel env add CALENDAR_ID
# 輸入: winter81943@yahoo.com.tw

vercel env add GOOGLE_CREDENTIALS_JSON
# 輸入: 完整的 credentials.json 內容（一行）
```

#### 選項 B：使用 Heroku

```bash
# 1. 安裝 Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# 2. 登入並建立 App
heroku login
heroku create hange-booking-api

# 3. 設定環境變數
heroku config:set CALENDAR_ID=winter81943@yahoo.com.tw
heroku config:set GOOGLE_CREDENTIALS_JSON='...'

# 4. 部署
git push heroku main
```

---

### 步驟 2：更新 HAN.BOT 前端

在你的 `han.bot/index.html` 中，找到這段程式碼：

```javascript
// 找到 form submit 事件
document.getElementById('bookingForm').addEventListener('submit', e => {
  e.preventDefault();
  // ... 原始程式碼
});
```

**替換為：**

```javascript
document.getElementById('bookingForm').addEventListener('submit', async e => {
  e.preventDefault();
  
  const name = document.getElementById('name').value.trim();
  const phone = document.getElementById('phone').value.trim();
  const date = document.getElementById('date').value;
  const time = document.getElementById('time').value;
  const services = Array.from(sel);
  
  if (!services.length) return alert('請選擇至少一項服務！');
  
  // ⭐ 先呼叫 API 同步到 Google Calendar
  try {
    const response = await fetch('https://YOUR-API-URL/api/booking', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, phone, date, time, services })
    });
    
    const result = await response.json();
    
    if (!result.success) {
      alert(result.message);
      return;
    }
    
    // Google Calendar 預約建立成功，繼續發送 LINE 訊息
    
  } catch (error) {
    console.error('API 錯誤:', error);
    alert('預約系統發生錯誤，請直接聯繫韓哥！');
    return;
  }
  
  // 原始的 Flex Message 發送邏輯...
  const servicesStr = services.join(', ');
  const flexMessage = { /* ... 保持原樣 ... */ };
  
  liff.sendMessages([flexMessage])
    .then(() => {
      alert('預約成功！已同步到 Google Calendar');
      liff.closeWindow();
    });
});
```

**重要！** 將 `YOUR-API-URL` 替換為你的 Vercel/Heroku URL。

---

### 步驟 3：添加時段可用性檢查

在時間選擇器中，當用戶選擇時間時，即時檢查是否可用：

```javascript
const timeSelect = document.getElementById('time');
const dateInput = document.getElementById('date');

timeSelect.addEventListener('change', async function() {
  const date = dateInput.value;
  const time = this.value;
  
  if (!date || !time) return;
  
  // 檢查時段可用性
  try {
    const response = await fetch('https://YOUR-API-URL/api/check-availability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, time })
    });
    
    const result = await response.json();
    
    if (!result.available) {
      alert(`⚠️ ${result.message}，請選擇其他時間！`);
      this.value = '';
    } else {
      // 顯示可用標記
      this.style.borderColor = 'green';
    }
  } catch (error) {
    console.error('檢查錯誤:', error);
  }
});
```

---

### 步驟 4：測試整合

```bash
# 1. 測試 API 健康檢查
curl https://YOUR-API-URL/api/health

# 應該回傳：
# {"status":"healthy","calendar_connected":true,...}

# 2. 測誕建立預約
curl -X POST https://YOUR-API-URL/api/booking \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試客戶",
    "phone": "0912-345-678",
    "date": "2025-12-20",
    "time": "14:00",
    "services": ["接髮"]
  }'

# 檢查 Google Calendar 是否出現預約！
```

---

### 步驟 5：上線使用

1. 將更新後的 `index.html` 上傳到 `han.bot` repository
2. 通知客戶可以開始使用線上預約
3. 韓哥在 Google Calendar 即時查看預約！

---

## 💡 進階功能

### 自動發送提醒 (Google Apps Script)

在 Google Calendar 中設定自動提醒：

```javascript
// Google Apps Script
function sendReminders() {
  const calendar = CalendarApp.getCalendarById('winter81943@yahoo.com.tw');
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  const events = calendar.getEventsForDay(tomorrow);
  
  events.forEach(event => {
    const description = event.getDescription();
    const phone = description.match(/電話：(\d+-\d+-\d+)/)?.[1];
    
    if (phone) {
      // 發送 LINE 提醒訊息
      sendLineMessage(phone, `提醒：明天 ${event.getTitle()}`);
    }
  });
}
```

---

## ❓ 常見問題

### Q1: API 部署後無法連線 Google Calendar？

**A:** 檢查環境變數：
```bash
vercel env ls  # 查看 Vercel 環境變數
heroku config  # 查看 Heroku 環境變數
```

確認設定：
- `CALENDAR_ID=winter81943@yahoo.com.tw`
- `GOOGLE_CREDENTIALS_JSON=...（完整JSON）`

### Q2: 客戶預約後沒出現在 Google Calendar？

**A:** 檢查：
1. API 是否回傳 `success: true`
2. Google Calendar 分享設定是否正確
3. 查看 API logs：`vercel logs` 或 `heroku logs`

### Q3: 如何測試不影響生產環境？

**A:** 建立測評環境：
1. 建立測誕用的 Google Calendar
2. 設定 `CALENDAR_ID=test-calendar@gmail.com`
3. 測誕完成後再切換到生產環境

---

## 📞 需要協助？

如果整合過程中遇到問題，歡迎：
- 在 GitHub 提交 Issue
- 聯繫技術支援

---

💇‍♀️ **Hange韓哥接髮 | 台北西門町 | 智能預約系統**
