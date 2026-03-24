# Google Drive Screenshots – duplicitní soubory po Migration Assistant

## Kontext

Při přenosu souborů ze starého MacBooku na nový pomocí **Migration Assistant**, viz [poznámky v GDoc](https://docs.google.com/document/d/1Y_AZjQ2-8oT2vhFlNBhJIWNCYq3WNHRg_kQD7Z1Ail0/edit?tab=t.0#heading=h.r32yaowy1lb), se přenesla i lokální cache Google Drive, včetně složky `Screenshots` (`~/Library/CloudStorage/GoogleDrive-borekb@gmail.com/My Drive/Archive/Screenshots/`).

Google Drive běží ve "streaming" módu (většina souborů jsou zástupci, stahují se on-demand).

## Problém

Po spuštění Google Drive for Desktop na novém Macu se začaly uploadovat duplicitní soubory se suffixem " 2" (např. `screenshot.png` → `screenshot 2.png`). Google Drive viděl migrované lokální soubory jako nové (nebyly v jeho interní databázi) a protože originály už existovaly v cloudu, vytvořil kopie s příponou " 2".

Jedná se o **známý problém** – Google doporučuje Google Drive na novém Macu nastavit čistě, ne migrovat přes Migration Assistant.

## Rozsah

- **~487 souborů** se suffixem " 2" v root složce `Screenshots/` (z toho 457 GDrive duplikátů, 28 Shottr anotací, zbytek falešné pozitivy)
- **~60 dalších duplikátů** se suffixem " 3", " 4" a vyšším — viz sekce níže
- Podsložky `2024/` a `2025/` mají jen pár " 2" souborů (32 a 25) – přesunuty do `Screenshots - archive`
    - Namátková kontrola archivních podsložek (2023, 2024, 2025): **všechny " 2" soubory mají odlišný obsah** — jsou to výhradně Shottr anotace vytvořené ručně dávno před migrací. V archivních složkách není co mazat.

## Zjištění

### Klasifikace " 2" souborů

Provedena automatická klasifikace (`classify-duplicates.py`) s porovnáním MD5 hashů a dekódovaných pixelových dat:

| Kategorie | Počet | Popis |
|---|---|---|
| **GDrive duplikát** | 457 | Byte-for-byte identické → bezpečně smazat |
| **Shottr anotace, stejné rozměry** | 22 | Stejné rozměry, ale jiná pixelová data (malá anotace: šipka, rámeček, text) |
| **Shottr anotace, jiné rozměry** | 6 | Jiné rozměry → jasně jiný obrázek |
| ~~Osiřelý soubor~~ | ~~8~~ | Falešné pozitivy — viz oprava níže |

Příklady GDrive duplikátů (kopie " 2", mají Drive item ID → lze otevřít v prohlížeči):
- [Screenshot 2026-01-02 at 21.46.59 2.png](https://drive.google.com/file/d/1iONVNSPzcFL2oL7Rtw6em4e4iZQ_1Tby/view)
- [Screenshot 2026-02-06 at 11.41.03 2.png](https://drive.google.com/file/d/1m5VeN6_Y22Mwqe1SuE2r8ykylGfgZs0k/view)
- [Screenshot 2026-03-23 at 17.37.50 2.png](https://drive.google.com/file/d/1gyDIuvUrtNItGOSWqEdjVKsXrk6M6sXX/view) – tento pár byl detailně analyzován v sekci Quick Look

Shottr anotace a originals nemají Drive item ID (nejsou trackované GDrivem), takže na ně nelze vytvořit přímý link.

**Google Drive neprovádí žádný re-processing PNG souborů.** Všech 28 párů s odlišným MD5 má odlišná pixelová data (ověřeno dekompresí IDAT chunků). Žádný pár nemá identické pixely s rozdílnými byty souboru. Rozdíly jsou vždy způsobeny Shottr anotacemi, nikoli změnou komprese/metadat ze strany GDrive.

### Duplikáty s vyšším suffixem (" 3", " 4", ...)

U screenshotů, kde existovaly Shottr anotace (" 2" soubory s jiným obsahem), GDrive vytvořil duplikáty **obou** verzí — originálu i anotace. Příklad:

| Soubor | Velikost | MD5 | Co to je |
|---|---|---|---|
| `...02-04 at 10.11.28.png` | 1.57 MB | ff8e... | originální screenshot |
| `...02-04 at 10.11.28 2.png` | 1.48 MB | 17f0... | Shottr anotace |
| `...02-04 at 10.11.28 3.png` | 1.57 MB | ff8e... | **GDrive duplikát originálu** |
| `...02-04 at 10.11.28 4.png` | 1.48 MB | 17f0... | **GDrive duplikát anotace** |

U screenshotů s více Shottr anotacemi (např. " 2", " 3", " 4" na starém Macu) se řetěz prodlužuje — např. `...03-12 at 10.51.45` má varianty až do " 8", kde " 5"–" 8" jsou duplikáty " orig"–" 4".

Celkem ~60 dalších duplikátů ke smazání. Klasifikační skript `classify-duplicates.py` zatím hledá jen suffix " 2" — pro mazání bude třeba porovnat MD5 všech variant a smazat ty, které jsou kopie existujícího souboru.

### Rozdíly mezi originálem a kopií " 2"

|                              | Originals (bez " 2")                      | Kopie " 2"                    |
| ---------------------------- | ----------------------------------------- | ----------------------------- |
| Permissions                  | `-rw-r--r--` (479/482)                    | `-rw-------` (457/482)        |
| Drive item ID                | 100 z 600                                 | 462 z 493                     |
| `kMDItemIsScreenCapture`     | **490**                                   | 31                            |
| `kMDItemScreenCaptureGlobalRect` | ano                                   | ne (až na 31 výjimek)         |
| `com.apple.FinderInfo`       | ano                                       | ne                            |
| `com.apple.quarantine`       | ano                                       | ne                            |

**Opravená interpretace** (po hlubší analýze xattr):

- **Originals (bez " 2") = soubory z Migration Assistant** – zachovaly si xattrs ze starého Maca (screenshot metadata, FinderInfo, quarantine). Většina nemá Google Drive item ID, protože GDrive je nepovažuje za "své" soubory.
- **Kopie " 2" = cloud-downloaded verze** – GDrive je stáhl z cloudu jako konfliktní kopie. Mají Drive item ID, ale nemají screenshot xattrs (cloud je nepřenáší).

### 28 Shottr anotací (podrobnosti)

Všech 28 párů s odlišným MD5 jsou **Shottr anotace** – manuálně vytvořené oanotované verze screenshotů, uložené jako "... 2.png". Shoda v pojmenování s GDrive duplikáty je náhoda.

**6 s odlišnými rozměry** (jasná anotace, často výrazně jiný canvas):

| Soubor | Originál | Anotace " 2" |
|---|---|---|
| `...01-23 at 11.30.00` | 1278×434 | 1610×766 |
| `...02-18 at 10.25.13` | 1794×804 | 2138×1148 |
| `...02-24 at 14.33.26` | 794×2792 | 802×2800 |
| `...03-12 at 10.51.45` | 2646×1808 | 2726×1906 |
| `...03-12 at 14.22.09` | 498×394 | 1200×674 |
| `...03-20 at 22.30.07` | 1082×640 | 2971×846 |

**22 se stejnými rozměry** (malá anotace typu šipka/rámeček, nemění canvas):
Většina " 2" verzí je o 1-11 % menší (Shottr exportuje s jinou PNG kompresí). Výjimka: `...02-12 at 0.13.28` je o 7.5 % větší.

### ~~8 osiřelých souborů~~ → opraveno: falešné pozitivy

Původně skript klasifikoval 8 souborů jako "osiřelé" (" 2" soubor bez originálu). Ve skutečnosti šlo o **chybu v detekci**: soubory jako `Screenshot 2026-02-22 at 2.06.56.png` mají "2." jako součást časového údaje (hodina 2:06), ne jako suffix " 2". Skript `classify-duplicates.py` opraven — detekce nyní správně rozlišuje suffix " 2" od číslovky v čase.

Po opravě: **0 skutečně osiřelých souborů**. Všech 8 falešných pozitiv jsou normální screenshoty, ne " 2" duplikáty.

### Quick Look anomálie – vyřešeno

Beyond Compare hlásí binárně identické soubory, ale Finder Quick Look zobrazuje originál (bez " 2") v "normální" velikosti a kopii " 2" **2× větší**. Mazání thumbnail cache nepomáhá, protože příčina je jinde.

**Příčina:** Rozdílné extended attributes (xattr), konkrétně `kMDItemScreenCaptureGlobalRect`.

Testovaný pár `Screenshot 2026-03-23 at 17.37.50.png`:
- Soubory jsou byte-for-byte identické (MD5 `3e00c6f3d2447a5d45ca5429fb772c09`, 978×976 px, DPI 144, Display P3)
- Originál má xattr `kMDItemScreenCaptureGlobalRect` = `[226, 228, 489, 488]` – tj. logická velikost **489×488 bodů** (= 978÷2 × 976÷2)
- Quick Look čte tento xattr a zobrazí screenshot v logické velikosti (respektuje Retina 2× škálování)
- Kopie " 2" tento xattr nemá → Quick Look zobrazí v plné pixelové velikosti 978×976, což vypadá 2× větší

**Závěr:** Nejde o bug thumbnail cache, ale o chybějící metadata. Quick Look se chová korektně v obou případech – problém je, že kopie " 2" přišla o informaci o tom, že jde o Retina screenshot.

## Kde se extended attributes ukládají

Extended attributes (xattr) jsou metadata uložená **ve filesystému** (APFS), odděleně od datového obsahu souboru:

- **Malé xattrs** (do ~3800 B): uloženy přímo v metadata oblasti APFS spolu se záznamem o xattr
- **Větší xattrs**: uloženy jako separátní datové streamy, ale stále mimo hlavní datový obsah souboru

Klíčový důsledek: xattrs jsou **lokální záležitost**. Nejsou součástí bytového obsahu souboru (PNG dat), takže se nepřenesou při uploadu/downloadu, pokud to cloud služba explicitně nepodporuje.

### Cloud služby a xattrs

| Služba       | Podpora xattrs |
|-------------|----------------|
| Google Drive | **NE** |
| OneDrive     | NE |
| Box          | NE |
| Dropbox      | Částečně (některé `com.apple.*`) |
| iCloud Drive | Částečně (Apple tvrdí plnou podporu, realita je omezená) |

Zdroj: [Eclectic Light Company – Which file systems and Cloud services preserve extended attributes?](https://eclecticlight.co/2018/01/12/which-file-systems-and-cloud-services-preserve-extended-attributes/)

### Co je uvnitř PNG (přežije cloud sync)

PNG soubor samotný obsahuje informaci o tom, že je to screenshot:
- **EXIF chunk** (`eXIf`): `UserComment: Screenshot`
- **XMP chunk** (`iTXt`): `<exif:UserComment>Screenshot</exif:UserComment>`
- **pHYs chunk**: DPI 144 (= Retina 2×)
- **iDOT chunk**: Apple-proprietární chunk pro optimalizované renderování
- **iCCP chunk**: ICC profil Display P3

Tyto data přežijí sync přes jakýkoli cloud, protože jsou součástí PNG bytů. **Ale macOS Quick Look je nečte** – místo toho se spoléhá na xattrs (`kMDItemScreenCaptureGlobalRect`), které jsou uloženy ve filesystému a cloud sync nepřežijí.

### Proč to dosud nebyl problém

Při normálním používání GDrive na jednom Macu:
1. Screenshot tool uloží soubor → nastaví xattrs (`kMDItemIsScreenCapture`, `kMDItemScreenCaptureGlobalRect` atd.)
2. GDrive uploadne bytový obsah souboru (bez xattrs) do cloudu
3. Lokální soubor si xattrs ponechá, protože je stále ten samý soubor na tom samém APFS disku
4. Quick Look čte lokální xattrs → zobrazí správně

**Na jiném Macu** (čistý GDrive download bez migrace) by soubor xattrs neměl a Quick Look by ho zobrazil 2× větší. Ale to zřejmě dosud nebylo viditelné, protože screenshoty byly primárně prohlíženy na Macu, kde vznikly.

Ověřeno: soubor `Screenshot 2025-01-02 at 0.06.00.png` v podsložce `2025/` (čistý cloud download, nikdy nemigrovaný) má pouze `com.google.drivefs.item-id` a `lastuseddate` – **žádné screenshot xattrs**. Na tomto Macu je navíc Spotlight vypnutý, takže ani ten xattrs z PNG obsahu neregeneruje.

### Teoretická náprava xattrs

Pokud bychom chtěli obnovit xattrs na soubory stažené z cloudu, šlo by:
1. Z PNG obsahu extrahovat EXIF `UserComment: Screenshot` a XMP data
2. Z `pHYs` chunku spočítat logickou velikost (pixely ÷ (DPI ÷ 72))
3. Nastavit `kMDItemIsScreenCapture`, `kMDItemScreenCaptureType`, `kMDItemScreenCaptureGlobalRect` xattrs

## Problém osiřelých lokálních souborů (chybějící Drive item ID)

### Stav

V root složce `Screenshots/` je 600 non-" 2" souborů, z nichž **500 nemá Drive item ID** — GDrive je nespravuje. Jsou to soubory, které Migration Assistant přenesl jako plně stažené lokální kopie. GDrive na novém Macu je nezná (nejsou v jeho interní databázi).

Archivní podsložky (2021–2025) tento problém nemají: **všechny soubory mají Drive item ID**. Ty byly na starém Macu zřejmě streaming placeholders → Migration Assistant je zkopíroval jako placeholders → GDrive na novém Macu je adoptoval bez problémů.

Problém se vyskytuje **výhradně v root složce Screenshots** a nikde jinde v celém GDrive (ověřeno prohledáním lokálního GDrive mimo Screenshots — žádné " 2" soubory vytvořené 24. března; pozn.: ověření přes lokální `find`, ne přes cloud API).

### Proč GDrive nedetekoval, že lokální soubory odpovídají cloudovým

GDrive File Provider si drží vlastní interní databázi (`~/Library/Application Support/Google/DriveFS/<account_id>/`), kde mapuje cloud soubory na lokální. Migration Assistant zkopíroval lokální soubory, ale **ne tuto databázi**. GDrive na novém Macu startoval s prázdnou databází → neměl s čím lokální soubory porovnat → uploadoval je jako nové → konflikty → " 2" kopie.

I přesto, že soubory jsou byte-for-byte identické, GDrive neporovnává obsah — řídí se výhradně svou databází.

### Proč to je třeba vyřešit před mazáním

Pokud smažeme " 2" kopie (které GDrive spravuje), zůstanou lokálně non-" 2" originals, které GDrive nezná. To by mohlo vést k:
1. GDrive nahraje non-" 2" soubory znovu do cloudu jako nové (další duplikáty)
2. Nebo je ignoruje (zůstanou jako nesynchronizovaný orphan)

### Neexistuje mechanismus "re-adopce"

Na základě online průzkumu: **GDrive File Provider nemá způsob, jak adoptovat existující lokální soubor.** Žádná operace se souborem (přejmenování, přesun, `touch`, restart GDrive, pause/resume sync) to nespustí. Příkaz `fileproviderctl` umí materializovat nebo evictovat soubory, ale jen ty, které GDrive už zná.

Google oficiálně doporučuje **nepoužívat Migration Assistant pro GDrive složky** a na novém Macu nainstalovat GDrive čistě.

### Ověření cloudového stavu (přes `gws` CLI)

Pomocí `gws drive files list` (Google Workspace CLI, jen čtení) ověřeno, že soubory bez lokálního Drive item ID existují v cloudu:

- **5/5 namátkově ověřených Shottr anotací** — existují v cloudu, velikosti odpovídají lokálním
- **6/6 falešných orphanů** (soubory s "2." v čase) — existují v cloudu

Cloud ID složky Screenshots: `1yz670ZkwiKMCu-8kt2TwMxh-HtevWMFz` (parent: Archive `0B5YLkzJ91X2NcW0yWGdzVV9RWUU`).

### Možné přístupy k opravě

**A) Záloha + kompletní reset GDrive + úklid v cloudu (zvolený přístup)**

Klíčový princip: **nejdřív dosáhnout čistého napojení na cloud, pak teprve mazat duplikáty.**

Riziko: nízké — záloha v Downloads obsahuje všechna data včetně xattrs, cloud obsahuje všechny soubory (ověřeno přes `gws`).

**B) Ponechat cloud-tracked kopie, smazat lokální orphans, přejmenovat v cloudu** — nezvoleno, složitější orchestrace.

**C) Disconnect/reconnect bez resetu** — nezvoleno, vysoké riziko dalších duplikátů.

## Provedení resetu (přístup A)

### Krok 1: Záloha Screenshots do ~/Downloads ✅

Finder zkopíroval celou složku Screenshots mimo GDrive knihovnu:
- Cíl: `/Users/borekb/Downloads/Screenshots-temp-2026-03/Screenshots`
- **1096 souborů, 472 MB** — shodné s GDrive originálem
- MD5 namátkově ověřeno (5/5 OK)
- **xattrs zachovány** (Finder je kopíruje) — záloha obsahuje screenshot metadata

Poznámka: kopírování 500 MB trvalo ~20 minut kvůli File Provider overhead (každý soubor prochází `fileproviderd` daemonem, i když je lokálně dostupný).

### Krok 2: Záloha DriveFS databáze ✅

Přesunuta interní databáze GDrive:
```
mv ~/Library/Application Support/Google/DriveFS → ~/Downloads/Screenshots-temp-2026-03/DriveFS-backup
```
- 570 MB, hlavní položka `metadata_sqlite_db` (281 MB) — mapování cloud ↔ lokální soubory
- `content_cache` prakticky prázdný (8 KB) — v streaming módu GDrive necachuje data

### Krok 3: Přesun CloudStorage složky ✅

Přesunuta celá GDrive CloudStorage složka:
```
sudo mv ~/Library/CloudStorage/GoogleDrive-borekb@gmail.com → ~/Downloads/Screenshots-temp-2026-03/GoogleDrive-CloudStorage-backup
```
- 9.4 GB (8.9 GB Screenshots archive + 473 MB Screenshots + drobné)
- Vyžadovalo `sudo` (macOS chrání CloudStorage složku)
- Odstraněn i pozůstatek `GoogleDrive-borekb@gmail.com (07.04.2024 9:51)` ze starého Maca

### Krok 4: Restart počítače ✅

Čistý restart pro reset `fileproviderd` a dalších systémových daemonů. Po restartu:
- macOS automaticky vytvořil prázdný placeholder `GoogleDrive-borekb@gmail.com` v CloudStorage
- GDrive vytvořil čistou novou DriveFS složku (bez account dat, bez `metadata_sqlite_db`)

### Krok 5: Přihlášení do GDrive ✅

GDrive zobrazil Welcome obrazovku → přihlášení k účtu → "Checking for latest updates..." → sync dokončen.

Ověření po syncu:

| | Před resetem | Po resetu |
|---|---|---|
| Počet souborů | 1096 | 1096 (beze změny) |
| Originals s Drive ID | 100 z 609 | **609 z 609** |
| Originals bez Drive ID | **500** | **0** |
| Kopie " 2" s Drive ID | 462 z 487 | **487 z 487** |
| Kopie " 2" bez Drive ID | 31 | **0** |

**Reset vyřešil klíčový problém: všech 1096 souborů má Drive item ID.** GDrive spravuje každý soubor ve složce, žádné orphany.

### Krok 6: Smazání GDrive duplikátů ✅

Postup:
1. Ve Finderu seřazeny soubory podle Date Modified, vybrány soubory vytvořené při migraci (24. 3. 2026 ~0:40)
2. Přesunuty do podsložky `Screenshots/duplicates/` (511 souborů)
3. Ověřeno skriptem `verify-duplicates.py`: **511/511 souborů je potvrzených duplikátů** (každý má v nadřazené složce originál se stejným MD5)
4. Složka `duplicates/` smazána

Následná kontrola přes `gws drive files list` (cloud API, bez stahování souborů) odhalila:
- 2 další GDrive duplikáty (`Screenshot 2026-03-20 at 7.32.14 4.png` a `7.png`) — smazány ručně
- ~40 souborů s numerickým suffixem (" 2", " 3" atd.) zůstává — jsou to **Shottr anotace** (odlišný obsah) a **Screen Recordings** (různé exporty), nikoli duplikáty

**Výsledek:** 586 → 573 souborů v cloud složce Screenshots po úklidu.

### Krok 7: Zbývající úkoly

- [ ] Volitelně: obnovit screenshot xattrs z PNG metadat nebo ze zálohy (bez nich Quick Look zobrazuje screenshoty 2× větší)
- [ ] Smazat zálohu z `~/Downloads/Screenshots-temp-2026-03/` (~10.5 GB), až bude jistota, že vše je v pořádku
- [ ] Volitelně: obdobný úklid v `Screenshots - archive` (podsložky 2021–2025), pokud tam jsou GDrive duplikáty — podle namátkové kontroly tam ale žádné nejsou

## Zálohy

| Co | Cesta | Velikost |
|---|---|---|
| Screenshots (kompletní kopie s xattrs) | `~/Downloads/Screenshots-temp-2026-03/Screenshots` | 472 MB |
| DriveFS databáze (stará) | `~/Downloads/Screenshots-temp-2026-03/DriveFS-backup` | 570 MB |
| CloudStorage (celá GDrive složka) | `~/Downloads/Screenshots-temp-2026-03/GoogleDrive-CloudStorage-backup` | 9.4 GB |

Zdroje:
- [Fix problems in Drive for desktop – Google Drive Help](https://support.google.com/drive/answer/2565956?hl=en&co=GENIE.Platform%3DDesktop)
- [Use Drive for desktop on macOS – Google Drive Help](https://support.google.com/drive/answer/12178485?hl=en)
- [File Duplication after Migration – Google Drive Community](https://support.google.com/drive/thread/248332490)
- [Apple's File Provider Forces Mac Cloud Storage Changes – TidBITS](https://tidbits.com/2023/03/10/apples-file-provider-forces-mac-cloud-storage-changes/)
- [Eclectic Light Company – Which file systems and Cloud services preserve extended attributes?](https://eclecticlight.co/2018/01/12/which-file-systems-and-cloud-services-preserve-extended-attributes/)
