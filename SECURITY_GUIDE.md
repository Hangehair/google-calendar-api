# 🔒 安全指南：使用環境變數管理憑證

這份指南教你如何安全地存儲和使用 Google 服務帳戶憑證，而不需要上傳敏感資訊到 GitHub。

---

## 為什麼要使用環境變數？

### ❌ 錯誤做法：直接上傳 credentials.json

```
✗ 上傳到 GitHub → 任何人都能看到你的私鑰
✗ 密碼寫在程式碼裡 → 無法在不同環境使用
✗ 分享給團隊成員 → 難以撤銷許可權
```

### ✅ 正確做法：使用環境變數

```
✓ 程式碼可以安全上傳到 GitHub
✓ 每個環境可以使用不同的憑證
✓ 容易更新或撤銷許可權
✓ 符合安全最佳實踐
```

---

## 🛠️ 三種設定方式

### 方法 1：完整 JSON（推薦用於雲端部署）

**適用於**：Docker, Heroku, Vercel, 雲端伺服器

#### 步驟 1：將 credentials.json 轉為一行

使用以下 Python 程式：

```python
import json

# 讀取 credentials.json
with open('credentials.json', 'r') as f:
    data = json.load(f)

# 轉為一行 JSON
one_line = json.dumps(data)
print(one_line)
```

或使用線上工具：[JSON Minify](https://www.cleancss.com/json-minify/)

#### 步驟 2：設定環境變數

在 `.env` 檔案中：

```bash
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"calendar-38de3","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvgIB...\n-----END PRIVATE KEY-----\n","client_email":"hangeapi@calendar-38de3.iam.gserviceaccount.com"}'
```

**注意：**
- 整個 JSON 用單引號 `'` 包裹
- JSON 內部用雙引號 `"`
- 換行符保持為 `\n`

---

### 方法 2：個別變數（推薦用於 GitHub Actions）

**適用於**：GitHub Actions, GitLab CI, 容易管理的場合

#### 將 credentials.json 拆分為個別變數

從你的 `credentials.json` 取得以下資訊：

```json
{
  "project_id": "calendar-38de3",
  "client_email": "hangeapi@calendar-38de3.iam.gserviceaccount.com",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADA...\n-----END PRIVATE KEY-----\n"
}
```

在 `.env` 檔案中：

```bash
GOOGLE_PROJECT_ID=calendar-38de3
GOOGLE_CLIENT_EMAIL=hangeapi@calendar-38de3.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQ...\\n-----END PRIVATE KEY-----\\n"
```

**重要！私鑰處理：**
- 私鑰用雙引號 `"` 包裹
- 換行符要使用 `\\n`（雙反斜線）

---

### 方法 3：本地檔案（推薦用於本地開發）

**適用於**：本地電腦開發測試

#### 直接使用 credentials.json

1. 將 `credentials.json` 放在專案根目錄
2. `.gitignore` 已設定不會上傳
3. 直接執行 `python calendar_secure.py`

**優點：**
- 最簡單的方式
- 不需設定環境變數

**缺點：**
- 只能本地使用
- 無法部署到雲端

---

## 💻 實際操作教學

### 情境 A：本地開發測試

```bash
# 1. 克隆專案
git clone https://github.com/Hangehair/google-calendar-api.git
cd google-calendar-api

# 2. 安裝套件
pip install -r requirements.txt

# 3. 放置 credentials.json
# 將你下載的 credentials.json 放在這裡

# 4. 設定 .env
cp .env.example .env
# 編輯 .env，填入 CALENDAR_ID

# 5. 執行
python calendar_secure.py
```

---

### 情境 B：雲端部署（Heroku 範例）

```bash
# 1. 將 credentials.json 轉為一行
python -c "import json; print(json.dumps(json.load(open('credentials.json'))))"

# 2. 設定 Heroku 環境變數
heroku config:set GOOGLE_CREDENTIALS_JSON='複製上一步的輸出'
heroku config:set CALENDAR_ID='your-email@gmail.com'
heroku config:set TIMEZONE='Asia/Taipei'

# 3. 部署
git push heroku main
```

---

### 情境 C：GitHub Actions 自動化

#### 步驟 1：設定 GitHub Secrets

1. 前往 GitHub repository
2. Settings → Secrets and variables → Actions
3. 點擊 "New repository secret"
4. 新增以下 secrets：

```
GOOGLE_PROJECT_ID = calendar-38de3
GOOGLE_CLIENT_EMAIL = hangeapi@calendar-38de3.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY = -----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgk...
-----END PRIVATE KEY-----

CALENDAR_ID = your-email@gmail.com
```

#### 步驟 2：建立 workflow

建立 `.github/workflows/calendar.yml`：

```yaml
name: Update Calendar

on:
  schedule:
    - cron: '0 9 * * *'  # 每天早上9點
  workflow_dispatch:  # 手動觸發

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run calendar script
        env:
          GOOGLE_PROJECT_ID: ${{ secrets.GOOGLE_PROJECT_ID }}
          GOOGLE_CLIENT_EMAIL: ${{ secrets.GOOGLE_CLIENT_EMAIL }}
          GOOGLE_PRIVATE_KEY: ${{ secrets.GOOGLE_PRIVATE_KEY }}
          CALENDAR_ID: ${{ secrets.CALENDAR_ID }}
          TIMEZONE: Asia/Taipei
        run: python calendar_secure.py
```

---

## 🛡️ 安全檢查清單

### ✅ 必做項目

- [ ] `.gitignore` 包含 `credentials.json`
- [ ] `.gitignore` 包含 `.env`
- [ ] 不要將 `.env` 上傳到 GitHub
- [ ] 不要在程式碼中寫死私鑰
- [ ] 定期檢查 Google Cloud 服務帳戶活動

### ❌ 禁止項目

- [ ] 不要透過 email 傳送憑證
- [ ] 不要透過 LINE/Messenger 傳送憑證
- [ ] 不要將憑證上傳到公開的雲端空間
- [ ] 不要在截圖中包含私鑰

---

## ❓ 常見問題

### Q1: 為什麼私鑰中的 `\n` 要改成 `\\n`？

**A:** 在 `.env` 檔案中，`\n` 會被識別為真正的換行。但 Google API 需要字面上的 `\n` 字串，所以要使用 `\\n`（脱逸反斜線）。

### Q2: 如何確認環境變數有正確設定？

**A:** 執行以下程式測試：

```python
import os
from dotenv import load_dotenv

load_dotenv()

print("CALENDAR_ID:", os.getenv('CALENDAR_ID'))
print("GOOGLE_PROJECT_ID:", os.getenv('GOOGLE_PROJECT_ID'))
print("GOOGLE_CLIENT_EMAIL:", os.getenv('GOOGLE_CLIENT_EMAIL'))
print("GOOGLE_PRIVATE_KEY 長度:", len(os.getenv('GOOGLE_PRIVATE_KEY', '')))
```

### Q3: 如果憑證洩漏怎麼辦？

**A:** 立即採取以下步驟：

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. IAM → 服務帳戶
3. 刪除舊的服務帳戶或移除其許可權
4. 建立新的服務帳戶
5. 更新環境變數

### Q4: 可以分享 .env 檔案給團隊成員嗎？

**A:** 不建議。每個成員應該：
- 使用自己的服務帳戶
- 或透過安全的密碼管理工具分享（如1Password、1Password Teams）

---

## 📚 相關資源

- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [The Twelve-Factor App - Config](https://12factor.net/config)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password)

---

💇‍♀️ **Hange韓哥接髮 | 台北西門町 | 接髮專家**
