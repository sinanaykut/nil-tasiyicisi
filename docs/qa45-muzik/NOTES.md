# v45 müzik — hışırtı temizliği

Sahibinin notu: "Nil'in Şafağı'nın başında ve bir çalgı girince hışırtı var; diğer parçalarda da bir çalgıda duyuluyor."
Parçalar Node'da oyunun kodunun aynısıyla işlendi, her bus (ud, arp/kanun, ney/kamış, bas, dron, davul, zil) ayrı ayrı da
çıkarılıp ölçüldü.

## Bulunan nedenler
| neden | nerede duyuluyordu | düzeltme |
|---|---|---|
| Ud ve bas tellerinin vuruş gürültüsü beyaz gürültüydü (8 kHz'lik tek kutup, alçak geçiren yok sayılır); ayrıca gecikme hattının başı/sonu arasında basamak vardı (her periyotta tık) | ud tremolosu ve riff'leri (liman, çarşı, yelken, takip), menüde ud girişi (37,9 sn); her bas vuruşu (menünün ilk saniyesi dahil) | uyarım: vuruş sertliğine göre 1,0–4,4 kHz biquad alçak geçiren gürültü + üçgen tel şekli, iki ucu sıfıra inen pencere; vuruşta 1,25 ms yumuşak giriş |
| Ney nefesi sürekli ve parlaktı (geniş bant geçiren, 0,2 + her notada 0,55 "chiff") | Nil'in Şafağı'nda ney girişi (3,2 sn) ve sonrası, liman/tapınak/yelken neyleri | nefes 0,11, ayrıca 3 kHz alçak geçiren; chiff 0,3 ve yalnızca tutulan (legato olmayan) notalarda tam |
| Yarım hızda çalışan yankının süzgeçleri zayıftı: 4. derece aşağı örnekleme + doğrusal ara değer → parlak vuruşlar yankıya katlanıyor, yankı kuyruğu 8 kHz üstüne aynalanıyordu | her parçada, yankılı çalgıların arkasında ince hışırtı | 6. derece (6,2 kHz) aşağı örnekleme, 4. derece (6,6 kHz) görüntü süzgeci |
| Def zilleri / sistrum / bendir tel gürültüsü biraz parlak | çarşı, liman, takip | riq gürültüsü 0,3→0,2 (4,6 kHz), sistrum 0,22→0,15, bendir zarı 0,07→0,05 (0,22 sn), zil bus'ı 8,8 kHz'te kesilir |

DC kayması, denormal, döngü dikişi, 16-bit önbellek: sorun yok (DC < 4e-5, dikiş sıçraması yerel örnek farkının altında).
Önbellek anahtarı `MUSIC_VER = 'm45'` (eski işlenmiş müzik atılır).

## Önce → şimdi (tam döngü)
| parça | 8 kHz üstü enerji (dB, toplama göre) | gürültü tabanı 3–12 kHz (dB, müziğe göre) | spektral düzlük 2–10 kHz | LUFS |
|---|---|---|---|---|
| menu (Nil'in Şafağı) | −27,1 → −40,9 | −29,8 → −40,3 | 0,046 → 0,002 | −18,0 → −17,9 |
| port1 | −19,4 → −34,5 | −28,6 → −37,1 | 0,018 → 0,0008 | −18,0 → −17,9 |
| port2 | −20,2 → −35,1 | −29,3 → −31,2 | 0,0034 → 0,0006 | −18,2 → −18,0 |
| port3 | −43,1 → −48,1 | −31,1 → −43,4 | 0,045 → 0,0015 | −18,0 → −18,0 |
| sail | −25,2 → −39,6 | −30,6 → −40,4 | 0,033 → 0,0013 | −18,0 → −18,0 |
| chase | −18,4 → −32,5 | −14,8 → −17,7 | 0,041 → 0,0095 | −19,2 → −19,2 |

- Tek çalgılar: ud vuruşunun ilk 50 ms'sinde 6 kHz üstü −9 → −23 dB; ney'in 3–6 kHz'i −24 → −40 dB (tona göre).
- 6 kHz altı denge korunur (bantlar ±1 dB); takip parçasındaki el çırpma gibi doğası gereği gürültülü vuruşlar bilerek kaldı.

## Dosyalar
- `*-30s-once.ogg` / `*-30s-simdi.ogg`: aynı 30 sn, önce ve şimdi (menu 0–30 sn: başlangıç ve ney girişi).
- `spektrum-<parça>.png`: tam döngü spektrogramı, üstte önce, altta şimdi.
- `yakin-plan-nilin-safagi.png`: başlangıç + ney girişi ve ud girişi, önce/şimdi.
