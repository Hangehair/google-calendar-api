# 🚀 Vercel 部署教學

完整的 Vercel 部署步驟，將 Google Calendar API 部署到雲端。

---

## 方法 1：直接從 GitHub 部署（最簡單！推薦）

### 步驟 1：前往 Vercel 網站

1. 開啟 [https://vercel.com](https://vercel.com)
2. 點擊 **Sign Up** 或 **Login**
3. 使用 **GitHub** 帳號登入

### 步驟 2：匯入 GitHub 專案

1. 登入後，點擊 **Add New...** → **Project**
2. 會看到你的 GitHub repositories
3. 找到 **`google-calendar-api`**
4. 點擊 **Import**

### 步驟 3：配置專案

**Configure Project 頁面：**

1. **Project Name**: `hange-calendar-api` (可自訂)
2. **Framework Preset**: `Other`
3. **Root Directory**: `./` (預設即可)
4. **Build Command**: 留空
5. **Output Directory**: 留空

### 步驟 4：設定環境變數（重要！）

在 **Environment Variables** 區塊，點擊 **Add** 並新增：

#### 變數 1: CALENDAR_ID
```
Key: CALENDAR_ID
Value: winter81943@yahoo.com.tw
```

#### 變數 2: TIMEZONE
```
Key: TIMEZONE
Value: Asia/Taipei
```

#### 變數 3: GOOGLE_CREDENTIALS_JSON

**這個比較複雜，需要將 credentials.json 轉成一行：**

**在電腦上執行：**

```bash
# 方法 A: 使用 Python
python -c "import json; print(json.dumps(json.load(open('credentials.json'))))"

# 方法 B: 使用線上工具
# 前往 https://www.cleancss.com/json-minify/
# 貼上 credentials.json 內容
# 點擊 "Minify"
# 複製結果
```

**然後在 Vercel 新增：**
```
Key: GOOGLE_CREDENTIALS_JSON
Value: {貼上上面的一行 JSON}
```

**重要！** 確保整個 JSON 是一行，並且包含所有內容。

### 步驟 5：部署

1. 設定完環境變數後，點擊 **Deploy**
2. 等待 1-2 分鐘
3. 看到 **Congratulations!** 就成功了！

### 步驟 6：獲取 API 網址

部署完成後，你會得到一個網址：

```
https://hange-calendar-api.vercel.app
```

你的 API 端點就是：
```
https://hange-calendar-api.vercel.app/api/booking
https://hange-calendar-api.vercel.app/api/check-availability
https://hange-calendar-api.vercel.app/api/health
```

---

## 方法 2：使用 Vercel CLI

### 步驟 1：安裝 Vercel CLI

```bash
# 在電腦上執行（需要先安裝 Node.js）
npm install -g vercel
```

### 步驟 2：登入 Vercel

```bash
vercel login
# 選擇 GitHub
# 在瀏覽器中授權
```

### 步驟 3：克隆專案

```bash
git clone https://github.com/Hangehair/google-calendar-api.git
cd google-calendar-api
```

### 步驟 4：部署

```bash
# 第一次部署
vercel

# 會問你幾個問題：
# Set up and deploy? Yes
# Which scope? 選擇你的帳號
# Link to existing project? No
# What's your project's name? hange-calendar-api
# In which directory is your code located? ./
# Want to modify these settings? No

# 部署成功後，會顯示 URL
```

### 步驟 5：設定環境變數

```bash
# 設定 CALENDAR_ID
vercel env add CALENDAR_ID
# 輸入: winter81943@yahoo.com.tw
# Environment: Production

# 設定 TIMEZONE
vercel env add TIMEZONE
# 輸入: Asia/Taipei
# Environment: Production

# 設定 GOOGLE_CREDENTIALS_JSON
vercel env add GOOGLE_CREDENTIALS_JSON
# 輸入: {一行 JSON}
# Environment: Production
```

### 步驟 6：重新部署

```bash
# 設定完環境變數後，需要重新部署
vercel --prod
```

---

## ✅ 測試部署

### 1. 測試健康檢查

```bash
curl https://YOUR-VERCEL-URL/api/health
```

**應該回傳：**
```json
{
  "status": "healthy",
  "calendar_connected": true,
  "timestamp": "2025-12-18T..."
}
```

### 2. 測試建立預約

```bash
curl -X POST https://YOUR-VERCEL-URL/api/booking \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試客戶",
    "phone": "0912-345-678",
    "date": "2025-12-20",
    "time": "14:00",
    "services": ["接髮"]
  }'
```

**成功回傳：**
```json
{
  "success": true,
  "message": "預約建立成功！...",
  "event_id": "...",
  "calendar_link": "https://..."
}
```

### 3. 檢查 Google Calendar

打開 [https://calendar.google.com](https://calendar.google.com)，切換到 `winter81943@yahoo.com.tw`，應該會看到測誕預約！

---

## 🔧 常見問題

### Q1: 部署失敗 - "Build Error"

**A:** 檢查：
1. `requirements.txt` 是否存在
2. `vercel.json` 是否存在
3. 查看 Vercel 部署 logs

### Q2: API 回傳 500 錯誤

**A:** 檢查環境變數：

```bash
# 查看 Vercel 環境變數
vercel env ls

# 或在 Vercel 網站上：
Settings → Environment Variables
```

確認：
- `CALENDAR_ID` 正確
- `GOOGLE_CREDENTIALS_JSON` 是完整的 JSON

### Q3: 如何查看 logs？

**在 Vercel 網站：**
1. 點擊你的專案
2. 點擊 "Deployments"
3. 點擊最新的部署
4. 點擊 "Functions" → 選擇 `api_booking.py`
5. 查看 logs

**使用 CLI：**
```bash
vercel logs
```

### Q4: 如何更新部署？

**方法 A：自動部署**
- 直接 push 到 GitHub
- Vercel 會自動重新部署

**方法 B：手動部署**
```bash
vercel --prod
```

### Q5: 如何刪除專案？

**在 Vercel 網站：**
1. 點擊專案
2. Settings → General
3. 滾動到最下方
4. 點擊 "Delete Project"

---

## 📧 更新環境變數

如果需要更新 `credentials.json`：

```bash
# 刪除舊的
vercel env rm GOOGLE_CREDENTIALS_JSON production

# 新增新的
vercel env add GOOGLE_CREDENTIALS_JSON
# 輸入新的 JSON

# 重新部署
vercel --prod
```

---

## ✅ 部署完成！

部署成功後，你的 API 就可以使用了！

**下一步：**
1. 將 API URL 更新到 HAN.BOT 前端
2. 測誕預約流程
3. 上線使用！

---

💇‍♀️ **Hange韓哥接髮 | 智能預約系統**
