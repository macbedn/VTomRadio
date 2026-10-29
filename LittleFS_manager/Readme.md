# LittleFS-SPIFFS Partition Manager v0.6.0 (by Botfai Tibor)

Windows és Linux alatt futtatható Python segédprogram ESP32 rádiók LittleFS/SPIFFS fájlrendszerének kezeléséhez WiFi karbantartó protokollon keresztül.     
- Nem szükséges soros kapcsolat, vezetékek, így egyszerűbb a használata!  
- Az ESP32 szoftverét fel kell készíteni a program parancsainak feldolgozásához!  
- A VTomRadio már tartalmazza a szükséges háttérszoftvert.

## Fő funkciók

- A rádió fájlrendszerének listázása fa nézetben.
- Teljes fájlrendszer mentése ZIP fájlba.
- Opcionális mentés-ellenőrzés: a program újra kiolvassa a fájlokat és byte-ra összeveti a ZIP tartalmával.
- ZIP mentés visszaállítása a rádióra.
- Kijelölt fájl mentése PC-re.
- Fájlok és teljes mappák feltöltése várósoron keresztül.
- Kijelölt fájlok vagy mappák törlése.
- Új mappa létrehozása és rádió újraindítása.
- Automatikus és becsült partícióméret-profilok a várósor helyellenőrzéséhez.
- HU/EN felület, sötét Windows témához igazodó megjelenés.

## Használat
Telepített Python környezetben futtasd a `.py` fájlt.   
```
VTomRadio/LittleFS_manager/LittleFS-SPIFFS_Partition_Manager_WiFi_v0.6.0.py
```
Ha a Python környezet nincs telepítve, Windows alatt használd az `.exe` fájlt, ez tartalmazza a futtatási környezetet is.    
```
VTomRadio/LittleFS_manager/dist/LittleFS-SPIFFS_Partition_Manager_WiFi_v0.6.0.exe
```
- A program elindítása után a "Rádió IP-címe" mezőbe írd be a rádió kijelzőjén látható IP-címet, majd ENTER vagy kattints a "Kapcsolódás" gombra. A program megpróbál csatlakozni a rádióhoz, és ha sikerül, a fájlrendszer listázása megjelenik a fa nézetben.    



## Mentés és visszaállítás

A teljes mentés ZIP formátumban készül. A program a rádióról olvasott fájlokat az eredeti útvonalukkal menti, beleértve a mappaszerkezetet is.

A `Mentés ellenőrzése` opció bekapcsolásakor a ZIP elkészülte után a program újra kiolvassa a rádió fájljait, majd byte-ra összehasonlítja őket a ZIP-ben lévő tartalommal. Ez lassabb, de fontos mentésnél nagyobb biztonságot ad.

Visszaállításkor a ZIP tartalma kerül feltöltésre a rádió fájlrendszerére.

## Partícióméret és helyellenőrzés

 A program csatlakozás után megpróbálja kiolvasni a rádió fájlrendszerét, és ha sikerül, a fájlok listázása megjelenik a fa nézetben. A listázás közben a program ellenőrzi a fájlok méretét és az összesített foglalt helyet, majd becsült szabad helyet számol. Ha nem sikerül kiolvasni a partíció méretét van lehetőség a becsült partícióméret-profilok használatára a "Partíció méret" nyomógomb alatt.

A program mutatja:

- valós vagy becsült teljes partícióméret,
- listázott fájlok alapján becsült foglalt hely,
- becsült szabad hely,
- várósor mérete,
- elfér / kevés tartalék / nem fér el jelzés.

## Feltöltési várósor
Fájlok vagy mappa feltöltésénél a program először a feltöltési várósorba helyezi az elemeket, majd a "Várósor indítása" gombbal lehet elindítani a tényleges feltöltést. A várósor indításakor a program egymás után tölti fel az elemeket, közben mutatja:

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

A program a rádió firmware-ének fs_api_http protokolljára épül. Ha a firmware eltérően listázza vagy kezeli a fájlokat, a program több ismert esetet javít, de hardveres teszt mindig javasolt mentés, visszaállítás és tömeges törlés előtt.

## Forrás

https://github.com/gidano/myRadio-SPIFFS-Manager