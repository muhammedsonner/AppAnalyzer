import time
import os
import json
import config
import pandas as pd
from google_play_scraper import app as play_app
from scrapers.playstore_scraper import scrape_playstore_reviews


def log_operation(message: str):
    """Yapılan işlemleri operation_history.log dosyasına ve ekrana yazar."""
    log_path = os.path.join(config.LOGS_DIR, "operation_history.log")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"[{timestamp}] {message}"
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_text + "\n")
    print(log_text)



# Çekilecek uygulamaların listesi
APPS_FILE_NAME = "apps_tr.json"

with open(
    os.path.join(config.APPS_LIST_DIR, APPS_FILE_NAME),
    encoding="utf-8"
) as file:
    APPS_TO_SCRAPE = json.load(file)


def main():

    from data_pipeline.db_manager import db_manager

    PLAYSTORE_REVIEWS_PER_SCORE = 1000  # Her yıldız için çekilecek en fazla yorum sayısı
    PLAYSTORE_TARGET_SCORES = [1, 2, 3, 4, 5]
    COOLDOWN_SECONDS = 5  # Bekleme süresi

    TARGET_COLLECTION = "raw_reviews"
    SCRAPE_LANG = "tr"
    SCRAPE_COUNTRY = "tr"
    TARGET_METADATA_COLLECTION = "apps_metadata"

    # --- MongoDB Bağlantı Kontrolü ---

    if not db_manager.is_connected():
        log_operation("HATA: MongoDB'ye bağlanılamadı")
        return
    
    log_operation("MongoDB bağlantısı BAŞARILI. Veri çekme işlemi başlıyor...")

    # ---------------------------------
    
    log_operation("Veri çekme işlemi BAŞLADI.")

    existing_app_ids = db_manager.get_existing_apps(collection_name=TARGET_COLLECTION)
    skipped_apps = []

    is_first_scrape = True
    
    for app in APPS_TO_SCRAPE:
        playstore_id = app["playstore_id"] if isinstance(app, dict) else str(app)

        # ATLAMA KONTROLÜ
        if playstore_id in existing_app_ids:
            skipped_apps.append(playstore_id)
            log_operation(f"[ATLANDI] {playstore_id} veritabanında zaten kayıtlı.")
            continue

        # BEKLEME İŞLEMİ
        if ( not is_first_scrape ):
            log_operation(f"Sistem dinleniyor... ({COOLDOWN_SECONDS} sn)")
            time.sleep(COOLDOWN_SECONDS)
        
        is_first_scrape = False
        
        # Uygulama adını dile/ülkeye göre Google Play'den çekme
        try:
            details = play_app(playstore_id, lang=SCRAPE_LANG, country=SCRAPE_COUNTRY)
            app_name = details.get("title") or playstore_id
        except Exception as e:
            log_operation(f"[UYARI] {playstore_id} için başlık çekilemedi: {e}. Paket adı kullanılacak.")
            app_name = playstore_id

        # Play Store'dan Veri Çekme
        expected_max = PLAYSTORE_REVIEWS_PER_SCORE * len(PLAYSTORE_TARGET_SCORES)
        log_operation(
            f"{app_name} ({playstore_id} - PlayStore): yıldız başına en fazla "
            f"{PLAYSTORE_REVIEWS_PER_SCORE} yorum çekiliyor. "
            f"Yıldızlar: {PLAYSTORE_TARGET_SCORES}; "
            f"toplam üst sınır: {expected_max}."
        )
        try:
            scrape_playstore_reviews(
                app_name=app_name, 
                package_name=playstore_id, 
                count=PLAYSTORE_REVIEWS_PER_SCORE,
                target_scores=PLAYSTORE_TARGET_SCORES,
                lang=SCRAPE_LANG,
                country=SCRAPE_COUNTRY,
                collection_name=TARGET_COLLECTION,
                metadata_collection=TARGET_METADATA_COLLECTION
            )
            log_operation(f"{app_name} (PlayStore) işlemi TAMAMLANDI.")
        except Exception as e:
            log_operation(f"HATA: {app_name} (PlayStore) çekilemedi. Detay: {e}")
        
    
    if skipped_apps:
        summary_msg = (
            f"\n{'='*50}\n"
            f"ATLANAN UYGULAMALAR (Zaten Veritabanında Mevcut - Toplam: {len(skipped_apps)}):\n"
            + "\n".join([f"  * {item}" for item in skipped_apps])
            + f"\n{'='*50}"
        )
        log_operation(summary_msg)
            
    log_operation("Tüm veri çekme işlemleri BİTTİ.")

if __name__ == "__main__":
    main()
