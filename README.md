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

Oynanış ve çizim regresyonları da tarayıcı gerektirmez:

```sh
node tools/qa/test-trade-ux.js
node tools/qa/test-haggle49.cjs
node tools/qa/test-scale49.cjs
node tools/qa/test-chars49.cjs
node tools/qa/test-city49.cjs
node tools/qa/test-combat49.cjs
node tools/qa/test-desert49.cjs
node tools/qa/test-sea49.cjs
```

Gerçek cihazda ayrıca 412×915 dikey, 915×412 yatay ve masaüstü görünümünü kontrol et: miktarı yazıp doğrudan pazarlığa başla, satış yönünü değiştir, sipariş teslim et, Kalpazanlar terazisini çöz ve şehirde rehber açıkken kaydır/yakınlaştır. Nehir pususunda silahlı mücadele veya kaçışı, çöl akıncılarında üç seçeneği de dene. 3B kapalıyken yolculukların tamamlanabilmesi gerekir. Bu kaynak testleri ekran görüntüsü ve gerçek GPU performans kontrolünün yerini almaz.

## GitHub Pages

`.github/workflows/pages.yml` derler ve `main` dalına her güncelleme geldiğinde `dist/site/` klasörünü GitHub Pages'e yayımlar. İlk kullanımda depoda **Settings → Pages → Build and deployment → Source: GitHub Actions** seç. Sonra **Actions** sekmesindeki “Yayımla – GitHub Pages” çalışmasını ve `github-pages` ortamındaki site bağlantısını kontrol et. İş akışı Actions sekmesinden elle de başlatılabilir.

> Depo private olduğundan Pages kullanımı hesap planına bağlıdır; GitHub Pro gerekir. Kişisel hesaplarda private Pages sitesi sunulmadığı için yayınlanan site herkese açık olabilir. Gizli erişimli Pages yalnızca Enterprise Cloud organizasyonlarında desteklenir.
