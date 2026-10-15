# v47 müzik — sahne parçaları

Sahibinin notu: "Sethi ile yarışın müziği daha heyecanlı olabilir. Haydutlar kovalarken uygun bir müzik olabilir. Normal ve
dalgalı yolculukların ayrı müzikleri olabilir. Dalış görevinin kendi müziği olabilir."

v44/v45 tarzı korundu: makamlı, ud / ney / kamış / kanun / arp / darbuka-tabl-bendir; v45 hışırtı düzeltmeleri aynen
geçerli (bant sınırlı tel vuruşları, süzülmüş ney nefesi, temiz yarım hızlı yankı). Hepsi −18 LUFS, tepe ≤ −1 dBFS.

## Yeni parçalar
| parça | ne zaman | makam · tempo | süre | çalgılar |
|---|---|---|---|---|
| **Sethi ile Yarış** (`race`) | Sethi ile yarış | Re Hicaz · 100 bpm | 48,0 sn (20 ölçü) | her vuruşta tabl, 16'lık darbuka, ud riff'i, kamış, kanun + ud yükselen dizi, el çırpma, zil |
| **Pusu** (`chase`) | haydut / çöl akıncısı / Medjay pususu | Re Nahavent (D E F G A B♭ C♯, inerken C) · 132 bpm | 50,9 sn (28 ölçü) | 3+3+2 alçak ud ostinatosu, tabl ve bendir, 16'lık darbuka, alçak kamış çağrıları, tiz ney + kanun vuruşları, ara bölüm |
| **Dalgalı Su** (`rough`) | çağlayan, fırtına, kum fırtınası (kayalık geçit dahil) | Re Kürdi · 112 bpm 12/8 | 51,4 sn (24 ölçü) | ağır bendir dalgaları, yuvarlanan bas, akor boyunca inen arp serpintisi, iki ölçüde bir ud tremolo kabarması, geniş vibratolu ney |
| **Batık** (`dive`) | batık ve hazine dalışı | La Hicaz · 72 bpm | 53,3 sn (16 ölçü) | boğuk arp/kanun arpejleri (alçak geçiren EQ + uzun eko), şarkı söyleyen kâse, "u" koro dronu, yumuşak alçak nabız, sessiz ney; zil/def zili yok |

- Sakin su, gece geçişi ve kum tepeleri "Yelkenler Açık"ta kalır (normal yolculuk = yelken müziği, dalgalı = Dalgalı Su).
- Eski "takip katmanı" (yelkenin üstüne biten davul katmanı) kaldırıldı; Pusu artık kendi başına bir parça.

## Yarış müziği davula kilitli
Yarışta oyunun kendi davulu 0,6 sn'de bir vurur ("davul vurunca Çek!"). Müzik tam 100 bpm (bir vuruş = 0,6 sn) yazıldı ve
ilk ölçüsü geri sayımın dört vuruşu. Oyunun davulu her vurduğunda `Snd.beat()` çağrılır (`src/sea/01-run-setup.txt`
`drumSnd`, efektler kapalıyken de):
- ilk vuruş ızgarayı kurar, parça o vuruşa hizalı başlar (o ana kadar önceki müzik çalmaya devam eder);
- sonraki vuruşlarda hata ölçülür: küçük sapma çalma hızını en çok %2,5 eğerek düzeltilir, 70 ms'den büyük sapmada
  (duraklatma, art arda yavaş kareler) parça 40 ms'lik çapraz geçişle ızgaraya geri atlar;
- düzensiz vuruş (yarışın yavaş çekim anı, takılan kare) kullanılmaz, parça kendi hızında akar.

## Ses yüksekliği (tam döngü, 32 kHz stereo, oyunun koduyla Node'da işlendi)
| parça | LUFS | tepe dBFS | RMS dBFS | kısa süreli en yüksek LUFS | yumuşak tavan % | ağırlık merkezi | 3–6 kHz | 6 kHz+ |
|---|---|---|---|---|---|---|---|---|
| race | −18,0 | −1,03 | −20,8 | −15,4 | 0,029 | 847 Hz | −14,2 dB | −28,0 dB |
| chase | −18,0 | −1,07 | −20,6 | −14,7 | 0,014 | 720 Hz | −16,3 dB | −31,7 dB |
| rough | −18,0 | −1,09 | −20,2 | −15,7 | 0,003 | 586 Hz | −19,7 dB | −34,5 dB |
| dive | −18,0 | −1,48 | −20,0 | −12,4 | 0,001 | 452 Hz | −35,3 dB | −63,8 dB |

Oyunda kazanç: yarış/pusu/dalgalı 0,62, batık ve yelken 0,6 (limandaki parçalarla aynı düzey).

## Hışırtı ölçüleri (v45 ile aynı yöntem)
| parça | 8 kHz üstü enerji (dB, toplama göre) | gürültü tabanı 3–12 kHz (dB, müziğe göre) | spektral düzlük 2–10 kHz |
|---|---|---|---|
| race | −36,4 | −34,6 | 0,0004 |
| chase | −39,5 | −22,8 * | 0,0042 |
| rough | −42,2 | −38,4 | 0,0017 |
| dive | −69,7 | −46,1 | 0,0005 |
| *(v45 karşılaştırma: sail / port1 / eski chase)* | −39,6 / −34,5 / −32,5 | −40,4 / −37,1 / −17,7 | 0,0013 / 0,0008 / 0,0095 |

\* Pusu'nun "gürültü tabanı" alçak ud ostinatosunun (La2–Re3) sık üst harmoniklerinden geliyor: ölçüm 1 kHz'lik
pencerede tonları ayıklayamıyor. Ud bus'ı ayrı çıkarılıp ölçüldü; ostinato yumuşak mızrapla çalınınca 8 kHz üstü
−30,3 → −37,5 dB indi. Davul/kamış bus'larının tabanı −40…−49 dB. Tüm parçalarda ses dizisi dışı nota yok (makam denetimi).

## Motor
- `MUSIC_VER = 'm47'` (eski işlenmiş müzik atılır), 9 parça. Bellekte en çok 4 çözülmüş parça (yeni parçalar kısa:
  11,7–13 MB) → en çok ≈ 60 MB; yolculukta yelken parçası hep hazır tutulur.
- İşleme sırası: menü + seçili liman + yelken önce, sonra sahne parçaları (dalgalı, yarış, pusu, batık), sonra öbür
  liman parçaları. Bir sahne henüz işlenmemiş parçasını isterse acil işlenir ve arka plandaki işle yan yana yürür
  (acil olan işlemcinin çoğunu alır); bu sırada önceki müzik kesilmez.
- Geçişler: pusu ve yarışa 0,25 sn, dalgalıya 0,5 sn, batığa 0,9 sn; sahneden yelkene 1,2 sn.
- Bağlantılar: `playScene` → `Snd.scene(kind)`; sahne bitince (yarış hariç: yarıştan sonra limana inilir) `Snd.mode('sea')`;
  başlık ekranından dönüşte son yolculuk modu (`Snd.lastSea()`).

## Oyun içinde denetim (Playwright, Chromium, 3B kapalı)
Tam oyun botu (yolculuk haritası, sahneleri oynayan bot; eksik sahne türleri haritadan `playScene` ile açıldı), her
250 ms'de `Snd.info()` kaydı:

| sahne | çalan parça | parçanın duyulması (sahne başından) |
|---|---|---|
| sakin su | Yelkenler Açık | — (zaten çalıyor) |
| çağlayan | Dalgalı Su | 0,50 sn |
| fırtına | Dalgalı Su | 0 (önceki sahneden) |
| gece geçişi | Yelkenler Açık | — |
| kum fırtınası | Dalgalı Su | 0,26 sn |
| pusu | Pusu | 0,76 sn |
| Sethi ile yarış | Sethi ile Yarış | 0,75 sn (ilk davul vuruşunda) |
| batık | Batık | 0,50 sn |

- 8 sahne türünün 8'i doğru parça; sahne bitince yelken parçasına, yarıştan sonra limana dönülüyor. Hata yok.
- Yarışta müzik ↔ oyunun davulu (oyunda ölçülen, yumuşatılmış hata): ortanca 2 ms, %90'ı 7 ms, en çok 14 ms.
- Sanal saatle kilit denemesi (kareler 0–8 ms geç): düz yarışta ≤ 7 ms; yavaş çekim + 1,7 sn duraklamadan sonra tek
  vuruşta ızgaraya dönüş; oyun saati %0,7 kayarsa çalma hızı %0,9 eğilerek hata ~9 ms'de kalır.
- Mod geçişleri (önbellekten): yelken/dalgalı/pusu/batık 0,6–1,2 sn'de duyuluyor; çözülmüş müzik en çok 58,9 MB.
- İlk açılışta parçalar arka planda işlenir; sahne parçası henüz yoksa acil işlenir, o arada önceki müzik sürer.
  İşleme süresi Node'da (boş makine) parça başına 4–6,5 sn; bu denemelerin yapıldığı makine başka işlerle aşırı yüklüydü
  (2 çekirdekte yük ortalaması 15–20), tarayıcıdaki süreler bu yüzden anlamlı ölçülemedi.

## Dosyalar (≈ 3,0 MB)
| dosya | ne |
|---|---|
| `race-30s.ogg` | yarış: geri sayım ölçüsü + ilk 30 sn |
| `race-oyundaki-davulla-30s.ogg` | aynısı, oyunun yarış davulu (0,6 sn'de bir) üstüne bindirilmiş: davul ile müzik aynı vuruşta |
| `chase-30s.ogg` | pusu, 4. ölçüden (kamış çağrıları girerken) |
| `rough-30s.ogg` | dalgalı su, 4. ölçüden (ney girerken) |
| `dive-30s.ogg` | batık, baştan |
| `dongu-dikisleri-20s.ogg` | dört parçanın döngü noktası: sonun 2,5 sn'si + başın 2,5 sn'si |
| `spektrum-sahne-parcalari.png` | dört parçanın tam spektrogramı ve ortalama spektrumu |
