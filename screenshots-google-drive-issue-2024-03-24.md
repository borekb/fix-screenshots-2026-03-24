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

|                              | Originály (cloud)                         | Kopie " 2" (migrované)       |
| ---------------------------- | ----------------------------------------- | ----------------------------- |
| Permissions                  | `-rw-r--r--` (479/482)                    | `-rw-------` (457/482)        |
| Drive item ID                | jen 3 mají                                | 457 má                        |
| macOS screenshot metadata    | ano (`kMDItemIsScreenCapture` atd.)        | ne                            |
| `com.apple.FinderInfo`       | ano                                       | ne                            |

Originály = soubory streamované z cloudu (jak Google Drive normálně funguje).
Kopie " 2" = soubory uploadnuté z lokální cache, kterou přenesl Migration Assistant.

### 28 párů s odlišným obsahem

Dvě možné příčiny:

1. **Shottr anotace** – ručně uložené soubory s jiným vizuálním obsahem (uživatel někdy ukládá anotované screenshoty jako "... 2.png")
2. **Google Drive re-procesované** – stejný obrázek, ale odlišná PNG komprese/metadata (originální PNG mají Apple-specifické chunky `iCCP`, `iTXt`, `iDOT`; kopie mají zjednodušenou strukturu s `sRGB`)

Rozlišení: pokud " 2" verze má jiné rozměry nebo výrazně jinou velikost, je to Shottr anotace. Pokud má stejné rozměry ale jiné PNG chunky, je to re-procesovaný duplikát.

**Stav:** Tyto páry je potřeba ještě projít a roztřídit.

### Quick Look anomálie

Beyond Compare hlásí binárně identické soubory, ale Finder Quick Look zobrazuje originál menší a kopii " 2" 2x větší. Příčina je pravděpodobně **bug Finder thumbnail cache** – originál streamovaný z cloudu měl uloženou low-res miniaturu.

Řešení:

```bash
qlmanage -r cache
qlmanage -r
killall Finder
```

## Další kroky

- [ ] Smazat 454 identických duplikátů " 2"
- [ ] Projít 28 párů s odlišným obsahem a roztřídit na Shottr anotace vs. re-procesované duplikáty
- [ ] Promazat Finder thumbnail cache
