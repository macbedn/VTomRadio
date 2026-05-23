# LittleFS-SPIFFS Partition Manager v0.4

Rövid, Windows és Linux alatt futtatható Python/Tkinter segédprogram ESP32 rádiók LittleFS/SPIFFS fájlrendszerének kezeléséhez soros karbantartó protokollon keresztül.<br>
Az ESP32 szoftverét fel kell készíteni a használatához!<br>
Telepített Python környezetben futtasd a `.py` fájlt.<br>
Ha a fenti környezet nincs telepítve, Windows alatt használd az `.exe` fájlt, ez tartalmazza a futtatási környezetet is.<br>

## Fő funkciók

- COM port kiválasztása és karbantartó mód indítása.
- A rádió fájlrendszerének listázása fa nézetben.
- Gyökér (`..`) bejegyzés a fájlrendszerfa tetején.
- Teljes fájlrendszer mentése ZIP fájlba.
- Opcionális mentés-ellenőrzés: a program újra kiolvassa a fájlokat és byte-ra összeveti a ZIP tartalmával.
- ZIP mentés visszaállítása a rádióra.
- Biztonságosabb ZIP visszaállítás: nem törli le előre a teljes fájlrendszert.
- Kijelölt fájl mentése PC-re.
- Fájlok és teljes mappák feltöltése várósoron keresztül.
- Kijelölt fájlok vagy mappák törlése.
- Új mappa létrehozása és rádió újraindítása.
- Becsült partícióméret-profilok a várósor helyellenőrzéséhez.
- HU/EN felület, sötét Windows témához igazodó megjelenés.

## Újdonságok a v0.4-ben

- `Becsült FS / Partíció méret` profilválasztó a kézi méretmegadás helyett.
- vTOMRadio / yoRadio 16 MB LittleFS 3.8 MB profil.
- Várósor méretének összevetése a becsült szabad hellyel.
- Mentés ellenőrzése opció teljes ZIP mentés után.
- Gyorsabb és stabilabb soros olvasás pufferelt protokollsor-kezeléssel.
- Nagyobb `.vlw` fontfájlok mentésének javítása.
- Biztonságosabb restore írási mód.
- Saját modális értesítőablakok.
- Nyelvváltáskor a fájlrendszerfa sorai is újrarajzolódnak.

## Mentés és visszaállítás

A teljes mentés ZIP formátumban készül. A program a rádióról olvasott fájlokat az eredeti útvonalukkal menti, beleértve a mappaszerkezetet is.

A `Mentés ellenőrzése` opció bekapcsolásakor a ZIP elkészülte után a program újra kiolvassa a rádió fájljait, majd byte-ra összehasonlítja őket a ZIP-ben lévő tartalommal. Ez lassabb, de fontos mentésnél nagyobb biztonságot ad.

Visszaállításkor a ZIP tartalma kerül feltöltésre a rádió fájlrendszerére. A v0.4 már nem törli le előre a teljes fájlrendszert, hanem fájlonként cserél, majd a sikeres visszaállítás után takarítja azokat az extra fájlokat, amelyek nincsenek a ZIP-ben.

## Partícióméret és helyellenőrzés

Firmware oldali FSINFO támogatás nélkül a Python program nem tudja pontosan kiolvasni a LittleFS/SPIFFS partíció valódi méretét. Ezért a v0.4 becsült partícióméret-profilokat használ.

A program mutatja:

- becsült teljes partícióméret,
- listázott fájlok alapján becsült foglalt hely,
- becsült szabad hely,
- várósor mérete,
- elfér / kevés tartalék / nem fér el jelzés.

## Feltöltési várósor

A fájlok és mappák először a feltöltési várósorba kerülnek. A várósor indításakor a program egymás után tölti fel az elemeket, közben mutatja:

- aktuális fájl,
- fájlszám,
- sebesség,
- becsült hátralévő idő,
- összesített folyamat,
- hibák száma.

Írási hibánál automatikus visszaesés történik biztonságosabb írási módra. Kritikus fájlrendszer-írási hiba esetén a várósor leáll.

## Törlés

A törlés fájlokra és mappákra is működik. Mappa törlésekor a program először a benne lévő fájlokat törli, majd a mappát. A művelet végén újralistázással ellenőrzi, hogy a kijelölt útvonal valóban eltűnt-e.

A gyökér (`..`) bejegyzés nem törölhető, ez csak a gyökér kiválasztására szolgál.

## Megjegyzés

A program a rádió firmware-ének karbantartó protokolljára épül. Ha a firmware eltérően listázza vagy kezeli a fájlokat, a program több ismert esetet javít, de hardveres teszt mindig javasolt mentés, visszaállítás és tömeges törlés előtt.

## Forrás

https://github.com/gidano/myRadio-SPIFFS-Manager/tree/main/LittleFS-SPIFFS%20Partition%20Manager