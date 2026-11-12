# Nil Kervancısı

Antik Mısır'da, Nil boyunca geçen tarayıcı ticaret oyunu. Tek bir HTML dosyası olarak çalışır (telefon ve masaüstü).

## Derleme
```
./build.sh
```
`dist/` içine şunlar çıkar:
- `nil-kervanci.html`: Claude artifact sayfası
- `nil-kervancisi.html`: tek dosyalık, paylaşılabilir sürüm
- `nil-kervancisi-site.zip`: Netlify'a sürüklenebilir PWA klasörü

Gerekenler: Python 3, zip.

## Klasörler
- `src/`: oyunun parçaları. Hangi parçada ne olduğu `docs/kaynak-haritasi.md` dosyasında, birleştirme sırası `src/assemble.py` içinde. `ui/`, `sea/` ve `v3/` klasörleri bölümlere ayrılmış tek dosyalardır; parçalar ad sırasıyla birleştirilir.
- `site/`: PWA dosyaları (manifest, service worker, simgeler, three.min.js r128).
- `tools/qa/`: Playwright testleri:
  - `test-arayuz.js`: arayüz regresyon testi
  - `t153_28.js`: 30 günlük otomatik oyuncu
  - `shots.js`: ekran görüntüleri

  `test-arayuz.js` ve `lib.js` depo içindeki yolları kullanır; `shots.js` eski ekran görüntüsü betiğidir ve yolları uyarlanmalıdır.
- `tools/blender-karakter/`: v33 3B karakter setini üreten Blender (bpy) betikleri.
- `tools/blender-portre/`: v31 portrelerini üreten Blender betikleri.
- `docs/`: tasarım notları (DESIGN*.md) ve kaynak haritası.
- `ref/`: izometrik görsel referanslar.

## Kontroller

Depo kökünde, Node.js kurulu bir ortamda çalıştır:

```sh
node tools/qa/test-storage.js
node tools/qa/test-run-status.js
```

Bu regresyon testleri tarayıcı gerektirmez. Tarayıcı testleri için önce Playwright ve Chromium kur:

```sh
npm install --no-save --package-lock=false playwright
npx playwright install chromium
./build.sh
node tools/qa/test-arayuz.js
D3=1 node tools/qa/test-arayuz.js
node tools/qa/t153_28.js 1 "$PWD/dist/preview.html"
```

Arayüz testi `ALL OK` yazmalı. 30 günlük bot, sonuç ekranına ulaşmalı ve `errs: none` yazmalı; eksik sonuç, adım sınırı veya sayfa hatası başarısız çıkış kodu üretir.

`test-arayuz.js` varsayılan olarak `dist/preview.html` açar; ilk argüman veya `HTML` ortam değişkeni başka bir dosya seçer. `lib.js` de `HTML` değişkenini kullanır; ekran görüntüleri varsayılan olarak `dist/qa/` içine yazılır, `OUT` ile değiştirilebilir. 3B testleri depodaki `site/three.min.js` dosyasını kullanır.
