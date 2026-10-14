# v44 müzik — ölçümler ve dinleme notları

Bütün parçalar koddan, nota nota çalınarak üretilir (`src/snd-syn.txt`, `NilSynth`). Buradaki örnekler oyunun
kullandığı kodun aynısıyla Node'da işlendi; Chromium'da (Worker ve ana iş parçacığı yolu) aynı RMS/tepe değerleri çıktı.

## Dosyalar (toplam ≈ 3,7 MB)
| dosya | ne |
|---|---|
| `menu-30s.ogg` | Nil'in Şafağı (ana menü): arp glissandosu, ney çağrısı, kanun cevabı (0–30 sn) |
| `port1-30s.ogg` | Mennefer Limanı: ud taksimi, ud soru / ney cevap, maksum (0–30 sn) |
| `port2-30s.ogg` | Çarşı Davulları: kamış ↔ ud, saidi ritmi, el çırpma, zil arası (4–34 sn) |
| `port3-30s.ogg` | Tapınak Gölgesi: ney taksimi, dron, kalp atışı def, kâse, sistrum (33–63 sn) |
| `sail-30s.ogg` | Yelkenler Açık: 12/8 arp dalgaları, ney ezgisi (5–35 sn) |
| `chase-over-sail-30s.ogg` | Takip katmanı oyundaki gibi yelken parçasının üstünde (sail 0,5 + chase 0,75), B bölümü |
| `loop-seams-30s.ogg` | Her parçanın döngü noktası: sonun 2,5 sn'si + başın 2,5 sn'si arka arkaya (tümsek / tık olmamalı) |
| `spektrum-tum-parcalar.png` | Her parçanın tam spektrogramı ve ortalama spektrumu |
| `enstruman-yakin-plan.png` | Yakın plan: ney + dron (tapınak), ud taksimi (liman), takip davulları |

## Ses yüksekliği (tam döngü, 32 kHz stereo)
| parça | süre | ölçü / tempo | makam | LUFS (yakl.) | tepe dBFS | RMS dBFS | yumuşak tavan % | spektral ağırlık merkezi |
|---|---|---|---|---|---|---|---|---|
| menu | 75,8 sn | 24 · 76 | Re Hicaz | −18,0 | −1,03 | −20,2 | 0,007 | 652 Hz |
| port1 | 76,8 sn | 32 · 100 | Do Rast (½♭ mi, si) | −18,0 | −1,01 | −20,9 | 0,019 | 1218 Hz |
| port2 | 66,2 sn | 32 · 116 | Sol Hicaz | −18,1 | −1,08 | −21,3 | 0,006 | 1262 Hz |
| port3 | 72,7 sn | 20 · 66 | Re Beyati (½♭ mi) | −18,0 | −1,20 | −20,1 | 0,002 | 509 Hz |
| sail | 73,8 sn | 32 · 104 (12/8) | Re Kürdi | −18,0 | −1,04 | −20,3 | 0,002 | 709 Hz |
| chase (katman) | 73,8 sn | 32 · 104 | Re Kürdi | −19,2 | −1,12 | −22,4 | 0,014 | 1307 Hz |

- LUFS: BS.1770'e yakın K-ağırlıklı, kapılı ölçüm (scipy ile). Hedef: tüm parçalar −18, takip katmanı −19. Oyunda kazançlar
  (menü 0,6, liman 0,62, yelken 0,6) ile limanda/menüde/nehirde ≈ −22 LUFS; takipte toplam ≈ 2,7 dB daha yüksek.
- Tepe hiçbir yerde −1 dBFS'yi geçmez (master: EQ → 2,2:1 yapıştırıcı kompresör → −3 dBFS'den başlayan yumuşak tavan).
  Yumuşak tavan örneklerin en çok %0,02'sinde devrede (yalnızca vuruş tepeleri).
- Bant dengesi (toplama göre dB): 3–6 kHz −10…−20, 6 kHz+ −15…−35 dB; telefon hoparlöründe tiz batmaz, tapınak bilerek koyu.
  Eski sürüme göre alt bas (<100 Hz) ve 300 Hz çamuru azaltıldı, 1–3 kHz (ezgi, mızrap) öne alındı.
- Bus payları (kuru enerji, dB) her parça için hedefe göre otomatik ayarlandı: örn. liman: ud −6, ney −6,5, davul −7, bas −11,
  kanun −12, dron −15, zil/def zilleri −16.

## Dinleme yerine yapılan kontroller
- Akort: telli (Karplus-Strong + all-pass) 38–81 MIDI arası ±1 sent; arp/kanun ±1,3 sent; ney/kamış vibratolu ±5 sent.
- Makam: her parçanın bütün notaları kendi makam dizisine karşı denetlendi — dizi dışı nota yok (takip katmanının
  ostinatosu ilk hâlinde Si♮/Do♯ veriyordu, dizi basamaklarına çevrildi).
- Döngü: ses, döngü sonundan taşan kuyruk (yankı, tınlayan teller) başa eklenerek kapatılır; başlangıçtan önceye kayan
  vuruşlar sona taşınır. `loop-seams-30s.ogg` ile dinlenebilir.
- Tık / patlama: 9 kHz üstü ani tepe taraması — yalnızca gerçek vuruş başlangıçları.

## Performans ve bellek
| | Node (bu sunucu) | Chromium Worker (headless, 2 çekirdek, yazılım GL) | Ana iş parçacığı yedeği |
|---|---|---|---|
| bir parçanın işlenmesi | 1,7–3,9 sn | 5–19 sn (oyunla aynı çekirdekleri paylaşıyor) | 20–58 sn (dilimlerle) |
| gerçek zamana oran | 19–45× | 4–14× | — |
| ilk duyulan müzik (sayfa açılışından) | — | 1,3–1,7 sn (akışla) | 2,1 sn |
| önbellekten (2. ziyaret) | — | 0,8–1,3 sn | 0,9 sn |

- İşleme bir Web Worker'da (NilSynth'in kendi kaynağından üretilir). Worker yoksa / engellenirse aynı iş ana iş parçacığında
  ≤ ~10 ms'lik dilimlerle (acil olan MessageChannel ile, arka plandaki boşta kalan zamanda) yürür; tek dilim Node'da en çok
  ~20 ms (eski sürümde parça başına ana iş parçacığında ~500 ms JS, 600–700 ms'lik takılmalar).
- Chromium profili (20 sn, başlık ekranı): müzik için ana iş parçacığında toplam ~170 ms JS (AudioContext 64 ms, tampon
  kopyaları 41 ms, IndexedDB yazımı 28 ms, kalanı < 10 ms). Headless ortamdaki uzun görevler müzik kapalıyken de var
  (yazılım çizim); az çekirdekli cihazlarda arka plan işlemesi işlemcinin ~%55'ini kullanır, acil parça tam hızda.
- İlk parça işlenirken çalar: 1 sn'lik parçalar sırayla zamanlanır, bitince aynı anda döngüye devredilir.
- Bellek: çözülmüş parça başına 16–19 MB (32 kHz stereo float); en çok 3 parça tutulur → ~55 MB (eskiden altısı birden, ~82 MB).
  IndexedDB'de 16-bit, parça başına 8–9,4 MB (toplam ~54 MB); IndexedDB yoksa düşen parçalar 16-bit olarak bellekte kalır.
  Worker'ın tepe belleği tek parça için ~40 MB (float çıktı + 16-bit kopya + FFT tamponları), iş bitince bırakılır.
- Önbellek anahtarı `MUSIC_VER = 'm44'`: eski işlenmiş müzikler ilk yeni kayıtta silinir.
