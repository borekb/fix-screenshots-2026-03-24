# Google Drive Screenshots – duplicitní soubory po Migration Assistant

## Shrnutí

Migration Assistant přenesl na nový Mac lokální cache Google Drive včetně složky `Screenshots` (`~/Library/CloudStorage/GoogleDrive-borekb@gmail.com/My Drive/Archive/Screenshots/`). GDrive na novém Macu neměl tyto soubory ve své interní databázi, uploadoval je znovu jako nové, a protože originály v cloudu už existovaly, vznikly konfliktní kopie se suffixem " 2" (a vyšším).

Viz [poznámky v GDoc](https://docs.google.com/document/d/1Y_AZjQ2-8oT2vhFlNBhJIWNCYq3WNHRg_kQD7Z1Ail0/edit?tab=t.0#heading=h.r32yaowy1lb). Jedná se o [známý problém](https://support.google.com/drive/thread/248332490) — Google doporučuje GDrive na novém Macu nastavit čistě, ne migrovat přes Migration Assistant.

**Rozsah:** ~487 souborů " 2" + ~60 dalších " 3"/" 4"/... v root složce `Screenshots/`. Archivní podsložky (2021–2025) nebyly zasaženy.

## Řešení: záloha + kompletní reset GDrive + úklid duplikátů

Klíčový princip: **nejdřív dosáhnout čistého napojení na cloud, pak teprve mazat duplikáty.** Bez resetu by 500 lokálních souborů zůstalo jako orphany (GDrive je nespravoval).

### 1. Záloha ✅

Dočasná záloha do `~/Downloads/Screenshots-temp-2026-03/` (~10.5 GB): Screenshots s xattrs, DriveFS databáze, celá CloudStorage složka. Po ověření smazána.

### 2. Reset GDrive ✅

1. `mv ~/Library/Application Support/Google/DriveFS` → záloha (interní databáze)
2. `sudo mv ~/Library/CloudStorage/GoogleDrive-borekb@gmail.com` → záloha (data)
3. Restart počítače (reset `fileproviderd`)
4. Přihlášení do GDrive → čistý sync

**Výsledek resetu:**

| | Před | Po |
|---|---|---|
| Originals s Drive ID | 100 z 609 | **609 z 609** |
| Originals bez Drive ID | **500** | **0** |
| Kopie " 2" s Drive ID | 462 z 487 | **487 z 487** |

Všech 1096 souborů má Drive item ID — žádné orphany.

### 3. Smazání duplikátů ✅

1. Ve Finderu vybrány soubory vytvořené při migraci (24. 3. 2026 ~0:40) → přesunuty do `Screenshots/duplicates/` (511 souborů)
2. Ověřeno skriptem `verify-duplicates.py`: **511/511 potvrzených duplikátů** (MD5 shodné s originálem)
3. Složka `duplicates/` smazána
4. Kontrola přes `gws drive files list` odhalila 2 další duplikáty — smazány ručně

**Výsledek:** 586 → 573 souborů v cloud složce Screenshots.

~40 souborů s numerickým suffixem (" 2", " 3" atd.) zůstává — jsou to Shottr anotace (odlišný obsah) a Screen Recordings, nikoli duplikáty.

### 4. Známé nedostatky

- Screenshoty stažené z cloudu nemají xattr `kMDItemScreenCaptureGlobalRect` → Quick Look je zobrazuje 2× větší (viz sekce Quick Look níže). Šlo by obnovit z PNG metadat, ale není to priorita.

---

## Detaily investigace

### Klasifikace " 2" souborů

Automatická klasifikace (`classify-duplicates.py`) s porovnáním MD5 hashů a dekódovaných pixelových dat:

| Kategorie | Počet | Popis |
|---|---|---|
| **GDrive duplikát** | 457 | Byte-for-byte identické → smazáno |
| **Shottr anotace, stejné rozměry** | 22 | Stejné rozměry, ale jiná pixelová data (šipka, rámeček, text) |
| **Shottr anotace, jiné rozměry** | 6 | Jiné rozměry → jasně jiný obrázek |

Google Drive neprovádí žádný re-processing PNG souborů. Všech 28 párů s odlišným MD5 má odlišná pixelová data (ověřeno dekompresí IDAT chunků).

### Duplikáty s vyšším suffixem (" 3", " 4", ...)

U screenshotů se Shottr anotacemi GDrive vytvořil duplikáty **obou** verzí — originálu i anotace. Příklad:

| Soubor | Co to je |
|---|---|
| `...02-04 at 10.11.28.png` | originální screenshot |
| `...02-04 at 10.11.28 2.png` | Shottr anotace |
| `...02-04 at 10.11.28 3.png` | **GDrive duplikát originálu** |
| `...02-04 at 10.11.28 4.png` | **GDrive duplikát anotace** |

### Proč GDrive nedetekoval shodu lokálních a cloudových souborů

GDrive File Provider si drží interní databázi (`~/Library/Application Support/Google/DriveFS/<account_id>/`), kde mapuje cloud soubory na lokální. Migration Assistant zkopíroval lokální soubory, ale **ne tuto databázi**. GDrive na novém Macu startoval s prázdnou DB → neměl s čím porovnat → uploadoval jako nové → konflikty.

GDrive neporovnává obsah souborů — řídí se výhradně svou databází. Neexistuje mechanismus "re-adopce" existujícího lokálního souboru.

### Rozdíly mezi originálem a kopií " 2"

- **Originals (bez " 2") = soubory z Migration Assistant** — zachovaly si xattrs ze starého Maca (screenshot metadata, FinderInfo, quarantine). Většina neměla Drive item ID.
- **Kopie " 2" = cloud-downloaded verze** — GDrive je stáhl z cloudu jako konfliktní kopie. Mají Drive item ID, ale nemají screenshot xattrs (cloud je nepřenáší).

### Quick Look anomálie

Byte-for-byte identické soubory se ve Finder Quick Look zobrazují v různých velikostech. Příčina: originál má xattr `kMDItemScreenCaptureGlobalRect` (logická velikost pro Retina), kopie " 2" stažená z cloudu tento xattr nemá → Quick Look zobrazí v plné pixelové velikosti (2× větší).

Řešení by bylo obnovit xattrs z PNG metadat (EXIF/XMP/pHYs chunky obsahují potřebná data), ale macOS Quick Look tyto PNG chunky nečte — spoléhá se na filesystem xattrs.

### Extended attributes a cloud služby

Xattrs jsou uloženy ve filesystému (APFS), ne v obsahu souboru. Žádná velká cloud služba je nesynchronizuje (Google Drive, OneDrive, Box — NE; Dropbox a iCloud částečně). Při normálním používání na jednom Macu to nevadí (xattrs zůstávají lokálně), problém nastane až při přechodu na jiný Mac.

Zdroj: [Eclectic Light Company – Which file systems and Cloud services preserve extended attributes?](https://eclecticlight.co/2018/01/12/which-file-systems-and-cloud-services-preserve-extended-attributes/)

## Zdroje

- [Fix problems in Drive for desktop – Google Drive Help](https://support.google.com/drive/answer/2565956?hl=en&co=GENIE.Platform%3DDesktop)
- [Use Drive for desktop on macOS – Google Drive Help](https://support.google.com/drive/answer/12178485?hl=en)
- [File Duplication after Migration – Google Drive Community](https://support.google.com/drive/thread/248332490)
- [Apple's File Provider Forces Mac Cloud Storage Changes – TidBITS](https://tidbits.com/2023/03/10/apples-file-provider-forces-mac-cloud-storage-changes/)
- [Eclectic Light Company – Which file systems and Cloud services preserve extended attributes?](https://eclecticlight.co/2018/01/12/which-file-systems-and-cloud-services-preserve-extended-attributes/)
