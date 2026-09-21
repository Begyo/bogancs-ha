# Bogáncs kisállatkönyv – Home Assistant integráció

A [Bogáncs kisállatkönyv](https://kisallatkonyv.hu/) napi gyógyszerezését és napi rutinját
hozza be a Home Assistantba. Telepítés után egyetlen dolgot kell megadnod: a kódot, amit
az appban generálsz.

> **Zárt próbaüzem.** A kisallatkonyv.hu jelenleg zárt próbaüzemben működik.

## Mit ad

**Szenzorok**

| Entitás | Mit mutat |
|---|---|
| `sensor.<család>_hatralevo_adagok` | hány adag van még ma hátra. A teljes napi lista az attribútumaiban (`doses`), így egy kártya külön lekérés nélkül ki tudja rajzolni |
| `sensor.<család>_kesesben` | hány adag csúszott már el |
| `sensor.<család>_kovetkezo_adag` | a következő adag időpontja, attribútumban az állat és a gyógyszer |
| `sensor.<család>_napi_rutin` | a napi teendők száma, a szövegek az `items` attribútumban |
| `sensor.<család>_hatralevo_etetes` | hány etetés van még ma hátra. A teljes napi lista a `rows` attribútumban |

**Kapcsolók**

Minden beütemezett adaghoz egy kapcsoló: bekapcsolva = beadva, kikapcsolva = még nem.
A visszakapcsolás visszavonja a beadást, ugyanúgy, mint az appban. A kapcsoló attribútumai
megmondják, ki és mikor adta be.

Ugyanez az etetésekre: minden napi etetési alkalomhoz egy kapcsoló. Ha a táphoz napi több
alkalom tartozik, a kapcsoló neve a sorszámot is mondja, különben két egyforma kapcsoló állna
egymás mellett, és a fali tableten nem lehetne eldönteni, melyik a reggeli.

**Kártya**

Az integráció a saját Lovelace-kártyáját is hozza, külön telepítés nélkül. A kártyaválasztóban
*Bogáncs – Mai adagok* néven találod. A mai adagok listáját mutatja időrendben, koppintásra
jelölhető és visszavonható, és magától követi, ha új gyógyszer kerül be.

A lista **soronként** frissül: egy adag megjelölésekor csak az az egy sor vált át, a többihez
hozzá sem nyúl. Így nem villan a képernyő, és a görgetés is ott marad, ahol volt – egy hosszú
lista aljáról nem dob vissza a tetejére.

```yaml
type: custom:bogancs-doses
```

| Opció | Mit csinál |
|---|---|
| `entity` | melyik adag-szenzort olvassa. Elhagyható: magától megtalálja |
| `title` | a kártya címe (alapból *Mai adagok*) |
| `hide_header` | `true` esetén csak a lista látszik, fejléc nélkül – ha a vezérlőpulton már van saját számláló |
| `hide_given` | `true` esetén a már beadott adagok kimaradnak |
| `by` | ez a név kerül a naplóba a beadás mellé (alapból *Home Assistant*) |

A *Bogáncs – Mai etetés* kártya ugyanígy működik, csak az etetésekre:

```yaml
type: custom:bogancs-feeds
```

| Opció | Mit csinál |
|---|---|
| `entity` | melyik etetés-szenzort olvassa. Elhagyható: magától megtalálja |
| `title` | a kártya címe (alapból *Mai etetés*) |
| `hide_header` | `true` esetén csak a lista látszik, fejléc nélkül |
| `hide_done` | `true` esetén a már megetetett sorok kimaradnak |
| `by` | ez a név kerül a naplóba (alapból *Home Assistant*) |

Az etetésnek nincs időpontja, csak napi sorszáma, ezért késés sincs: ami nincs kipipálva, az
egyszerűen hátravan. A soron lévő külön gombbal az etetés **kimaradtnak** jelölhető, ugyanúgy,
mint a gyógyszeradag: ez se nem kész, se nem hátravan, hanem eldőlt. A gomb csak akkor jelenik
meg, ha a kiszolgáló tudja fogadni (kisállatkönyv 2.14.0-tól).

**Szolgáltatás**

`bogancs.dose` – automatizálásból jelölhetsz be egy adagot, vagy vonhatsz vissza egyet.

`bogancs.feed` – ugyanez az etetésre: a táp azonosítója és a napi alkalom sorszáma kell hozzá.
A `missed` mezővel kimaradtként is rögzíthető.

## Telepítés HACS-ból

1. HACS → jobb felül a három pont → *Custom repositories*
2. Add meg: `https://github.com/Begyo/bogancs-ha`, kategória: *Integration*
3. Keresd meg a listában a *Bogáncs kisállatkönyv* elemet, és telepítsd
4. Indítsd újra a Home Assistantet
5. *Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása → Bogáncs*

## Telepítés kézzel

Töltsd le a repó tartalmát, és másold át a `custom_components/bogancs` mappát úgy, hogy a
Home Assistant konfigurációs mappájában ez legyen a végeredmény:

```
<Home Assistant konfigurációs mappa>/
└── custom_components/
    └── bogancs/
        ├── __init__.py
        ├── manifest.json
        └── ...
```

A konfigurációs mappa Home Assistant OS és konténeres telepítés esetén `/config`, Core
telepítésnél jellemzően `~/.homeassistant`. Ha a `custom_components` könyvtár még nem létezik,
hozd létre. Végül indítsd újra a Home Assistantet.

## Hozzáférési kód

Az appban: *Beállítások → Home Assistant → Kód készítése*. A kód a családodhoz tartozik,
és csak a saját családod adatait éri el. Bármikor lecserélheted; a régi azonnal érvénytelen
lesz, és a Home Assistant új kódot fog kérni.

## Saját példány

Ha nem a kisallatkonyv.hu-t használod, a telepítéskor a *Cím* mezőben add meg a saját
példányod címét.

## Példa automatizálás

```yaml
automation:
  - alias: "Szólj, ha egy adag elcsúszott"
    trigger:
      - platform: numeric_state
        entity_id: sensor.csalad_kesesben
        above: 0
    action:
      - service: notify.mobile_app
        data:
          message: >-
            {{ states('sensor.csalad_kesesben') }} adag késésben van.
```

## Ikonok

Az integráció a saját ikonjait hozza magával (a custom_components/bogancs/brand mappában), külön
világos és sötét témához. Ehhez Home Assistant 2026.3 vagy újabb kell; korábbi verzión
általános ikon látszik.

## Változások

Minden kiadás szerepel a [CHANGELOG.md](CHANGELOG.md) fájlban, és GitHub kiadásként is,
így a Home Assistant frissítési kártyáján a verziószám mellett a „kiadási megjegyzések”
hivatkozás is azt mutatja, mi változott az előző verzióhoz képest.

## Licenc

MIT
