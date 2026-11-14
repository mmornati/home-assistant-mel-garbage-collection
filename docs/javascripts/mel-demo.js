/*
 * Démonstrations en direct : les vraies cartes de l'intégration, alimentées
 * par un jeu de données d'exemple recalé sur la date du jour.
 *
 *   <div data-mel-card="mel-collecte-card" data-config='{"days": 14}'></div>
 *   <button data-mel-moment="truck">…</button>   (fige l'heure des cartes)
 */
(() => {
  const script = document.currentScript;
  const base = new URL("../assets/", script.src);

  function at(date, hours, minutes) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate(), hours, minutes);
  }

  /* Collectes d'exemple : gris mardi et vendredi soir, jaune vendredi soir, marron mercredi matin */
  function events(now) {
    const list = [];
    for (let offset = -1; offset < 75; offset += 1) {
      const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() + offset);
      const add = (types, h1, m1, h2, m2) =>
        list.push({ start: at(day, h1, m1).toISOString(), end: at(day, h2, m2).toISOString(), types, mode: "truck" });
      if (day.getDay() === 2) add(["omr"], 18, 30, 23, 59);
      if (day.getDay() === 3) add(["dv"], 6, 0, 13, 0);
      if (day.getDay() === 5) add(["omr", "emb"], 18, 30, 23, 59);
    }
    return list;
  }

  /* Horaires des déchèteries de la MEL : 7 h 30 – 18 h (19 h d'avril à octobre), dimanche 8 h – 13 h */
  function hours(day) {
    if (day.getDay() === 0) return [8, 0, 13, 0];
    const summer = day.getMonth() >= 3 && day.getMonth() <= 9;
    return [7, 30, summer ? 19 : 18, 0];
  }

  function status(place, now) {
    if (place.kind === "recycling_center") {
      const [h1, m1, h2, m2] = hours(now);
      const open = at(now, h1, m1);
      const close = at(now, h2, m2);
      place.open = now >= open && now < close;
      place.closes_at = place.open ? close.toISOString() : null;
      let next = open;
      if (now >= open) {
        const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        const [h, m] = hours(tomorrow);
        next = at(tomorrow, h, m);
      }
      place.next_open = next.toISOString();
    } else if (place.kind === "mobile") {
      place.open = false;
      if (place.next_open && new Date(place.next_open) < now) place.next_open = null;
    }
    return place;
  }

  function payload(source, now) {
    const data = JSON.parse(JSON.stringify(source));
    for (const entry of data.entries) {
      entry.events = events(now).filter((event) => new Date(event.end) > now);
      entry.now = now.toISOString();
      for (const places of Object.values(entry.facilities)) places.forEach((place) => status(place, now));
    }
    return data;
  }

  /* Moments proposés par le simulateur d'heure */
  function moment(name) {
    const now = new Date();
    const next = (weekday, h, m) => {
      const day = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      do day.setDate(day.getDate() + 1);
      while (day.getDay() !== weekday);
      return at(day, h, m);
    };
    return {
      eve: next(2, 20, 15), // mardi soir : le bac marron sort ce soir
      today: next(5, 9, 30), // vendredi matin : deux bacs à sortir avant 18 h 30
      truck: next(5, 19, 40), // vendredi soir : le camion passe
      later: next(6, 10, 0), // samedi : rien avant mardi
    }[name];
  }

  let source;

  function mount(now) {
    // les anciennes cartes sont retirées avant de vider leur cache commun
    for (const holder of document.querySelectorAll("[data-mel-card]")) holder.replaceChildren();
    window.dispatchEvent(new Event("mel-collecte-refresh"));
    const data = payload(source, now || new Date());
    const hass = { callWS: async () => data };
    for (const holder of document.querySelectorAll("[data-mel-card]")) {
      const config = JSON.parse(holder.dataset.config || "{}");
      if (now) config.now = now.toISOString();
      const card = document.createElement(holder.dataset.melCard);
      card.setConfig(config);
      holder.replaceChildren(card);
      card.hass = hass;
    }
  }

  function start() {
    if (!document.querySelector("[data-mel-card]")) return;
    const ready = customElements.get("mel-collecte-card")
      ? Promise.resolve()
      : new Promise((resolve, reject) => {
          const tag = document.createElement("script");
          tag.src = new URL("mel-collecte-cards.js", base);
          tag.onload = resolve;
          tag.onerror = reject;
          document.head.appendChild(tag);
        });
    Promise.all([ready, source ? source : fetch(new URL("demo.json", base)).then((response) => response.json())])
      .then(([, data]) => {
        source = data;
        mount();
      })
      .catch(() => {
        for (const holder of document.querySelectorAll("[data-mel-card]")) {
          holder.textContent = "La démonstration n'a pas pu être chargée.";
        }
      });
  }

  document.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-mel-moment]");
    if (!chip || !source) return;
    for (const other of document.querySelectorAll("[data-mel-moment]")) {
      other.setAttribute("aria-pressed", String(other === chip));
    }
    const name = chip.dataset.melMoment;
    mount(name === "live" ? null : moment(name));
  });

  // Material recharge les pages sans recharger le document
  if (window.document$ && window.document$.subscribe) window.document$.subscribe(start);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
