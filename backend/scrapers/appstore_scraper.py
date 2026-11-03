import os
import pandas as pd
from tqdm import tqdm
import sys
from app_store_scraper import AppStore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from data_pipeline.db_manager import db_manager

def scrape_appstore_reviews(app_name: str, app_id: str, count: int = 500, target_scores: list = None):
    """
    App Store üzerinden gerçek kullanıcı yorumlarını çeker ve MongoDB'ye aktarır.
    Not: Apple RSS feed limiti nedeniyle maksimum ~500 yorum çekilebilir.
    """
    print(f"\nApp Store'dan '{app_name}' ({app_id}) için yorumlar çekiliyor...", flush=True)

    # Apple RSS feed'i ~500 ile sınırlıdır
    effective_count = min(count, 500)
    if count > 500:
        print(f"[UYARI] App Store maks. ~500 yoruma izin veriyor. {count} yerine 500 çekilecek.", flush=True)

    try:
        app = AppStore(country="tr", app_name=app_name, app_id=app_id)
        app.review(how_many=effective_count)
    except Exception as e:
        print(f"[HATA] App Store'dan veri çekilirken hata oluştu: {e}", flush=True)
        return pd.DataFrame()

    fetched_reviews = []
    raw_reviews = app.reviews if app.reviews else []

    # target_scores filtresi: App Store API desteklemiyor, Python seviyesinde filtreliyoruz
    if target_scores:
        raw_reviews = [r for r in raw_reviews if r.get("rating") in target_scores]

    for rv in tqdm(raw_reviews, desc=f"İşleniyor ({app_name})", leave=False):
        fetched_reviews.append({
            "app_name": app_name,
            "platform": "AppStore",
            "app_id": app_id,
            "review_id": str(rv.get("reviewId", "")),
            "text": rv.get("review", ""),
            "rating": rv.get("rating"),
            "date": str(rv.get("date", ""))
        })

    df = pd.DataFrame(fetched_reviews)

    if fetched_reviews:
        db_manager.insert_raw_reviews(fetched_reviews)
        db_manager.update_app_metadata(
            app_id=app_id,
            name=app_name,
            platform="AppStore",
            is_analyzed=False,
            review_count=len(fetched_reviews)
        )

    return df
