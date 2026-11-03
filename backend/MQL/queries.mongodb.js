use("AppAnalyzerDB");

// apps_tr.json dosyasındaki incelenecek uygulamaların listesi
const targetAppIds = [
  "com.ovz.carscanner",
  "org.eobdfacile.android",
  "ru.yandex.yandexnavi",
  "com.vialsoft.radarbot_free",
  "com.hundred.qibla.finder",
  "ru.yandex.yandexmaps",
  "com.dwarfplanet.bundle",
  "com.mynet.android.mynetapp",
  "app.ym.sondakika",
  "com.Kamu.Personeli.Alimi",
  "com.google.android.apps.magazines",
  "hurriyet.mobil.android"
];

const KEEP_LIMIT = 1000;
const results = [];

targetAppIds.forEach(appId => {
  // Uygulamanın raw_reviews içindeki toplam yorum sayısı
  const totalReviews = db.raw_reviews.countDocuments({ app_id: appId });

  if (totalReviews > KEEP_LIMIT) {
    // İlk 1000 yorumu tut, 1000'den sonrasının _id'lerini topla
    const idsToDelete = db.raw_reviews
      .find({ app_id: appId }, { _id: 1 })
      .skip(KEEP_LIMIT)
      .toArray()
      .map(doc => doc._id);

    let deletedCount = 0;
    if (idsToDelete.length > 0) {
      // 1000'den fazla olan yorumları sil
      const delResult = db.raw_reviews.deleteMany({ _id: { $in: idsToDelete } });
      deletedCount = delResult.deletedCount;
    }

    // apps_metadata tablosundaki review_count değerini 1000 olarak güncelle
    db.apps_metadata.updateOne(
      { app_id: appId },
      { $set: { review_count: KEEP_LIMIT } }
    );

    results.push({
      app_id: appId,
      durum: "1000_YORUMA_SINIRLANDI",
      eski_yorum_sayisi: totalReviews,
      silinen_yorum_sayisi: deletedCount,
      guncel_yorum_sayisi: KEEP_LIMIT
    });
  } else {
    // 1000 ve altı ise dokunma
    results.push({
      app_id: appId,
      durum: "DOKUNULMADI (<= 1000)",
      eski_yorum_sayisi: totalReviews,
      silinen_yorum_sayisi: 0,
      guncel_yorum_sayisi: totalReviews
    });
  }
});

// VS Code MongoDB Playground ekranında sonuçları JSON olarak listeler
results;