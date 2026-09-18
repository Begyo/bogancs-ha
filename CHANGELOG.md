# Változások

Az integráció verziószáma `FŐ.ALVERZIÓ.JAVÍTÁS` alakú (szemantikus verziózás):

- **FŐ**: olyan változás, ami után kézzel is hozzá kell nyúlni (például megszűnik egy entitás).
- **ALVERZIÓ**: új funkció, új entitás, visszafelé kompatibilis módon.
- **JAVÍTÁS**: hibajavítás, szövegjavítás, a viselkedés nem bővül.

Minden kiadáshoz tartozik egy `vX.Y.Z` címke és egy GitHub kiadás, így a Home Assistant
frissítési kártyáján a verziószám és a „kiadási megjegyzések” hivatkozás is ezt mutatja.

---

## v1.4.2 (2026-09-18)

**Javítva: a kártya néha így is eltűnt, „Configuration error” maradt a helyén**

A v1.4.1 a hibának csak a felét orvosolta. A valódi ok az, hogy néhány másik egyéni kártya
**menet közben kicseréli a böngésző elem-nyilvántartását**. Ami a csere előtt került be, az az
új nyilvántartásban nem látszik, és a Home Assistant nem találja a kártyát. Hogy melyik fut
előbb, az a betöltés sorrendjén múlik, ezért ugyanaz a fájl egyszer működött, másszor nem.

A kártya mostantól a betöltés utáni első másodpercekben többször ellenőrzi, hogy szerepel-e még
a nyilvántartásban, és ha eltűnt, újra bejelentkezik. Így mindegy, milyen sorrendben töltődnek
a kártyák.

---

## v1.4.1 (2026-09-18)

**Javítva: a kártya nem jelent meg, „Configuration error” állt a helyén**

A „Mai adagok” kártya csak feltételesen regisztrálta magát a böngészőben. Ha a Home Assistantban
van olyan másik egyéni kártya, ami saját elem-nyilvántartást hoz magával (több népszerű kártya
ilyen), akkor az a nyilvántartás **tévesen azt mondja, hogy a kártya még nincs regisztrálva**,
a feltétel viszont épp ezért kihagyta a regisztrációt. Az eredmény: a lista helyén
„Configuration error” jelent meg.

Mostantól a kártya feltétel nélkül regisztrál, a kétszeres regisztrációt pedig elnyeli. Ha
eddig működött, ezután is ugyanúgy fog.

---

## v1.4.0 (2026-09-17)

**Kimaradt adag a vezérlőpultról**

Eddig egy adagot csak beadottnak lehetett jelölni innen, vagy visszavonni. A harmadik
állapotot, hogy az állat **nem kapta meg**, csak az appban lehetett rögzíteni. Pedig a
kimaradás tény: ha csak hiányzik a sor, az „még nem adtuk be” képet mutat.

- A **kártyán minden sor végén ott a figyelmeztető jel**: egy koppintás, és az adag
  kimaradtként rögzül. A sor onnantól saját színnel és ikonnal látszik, alatta az ok és az,
  hogy ki rögzítette. Ha mégis beadják, a sorra koppintás javítja az állapotot.
- Új **„Kimaradt ma”** érzékelő, a kimaradt adagok listájával. Erre lehet automatizálást
  építeni: ez az egyetlen állapot, amiről a vezérlőpult magától sosem szólna, mert nem múlik
  el az idővel.
- A `bogancs.dose` szolgáltatás két új mezőt kapott: `missed` és `reason`.
- Az adag-kapcsolók `missed` attribútumot kaptak, és kimaradt adagnál más az ikonjuk.
- A „Hátralévő adagok” érzékelő `given` száma **többé nem számolja beadottnak a kimaradt
  adagot**. Eddig a nap teljesnek látszhatott úgy, hogy az állat nem kapta meg a gyógyszert.

A kimaradás-gomb csak akkor jelenik meg, ha a kiszolgáló is tudja fogadni. Saját üzemeltetésű
példánynál ehhez a Bogáncs 2.12.0 vagy újabb kell; a régebbi kiszolgálóval minden más
változatlanul működik.

---

## v1.3.3 (2026-09-16)

**Javítva a leírásban**

- A *Telepítés kézzel* szakasz mostantól a **végeredményt** írja le mappa-fa alakban, nem a
  másolás irányát. Megmondja azt is, hol keresd a konfigurációs mappát (Home Assistant OS és
  konténeres telepítésnél `/config`, Core telepítésnél `~/.homeassistant`), és hogy a
  `custom_components` könyvtárat létre kell hozni, ha még nincs. A korábbi mondatból nem derült
  ki egyértelműen, hová kerüljön a mappa.

**Megjegyzés**

- A kód nem változott az előző kiadáshoz képest. Azért lett új kiadás, mert a HACS a leírást
  ahhoz a kiadáshoz köti, amelyikkel letöltötted: a javítás a v1.3.2 címke után készült el,
  ezért ott még a régi szöveg látszott.

## v1.3.2 (2026-09-16)

**Új: az integráció hozza a saját kártyáját**

- A kártyaválasztóban megjelenik a *Bogáncs – Mai adagok* kártya. Külön telepíteni nem kell
  semmit: eddig egy ilyen lista összerakásához három külön front-end kiegészítő kellett.
- A lista **soronként** frissül. Egy adag megjelölésekor csak az az egy sor vált át, ezért
  nem villan a képernyő, és a görgetés a helyén marad. A korábbi, sablonból épített
  megoldások a teljes listát újragyártották minden változásnál, és egy hosszú lista aljáról
  visszadobtak a tetejére.
- A koppintás azonnal látszik, a mentés a háttérben fut. Ha a mentés nem sikerül, a sor
  visszaáll: nem marad a képernyőn olyan pipa, ami mögött nincs mentett adag.
- Opciók: `entity`, `title`, `hide_header`, `hide_given`, `by`. Részletek a README-ben.

**Megjegyzés a verziószámhoz**

- Az 1.3.0 és 1.3.1 fejlesztés közben keletkezett, kiadás nem készült belőlük.

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
