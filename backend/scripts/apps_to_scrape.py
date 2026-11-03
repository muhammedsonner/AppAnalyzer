APPS_TO_SCRAPE = [
  {
    "name": "",
    "playstore_id": ""
  }
]


import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from google_play_scraper import app

cleaned_apps = []

for item in APPS_TO_SCRAPE:
    package_name = (item.get("playstore_id") or "").strip()

    # Boş bırakılan uygulamaları atla
    if not package_name:
        continue

    item = item.copy()
    old_name = item.get("name", "")

    try:
        details = app(
            package_name,
            lang="tr",
            country="tr"
        )

        official_name = details.get("title")

        if official_name:
            item["name"] = official_name
            print(f"{old_name} -> {official_name}")
        else:
            print(f"İsim alınamadı: {package_name}")

    except Exception as e:
        # Hata durumunda eski ismi koru
        print(f"HATA: {package_name} | {e}")

    cleaned_apps.append(item)
    time.sleep(0.5)

APPS_TO_SCRAPE = cleaned_apps

with open(
    os.path.join(config.APPS_LIST_DIR, "apps_tr.json"),
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        APPS_TO_SCRAPE,
        file,
        ensure_ascii=False,
        indent=4
    )

print(f"\nToplam uygulama: {len(APPS_TO_SCRAPE)}")
print("Temiz liste apps_to_scrape/apps_tr.json dosyasına kaydedildi.")