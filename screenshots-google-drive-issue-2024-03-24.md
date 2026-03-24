# Google Drive Screenshots – duplicitní soubory po Migration Assistant

## Kontext

Při přenosu souborů ze starého MacBooku na nový pomocí **Migration Assistant** se přenesla i lokální cache Google Drive, včetně složky `Screenshots` (`~/Library/CloudStorage/GoogleDrive-borekb@gmail.com/My Drive/Archive/Screenshots/`).

Google Drive běží ve "streaming" módu (většina souborů jsou zástupci, stahují se on-demand).

## Problém

Po spuštění Google Drive for Desktop na novém Macu se začaly uploadovat duplicitní soubory se suffixem " 2" (např. `screenshot.png` → `screenshot 2.png`). Google Drive viděl migrované lokální soubory jako nové (nebyly v jeho interní databázi) a protože originály už existovaly v cloudu, vytvořil kopie s příponou " 2".

Jedná se o **známý problém** – Google doporučuje Google Drive na novém Macu nastavit čistě, ne migrovat přes Migration Assistant.

## Rozsah

- **484 souborů** s příponou " 2" v root složce `Screenshots/`
- Každý " 2" soubor má odpovídající originál (žádné sirotky)
- Podsložky `2024/` a `2025/` mají jen pár duplikátů (32 a 25)

## Zjištění

### Identita souborů

- **454 párů** je byte-for-byte identických (ověřeno MD5) → dají se bezpečně smazat
- **28 párů** má odlišný MD5 hash (jiný obsah)

### Rozdíly mezi originálem a kopií " 2"

|                              | Originals (bez " 2")                      | Kopie " 2"                    |
| ---------------------------- | ----------------------------------------- | ----------------------------- |
| Permissions                  | `-rw-r--r--` (479/482)                    | `-rw-------` (457/482)        |
| Drive item ID                | 83                                        | většina                       |
| `kMDItemIsScreenCapture`     | **490**                                   | 31                            |
| `kMDItemScreenCaptureGlobalRect` | ano                                   | ne (až na 31 výjimek)         |
| `com.apple.FinderInfo`       | ano                                       | ne                            |
| `com.apple.quarantine`       | ano                                       | ne                            |

**Opravená interpretace** (po hlubší analýze xattr):

- **Originals (bez " 2") = soubory z Migration Assistant** – zachovaly si xattrs ze starého Maca (screenshot metadata, FinderInfo, quarantine). Většina nemá Google Drive item ID, protože GDrive je nepovažuje za "své" soubory.
- **Kopie " 2" = cloud-downloaded verze** – GDrive je stáhl z cloudu jako konfliktní kopie. Mají Drive item ID, ale nemají screenshot xattrs (cloud je nepřenáší).

### 28 párů s odlišným obsahem

Dvě možné příčiny:

1. **Shottr anotace** – ručně uložené soubory s jiným vizuálním obsahem (uživatel někdy ukládá anotované screenshoty jako "... 2.png")
2. **Google Drive re-procesované** – stejný obrázek, ale odlišná PNG komprese/metadata (originální PNG mají Apple-specifické chunky `iCCP`, `iTXt`, `iDOT`; kopie mají zjednodušenou strukturu s `sRGB`)

Rozlišení: pokud " 2" verze má jiné rozměry nebo výrazně jinou velikost, je to Shottr anotace. Pokud má stejné rozměry ale jiné PNG chunky, je to re-procesovaný duplikát.

**Stav:** Tyto páry je potřeba ještě projít a roztřídit.

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

### Teoretická náprava

Pokud bychom chtěli obnovit xattrs na kopie " 2" (nebo obecně na soubory stažené z cloudu), šlo by:
1. Z PNG obsahu extrahovat EXIF `UserComment: Screenshot` a XMP data
2. Z `pHYs` chunku spočítat logickou velikost (pixely ÷ (DPI ÷ 72))
3. Nastavit `kMDItemIsScreenCapture`, `kMDItemScreenCaptureType`, `kMDItemScreenCaptureGlobalRect` xattrs

V praxi to ale není potřeba, pokud kopie " 2" budeme mazat.

## Další kroky

- [ ] Smazat 454 identických duplikátů " 2"
- [ ] Projít 28 párů s odlišným obsahem a roztřídit na Shottr anotace vs. re-procesované duplikáty
- [ ] Zvážit, zda si ponechat originals (migrované, s xattrs) nebo kopie " 2" (cloud-tracked, bez xattrs) – viz sekce výše
