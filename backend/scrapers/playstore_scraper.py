import os
import pandas as pd
from tqdm import tqdm
import time
import sys
from google_play_scraper import reviews, Sort

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from data_pipeline.db_manager import db_manager

def scrape_playstore_reviews(
                             app_name: str,
                             package_name: str, 
                             count: int = 100, 
                             target_scores: list = None, 
                             lang: str = "tr", 
                             country: str = "tr", 
                             collection_name: str = "raw_reviews",
                             metadata_collection: str = "apps_metadata"):
    """
    Google Play Store üzerinden yorumları çeker. target_scores verilirse sadece o yıldızları çeker.
    """
    print(f"\nGoogle Play Store'dan '{app_name}' ({package_name}) için yorumlar çekiliyor...", flush=True)
    
    fetched_reviews = []
    
    scores_to_fetch = target_scores if target_scores else [None]

    for score in scores_to_fetch:
        score_msg = f"{score} Yıldızlı " if score else "Karışık "
        print(f"-> {score_msg}Yorumlar getiriliyor...", flush=True)
        
        try:
            result, continuation_token = reviews(
                package_name,
                lang=lang,
                country=country,
                sort=Sort.NEWEST,
                count=count,
                filter_score_with=score
            )

            received_count = len(result)
            if received_count < count:
                print(
                    f"UYARI: {score_msg}için {count} yorum istendi, ancak "
                    f"{received_count} yorum alındı. API istenen adede ulaşmadan "
                    "yanıt döndürdü; bu skor için mevcut sonuçlarla devam ediliyor.",
                    flush=True
                )
            else:
                print(
                    f"-> {score_msg}için istenen {count} yorum alındı.",
                    flush=True
                )
            
            for rv in tqdm(result, desc=f"İşleniyor ({app_name})", leave=False):
                time.sleep(0.002)
                fetched_reviews.append({
                    "app_name": app_name,
                    "platform": "PlayStore",
                    "app_id": package_name,
                    "review_id": rv.get("reviewId"),
                    "text": rv.get("content"),
                    "rating": rv.get("score"),
                    "date": str(rv.get("at")),
                    "lang": lang
                })
                
        except Exception as e:
            print(f"HATA: {score_msg}veriler çekilirken bir sorun oluştu: {e}", flush=True)
            continue

    df = pd.DataFrame(fetched_reviews)
    
    if fetched_reviews:
        db_manager.insert_raw_reviews(fetched_reviews, collection_name = collection_name)
        db_manager.update_app_metadata(
            app_id=package_name,
            name=app_name,
            platform="PlayStore",
            is_analyzed=False,
            review_count=len(fetched_reviews),
            collection_name= metadata_collection,
            lang=lang
        )
    
    return df
