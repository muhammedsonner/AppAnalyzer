# Veritabanı bağlantı ayarları
# Not: Veritabanı bağlantısı daha sonra yapılandırılacaktır.

import os
from dotenv import load_dotenv

# Proje Kök Dizini
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# En dıştaki (AppAnalyzer/) .env dosyasını yükle
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))

# MongoDB Connection String ve veritabanı adı (.env'den okunur, yoksa varsayılan)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "AppAnalyzerDB")

RAW_DATA_DIR = os.path.join(BASE_DIR, "raw_data")
APPS_LIST_DIR = os.path.join(BASE_DIR, "apps_to_scrape")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Klasörler yoksa oluştur
for _dir in (RAW_DATA_DIR, APPS_LIST_DIR, LOGS_DIR):
    os.makedirs(_dir, exist_ok=True)
