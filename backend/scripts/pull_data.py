import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.db_manager import db_manager

def export():
    APP_NAME = None # None => veritabanındaki tüm uygulamaları alır
    PLATFORM = "PlayStore" # "PlayStore", "AppStore" veya None (tüm platformlar)
    LIMIT = 0 # 0 => Tümü
    COLLECTION_NAME = "raw_reviews" # İngilizce için: "raw_reviews_en"
    # ----------------------------------------------------

    print(f"Dışa aktarma başlatılıyor...")
    csv_yolu = db_manager.export_reviews_to_csv(
        app_name=APP_NAME, 
        platform=PLATFORM, 
        limit=LIMIT,
        collection_name= COLLECTION_NAME
    )

    if csv_yolu:
        print(f"İşlem Tamam! CSV dosyan şurada hazır: {csv_yolu}")
    else:
        print("Kriterlere uygun kayıt bulunamadı veya aktarılamadı.")

if __name__ == "__main__":
    export()
