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

**Kapcsolók**

Minden beütemezett adaghoz egy kapcsoló: bekapcsolva = beadva, kikapcsolva = még nem.
A visszakapcsolás visszavonja a beadást, ugyanúgy, mint az appban. A kapcsoló attribútumai
megmondják, ki és mikor adta be.

**Szolgáltatás**

`bogancs.dose` – automatizálásból jelölhetsz be egy adagot, vagy vonhatsz vissza egyet.

## Telepítés HACS-ból

1. HACS → jobb felül a három pont → *Custom repositories*
2. Add meg: `https://github.com/Begyo/bogancs-ha`, kategória: *Integration*
3. Keresd meg a listában a *Bogáncs kisállatkönyv* elemet, és telepítsd
4. Indítsd újra a Home Assistantet
5. *Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása → Bogáncs*

## Telepítés kézzel

Másold a `custom_components/bogancs` mappát a Home Assistant `config/custom_components`
mappájába, majd indítsd újra.

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
