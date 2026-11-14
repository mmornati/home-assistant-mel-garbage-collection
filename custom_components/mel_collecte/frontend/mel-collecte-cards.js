/*
 * Cartes de tableau de bord de l'intégration MEL Collecte.
 *
 * JavaScript simple, sans compilation ni dépendance : Home Assistant charge ce
 * fichier dans chaque navigateur et les cartes apparaissent dans le sélecteur
 * « Ajouter une carte ».
 *
 * Les cartes ne lisent pas les entités une à une : elles demandent à
 * l'intégration (commande websocket `mel_collecte/dashboard`) tout ce qu'il
 * faut afficher pour une adresse. Elles fonctionnent donc quels que soient les
 * noms et la langue des entités.
 */
(() => {
  const DOMAIN = "mel_collecte";
  const REFRESH_MS = 5 * 60 * 1000;

  // Couleurs des couvercles des bacs de la MEL
  const COLORS = {
    grey: "#7b8794",
    yellow: "#f0b90b",
    brown: "#8d5b3a",
    green: "#2e9d5c",
    purple: "#8a5cd6",
    "light-green": "#6faa2c",
    blue: "#2f7fd1",
    pink: "#d6558f",
    orange: "#e5822b",
    red: "#d64545",
    teal: "#16968a",
    "blue-grey": "#6c7f8c",
  };

  const TEXTS = {
    fr: {
      loading: "Chargement des collectes…",
      unavailable: "Les données MEL Collecte ne sont pas disponibles pour le moment.",
      no_entry: "Aucune adresse MEL Collecte n'est configurée.",
      no_collection: "Aucune collecte prévue pour l'instant",
      no_collection_sub: "Le calendrier de votre adresse ne contient pas de passage à venir.",
      bins: {
        omr: "le bac gris",
        emb: "le bac jaune",
        cs: "le bac jaune",
        dv: "le bac marron",
        bio: "le bac marron",
        verre: "le verre",
        enc: "les encombrants",
      },
      short: {
        omr: "Ordures ménagères",
        emb: "Emballages",
        cs: "Emballages",
        dv: "Biodéchets",
        bio: "Biodéchets",
        alim: "Déchets alimentaires",
        verre: "Verre",
        enc: "Encombrants",
        jrm: "Papiers",
        text: "Textiles",
        compost: "Compost",
      },
      and: "et",
      now_title: (bins) => `Collecte en cours : ${bins}`,
      now_sub: (end) => `Le camion passe jusqu'à ${end}. Rentrez le bac dès qu'il est vidé.`,
      out_now: (bins) => `Sortez ${bins} maintenant`,
      out_today: (bins, start) => `Sortez ${bins} avant ${start}`,
      out_tonight: (bins) => `Ce soir, sortez ${bins}`,
      tomorrow: (bins) => `Demain : ${bins}`,
      later: (day, bins) => `${day} : ${bins}`,
      sub_window: (labels, day, start, end) => `${labels} · ${day} de ${start} à ${end}`,
      sub_tonight: (labels, start, end) => `${labels} · passage demain de ${start} à ${end}, bac à sortir après 19 h`,
      in_days: (n) => (n === 0 ? "aujourd'hui" : n === 1 ? "demain" : `dans ${n} jours`),
      today: "Aujourd'hui",
      alerts_more: (n) => `${n} autres informations`,
      collections_on: (day) => `Collectes du ${day}`,
      nothing_that_day: "Pas de collecte ce jour-là.",
      previous_month: "Mois précédent",
      next_month: "Mois suivant",
      guide_title: "Où ça se jette ?",
      search: "Un déchet, un objet…",
      search_label: "Chercher un déchet",
      accepted: "À déposer",
      rejected: "À ne pas déposer",
      yes: "Oui",
      no: "Non",
      no_match: (q) => `Rien trouvé pour « ${q} ». Essayez un mot plus simple, ou appelez la MEL.`,
      goes_in: (label) => `Va dans : ${label}`,
      not_in: (label) => `Pas dans : ${label}`,
      contact: "Une question ? Service déchets de la MEL",
      places_title: "Autour de chez vous",
      tabs: { recycling_center: "Déchèteries", mobile: "Mobiles", glass: "Verre", composter: "Compost" },
      open_until: (t) => `Ouverte jusqu'à ${t}`,
      closed_opens: (when) => `Fermée · ouvre ${when}`,
      closed: "Fermée",
      visit_now: (t) => `Sur place jusqu'à ${t}`,
      next_visit: (when) => `Prochain passage ${when}`,
      no_visit: "Pas de passage prévu",
      free_access: "Accès libre",
      route: "Itinéraire",
      route_to: (name) => `Itinéraire vers ${name}`,
      home: "Chez vous",
      km: (n) => `${n} km`,
      m: (n) => `${n} m`,
      no_places: "Aucun lieu connu près de cette adresse.",
      at: "à",
      updated: (when) => `Données MEL du ${when}`,
      map_label: "Carte des lieux autour de l'adresse",
    },
    en: {
      loading: "Loading collections…",
      unavailable: "MEL Collecte data is not available right now.",
      no_entry: "No MEL Collecte address is set up.",
      no_collection: "No collection planned for now",
      no_collection_sub: "The calendar for your address has no upcoming collection.",
      bins: {
        omr: "the grey bin",
        emb: "the yellow bin",
        cs: "the yellow bin",
        dv: "the brown bin",
        bio: "the brown bin",
        verre: "the glass",
        enc: "bulky items",
      },
      short: {
        omr: "Household waste",
        emb: "Packaging",
        cs: "Packaging",
        dv: "Biowaste",
        bio: "Biowaste",
        alim: "Food waste",
        verre: "Glass",
        enc: "Bulky items",
        jrm: "Paper",
        text: "Textiles",
        compost: "Compost",
      },
      and: "and",
      now_title: (bins) => `Collection in progress: ${bins}`,
      now_sub: (end) => `The truck comes by until ${end}. Bring the bin back in once it is emptied.`,
      out_now: (bins) => `Put out ${bins} now`,
      out_today: (bins, start) => `Put out ${bins} before ${start}`,
      out_tonight: (bins) => `Tonight, put out ${bins}`,
      tomorrow: (bins) => `Tomorrow: ${bins}`,
      later: (day, bins) => `${day}: ${bins}`,
      sub_window: (labels, day, start, end) => `${labels} · ${day} from ${start} to ${end}`,
      sub_tonight: (labels, start, end) => `${labels} · collected tomorrow from ${start} to ${end}, bin out after 7 pm`,
      in_days: (n) => (n === 0 ? "today" : n === 1 ? "tomorrow" : `in ${n} days`),
      today: "Today",
      alerts_more: (n) => `${n} more notices`,
      collections_on: (day) => `Collections on ${day}`,
      nothing_that_day: "No collection that day.",
      previous_month: "Previous month",
      next_month: "Next month",
      guide_title: "Where does it go?",
      search: "A piece of waste, an object…",
      search_label: "Search for a piece of waste",
      accepted: "Goes in",
      rejected: "Keep out",
      yes: "Yes",
      no: "No",
      no_match: (q) => `Nothing found for “${q}”. Try a simpler word, or call the MEL.`,
      goes_in: (label) => `Goes in: ${label}`,
      not_in: (label) => `Not in: ${label}`,
      contact: "A question? MEL waste service",
      places_title: "Around you",
      tabs: { recycling_center: "Recycling centres", mobile: "Mobile", glass: "Glass", composter: "Compost" },
      open_until: (t) => `Open until ${t}`,
      closed_opens: (when) => `Closed · opens ${when}`,
      closed: "Closed",
      visit_now: (t) => `On site until ${t}`,
      next_visit: (when) => `Next visit ${when}`,
      no_visit: "No visit planned",
      free_access: "Open access",
      route: "Directions",
      route_to: (name) => `Directions to ${name}`,
      home: "Home",
      km: (n) => `${n} km`,
      m: (n) => `${n} m`,
      no_places: "No known place near this address.",
      at: "at",
      updated: (when) => `MEL data from ${when}`,
      map_label: "Map of places around the address",
    },
  };

  // ---------------------------------------------------------------- données

  let cache = null; // { promise, data, at }
  const listeners = new Set();

  function loadDashboard(hass, force) {
    const fresh = cache && Date.now() - cache.at < REFRESH_MS;
    if (cache && (fresh || cache.pending) && !force) return cache.promise;
    const request = { at: Date.now(), pending: true, data: cache && cache.data };
    request.promise = hass
      .callWS({ type: `${DOMAIN}/dashboard` })
      .then((data) => {
        request.data = data;
        request.pending = false;
        listeners.forEach((listener) => listener());
        return data;
      })
      .catch((error) => {
        request.pending = false;
        request.error = error;
        request.at = Date.now() - REFRESH_MS + 30000; // nouvel essai dans 30 s
        listeners.forEach((listener) => listener());
        throw error;
      });
    cache = request;
    return request.promise;
  }

  /* `window.dispatchEvent(new Event("mel-collecte-refresh"))` force une relecture immédiate */
  const mounted = new Set();
  window.addEventListener("mel-collecte-refresh", () => {
    cache = null;
    mounted.forEach((card) => card._hass && card._load());
  });

  // ---------------------------------------------------------------- outils

  const esc = (value) =>
    String(value == null ? "" : value).replace(
      /[&<>"']/g,
      (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char],
    );
  const fold = (text) =>
    String(text || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase();
  const dayKey = (date) => `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
  const startOfDay = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const daysBetween = (from, to) => Math.round((startOfDay(to) - startOfDay(from)) / 86400000);
  const capital = (text) => text.charAt(0).toUpperCase() + text.slice(1);

  function formatters(lang) {
    const locale = lang === "en" ? "en-GB" : "fr-FR";
    const time = new Intl.DateTimeFormat(locale, { hour: "numeric", minute: "2-digit" });
    return {
      time: (date) => {
        const text = time.format(date);
        return lang === "en" ? text : text.replace(":", " h ").replace(" h 00", " h");
      },
      weekday: (date) => new Intl.DateTimeFormat(locale, { weekday: "long" }).format(date),
      weekdayShort: (date) => new Intl.DateTimeFormat(locale, { weekday: "narrow" }).format(date),
      dayMonth: (date) => new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long" }).format(date),
      shortDate: (date) => new Intl.DateTimeFormat(locale, { weekday: "short", day: "numeric", month: "short" }).format(date),
      month: (date) => new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(date),
      number: (value, digits) => new Intl.NumberFormat(locale, { maximumFractionDigits: digits }).format(value),
    };
  }

  const colorOf = (entry, code) => COLORS[(entry.types[code] || {}).color] || COLORS[code] || COLORS["blue-grey"];

  function list(items, and) {
    if (items.length < 2) return items.join("");
    return `${items.slice(0, -1).join(", ")} ${and} ${items[items.length - 1]}`;
  }

  /* Regroupe les collectes par jour : [{ date, start, end, types: [codes] }] */
  function collectionDays(entry) {
    const days = new Map();
    for (const event of entry.events) {
      const start = new Date(event.start);
      const end = new Date(event.end);
      const key = dayKey(start);
      const day = days.get(key) || { date: startOfDay(start), start, end, types: [] };
      if (start < day.start) day.start = start;
      if (end > day.end) day.end = end;
      for (const code of event.types) if (!day.types.includes(code)) day.types.push(code);
      days.set(key, day);
    }
    return [...days.values()].sort((a, b) => a.start - b.start);
  }

  // ---------------------------------------------------------------- dessins

  /* Un bac roulant : cuve anthracite, couvercle à la couleur de la collecte */
  function binSvg(color, extra = "") {
    return `<svg class="bin ${extra}" viewBox="0 0 64 84" aria-hidden="true" style="--lid:${color}">
      <ellipse class="bin-shadow" cx="33" cy="80" rx="24" ry="3.2"/>
      <path class="bin-body" d="M11 25h42l-4.2 47.5a5 5 0 0 1-5 4.5H20.2a5 5 0 0 1-5-4.5z"/>
      <path class="bin-rib" d="M20 34l1.6 34M32 34v34M44 34l-1.6 34"/>
      <circle class="bin-wheel" cx="19" cy="76" r="5.5"/><circle class="bin-hub" cx="19" cy="76" r="1.8"/>
      <g class="bin-lid">
        <path class="bin-lid-top" d="M7 15.5a5 5 0 0 1 5-5h40a5 5 0 0 1 5 5V22a3 3 0 0 1-3 3H10a3 3 0 0 1-3-3z"/>
        <rect class="bin-lid-grip" x="24" y="5.5" width="16" height="6" rx="3"/>
        <path class="bin-lid-shine" d="M12 14.5h26"/>
      </g>
    </svg>`;
  }

  const truckSvg = `<svg class="truck" viewBox="0 0 120 60" aria-hidden="true">
    <path class="truck-box" d="M4 12a6 6 0 0 1 6-6h58a4 4 0 0 1 4 4v34H4z"/>
    <path class="truck-rib" d="M20 12v26M36 12v26M52 12v26"/>
    <path class="truck-cab" d="M76 18h17a6 6 0 0 1 5 2.7l9.5 14.3a6 6 0 0 1 1 3.3V44H76z"/>
    <path class="truck-glass" d="M82 23h10.5l7.5 11.5H82z"/>
    <rect class="truck-base" x="2" y="42" width="110" height="6" rx="2"/>
    <circle class="truck-wheel" cx="24" cy="49" r="8"/><circle class="truck-hub" cx="24" cy="49" r="3"/>
    <circle class="truck-wheel" cx="46" cy="49" r="8"/><circle class="truck-hub" cx="46" cy="49" r="3"/>
    <circle class="truck-wheel" cx="92" cy="49" r="8"/><circle class="truck-hub" cx="92" cy="49" r="3"/>
  </svg>`;

  /* Silhouette lilloise : pignons à gradins et beffroi, derrière le trottoir */
  const skylineSvg = `<svg class="skyline" viewBox="0 0 400 96" preserveAspectRatio="xMaxYMax slice" aria-hidden="true">
    <path d="M0 96V58h8v-6h8v-6h8v-6h10v6h8v6h8v6h6V44h7v-7h7v-7h9v7h7v7h7v52zM120 96V62h10V50h6v-8h6v-8h8v8h6v8h6v12h8v34zM176 96V66h9v-7h8v-7h9v7h8v7h8v30z
      M232 96V40h5V22h4V10h3V2h4v8h3v12h4v18h5v56zM262 96V60h7v-7h7v-7h8v7h7v7h7v36zM306 96V52h8v-7h7v-7h9v7h7v7h8v44zM352 96V64h8v-6h8v-6h8v6h8v6h8v32z"/>
    <path class="skyline-win" d="M20 70h5v9h-5zm14 0h5v9h-5zM74 62h5v9h-5zm14 0h5v9h-5zM136 68h5v9h-5zm14 0h5v9h-5zM190 76h5v8h-5zm12 0h5v8h-5zM241 50h6v10h-6zm0 20h6v10h-6zM274 72h5v8h-5zm12 0h5v8h-5zM318 64h5v9h-5zm13 0h5v9h-5zM364 76h5v8h-5zm12 0h5v8h-5z"/>
  </svg>`;

  const ICONS = {
    check: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4.5 10.5l3.6 3.6 7.4-8" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    cross: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5.5 5.5l9 9m0-9l-9 9" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
    search: '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="9" cy="9" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M13.2 13.2L17 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    chevron: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M8 4.5l5.5 5.5L8 15.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    route: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.5l7.5 7.5-7.5 7.5L2.5 10z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M7.5 12.5V10a1 1 0 0 1 1-1h4m-1.8-2l2 2-2 2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    info: '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M10 9.2v4.6" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/><circle cx="10" cy="6.3" r="1.1" fill="currentColor"/></svg>',
    warning: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3l7.5 13h-15z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M10 8.2v3.6" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/><circle cx="10" cy="14" r="1" fill="currentColor"/></svg>',
    phone: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5.2 3h2.4l1.2 3.6-1.7 1.3a9 9 0 0 0 5 5l1.3-1.7L17 12.4v2.4a2 2 0 0 1-2.2 2A13 13 0 0 1 3.2 5.2 2 2 0 0 1 5.2 3z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
  };

  // ---------------------------------------------------------------- styles

  const STYLES = `
    :host {
      display: block;
      --mel-ink: var(--primary-text-color, #1c1f24);
      --mel-soft: var(--secondary-text-color, #5f6875);
      --mel-line: var(--divider-color, rgba(127, 127, 127, 0.25));
      --mel-surface: var(--ha-card-background, var(--card-background-color, #fff));
      --mel-accent: var(--primary-color, #1f6fd0);
      --mel-open: #1f9254;
      --mel-shut: #c2453c;
      --mel-ease: cubic-bezier(0.16, 1, 0.3, 1);
      --tint: var(--mel-accent);
    }
    * { box-sizing: border-box; }
    ::selection { background: color-mix(in srgb, var(--tint) 30%, transparent); }
    ha-card, .card {
      display: block;
      overflow: hidden;
      color: var(--mel-ink);
      font-variant-numeric: tabular-nums;
    }
    .card {
      background: var(--mel-surface);
      border-radius: var(--ha-card-border-radius, 12px);
      border: 1px solid var(--mel-line);
    }
    button { font: inherit; color: inherit; background: none; border: 0; padding: 0; cursor: pointer; }
    button:focus-visible, a:focus-visible, input:focus-visible {
      outline: 2px solid var(--tint);
      outline-offset: 2px;
    }
    a { color: inherit; }
    h2 { margin: 0; font-size: 1.05rem; font-weight: 600; letter-spacing: -0.01em; }
    .head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 18px 0; }
    .message { padding: 28px 20px; color: var(--mel-soft); text-align: center; text-wrap: balance; }
    .icon { width: 20px; height: 20px; flex: none; display: inline-flex; }
    .icon svg { width: 100%; height: 100%; }

    /* --- bacs --- */
    .bin { display: block; overflow: visible; }
    .bin-shadow { fill: rgba(0, 0, 0, 0.16); }
    .bin-body { fill: #46515c; }
    .bin-rib { fill: none; stroke: rgba(255, 255, 255, 0.13); stroke-width: 2; stroke-linecap: round; }
    .bin-wheel { fill: #20262c; }
    .bin-hub { fill: #8a949e; }
    .bin-lid { transform-origin: 8px 24px; transform-box: view-box; }
    .bin-lid-top, .bin-lid-grip { fill: var(--lid); }
    .bin-lid-shine { stroke: rgba(255, 255, 255, 0.45); stroke-width: 2.4; stroke-linecap: round; fill: none; }

    /* --- prochaine collecte --- */
    .scene {
      position: relative;
      padding: 20px 20px 0;
      background:
        linear-gradient(180deg, color-mix(in srgb, var(--tint) 20%, var(--mel-surface)) 0%, color-mix(in srgb, var(--tint) 7%, var(--mel-surface)) 100%);
      transition: background 0.6s var(--mel-ease);
    }
    .scene h2 {
      font-size: clamp(1.35rem, 5.2cqi, 1.75rem);
      line-height: 1.15;
      font-weight: 700;
      letter-spacing: -0.02em;
      text-wrap: balance;
      max-width: 22ch;
    }
    .scene p { margin: 8px 0 0; color: color-mix(in srgb, var(--mel-ink) 72%, var(--tint)); line-height: 1.4; max-width: 46ch; text-wrap: pretty; }
    .street { position: relative; height: 118px; margin: 10px -20px 0; overflow: hidden; }
    .skyline { position: absolute; right: 0; bottom: 22px; width: 100%; height: 96px; fill: color-mix(in srgb, var(--tint) 30%, var(--mel-surface)); }
    .skyline-win { fill: color-mix(in srgb, var(--tint) 9%, var(--mel-surface)); }
    .kerb {
      position: absolute; left: 0; right: 0; bottom: 0; height: 22px;
      background: color-mix(in srgb, var(--mel-ink) 13%, var(--mel-surface));
      border-top: 3px solid color-mix(in srgb, var(--mel-ink) 26%, var(--mel-surface));
    }
    .kerb::after {
      content: ""; position: absolute; left: 0; right: 0; top: 8px; height: 2px;
      background: repeating-linear-gradient(90deg, color-mix(in srgb, var(--mel-surface) 80%, transparent) 0 18px, transparent 18px 34px);
    }
    .lineup { position: absolute; left: 20px; right: 20px; bottom: 12px; display: flex; align-items: flex-end; gap: 6px; }
    .lineup .slot { display: flex; flex-direction: column; align-items: center; }
    .lineup .bin { width: 44px; opacity: 0.5; filter: saturate(0.55); transition: opacity 0.4s, filter 0.4s; }
    .lineup .due { margin-right: 10px; }
    .lineup .due .bin { width: 78px; opacity: 1; filter: none; animation: roll-in 0.9s var(--mel-ease) both; }
    .lineup .due .bin-lid { animation: lid 3.6s var(--mel-ease) 0.9s infinite; }
    .lineup .due:nth-child(2) .bin { animation-delay: 0.12s; }
    .truck { position: absolute; bottom: 9px; right: 18px; width: 128px; scale: -1 1; }
    .truck-box { fill: color-mix(in srgb, var(--tint) 78%, #1d2329); }
    .truck-rib { stroke: rgba(255, 255, 255, 0.22); stroke-width: 2; fill: none; }
    .truck-cab { fill: #f4f6f8; }
    .truck-glass { fill: #8ec3ea; }
    .truck-base { fill: #2a3138; }
    .truck-wheel { fill: #1b2025; }
    .truck-hub { fill: #9aa4ad; }
    .moving .truck { animation: drive 7s cubic-bezier(0.45, 0, 0.2, 1) infinite; }
    .rail { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; padding: 12px 12px 14px; }
    .rail .day { display: flex; flex-direction: column; align-items: center; gap: 3px; min-width: 0; padding: 4px 0; border-radius: 9px; }
    .rail .wd { font-size: 0.68rem; color: var(--mel-soft); text-transform: uppercase; }
    .rail .num { font-size: 0.86rem; line-height: 1; padding: 5px 0; width: 26px; text-align: center; border-radius: 99px; }
    .rail .today .num { background: var(--mel-ink); color: var(--mel-surface); font-weight: 600; }
    .rail .lids { display: flex; flex-direction: column; gap: 2px; height: 14px; justify-content: flex-start; }
    .lid-mark { display: block; width: 16px; height: 5px; border-radius: 3px 3px 1px 1px; background: var(--c); }
    .notices { border-top: 1px solid var(--mel-line); }
    .notice { display: flex; gap: 10px; padding: 12px 18px; align-items: flex-start; width: 100%; text-align: left; }
    .notice + .notice { border-top: 1px solid var(--mel-line); }
    .notice .icon { margin-top: 1px; color: var(--mel-accent); }
    .notice.danger .icon, .notice.warning .icon { color: #c9731a; }
    .notice strong { display: block; font-weight: 600; line-height: 1.3; }
    .notice span.body { display: block; color: var(--mel-soft); font-size: 0.88rem; line-height: 1.45; margin-top: 3px; }
    .notice:not(.open) span.body { display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
    .foot { padding: 0 18px 12px; font-size: 0.75rem; color: var(--mel-soft); }

    /* --- calendrier --- */
    .nav { display: flex; gap: 4px; }
    .nav button { width: 34px; height: 34px; border-radius: 99px; display: grid; place-items: center; color: var(--mel-soft); }
    .nav button:hover { background: color-mix(in srgb, var(--mel-ink) 8%, transparent); color: var(--mel-ink); }
    .nav button:first-child .icon { transform: scaleX(-1); }
    .nav button[disabled] { opacity: 0.3; cursor: default; }
    .month { display: grid; grid-template-columns: repeat(7, 1fr); padding: 10px 12px 6px; row-gap: 2px; }
    .month .wd { font-size: 0.7rem; color: var(--mel-soft); text-align: center; padding: 4px 0 6px; text-transform: uppercase; }
    .cell { display: flex; flex-direction: column; align-items: center; gap: 3px; padding: 5px 0 6px; border-radius: 10px; min-height: 46px; }
    button.cell:hover { background: color-mix(in srgb, var(--mel-ink) 6%, transparent); }
    .cell .num { font-size: 0.9rem; width: 28px; line-height: 28px; text-align: center; border-radius: 99px; }
    .cell.past .num { color: var(--mel-soft); opacity: 0.6; }
    .cell.today .num { background: var(--mel-ink); color: var(--mel-surface); font-weight: 600; }
    .cell.picked { background: color-mix(in srgb, var(--tint) 14%, transparent); }
    .cell .lids { display: flex; gap: 2px; }
    .cell .lid-mark { width: 12px; }
    .detail { border-top: 1px solid var(--mel-line); padding: 12px 18px 14px; min-height: 62px; }
    .detail h3 { margin: 0 0 8px; font-size: 0.82rem; font-weight: 600; color: var(--mel-soft); }
    .detail ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
    .detail li { display: flex; align-items: center; gap: 10px; }
    .detail li .lid-mark { width: 18px; height: 6px; flex: none; }
    .detail li small { color: var(--mel-soft); margin-left: auto; font-size: 0.85rem; white-space: nowrap; }
    .legend { display: flex; flex-wrap: wrap; gap: 6px 14px; padding: 0 18px 14px; font-size: 0.8rem; color: var(--mel-soft); }
    .legend span { display: inline-flex; align-items: center; gap: 6px; }

    /* --- guide du tri --- */
    .search { position: relative; margin: 14px 18px 0; }
    .search .icon { position: absolute; left: 12px; top: 50%; translate: 0 -50%; color: var(--mel-soft); pointer-events: none; }
    .search input {
      width: 100%; font: inherit; color: var(--mel-ink); caret-color: var(--tint);
      padding: 11px 12px 11px 40px; border-radius: 12px;
      border: 1px solid var(--mel-line);
      background: color-mix(in srgb, var(--mel-ink) 4%, var(--mel-surface));
    }
    .search input::placeholder { color: var(--mel-soft); opacity: 1; }
    .chips { display: flex; gap: 6px; padding: 12px 18px 2px; overflow-x: auto; scrollbar-width: none; }
    .chips::-webkit-scrollbar { display: none; }
    .chip {
      display: inline-flex; align-items: center; gap: 7px; white-space: nowrap;
      padding: 7px 12px; border-radius: 99px; font-size: 0.86rem;
      border: 1px solid var(--mel-line); color: var(--mel-soft);
      transition: background 0.2s, color 0.2s, border-color 0.2s;
    }
    .chip:hover { color: var(--mel-ink); }
    .chip[aria-selected="true"] { background: color-mix(in srgb, var(--c) 16%, var(--mel-surface)); border-color: color-mix(in srgb, var(--c) 55%, var(--mel-surface)); color: var(--mel-ink); font-weight: 600; }
    .chip .lid-mark { width: 14px; }
    .sorted { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 4px 22px; padding: 12px 18px 6px; }
    .sorted h3, .results h3 { margin: 6px 0 6px; font-size: 0.8rem; font-weight: 600; display: flex; align-items: center; gap: 7px; }
    .sorted h3.ok, .mark.ok { color: var(--mel-open); }
    .sorted h3.ko, .mark.ko { color: var(--mel-shut); }
    .sorted ul, .results ul { list-style: none; margin: 0; padding: 0; }
    .sorted li { padding: 5px 0; line-height: 1.4; font-size: 0.92rem; border-top: 1px solid color-mix(in srgb, var(--mel-line) 60%, transparent); }
    .sorted li:first-child { border-top: 0; }
    .sorted .more { color: var(--mel-accent); font-size: 0.86rem; padding: 6px 0; }
    .rules { margin: 4px 18px 12px; padding: 10px 12px; border-radius: 10px; font-size: 0.86rem; line-height: 1.45; color: var(--mel-soft); background: color-mix(in srgb, var(--mel-ink) 5%, transparent); }
    .results { padding: 10px 18px 8px; }
    .results li { display: flex; gap: 10px; padding: 9px 0; border-top: 1px solid var(--mel-line); align-items: flex-start; }
    .results li:first-child { border-top: 0; }
    .results .mark { margin-top: 1px; }
    .results p { margin: 0; line-height: 1.4; }
    .results small { display: flex; align-items: center; gap: 6px; color: var(--mel-soft); margin-top: 3px; font-size: 0.82rem; }
    mark { background: color-mix(in srgb, var(--tint) 28%, transparent); color: inherit; border-radius: 3px; padding: 0 1px; }
    .contact { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; padding: 10px 18px 14px; border-top: 1px solid var(--mel-line); font-size: 0.85rem; color: var(--mel-soft); }
    .contact a { display: inline-flex; align-items: center; gap: 6px; color: var(--mel-ink); font-weight: 600; text-decoration: none; }
    .contact a:hover { text-decoration: underline; text-underline-offset: 3px; }

    /* --- déchèteries --- */
    .tabs { display: flex; gap: 2px; padding: 10px 14px 0; overflow-x: auto; scrollbar-width: none; }
    .tabs::-webkit-scrollbar { display: none; }
    .tab { padding: 8px 12px; border-radius: 99px; font-size: 0.88rem; color: var(--mel-soft); white-space: nowrap; }
    .tab:hover { color: var(--mel-ink); }
    .tab[aria-selected="true"] { background: var(--mel-ink); color: var(--mel-surface); font-weight: 600; }
    .map { display: block; width: 100%; height: auto; margin-top: 8px; }
    .map .ring { fill: none; stroke: var(--mel-line); stroke-dasharray: 2 5; }
    .map .ring-label { fill: var(--mel-soft); font-size: 9px; paint-order: stroke; stroke: var(--mel-surface); stroke-width: 4px; stroke-linejoin: round; }
    .map .spoke { stroke: color-mix(in srgb, var(--mel-ink) 18%, transparent); stroke-width: 1; }
    .map .home { fill: var(--mel-ink); }
    .map .home-roof { fill: var(--mel-surface); }
    .map .pin circle { fill: var(--mel-surface); stroke: var(--mel-soft); stroke-width: 1.6; }
    .map .pin text { fill: var(--mel-ink); font-size: 10px; font-weight: 600; text-anchor: middle; dominant-baseline: central; }
    .map .pin.open circle { fill: var(--mel-open); stroke: var(--mel-open); }
    .map .pin.open text { fill: #fff; }
    .map .pin.shut circle { stroke: var(--mel-shut); }
    .map .pin.first circle { stroke-width: 2.4; }
    .places { list-style: none; margin: 0; padding: 4px 8px 10px; }
    .place { display: grid; grid-template-columns: 26px 1fr auto; gap: 2px 10px; align-items: center; padding: 10px; border-radius: 12px; }
    .place:hover { background: color-mix(in srgb, var(--mel-ink) 5%, transparent); }
    .place .rank { width: 24px; height: 24px; border-radius: 99px; display: grid; place-items: center; font-size: 0.78rem; font-weight: 600; border: 1.6px solid var(--mel-soft); grid-row: span 2; }
    .place.open .rank { background: var(--mel-open); border-color: var(--mel-open); color: #fff; }
    .place.shut .rank { border-color: var(--mel-shut); }
    .place .name { font-weight: 600; line-height: 1.3; min-width: 0; overflow-wrap: anywhere; }
    .place .dist { color: var(--mel-soft); font-size: 0.86rem; white-space: nowrap; }
    .place .state { font-size: 0.86rem; color: var(--mel-soft); line-height: 1.35; grid-column: 2; }
    .place.open .state b { color: var(--mel-open); }
    .place.shut .state b { color: var(--mel-shut); }
    .place .state b { font-weight: 600; }
    .place .go { grid-column: 3; grid-row: 2; justify-self: end; display: inline-flex; align-items: center; gap: 4px; font-size: 0.82rem; color: var(--mel-accent); text-decoration: none; padding: 4px 0 4px 6px; }
    .place .go:hover { text-decoration: underline; text-underline-offset: 3px; }
    .place .go .icon { width: 16px; height: 16px; }

    @keyframes roll-in { from { transform: translateX(-46px) rotate(-7deg); } to { transform: none; } }
    @keyframes lid { 0%, 62%, 100% { transform: rotate(0); } 70% { transform: rotate(-16deg); } 80% { transform: rotate(-3deg); } 88% { transform: rotate(-9deg); } }
    @keyframes drive {
      0% { translate: 170px 0; } 30%, 62% { translate: 0 0; }
      34%, 38%, 42%, 46%, 50%, 54%, 58% { translate: 0 -1px; } 36%, 40%, 44%, 48%, 52%, 56% { translate: 0 0.6px; }
      100% { translate: -520px 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .lineup .due .bin, .lineup .due .bin-lid, .moving .truck { animation: none; }
      * { transition: none !important; }
    }
  `;

  // ---------------------------------------------------------------- base

  class MelCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._config = {};
      this._onData = () => this._render();
    }

    setConfig(config) {
      this._config = config || {};
      this._render();
    }

    set hass(hass) {
      const first = !this._hass;
      this._hass = hass;
      if (first) this._load();
    }

    connectedCallback() {
      mounted.add(this);
      listeners.add(this._onData);
      // l'affichage dépend de l'heure : il est rafraîchi chaque minute
      this._timer = setInterval(() => {
        if (this._hass && cache && Date.now() - cache.at >= REFRESH_MS) this._load();
        else this._render();
      }, 60000);
      this._render();
    }

    disconnectedCallback() {
      mounted.delete(this);
      listeners.delete(this._onData);
      clearInterval(this._timer);
    }

    _load() {
      loadDashboard(this._hass).then(
        () => this._render(),
        () => this._render(),
      );
    }

    _entry() {
      const entries = (cache && cache.data && cache.data.entries) || [];
      return entries.find((entry) => entry.entry_id === this._config.entry) || entries[0];
    }

    get _lang() {
      const entry = this._entry();
      const lang = this._config.language || (entry && entry.language) || "fr";
      return TEXTS[lang] ? lang : "fr";
    }

    get _t() {
      return TEXTS[this._lang];
    }

    _shell(inner, tint) {
      const style = tint ? ` style="--tint:${tint}"` : "";
      const tag = customElements.get("ha-card") ? "ha-card" : "div";
      return `<style>${STYLES}</style><${tag} class="card"${style}>${inner}</${tag}>`;
    }

    _render() {
      if (!this.isConnected) return;
      const entry = this._entry();
      let html;
      if (!entry) {
        const text = !cache || cache.pending ? this._t.loading : cache.error ? this._t.unavailable : this._t.no_entry;
        html = this._shell(`<div class="message">${esc(text)}</div>`);
      } else {
        // `now` (date ISO) fige l'heure : utile pour essayer la carte ou la documenter
        const now = this._config.now ? new Date(this._config.now) : new Date();
        html = this.renderCard(entry, now, formatters(this._lang));
      }
      if (html === this._html) return;
      this._html = html;
      const active = this.shadowRoot.activeElement;
      const keep = active && active.id ? { id: active.id, start: active.selectionStart, end: active.selectionEnd } : null;
      this.shadowRoot.innerHTML = html;
      if (keep) {
        const again = this.shadowRoot.getElementById(keep.id);
        if (again) {
          again.focus();
          if (keep.start != null) again.setSelectionRange(keep.start, keep.end);
        }
      }
    }

    _title(fallback) {
      return esc(this._config.title || fallback);
    }

    getCardSize() {
      return 4;
    }

    static baseSchema() {
      return [
        { name: "title", selector: { text: {} } },
        { name: "entry", selector: { config_entry: { integration: DOMAIN } } },
      ];
    }

    static labels(schema) {
      const names = {
        title: "Titre (facultatif)",
        entry: "Adresse (si plusieurs sont configurées)",
        days: "Nombre de jours affichés",
        show_alerts: "Afficher les informations de la MEL",
        show_map: "Afficher la carte",
        count: "Nombre de lieux affichés",
      };
      return names[schema.name] || schema.name;
    }
  }

  // ---------------------------------------------------------------- prochaine collecte

  class MelCollecteCard extends MelCard {
    constructor() {
      super();
      this._openNotice = null;
      this.shadowRoot.addEventListener("click", (event) => {
        const notice = event.target.closest(".notice");
        if (!notice) return;
        this._openNotice = this._openNotice === notice.dataset.id ? null : notice.dataset.id;
        this._render();
      });
    }

    static getStubConfig() {
      return {};
    }

    static getConfigForm() {
      return {
        schema: [
          ...MelCard.baseSchema(),
          { name: "days", selector: { number: { min: 7, max: 21, mode: "slider" } } },
          { name: "show_alerts", selector: { boolean: {} } },
        ],
        computeLabel: MelCard.labels,
      };
    }

    getCardSize() {
      return 5;
    }

    _headline(next, now, f) {
      const t = this._t;
      const bins = list(
        [...new Set(next.types.map((code) => t.bins[code] || (t.short[code] || code).toLowerCase()))],
        t.and,
      );
      const labels = list([...new Set(next.types.map((code) => t.short[code] || code))], t.and);
      const days = daysBetween(now, next.start);
      const start = f.time(next.start);
      const end = f.time(next.end);
      const morning = next.start.getHours() * 60 + next.start.getMinutes() < 12 * 60 + 30;
      const window = (day) => t.sub_window(labels, day, start, end);

      if (next.start <= now) return { title: t.now_title(bins), sub: t.now_sub(end), state: "now" };
      if (days === 0) {
        const soon = next.start - now < 2 * 3600000;
        return { title: soon ? t.out_now(bins) : t.out_today(bins, start), sub: window(t.in_days(0)), state: "due" };
      }
      if (days === 1 && morning) {
        // collecte du matin : le bac se sort la veille au soir
        if (now.getHours() >= 17) return { title: t.out_tonight(bins), sub: t.sub_tonight(labels, start, end), state: "due" };
        return { title: t.out_tonight(bins), sub: t.sub_tonight(labels, start, end), state: "soon" };
      }
      if (days === 1) return { title: capital(t.tomorrow(bins)), sub: window(t.in_days(1)), state: "soon" };
      return {
        title: t.later(capital(f.weekday(next.start)), bins),
        sub: window(`${t.in_days(days)}, ${f.dayMonth(next.start)}`),
        state: "later",
      };
    }

    renderCard(entry, now, f) {
      const t = this._t;
      const days = collectionDays(entry).filter((day) => day.end > now);
      const next = days[0];
      const span = Math.max(7, Math.min(21, Number(this._config.days) || 14));

      let scene;
      let tint;
      if (!next) {
        scene = `<div class="scene"><h2>${esc(t.no_collection)}</h2><p>${esc(t.no_collection_sub)}</p><div class="street">${skylineSvg}<div class="kerb"></div></div></div>`;
      } else {
        const head = this._headline(next, now, f);
        tint = colorOf(entry, next.types[0]);
        // un bac par couleur : les types qui partagent un bac ne sont dessinés qu'une fois
        const seen = new Set();
        const household = [];
        for (const code of [...next.types, ...Object.keys(entry.types)]) {
          const color = colorOf(entry, code);
          if (seen.has(color)) continue;
          seen.add(color);
          household.push({ color, due: next.types.includes(code) });
        }
        const bins = household
          .map((bin) => `<div class="slot${bin.due ? " due" : ""}">${binSvg(bin.color)}</div>`)
          .join("");
        scene = `<div class="scene${head.state === "now" ? " moving" : ""}">
          <h2>${esc(head.title)}</h2><p>${esc(head.sub)}</p>
          <div class="street">${skylineSvg}<div class="kerb"></div>${head.state === "now" ? truckSvg : ""}<div class="lineup">${bins}</div></div>
        </div>`;
      }

      const byDay = new Map(days.map((day) => [dayKey(day.date), day]));
      let rail = "";
      for (let index = 0; index < span; index += 1) {
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate() + index);
        const day = byDay.get(dayKey(date));
        const marks = day
          ? day.types.map((code) => `<i class="lid-mark" style="--c:${colorOf(entry, code)}"></i>`).join("")
          : "";
        const label = day
          ? `${f.dayMonth(date)} : ${list(day.types.map((code) => (entry.types[code] || {}).label || code), t.and)}`
          : f.dayMonth(date);
        rail += `<div class="day${index === 0 ? " today" : ""}" title="${esc(label)}">
          <span class="wd">${esc(f.weekdayShort(date))}</span><span class="num">${date.getDate()}</span><span class="lids">${marks}</span></div>`;
      }

      let notices = "";
      if (this._config.show_alerts !== false && entry.alerts.length) {
        notices = `<div class="notices">${entry.alerts
          .slice(0, 3)
          .map((alert) => {
            const kind = alert.alert_type === "danger" || alert.alert_type === "warning" ? alert.alert_type : "info";
            const open = String(alert.id) === this._openNotice;
            return `<button class="notice ${kind}${open ? " open" : ""}" data-id="${esc(alert.id)}" aria-expanded="${open}">
              <span class="icon">${kind === "info" ? ICONS.info : ICONS.warning}</span>
              <span><strong>${esc((alert.name || "").replace(/^[^\p{L}\p{N}]+/u, ""))}</strong><span class="body">${esc(alert.text || "")}</span></span>
            </button>`;
          })
          .join("")}</div>`;
      }

      return this._shell(`${scene}<div class="rail" role="img" aria-label="${esc(entry.address || "")}">${rail}</div>${notices}`, tint);
    }
  }

  // ---------------------------------------------------------------- calendrier

  class MelCollecteCalendarCard extends MelCard {
    constructor() {
      super();
      this._offset = 0;
      this._picked = null;
      this.shadowRoot.addEventListener("click", (event) => {
        const nav = event.target.closest("[data-nav]");
        const cell = event.target.closest("[data-day]");
        if (nav && !nav.disabled) {
          this._offset += Number(nav.dataset.nav);
          this._picked = null;
        } else if (cell) {
          this._picked = cell.dataset.day;
        } else return;
        this._render();
      });
    }

    static getStubConfig() {
      return {};
    }

    static getConfigForm() {
      return { schema: MelCard.baseSchema(), computeLabel: MelCard.labels };
    }

    getCardSize() {
      return 7;
    }

    renderCard(entry, now, f) {
      const t = this._t;
      const days = collectionDays(entry);
      const byDay = new Map(days.map((day) => [dayKey(day.date), day]));
      const last = days.length ? days[days.length - 1].date : now;
      const maxOffset = (last.getFullYear() - now.getFullYear()) * 12 + last.getMonth() - now.getMonth();
      this._offset = Math.max(0, Math.min(this._offset, maxOffset));
      const first = new Date(now.getFullYear(), now.getMonth() + this._offset, 1);
      const length = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
      const lead = (first.getDay() + 6) % 7; // la semaine commence le lundi
      const today = dayKey(now);

      let grid = "";
      for (let index = 0; index < 7; index += 1) {
        grid += `<span class="wd">${esc(f.weekdayShort(new Date(2024, 0, 1 + index)))}</span>`;
      }
      grid += "<span></span>".repeat(lead);
      for (let number = 1; number <= length; number += 1) {
        const date = new Date(first.getFullYear(), first.getMonth(), number);
        const key = dayKey(date);
        const day = byDay.get(key);
        const classes = ["cell"];
        if (key === today) classes.push("today");
        else if (date < now) classes.push("past");
        if (key === this._picked) classes.push("picked");
        const marks = day ? day.types.map((code) => `<i class="lid-mark" style="--c:${colorOf(entry, code)}"></i>`).join("") : "";
        grid += day
          ? `<button class="${classes.join(" ")}" data-day="${key}" aria-label="${esc(f.dayMonth(date))}"><span class="num">${number}</span><span class="lids">${marks}</span></button>`
          : `<span class="${classes.join(" ")}"><span class="num">${number}</span></span>`;
      }

      // détail : le jour choisi, sinon la prochaine collecte du mois affiché
      const upcoming = days.find((day) => day.end > now && day.date >= first) || days.find((day) => day.end > now);
      const shown = (this._picked && byDay.get(this._picked)) || upcoming;
      let detail = `<p class="message" style="padding:6px 0">${esc(t.nothing_that_day)}</p>`;
      if (shown) {
        detail = `<h3>${esc(capital(f.dayMonth(shown.date)))} · ${esc(t.in_days(Math.max(0, daysBetween(now, shown.date))))}</h3><ul>${entry.events
          .filter((event) => dayKey(new Date(event.start)) === dayKey(shown.date))
          .flatMap((event) =>
            event.types.map(
              (code) => `<li><i class="lid-mark" style="--c:${colorOf(entry, code)}"></i>${esc((entry.types[code] || {}).label || code)}
                <small>${esc(f.time(new Date(event.start)))} – ${esc(f.time(new Date(event.end)))}</small></li>`,
            ),
          )
          .join("")}</ul>`;
      }

      const legend = Object.entries(entry.types)
        .map(([code, type]) => `<span><i class="lid-mark" style="--c:${colorOf(entry, code)}"></i>${esc(t.short[code] || type.label)}</span>`)
        .join("");

      return this._shell(
        `<div class="head"><h2>${this._title(capital(f.month(first)))}</h2>
          <div class="nav">
            <button data-nav="-1" aria-label="${esc(t.previous_month)}"${this._offset <= 0 ? " disabled" : ""}><span class="icon">${ICONS.chevron}</span></button>
            <button data-nav="1" aria-label="${esc(t.next_month)}"${this._offset >= maxOffset ? " disabled" : ""}><span class="icon">${ICONS.chevron}</span></button>
          </div></div>
        <div class="month">${grid}</div>
        <div class="legend">${legend}</div>
        <div class="detail">${detail}</div>`,
        shown ? colorOf(entry, shown.types[0]) : null,
      );
    }
  }

  // ---------------------------------------------------------------- guide du tri

  const GUIDE_ORDER = ["omr", "emb", "cs", "dv", "bio", "alim", "verre", "jrm", "text", "compost"];

  class MelCollecteGuideCard extends MelCard {
    constructor() {
      super();
      this._query = "";
      this._type = null;
      this._all = false;
      this.shadowRoot.addEventListener("input", (event) => {
        if (event.target.id !== "q") return;
        this._query = event.target.value;
        this._render();
      });
      this.shadowRoot.addEventListener("click", (event) => {
        const chip = event.target.closest("[data-type]");
        if (chip) {
          this._type = chip.dataset.type;
          this._query = "";
          this._all = false;
        } else if (event.target.closest(".more")) {
          this._all = true;
        } else return;
        this._render();
      });
    }

    static getStubConfig() {
      return {};
    }

    static getConfigForm() {
      return { schema: MelCard.baseSchema(), computeLabel: MelCard.labels };
    }

    getCardSize() {
      return 8;
    }

    renderCard(entry) {
      const t = this._t;
      const guide = [...entry.guide].sort((a, b) => {
        const rank = (item) => (GUIDE_ORDER.includes(item.type) ? GUIDE_ORDER.indexOf(item.type) : 99);
        return rank(a) - rank(b);
      });
      if (!guide.length) return this._shell(`<div class="message">${esc(t.unavailable)}</div>`);
      const current = guide.find((item) => item.type === this._type) || guide[0];
      const color = (item) => COLORS[item.color] || COLORS["blue-grey"];
      const query = fold(this._query.trim());

      const chips = guide
        .map(
          (item) => `<button class="chip" role="tab" data-type="${esc(item.type)}" aria-selected="${!query && item === current}" style="--c:${color(item)}">
            <i class="lid-mark" style="--c:${color(item)}"></i>${esc(t.short[item.type] || item.label)}</button>`,
        )
        .join("");

      let body;
      if (query.length >= 2) {
        const highlight = (text) => {
          const at = fold(text).indexOf(query);
          if (at < 0) return esc(text);
          return `${esc(text.slice(0, at))}<mark>${esc(text.slice(at, at + query.length))}</mark>${esc(text.slice(at + query.length))}`;
        };
        const hits = [];
        for (const item of guide) {
          for (const [ok, texts] of [[true, item.accepted], [false, item.rejected]]) {
            for (const text of texts) {
              if (fold(text).includes(query)) hits.push({ item, ok, text });
            }
          }
        }
        hits.sort((a, b) => Number(b.ok) - Number(a.ok));
        body = hits.length
          ? `<div class="results"><ul>${hits
              .slice(0, 12)
              .map(
                (hit) => `<li><span class="icon mark ${hit.ok ? "ok" : "ko"}">${hit.ok ? ICONS.check : ICONS.cross}</span>
                  <div><p>${highlight(hit.text)}</p><small><i class="lid-mark" style="--c:${color(hit.item)}"></i>${esc(
                    (hit.ok ? t.goes_in : t.not_in)(hit.item.label),
                  )}</small></div></li>`,
              )
              .join("")}</ul></div>`
          : `<div class="message">${esc(t.no_match(this._query.trim()))}</div>`;
      } else {
        const column = (ok, texts) => {
          if (!texts.length) return "";
          const limit = this._all ? texts.length : 6;
          const more = texts.length > limit ? `<button class="more">+ ${texts.length - limit}</button>` : "";
          return `<div><h3 class="${ok ? "ok" : "ko"}"><span class="icon">${ok ? ICONS.check : ICONS.cross}</span>${esc(ok ? t.accepted : t.rejected)}</h3>
            <ul>${texts.slice(0, limit).map((text) => `<li>${esc(text)}</li>`).join("")}</ul>${more}</div>`;
        };
        const rules = current.note || current.rules;
        body = `<div class="sorted" role="tabpanel">${column(true, current.accepted)}${column(false, current.rejected)}</div>
          ${rules ? `<p class="rules">${esc(rules)}</p>` : ""}`;
      }

      const contacts = entry.contacts || {};
      const contact = contacts.phone
        ? `<div class="contact"><span>${esc(t.contact)}</span><a href="tel:${esc(contacts.phone.replace(/\s/g, ""))}"><span class="icon">${ICONS.phone}</span>${esc(contacts.phone)}</a></div>`
        : "";

      return this._shell(
        `<div class="head"><h2>${this._title(t.guide_title)}</h2></div>
        <div class="search"><span class="icon">${ICONS.search}</span>
          <input id="q" type="search" autocomplete="off" placeholder="${esc(t.search)}" aria-label="${esc(t.search_label)}" value="${esc(this._query)}"></div>
        <div class="chips" role="tablist">${chips}</div>${body}${contact}`,
        color(current),
      );
    }
  }

  // ---------------------------------------------------------------- déchèteries

  const PLACE_KINDS = ["recycling_center", "mobile", "glass", "composter"];

  class MelCollectePlacesCard extends MelCard {
    constructor() {
      super();
      this._kind = null;
      this.shadowRoot.addEventListener("click", (event) => {
        const tab = event.target.closest("[data-kind]");
        if (!tab) return;
        this._kind = tab.dataset.kind;
        this._render();
      });
    }

    static getStubConfig() {
      return {};
    }

    static getConfigForm() {
      return {
        schema: [
          ...MelCard.baseSchema(),
          { name: "count", selector: { number: { min: 2, max: 8, mode: "slider" } } },
          { name: "show_map", selector: { boolean: {} } },
        ],
        computeLabel: MelCard.labels,
      };
    }

    getCardSize() {
      return 8;
    }

    _when(iso, now, f) {
      const date = new Date(iso);
      const days = Math.max(0, daysBetween(now, date));
      const day = days <= 1 ? this._t.in_days(days) : days < 7 ? f.weekday(date) : f.shortDate(date);
      return `${day} ${this._t.at} ${f.time(date)}`;
    }

    _state(place, now, f) {
      const t = this._t;
      if (place.kind === "glass" || place.kind === "composter") return { cls: "", html: esc(place.kind === "composter" ? t.free_access : place.address || "") };
      if (place.kind === "mobile") {
        if (place.open) return { cls: "open", html: `<b>${esc(t.visit_now(f.time(new Date(place.closes_at))))}</b>` };
        return { cls: "", html: esc(place.next_open ? capital(t.next_visit(this._when(place.next_open, now, f))) : t.no_visit) };
      }
      if (place.open) return { cls: "open", html: `<b>${esc(t.open_until(f.time(new Date(place.closes_at))))}</b>` };
      if (place.next_open) {
        const [shut, opens] = t.closed_opens(this._when(place.next_open, now, f)).split(" · ");
        return { cls: "shut", html: `<b>${esc(shut)}</b> · ${esc(opens)}` };
      }
      return { cls: "shut", html: `<b>${esc(t.closed)}</b>` };
    }

    _distance(km, f) {
      if (km == null) return "";
      return km < 1 ? this._t.m(f.number(Math.round(km * 100) * 10, 0)) : this._t.km(f.number(km, 1));
    }

    _map(entry, places, states, f) {
      const home = entry.home;
      if (!home || !places.length) return "";
      const width = 360;
      const height = 190;
      const cx = width / 2;
      const cy = height / 2;
      const scaleLon = Math.cos((home.lat * Math.PI) / 180);
      const points = places.map((place) => ({
        x: (place.lon - home.lon) * 111.32 * scaleLon,
        y: (home.lat - place.lat) * 110.57,
      }));
      const reach = Math.max(0.0005, ...points.map((point) => Math.max(Math.abs(point.x) / (cx - 22), Math.abs(point.y) / (cy - 20))));
      const far = Math.max(...places.map((place) => place.distance_km || 0));
      const step = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20].find((value) => far / value <= 3) || 20;
      let rings = "";
      for (let radius = step; radius / reach < width; radius += step) {
        const r = radius / reach;
        if (r > cx + 40) break;
        rings += `<circle class="ring" cx="${cx}" cy="${cy}" r="${r.toFixed(1)}"/>`;
        if (r < cy - 4) rings += `<text class="ring-label" x="${cx + 3}" y="${(cy - r - 3).toFixed(1)}">${esc(this._distance(radius, f))}</text>`;
      }
      const pins = points
        .map((point, index) => {
          const x = (cx + point.x / reach).toFixed(1);
          const y = (cy + point.y / reach).toFixed(1);
          return { index, html: `<line class="spoke" x1="${cx}" y1="${cy}" x2="${x}" y2="${y}"/>`, pin: `<g class="pin ${states[index].cls}${index === 0 ? " first" : ""}"><circle cx="${x}" cy="${y}" r="9"/><text x="${x}" y="${y}">${index + 1}</text></g>` };
        })
        .reverse();
      return `<svg class="map" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(this._t.map_label)}">
        ${rings}${pins.map((pin) => pin.html).join("")}${pins.map((pin) => pin.pin).join("")}
        <g transform="translate(${cx - 9} ${cy - 9})"><path class="home" d="M9 0l9 8v10H0V8z"/><rect class="home-roof" x="6.5" y="10" width="5" height="8"/></g>
      </svg>`;
    }

    renderCard(entry, now, f) {
      const t = this._t;
      const kinds = PLACE_KINDS.filter((kind) => (entry.facilities[kind] || []).length);
      if (!kinds.length) return this._shell(`<div class="head"><h2>${this._title(t.places_title)}</h2></div><div class="message">${esc(t.no_places)}</div>`);
      const kind = kinds.includes(this._kind) ? this._kind : kinds[0];
      const count = Math.max(2, Math.min(8, Number(this._config.count) || 4));
      const places = entry.facilities[kind].slice(0, count);
      const states = places.map((place) => this._state(place, now, f));

      const tabs = kinds
        .map((item) => `<button class="tab" role="tab" data-kind="${item}" aria-selected="${item === kind}">${esc(t.tabs[item])}</button>`)
        .join("");
      const rows = places
        .map((place, index) => {
          const name = place.kind === "glass" ? place.address || place.name : place.name;
          const state = place.kind === "glass" ? { cls: "", html: esc(t.tabs.glass) } : states[index];
          const url = `https://www.google.com/maps/dir/?api=1&destination=${Number(place.lat)},${Number(place.lon)}`;
          return `<li class="place ${state.cls}"><span class="rank">${index + 1}</span>
            <span class="name">${esc(name)}</span><span class="dist">${esc(this._distance(place.distance_km, f))}</span>
            <span class="state">${state.html}</span>
            <a class="go" href="${url}" target="_blank" rel="noopener" aria-label="${esc(t.route_to(name))}"><span class="icon">${ICONS.route}</span>${esc(t.route)}</a></li>`;
        })
        .join("");

      return this._shell(
        `<div class="head"><h2>${this._title(t.places_title)}</h2></div>
        <div class="tabs" role="tablist">${tabs}</div>
        ${this._config.show_map === false ? "" : this._map(entry, places, states, f)}
        <ul class="places">${rows}</ul>`,
      );
    }
  }

  // ---------------------------------------------------------------- déclaration

  const CARDS = [
    ["mel-collecte-card", MelCollecteCard, "MEL · Prochaine collecte", "Le bac à sortir, quand le sortir, et les jours à venir."],
    ["mel-collecte-calendar-card", MelCollecteCalendarCard, "MEL · Calendrier des collectes", "Le mois en un coup d'œil, aux couleurs des bacs."],
    ["mel-collecte-guide-card", MelCollecteGuideCard, "MEL · Guide du tri", "Cherchez un déchet : la carte dit dans quel bac il va."],
    ["mel-collecte-places-card", MelCollectePlacesCard, "MEL · Déchèteries et points d'apport", "Les lieux les plus proches, ouverts ou fermés, avec l'itinéraire."],
  ];
  window.customCards = window.customCards || [];
  for (const [type, element, name, description] of CARDS) {
    if (!customElements.get(type)) customElements.define(type, element);
    if (!window.customCards.some((card) => card.type === type)) {
      window.customCards.push({ type, name, description, preview: true, documentationURL: "https://mmornati.github.io/home-assistant-mel-garbage-collection/cartes/" });
    }
  }
})();
