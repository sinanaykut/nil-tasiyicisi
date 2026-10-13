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

  Betiklerdeki `ROOT` yolunu kendi ortamına göre değiştir.
- `tools/blender-karakter/`: v33 3B karakter setini üreten Blender (bpy) betikleri.
- `tools/blender-portre/`: v31 portrelerini üreten Blender betikleri.
- `docs/`: tasarım notları (DESIGN*.md) ve kaynak haritası.
- `ref/`: izometrik görsel referanslar.
