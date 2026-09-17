/*
 * Bogancs kisallatkonyv -- "Mai adagok" kartya.
 *
 * MIERT SAJAT KARTYA (Begyo, 2026-09-16): a kioszkon egy config-template-card allitotta elo a
 * listat a szenzor `doses` attributumabol. Az a kartya minden szenzor-valtozaskor UJRA GENERALJA
 * a teljes gyerek-kartyafat, ezert egy pipa bejelolese utan villant a kepernyo, es a gorgetes
 * visszaugrott a lista tetejere. Ez a kartya SOR-SZINTEN frissit: a DOM egyszer epul fel, utana
 * csak az valtozik, ami tenylegesen mas lett.
 *
 * Tovabbi szempont: az integracio telepitese ONMAGABAN legyen eleg. Ezert a kartya nem tamaszkodik
 * se mushroom-ra, se card-mod-ra, se config-template-card-ra, es a HA sajat tema-valtozoibol
 * szinezodik.
 */

const KARTYA = "bogancs-doses";

class BogancsDosesCard extends HTMLElement {
  constructor() {
    super();
    this._sorok = new Map(); // kulcs -> { gyoker, ikon, cim, alcim }
    this._utolso = "";       // az utoljara kirajzolt adatok ujjlenyomata
    this._varakozo = new Map(); // kulcs -> a felhasznalo altal VART allapot, amig a szerver valaszol
    this._varakozoKimaradt = new Map(); // ugyanez a kimaradas-gombra
  }

  setConfig(config) {
    // `hide_header`: a kioszkon mar van sajat fejlec-kartya a szamlaloval, ott a mienk csak
    // ismetles lenne. Ezert a fejlec elrejtheto, es a kartya CSAK a listat adja.
    this._config = Object.assign({ hide_given: false, hide_header: false }, config || {});
  }

  getCardSize() {
    return 3 + Math.ceil(this._sorok.size / 2);
  }

  static getStubConfig(hass) {
    const e = Object.keys(hass.states).find(
      (id) => id.startsWith("sensor.") && hass.states[id].attributes && Array.isArray(hass.states[id].attributes.doses)
    );
    return { type: "custom:" + KARTYA, entity: e || "" };
  }

  set hass(hass) {
    this._hass = hass;
    const allapot = this._allapot();
    if (!allapot) { this._uresen("Nincs Bogáncs adag-szenzor. Add meg az entitást a kártya beállításában."); return; }
    const a = allapot.attributes || {};
    const adagok = Array.isArray(a.doses) ? a.doses : [];
    /* A kimaradas-gomb csak akkor jelenik meg, ha a SZERVER is tudja fogadni. A regi
       kiszolgalo a "missed" mezot nem ismeri, es a given:false-t TORLESNEK veszi -- ott a
       gomb csendben letorolne a sort ahelyett, hogy kimaradast rogzitene. A jel: az uj
       allapot mindig kuld "missed" osszesitot es sor-szintu "missed" mezot. */
    this._tamogatKimaradt = a.missed !== undefined || adagok.some((d) => d.missed !== undefined);
    if (!this._keret) this._epit();
    if (this._config.hide_header) { if (this._fejDoboz) this._fejDoboz.style.display = "none"; this._keret.classList.add("nincs-fej"); }
    else { if (this._fejDoboz) this._fejDoboz.style.display = ""; this._fejlec(a, adagok); }
    this._lista(adagok);
  }

  /* Az entitas: vagy a configbol, vagy az elso olyan szenzor, aminek van `doses` attributuma.
     Az automatikus keresest azert hagyjuk benne, hogy a kartya beallitas NELKUL is mukodjon. */
  _allapot() {
    const h = this._hass;
    if (!h) return null;
    const nev = this._config && this._config.entity;
    if (nev && h.states[nev]) return h.states[nev];
    if (nev) return null;
    const talalt = Object.keys(h.states).find(
      (id) => id.startsWith("sensor.") && h.states[id].attributes && Array.isArray(h.states[id].attributes.doses)
    );
    return talalt ? h.states[talalt] : null;
  }

  _uresen(uzenet) {
    if (!this._keret) this._epit();
    this._sorokDoboz.textContent = "";
    this._sorok.clear();
    const p = document.createElement("div");
    p.className = "ures";
    p.textContent = uzenet;
    this._sorokDoboz.appendChild(p);
  }

  _epit() {
    const arnyek = this.attachShadow ? (this.shadowRoot || this.attachShadow({ mode: "open" })) : this;
    const stilus = document.createElement("style");
    stilus.textContent = `
      ha-card { padding: 12px 8px 8px; }
      ha-card.nincs-fej { padding: 6px 8px 8px; }
      .fej { display:flex; align-items:center; gap:10px; padding: 0 10px 8px; }
      .fej .cim { font-size: 1.05rem; font-weight: 600; color: var(--primary-text-color); flex: 1; }
      .fej .szam { font-size: 1.35rem; font-weight: 700; color: var(--primary-text-color); }
      .fej .alcim { font-size: .82rem; color: var(--secondary-text-color); }
      .sor { display:flex; align-items:center; gap:12px; padding: 10px 10px; border-radius: 10px; cursor: pointer; }
      .sor:hover { background: var(--secondary-background-color); }
      .sor ha-icon { --mdc-icon-size: 26px; flex: none; }
      .szoveg { min-width: 0; flex: 1; }
      .cim1 { font-size: .95rem; color: var(--primary-text-color); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .cim2 { font-size: .78rem; color: var(--secondary-text-color); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .kesik .cim1 { color: var(--error-color); font-weight: 600; }
      .kesz .cim1 { color: var(--secondary-text-color); text-decoration: line-through; }
      /* A kimaradt adag se nem kesz, se nem hatravan: sajat kepe van, kulonben a ket
         allapot osszemosodik es a nap teljesnek latszik ugy, hogy az allat nem kapta meg. */
      .kimaradt .cim1 { color: var(--warning-color, #e8a33d); font-weight: 600; }
      .kihagy { --mdc-icon-size: 20px; flex: none; border: none; background: none; cursor: pointer;
                color: var(--secondary-text-color); padding: 4px; border-radius: 8px; }
      .kihagy:hover { background: var(--secondary-background-color); color: var(--warning-color, #e8a33d); }
      .ures { padding: 14px 12px; color: var(--secondary-text-color); font-size: .9rem; }
    `;
    const kartya = document.createElement("ha-card");
    const fej = document.createElement("div");
    fej.className = "fej";
    this._fejDoboz = fej;
    this._fejIkon = document.createElement("ha-icon");
    this._fejCim = document.createElement("div");
    this._fejCim.className = "cim";
    this._fejSzam = document.createElement("div");
    this._fejSzam.className = "szam";
    fej.appendChild(this._fejIkon);
    const fejSzoveg = document.createElement("div");
    fejSzoveg.className = "cim";
    this._fejFo = document.createElement("div");
    this._fejAlcim = document.createElement("div");
    this._fejAlcim.className = "alcim";
    fejSzoveg.appendChild(this._fejFo);
    fejSzoveg.appendChild(this._fejAlcim);
    fej.appendChild(fejSzoveg);
    fej.appendChild(this._fejSzam);
    this._sorokDoboz = document.createElement("div");
    kartya.appendChild(fej);
    kartya.appendChild(this._sorokDoboz);
    arnyek.appendChild(stilus);
    arnyek.appendChild(kartya);
    this._keret = kartya;
  }

  _fejlec(a, adagok) {
    const kesik = adagok.filter((d) => !this._vartGiven(d) && this._kesikE(d)).length;
    const kesz = adagok.filter((d) => this._vartGiven(d) && !this._vartKimaradt(d)).length;
    const kimaradt = adagok.filter((d) => this._vartKimaradt(d)).length;
    const cim = (this._config && this._config.title) || "Mai adagok";
    if (this._fejFo.textContent !== cim) this._fejFo.textContent = cim;
    const szam = kesz + " / " + adagok.length;
    if (this._fejSzam.textContent !== szam) this._fejSzam.textContent = szam;
    const reszek = [];
    if (kesik > 0) reszek.push(kesik + " késésben");
    if (kimaradt > 0) reszek.push(kimaradt + " kimaradt");
    const alcim = reszek.length
      ? reszek.join(" · ")
      : (kesz === adagok.length && adagok.length ? "mindet megkapta" : "");
    if (this._fejAlcim.textContent !== alcim) this._fejAlcim.textContent = alcim;
    const ikon = kesik > 0 ? "mdi:alert-decagram" : (adagok.length && kesz === adagok.length ? "mdi:check-decagram" : "mdi:pill-multiple");
    if (this._fejIkon.getAttribute("icon") !== ikon) this._fejIkon.setAttribute("icon", ikon);
    this._fejIkon.style.color = kesik > 0 ? "var(--error-color)" : (adagok.length && kesz === adagok.length ? "var(--success-color)" : "var(--state-icon-color)");
  }

  _kulcs(d) { return String(d.medication) + "|" + String(d.scheduled || ""); }

  /* A felhasznalo koppintasa AZONNAL latszik, meg mielott a szerver valaszolna. Amint a
     szenzor ugyanazt mondja, a varakozo bejegyzes torlodik. */
  _vartGiven(d) {
    const k = this._kulcs(d);
    if (this._varakozo.has(k)) {
      const vart = this._varakozo.get(k);
      if (!!d.given === vart) { this._varakozo.delete(k); return !!d.given; }
      return vart;
    }
    return !!d.given;
  }

  _vartKimaradt(d) {
    const k = this._kulcs(d);
    if (this._varakozoKimaradt.has(k)) {
      const vart = this._varakozoKimaradt.get(k);
      if (!!d.missed === vart) { this._varakozoKimaradt.delete(k); return !!d.missed; }
      return vart;
    }
    return !!d.missed;
  }

  _kesikE(d) {
    // A kimaradas LEZART allapot: nem keses. Enelkul a fejlec pirosan sirna olyasmiert,
    // amit mar elintezett valaki.
    if (this._vartKimaradt(d)) return false;
    const m = /^(\d{1,2}):(\d{2})$/.exec(String(d.scheduled || ""));
    if (!m) return false;
    const most = new Date();
    return parseInt(m[1], 10) * 60 + parseInt(m[2], 10) < most.getHours() * 60 + most.getMinutes();
  }

  _lista(adagok) {
    const mutat = this._config && this._config.hide_given
      ? adagok.filter((d) => !this._vartGiven(d))
      : adagok;

    // A DOM-ot csak akkor rendezzuk at, ha a SORREND vagy a TAGSAG valtozott. A tartalom
    // frissitese ettol fuggetlenul, sor-szinten megy -- ez a lenyege az egesznek.
    const kulcsok = mutat.map((d) => this._kulcs(d));
    const ujjlenyomat = kulcsok.join(",");
    if (ujjlenyomat !== this._utolso) {
      this._utolso = ujjlenyomat;
      const kell = new Set(kulcsok);
      for (const [k, sor] of this._sorok) {
        if (!kell.has(k)) { sor.gyoker.remove(); this._sorok.delete(k); }
      }
      let elozo = null;
      for (const k of kulcsok) {
        let sor = this._sorok.get(k);
        if (!sor) { sor = this._sorLetrehoz(k); this._sorok.set(k, sor); }
        const utan = elozo ? elozo.nextSibling : this._sorokDoboz.firstChild;
        if (utan !== sor.gyoker) this._sorokDoboz.insertBefore(sor.gyoker, utan);
        elozo = sor.gyoker;
      }
      const ures = this._sorokDoboz.querySelector(".ures");
      if (ures && kulcsok.length) ures.remove();
      if (!kulcsok.length && !ures) {
        const p = document.createElement("div");
        p.className = "ures";
        p.textContent = adagok.length ? "Mára minden adag megvan." : "Mára nincs beütemezett adag.";
        this._sorokDoboz.appendChild(p);
      }
    }

    for (const d of mutat) this._sorFrissit(this._sorok.get(this._kulcs(d)), d);
  }

  _sorLetrehoz(kulcs) {
    const gyoker = document.createElement("div");
    gyoker.className = "sor";
    const ikon = document.createElement("ha-icon");
    const szoveg = document.createElement("div");
    szoveg.className = "szoveg";
    const cim = document.createElement("div");
    cim.className = "cim1";
    const alcim = document.createElement("div");
    alcim.className = "cim2";
    szoveg.appendChild(cim);
    szoveg.appendChild(alcim);
    // A kimaradasnak SAJAT celpontja van, nem a sorra koppintas: a sor beadast rogzit, a
    // ketto nem fer el ugyanazon a helyen (ugyanez a dontes az appban is).
    const kihagy = document.createElement("ha-icon");
    kihagy.className = "kihagy";
    kihagy.setAttribute("icon", "mdi:alert-outline");
    kihagy.setAttribute("role", "button");
    kihagy.setAttribute("title", "Kimaradt");
    kihagy.addEventListener("click", (ev) => { ev.stopPropagation(); this._kihagy(kulcs); });
    gyoker.appendChild(ikon);
    gyoker.appendChild(szoveg);
    gyoker.appendChild(kihagy);
    gyoker.addEventListener("click", () => this._koppint(kulcs));
    return { gyoker, ikon, cim, alcim, kihagy };
  }

  _sorFrissit(sor, d) {
    if (!sor) return;
    const kimaradt = this._vartKimaradt(d);
    const kesz = !kimaradt && this._vartGiven(d);
    const kesik = !kesz && !kimaradt && this._kesikE(d);
    const ikon = kimaradt ? "mdi:pill-off"
      : (kesz ? "mdi:check-circle" : (kesik ? "mdi:alert-circle" : "mdi:circle-outline"));
    if (sor.ikon.getAttribute("icon") !== ikon) sor.ikon.setAttribute("icon", ikon);
    const szin = kimaradt ? "var(--warning-color, #e8a33d)"
      : (kesz ? "var(--success-color)" : (kesik ? "var(--error-color)" : "var(--state-icon-color)"));
    if (sor.ikon.style.color !== szin) sor.ikon.style.color = szin;
    const cim = [d.scheduled, d.pet, d.med].filter(Boolean).join("  ·  ");
    if (sor.cim.textContent !== cim) sor.cim.textContent = cim;
    // A kimaradasnal nem "megkapta" all, hanem hogy KIMARADT, es ki rogzitette. Ez a ket
    // mondat nem cserelheto fel: az egyik szerint az allat megkapta a gyogyszert.
    const alcim = kimaradt
      ? ["kimaradt", d.miss_reason ? "· " + d.miss_reason : "", d.given_by ? "· " + d.given_by : ""].filter(Boolean).join(" ")
      : (kesz
        ? ["megkapta", d.given_at || "", d.given_by ? "· " + d.given_by : ""].filter(Boolean).join(" ")
        : (d.dose || ""));
    if (sor.alcim.textContent !== alcim) sor.alcim.textContent = alcim;
    if (sor.kihagy) sor.kihagy.style.display = (kimaradt || !this._tamogatKimaradt) ? "none" : "";
    const osztaly = "sor" + (kesz ? " kesz" : "") + (kesik ? " kesik" : "") + (kimaradt ? " kimaradt" : "");
    if (sor.gyoker.className !== osztaly) sor.gyoker.className = osztaly;
  }

  _kihagy(kulcs) {
    const allapot = this._allapot();
    if (!allapot || !this._hass) return;
    const adagok = (allapot.attributes && allapot.attributes.doses) || [];
    const d = adagok.find((x) => this._kulcs(x) === kulcs);
    if (!d || this._vartKimaradt(d)) return;
    this._varakozoKimaradt.set(kulcs, true);
    this._varakozo.delete(kulcs);
    this._sorFrissit(this._sorok.get(kulcs), d);   // azonnali visszajelzes
    if (!this._config.hide_header) this._fejlec(allapot.attributes || {}, adagok);
    this._hass.callService("bogancs", "dose", {
      medication: d.medication,
      scheduled: d.scheduled || "",
      given: false,
      missed: true,
      by: (this._config && this._config.by) || "Home Assistant",
    }).catch(() => {
      // Ha a mentes elszall, NE maradjon a kepernyon kimaradas, ami nincs rogzitve.
      this._varakozoKimaradt.delete(kulcs);
      this._sorFrissit(this._sorok.get(kulcs), d);
    });
  }

  _koppint(kulcs) {
    const allapot = this._allapot();
    if (!allapot || !this._hass) return;
    const adagok = (allapot.attributes && allapot.attributes.doses) || [];
    const d = adagok.find((x) => this._kulcs(x) === kulcs);
    if (!d) return;
    const uj = !this._vartGiven(d);
    this._varakozo.set(kulcs, uj);
    // Ha kimaradtkent allt, a beadas JAVITJA (a szerver is igy kezeli), tehat a kepernyon
    // sem maradhat ott a kimaradas.
    if (uj) this._varakozoKimaradt.set(kulcs, false);
    this._sorFrissit(this._sorok.get(kulcs), d);   // azonnali visszajelzes
    if (!this._config.hide_header) this._fejlec(allapot.attributes || {}, adagok);
    this._hass.callService("bogancs", "dose", {
      medication: d.medication,
      scheduled: d.scheduled || "",
      given: uj,
      by: (this._config && this._config.by) || "Home Assistant",
    }).catch(() => {
      // Ha a mentes elszall, NE maradjon hamis pipa a kepernyon.
      this._varakozo.delete(kulcs);
      this._sorFrissit(this._sorok.get(kulcs), d);
    });
  }
}

if (!customElements.get(KARTYA)) customElements.define(KARTYA, BogancsDosesCard);

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === KARTYA)) {
  window.customCards.push({
    type: KARTYA,
    name: "Bogáncs – Mai adagok",
    description: "A mai gyógyszeradagok listája, koppintásra jelölhető. Az integrációval együtt érkezik.",
    preview: false,
  });
}
