# Változások

Az integráció verziószáma `FŐ.ALVERZIÓ.JAVÍTÁS` alakú (szemantikus verziózás):

- **FŐ**: olyan változás, ami után kézzel is hozzá kell nyúlni (például megszűnik egy entitás).
- **ALVERZIÓ**: új funkció, új entitás, visszafelé kompatibilis módon.
- **JAVÍTÁS**: hibajavítás, szövegjavítás, a viselkedés nem bővül.

Minden kiadáshoz tartozik egy `vX.Y.Z` címke és egy GitHub kiadás, így a Home Assistant
frissítési kártyáján a verziószám és a „kiadási megjegyzések” hivatkozás is ezt mutatja.

---

## v1.2.1 (2026-09-09)

**Javítva**

- Az adag megjelölése azonnal látszik a felületen, nem csak a következő lekérdezéskor.
  A kapcsoló átbillenése után a hátralévő adagok száma és a késés is rögtön frissül,
  nem fagy be a többi koppintás.

## v1.2.0 (2026-09-04)

**Új szenzorok**

- **Időpontok**: orvos és kozmetikus a következő 7 napban.
- **Veszély a környéken**: bejelentett veszélyforrás, kerekített távolsággal.
- **Elveszett állat a környéken**: másik család állata a közelben.
- **Fogyóban**: táp és gyógyszer, ami hamarosan elfogy.

**Kikerült**

- A **napi rutin** szenzor. Az egy lista, amit az appban olvas el az ember, és magától
  sosem változott. A vezérlőpultra az való, ami időhöz kötött vagy riaszt.

**Megjegyzés**

- Szerver oldali párja a Bogáncs app `b2f92d0` verziója (`/api/ha/state`).

## v1.1.0 (2026-08-25)

**Új**

- Saját ikonok az integrációhoz, külön világos és sötét témához (256 és 512 képpont).
  A sötét témás ikon világos vonalakkal készült, így nem kell kompromisszumos változat.

## v1.0.2 (2026-08-25)

**Változott**

- A telepítő űrlapon a mező neve „Kód” helyett „Hozzáférési kód”, magyarul és angolul is.

## v1.0.1 (2026-08-25)

**Változott**

- Szövegjavítások a leírásban, és jelzés, hogy az app zárt próbaüzemben van.

## v1.0.0 (2026-08-25)

**Első kiadás**

- Telepítés a Home Assistant felületéről, egyetlen mezővel: a hozzáférési kóddal.
  A kód egyben az azonosító, így ugyanaz a család nem vehető fel kétszer.
  Ha az appban lecserélik a kódot, az integráció újat kér, nem hal el csendben.
- Négy szenzor: hátralévő adagok, késésben, következő adag, napi rutin.
- Adagonként egy kapcsoló, nem gomb, hogy látszódjon, megtörtént-e már.
- `bogancs.dose` szolgáltatás automatizáláshoz.
- Magyar és angol fordítás.
