import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.db_manager import db_manager


def dedupe_reviews():
    # --- AYARLAR ---------------------------------------------------------
    COLLECTION_NAME = "raw_reviews"   # İngilizce için: "raw_reviews_en"
    DRY_RUN = False                    # True => sadece sayar, HİÇBİR ŞEY SİLMEZ. Silmek için False yap.
    CREATE_UNIQUE_INDEX = False       # True => temizlikten sonra (app_id, review_id) unique index oluşturur
    BATCH_SIZE = 5000                 # Silme işlemi bu kadarlık gruplar halinde yapılır
    # ---------------------------------------------------------------------

    if not db_manager.is_connected():
        print("[HATA] MongoDB'ye bağlanılamadı.")
        return

    collection = db_manager.db[COLLECTION_NAME]
    total_before = collection.count_documents({})
    print(f"[{COLLECTION_NAME}] Temizlik öncesi toplam kayıt: {total_before}")

    # (app_id, review_id) çifti birden fazla kez geçiyorsa o grubun tüm _id'lerini topla
    pipeline = [
        {"$group": {
            "_id": {"app_id": "$app_id", "review_id": "$review_id"},
            "ids": {"$push": "$_id"},
            "n": {"$sum": 1},
        }},
        {"$match": {"n": {"$gt": 1}}},
    ]

    ids_to_delete = []
    duplicate_groups = 0
    per_app = {}
    deleted = 0

    for group in collection.aggregate(pipeline, allowDiskUse=True):
        duplicate_groups += 1
        app_id = group["_id"]["app_id"]
        extras = sorted(group["ids"])[1:]   # en eski kaydı (ilk _id) tut, geri kalanı sil
        per_app[app_id] = per_app.get(app_id, 0) + len(extras)
        ids_to_delete.extend(extras)

        if not DRY_RUN and len(ids_to_delete) >= BATCH_SIZE:
            deleted += collection.delete_many({"_id": {"$in": ids_to_delete}}).deleted_count
            ids_to_delete = []

    if not DRY_RUN and ids_to_delete:
        deleted += collection.delete_many({"_id": {"$in": ids_to_delete}}).deleted_count

    extra_total = sum(per_app.values())
    print(f"Mükerrer grup sayısı : {duplicate_groups}")
    print(f"Fazla (silinecek) kayıt: {extra_total}")
    for app_id, count in sorted(per_app.items(), key=lambda x: -x[1]):
        print(f"  - {app_id}: {count} fazla kayıt")

    if DRY_RUN:
        print("\nDRY_RUN açık: hiçbir kayıt silinmedi. Silmek için DRY_RUN = False yap.")
        return

    total_after = collection.count_documents({})
    print(f"\nSilinen kayıt: {deleted}")
    print(f"[{COLLECTION_NAME}] Temizlik sonrası toplam kayıt: {total_after}")

    if CREATE_UNIQUE_INDEX:
        collection.create_index([("app_id", 1), ("review_id", 1)], unique=True, name="uniq_app_review")
        print("Unique index oluşturuldu: (app_id, review_id)")


if __name__ == "__main__":
    dedupe_reviews()
