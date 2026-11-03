import os
import sys
import pandas as pd
from pymongo import MongoClient, errors

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class DBManager:
    """
    MongoDB bağlantısı ve koleksiyon CRUD işlemlerini yöneten sınıf.
    """
    def __init__(self, uri: str = None, db_name: str = None):
        self.uri = uri or config.MONGO_URI
        self.db_name = db_name or config.DB_NAME
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            print(f"[DB] MongoDB bağlantısı başarılı! Veritabanı: {self.db_name}", flush=True)
        except errors.ServerSelectionTimeoutError as e:
            print(f"[DB UYARI] MongoDB sunucusuna bağlanılamadı ({self.uri}): {e}", flush=True)
            self.db = None
        except Exception as e:
            print(f"[DB HATA] Beklenmeyen veritabanı hatası: {e}", flush=True)
            self.db = None

    def is_connected(self) -> bool:
        if self.client is None or self.db is None:
            return False
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False

    def insert_raw_reviews(self, reviews: list, collection_name: str = "raw_reviews") -> int:
        """
        Ham yorumları 'raw_reviews' koleksiyonuna ekler.
        """
        if not reviews:
            print("[DB] Kaydedilecek yorum listesi boş.", flush=True)
            return 0

        if not self.is_connected():
            print("[DB UYARI] Veritabanı bağlı değil, veri kaydedilemedi.", flush=True)
            return 0

        try:
            collection = self.db[collection_name]
            result = collection.insert_many(reviews)
            inserted_count = len(result.inserted_ids)
            print(f"[DB] {inserted_count} adet ham yorum {collection_name} koleksiyonuna kaydedildi.", flush=True)
            return inserted_count
        except Exception as e:
            print(f"[DB HATA] Ham yorumlar kaydedilirken hata: {e}", flush=True)
            return 0

    def update_app_metadata(self, 
                            app_id: str, 
                            name: str, 
                            platform: str, 
                            is_analyzed: bool = False, 
                            review_count: int = 0, 
                            collection_name: str = "apps_metadata", 
                            lang: str = "tr"):
        """
        'apps_metadata' koleksiyonunu günceller (Yoksa yeni ekler - upsert).
        """
        if not self.is_connected():
            print("[DB UYARI] Veritabanı bağlı değil, meta veri güncellenemedi.", flush=True)
            return

        try:
            collection = self.db[collection_name]
            query = {"app_id": app_id, "platform": platform}
            update_data = {
                "$set": {
                    "app_id": app_id,
                    "name": name,
                    "platform": platform,
                    "is_analyzed": is_analyzed,
                    "review_count": review_count,
                    "lang": lang
                }
            }
            collection.update_one(query, update_data, upsert=True)
            print(f"[DB] '{name}' ({platform}) için meta veri güncellendi (is_analyzed={is_analyzed}).", flush=True)
        except Exception as e:
            print(f"[DB HATA] Meta veri güncellenirken hata: {e}", flush=True)

    def get_raw_reviews(self, 
                        app_name: str = None, 
                        limit: int = 0, 
                        collection_name: str = "raw_reviews"):
        """
        raw_reviews koleksiyonundan verileri okur.
        """
        if not self.is_connected():
            return []
        filter_query = {"app_name": app_name} if app_name else {}
        cursor = self.db[collection_name].find(filter_query)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)

    def get_apps_metadata(self, collection_name: str = "apps_metadata"):
        """
        apps_metadata koleksiyonundaki tüm uygulama kayıtlarını listeler.
        """
        if not self.is_connected():
            return []
        return list(self.db[collection_name].find({}, {"_id": 0}))

    def export_reviews_to_csv(self, 
                            app_name: str = None, 
                            platform: str = None, 
                            limit: int = 0, 
                            collection_name: str = "raw_reviews"):
        """
        Veritabanından yorumları çeker ve tek seferlik CSV'ye kaydeder.
        app_name verilmezse tüm uygulamaların verisini çeker. limit verilirse sadece o kadar getirir.
        """
        app_label = app_name if app_name else "Tum_Uygulamalar"
        limit_label = f" (Maks: {limit})" if limit > 0 else " (Tümü)"
        print(f"[DB] '{app_label}' için veriler CSV'ye aktarılıyor...{limit_label}", flush=True)
        
        if not self.is_connected():
            print("[DB UYARI] Veritabanı bağlı değil, CSV oluşturulamadı.", flush=True)
            return

        filter_query = {}
        if app_name:
            filter_query["app_name"] = app_name
        if platform:
            filter_query["platform"] = platform
            
        cursor = self.db[collection_name].find(filter_query)
        if limit > 0:
            cursor = cursor.limit(limit)
            
        reviews = list(cursor)
        
        if not reviews:
            print(f"[DB] '{app_label}' için veritabanında belirtilen kriterlere uygun yorum bulunamadı.", flush=True)
            return

        df = pd.DataFrame(reviews)
        
        if '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)
            
        file_name = f"{collection_name}_{app_label.replace(' ', '')}_exported_reviews.csv"
        file_path = os.path.join(config.RAW_DATA_DIR, file_name)
        
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"[DB] Başarılı! {len(reviews)} adet yorum CSV olarak şuraya kaydedildi: {file_path}", flush=True)
        return file_path


    def get_existing_apps(self, 
                            platform: str = "PlayStore", 
                            collection_name: str = "raw_reviews") -> set:
        if not self.is_connected():
            return set()
        
        try:
            filter_query = {"platform": platform} if platform else {}

            existing_apps = set(self.db[collection_name].distinct('app_id', filter_query))
            
            return existing_apps
        except Exception as e:
            print(f"[DB HATA] Kayıtlı uygulamalar alınırken hata: {e}", flush=True)
            return set()


db_manager = DBManager()

if __name__ == "__main__":
    print(f"Bağlantı durumu: {db_manager.is_connected()}")
