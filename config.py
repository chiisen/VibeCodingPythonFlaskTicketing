"""
環境變數設定模組
使用 python-dotenv 載入 .env 檔案中的設定
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
# (1) 載入 .env 檔案
# (2) 若有環境變數已設定，則使用環境變數（方便部署時覆寫）
load_dotenv()

# Flask 設定載入
FLASK_APP = os.getenv('FLASK_APP', 'app.py')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
# 支援多種格式: '1', 'true', 'yes', 'on' (不分大小寫)
FLASK_DEBUG = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes', 'on')

# 安全設定
SECRET_KEY = os.getenv('SECRET_KEY')

# 驗證 SECRET_KEY 已設定
if not SECRET_KEY or SECRET_KEY == 'your_secure_random_secret_key_here':
    import sys
    print("⚠️  警告：SECRET_KEY 未正確設定！")
    print("   請執行以下命令產生隨機密鑰：")
    print("   python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("   並複製輸出結果至 .env 檔案的 SECRET_KEY 變數")
    print("")
    print("   或是複製 .env.example 為 .env 並填寫正確的值")
    sys.exit(1)

# 資料庫設定 (預設使用 SQLite)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')

# 郵件服務設定
SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

# Flask-WTF CSRF 設定
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 3600  # CSRF token有效期：1小時

# SQLAlchemy 設定
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False  # 設為 True 可顯示 SQL 語句
