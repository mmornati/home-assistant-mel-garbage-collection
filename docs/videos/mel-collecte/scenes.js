/* Scènes de la vidéo de présentation de MEL Collecte (voir ../engine/engine.js).
 *
 * Chaque scène est fn(t, d, cues) : t = temps local en secondes, d = durée de la
 * scène, cues = les phrases dites [{s, e, text}] de timing.js. Les animations
 * s'accrochent à at(cues, i), le début de la phrase i, pour suivre la voix.
 * Règle : une fonction pure de t. Pas de Math.random() ni de Date.now().
 *
 * L'interface de Home Assistant est redessinée de façon schématique, avec une
 * adresse d'exemple.
 */
"use strict";

const STR = {
  fr: {
    clock: "22:00",
    doubt: "C'était ce soir, le bac jaune ?",
    name: "MEL Collecte",
    tag: "Les collectes de la Métropole Européenne de Lille dans Home Assistant",
    p1: "Gratuit",
    p2: "95 communes",
    p3: "Sans compte",
    hInstall: "Deux gestes, et c'est prêt",
    hacs: "HACS",
    repo: "MEL Collecte des déchets",
    download: "Télécharger",
    addrLabel: "Adresse complète",
    addr: "19 rue Gambetta, Lille",
    demo: "Adresse d'exemple",
    f1: "Secteur de collecte",
    f2: "Vos bacs",
    f3: "Vos horaires",
    f1v: "trouvé pour votre rue",
    f2v: "gris, jaune, marron",
    f3v: "calendrier créé",
    hCard: "Une carte qui dit quoi faire",
    cardTonight: "Ce soir, sortez le bac marron",
    cardTonightSub: "Biodéchets · passage demain de 6 h à 13 h",
    cardNow: "Collecte en cours : le bac marron",
    cardNowSub: "Le camion passe jusqu'à 13 h",
    hSort: "Le mois, et le bon bac",
    month: "Novembre",
    wd: "LMMJVSD",
    search: "yaourt",
    result: "Les pots de yaourt",
    goes: "Va dans : Emballages recyclables",
    guide: "Où ça se jette ?",
    hPlaces: "La déchèterie la plus proche",
    count: "14",
    countLabel: "déchèteries dans la métropole",
    open: "Ouverte",
    until: "jusqu'à 18 h",
    closed: "Fermée",
    route: "Itinéraire",
    d1: "Lille Alsace",
    d2: "Lille Borda",
    d3: "La Madeleine",
    d4: "Mons-en-Barœul",
    hRemind: "Votre maison vous le rappelle",
    notifApp: "Home Assistant",
    notifTitle: "Poubelles",
    notifBody: "À sortir ce soir : le bac jaune",
    lamp: "Lampe de l'entrée",
    free: "Gratuit · Libre · Prêt en deux minutes",
    last: "Ne ratez plus jamais le camion.",
    url: "github.com/mmornati/home-assistant-mel-garbage-collection",
  },
};
STR.en = STR.fr; // la vidéo n'existe qu'en français

/* Palette : l'anthracite des bacs et les couleurs de leurs couvercles */
const INK = "#1e2329", PAPER = "#f6f2e9", CARD = "#fffdf8", SOFT = "#5a6470", LINE = "#ddd6c6";
const YELLOW = "#f2bb0c", YDEEP = "#d9a400", GREY = "#7b8794", BROWN = "#8d5b3a", GREEN = "#2e9d5c", RED = "#c2453c", NIGHT = "#141a24";

function fill(color) { ctx.fillStyle = color; ctx.fillRect(0, 0, W, H); }
function box(x, y, w, h, r, color, alpha = 1) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; rr(x, y, w, h, r); ctx.fill(); ctx.restore();
}
function mix(a, b, k) {
  const p = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
  const [x, y] = [p(a), p(b)];
  return `rgb(${x.map((v, i) => Math.round(lerp(v, y[i], k))).join(",")})`;
}

/* Un bac roulant posé en (x, y) : y est le sol. open = angle du couvercle, 0 à 1 */
function bin(x, y, s, lid, o = {}) {
  ctx.save();
  ctx.translate(x, y); ctx.scale(s, s); ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  if (o.tilt) ctx.rotate(o.tilt);
  ctx.fillStyle = "rgba(0,0,0,0.18)"; ctx.beginPath(); ctx.ellipse(1, 2, 26, 3.5, 0, 0, 7); ctx.fill();
  ctx.fillStyle = o.body || "#46515c";
  ctx.beginPath(); ctx.moveTo(-21, -52); ctx.lineTo(21, -52); ctx.lineTo(17, -6); ctx.quadraticCurveTo(16.5, -1, 12, -1);
  ctx.lineTo(-12, -1); ctx.quadraticCurveTo(-16.5, -1, -17, -6); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.14)"; ctx.lineWidth = 2; ctx.lineCap = "round";
  [-11, 0, 11].forEach((dx) => { ctx.beginPath(); ctx.moveTo(dx, -43); ctx.lineTo(dx * 0.86, -10); ctx.stroke(); });
  ctx.fillStyle = "#20262c"; ctx.beginPath(); ctx.arc(-13, -2, 5.5, 0, 7); ctx.fill();
  ctx.fillStyle = "#8a949e"; ctx.beginPath(); ctx.arc(-13, -2, 1.8, 0, 7); ctx.fill();
  ctx.translate(-24, -53); ctx.rotate(-(o.open || 0) * 0.5); ctx.translate(24, 53);
  ctx.fillStyle = lid; rr(-25, -67, 50, 15, 4.5); ctx.fill(); rr(-8, -72, 16, 7, 3); ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.45)"; ctx.lineWidth = 2.4; ctx.beginPath(); ctx.moveTo(-19, -62); ctx.lineTo(6, -62); ctx.stroke();
  ctx.restore();
}

/* Le camion de collecte, cabine à gauche, roues posées en y */
function truck(x, y, s, color) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = color; rr(-10, -58, 78, 44, 6); ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.22)"; ctx.lineWidth = 2;
  [8, 26, 44].forEach((dx) => { ctx.beginPath(); ctx.moveTo(dx, -52); ctx.lineTo(dx, -22); ctx.stroke(); });
  ctx.fillStyle = "#f4f6f8";
  ctx.beginPath(); ctx.moveTo(-14, -46); ctx.lineTo(-34, -46); ctx.quadraticCurveTo(-39, -46, -42, -41);
  ctx.lineTo(-52, -26); ctx.lineTo(-52, -14); ctx.lineTo(-14, -14); ctx.closePath(); ctx.fill();
  ctx.fillStyle = "#8ec3ea"; ctx.beginPath(); ctx.moveTo(-20, -41); ctx.lineTo(-33, -41); ctx.lineTo(-42, -27); ctx.lineTo(-20, -27); ctx.closePath(); ctx.fill();
  ctx.fillStyle = "#2a3138"; rr(-54, -16, 124, 7, 2); ctx.fill();
  [-36, 30, 52].forEach((dx) => {
    ctx.fillStyle = "#1b2025"; ctx.beginPath(); ctx.arc(dx, -8, 9, 0, 7); ctx.fill();
    ctx.fillStyle = "#9aa4ad"; ctx.beginPath(); ctx.arc(dx, -8, 3.2, 0, 7); ctx.fill();
  });
  ctx.restore();
}

/* Silhouette lilloise : maisons à pignons à gradins et beffroi, posées sur y */
function skyline(y, color, s = 1, windows) {
  const R = rng(7);
  let x = -20;
  ctx.fillStyle = color;
  const lit = [];
  while (x < W + 40) {
    const belfry = x > 700 * s && x < 760 * s;
    const w = (belfry ? 44 : 64 + R() * 46) * s;
    const h = (belfry ? 200 : 60 + R() * 70) * s;
    ctx.fillRect(x, y - h, w, h);
    if (belfry) {
      ctx.fillRect(x + w * 0.2, y - h - 34 * s, w * 0.6, 34 * s);
      ctx.fillRect(x + w * 0.36, y - h - 62 * s, w * 0.28, 28 * s);
      ctx.fillRect(x + w * 0.46, y - h - 80 * s, w * 0.08, 18 * s);
    } else {
      const steps = 3;
      for (let i = 1; i <= steps; i += 1) {
        const inset = (w / 2) * (i / (steps + 0.6));
        ctx.fillRect(x + inset, y - h - i * 9 * s, w - inset * 2, 9 * s + 1);
      }
      if (windows) lit.push([x + w * 0.3, y - h * 0.62, R() > 0.55], [x + w * 0.6, y - h * 0.62, R() > 0.6]);
    }
    x += w + (4 + R() * 14) * s;
  }
  if (windows) lit.forEach(([wx, wy, on]) => box(wx, wy, 10 * s, 15 * s, 1, on ? windows : "rgba(255,255,255,0.05)"));
}

function kerb(y, color, dash) {
  ctx.fillStyle = color; ctx.fillRect(0, y, W, H - y);
  ctx.fillStyle = dash;
  for (let x = 20; x < W; x += 64) ctx.fillRect(x, y + 22, 34, 4);
}

function title(s, k, color = INK) {
  text(s, 80, 104 + (1 - outCubic(k)) * 18, { size: 44, weight: 800, font: SORA, color, alpha: k });
}

/* 1. Le doute : la nuit, la rue, le bac jaune ? */
function sDoute(t, d, cues) {
  fill(NIGHT);
  const a1 = at(cues, 1, 3.1);
  const R = rng(3);
  for (let i = 0; i < 46; i += 1) dot(R() * W, R() * 330, 0.8 + R() * 1.2, "#cfd8e6", 0.25 + 0.5 * Math.abs(Math.sin(t * 0.8 + i)));
  dot(1040, 150, 46, "#f3e9c6"); dot(1060, 138, 40, NIGHT);
  skyline(560, "#1d2633", 1, "#f2bb0c");
  kerb(560, "#0d1118", "#2a3444");
  text(S.clock, 80, 250, { size: 150, weight: 800, font: SORA, color: "#f6f2e9", alpha: seg(t, 0.3, 0.9) });
  const k = outBack(seg(t, a1, a1 + 0.6));
  const wig = Math.sin((t - a1) * 9) * 0.05 * seg(t, a1 + 0.5, a1 + 0.8) * (1 - seg(t, a1 + 2.2, a1 + 2.6));
  bin(760, 566, 1.6, GREY, { alpha: 0.75 });
  bin(880, 566, 2.2 * (0.9 + 0.1 * k), YELLOW, { tilt: wig, open: Math.max(0, Math.sin((t - a1) * 5)) * 0.35 * seg(t, a1 + 0.4, a1 + 0.6) });
  bin(1010, 566, 1.6, BROWN, { alpha: 0.75 });
  text("?", 880, 372 - 10 * k, { size: 110, weight: 800, font: SORA, color: YELLOW, align: "center", alpha: k });
  text(S.doubt, 80, 330, { size: 34, weight: 600, font: SORA, color: YELLOW, alpha: seg(t, a1 + 0.2, a1 + 0.8) });
}

/* 2. MEL Collecte : le champ jaune */
function sIntro(t, d, cues) {
  fill(NIGHT);
  const k = inOut(seg(t, 0, 0.9));
  ctx.save(); ctx.beginPath(); ctx.arc(880, 500, k * 1500, 0, 7); ctx.clip();
  fill(YELLOW);
  skyline(600, YDEEP, 1);
  kerb(600, INK, YELLOW);
  const a1 = at(cues, 1, 4.4);
  const pop = outBack(seg(t, 0.5, 1.2));
  bin(190, 330, 3.1 * pop, YELLOW, { body: INK, open: Math.max(0, Math.sin((t - 1.2) * 3.2)) * 0.5 * seg(t, 1.2, 1.5) * (1 - seg(t, 3.2, 3.6)) });
  text(S.name, 320, 262, { size: 104, weight: 800, font: SORA, color: INK, alpha: seg(t, 0.7, 1.3) });
  para(S.tag, 324, 318, 760, { size: 28, lh: 38, weight: 500, color: "#3a3320", alpha: seg(t, a1, a1 + 0.6) });
  [S.p1, S.p2, S.p3].forEach((p, i) => {
    const kp = outBack(seg(t, a1 + 1.4 + i * 0.35, a1 + 1.9 + i * 0.35));
    if (kp <= 0) return;
    const w = measure(p, 24, 700, INTER) + 44;
    const x = 324 + [0, 170, 400][i];
    box(x, 432 - 6 * kp, w, 50, 25, INK, kp);
    text(p, x + 22, 465 - 6 * kp, { size: 24, weight: 700, color: YELLOW, alpha: kp });
  });
  const drive = seg(t, a1 + 2.2, d + 0.4);
  truck(lerp(1460, -200, drive), 622, 2, GREY);
  ctx.restore();
}

/* 3. Installation : HACS, puis l'adresse */
function sInstall(t, d, cues) {
  fill(PAPER);
  title(S.hInstall, seg(t, 0.1, 0.7));
  const a1 = at(cues, 1, 3.7);
  // HACS
  const k0 = outCubic(seg(t, 0.3, 0.9));
  panel(80, 160 + (1 - k0) * 20, 520, 190, { r: 18, fill: CARD, stroke: LINE, alpha: k0 });
  text(S.hacs, 112, 206, { size: 18, weight: 700, font: MONO, color: SOFT, alpha: k0 });
  bin(140, 316, 1.05, YELLOW, { body: INK, alpha: k0 });
  text(S.repo, 186, 276, { size: 26, weight: 700, font: SORA, color: INK, alpha: k0 });
  const done = seg(t, 1.5, 1.8);
  const press = 1 - 0.06 * seg(t, 1.3, 1.45) * (1 - seg(t, 1.45, 1.6));
  ctx.save(); ctx.translate(286, 316); ctx.scale(press, press);
  box(-100, -22, 200, 44, 22, done ? GREEN : INK, k0);
  if (done < 1) text(S.download, 0, 7, { size: 18, weight: 700, color: CARD, align: "center", alpha: k0 * (1 - done) });
  ctx.restore();
  check(286, 316, 13, CARD, done);
  // adresse
  const k1 = outCubic(seg(t, 1.7, 2.3));
  panel(80, 380 + (1 - k1) * 20, 520, 150, { r: 18, fill: CARD, stroke: LINE, alpha: k1 });
  text(S.addrLabel, 112, 424, { size: 18, weight: 600, color: SOFT, alpha: k1 });
  box(112, 444, 456, 56, 12, "#efe9dc", k1);
  const typedK = seg(t, 2.2, a1 - 0.2);
  const shown = typed(S.addr, typedK);
  text(shown, 132, 480, { size: 24, weight: 500, color: INK, alpha: k1 });
  if (k1 > 0 && typedK < 1 && Math.floor(t * 2.5) % 2 === 0) box(134 + measure(shown, 24, 500, INTER), 458, 2, 28, 1, INK);
  text(S.demo, 112, 556, { size: 14, font: MONO, color: SOFT, alpha: k1 });
  // ce que l'intégration trouve seule
  arrow(620, 345, 690, 345, seg(t, a1, a1 + 0.5), INK);
  [[S.f1, S.f1v, GREY], [S.f2, S.f2v, YELLOW], [S.f3, S.f3v, BROWN]].forEach(([label, value, color], i) => {
    const k = outCubic(seg(t, a1 + 0.5 + i * 0.75, a1 + 1.1 + i * 0.75));
    const y = 170 + i * 124;
    panel(720 + (1 - k) * 40, y, 480, 104, { r: 18, fill: CARD, stroke: LINE, alpha: k });
    box(748 + (1 - k) * 40, y + 30, 44, 14, 5, color, k);
    text(label, 812 + (1 - k) * 40, y + 46, { size: 24, weight: 700, font: SORA, color: INK, alpha: k });
    text(value, 812 + (1 - k) * 40, y + 78, { size: 19, color: SOFT, alpha: k });
    check(1158, y + 52, 13, GREEN, seg(t, a1 + 1.0 + i * 0.75, a1 + 1.4 + i * 0.75));
  });
}

/* La carte « Prochaine collecte », redessinée. now = 0 (ce soir) → 1 (le camion passe) */
function heroCard(x, y, w, t, now, k) {
  const h = 430;
  const tint = mix("#efe3da", "#e9dccf", now);
  ctx.save(); ctx.globalAlpha *= k; ctx.translate(0, (1 - k) * 30);
  ctx.shadowColor = "rgba(30,35,41,0.28)"; ctx.shadowBlur = 50; ctx.shadowOffsetY = 24;
  box(x, y, w, h, 20, CARD);
  ctx.shadowColor = "transparent";
  ctx.save(); rr(x, y, w, h, 20); ctx.clip();
  box(x, y, w, 300, 0, tint);
  // rue
  ctx.save(); ctx.translate(x, y + 278); ctx.scale(w / W, w / W);
  skyline(0, "#dccbbd", 1);
  ctx.restore();
  box(x, y + 278, w, 24, 0, "#d3cbc0");
  ctx.fillStyle = "#b9b0a3"; ctx.fillRect(x, y + 278, w, 3);
  if (now > 0) truck(lerp(x + w + 160, x - 160, inOut(seg(now, 0.05, 1))), y + 296, 1.5, BROWN);
  const roll = outCubic(seg(t, 0.2, 1.1));
  bin(x + 96 - (1 - roll) * 60, y + 292, 1.45, BROWN, { open: Math.max(0, Math.sin(t * 2.4)) * 0.45 * (1 - now), tilt: -(1 - roll) * 0.12 });
  bin(x + 196, y + 290, 0.85, GREY, { alpha: 0.55 });
  bin(x + 256, y + 290, 0.85, YELLOW, { alpha: 0.55 });
  // jours à venir
  const days = "MMJVSDLMMJVSDL"; // le 17 novembre 2026 est un mardi
  for (let i = 0; i < 14; i += 1) {
    const dx = x + 30 + i * ((w - 60) / 13);
    text(days[i], dx, y + 336, { size: 13, color: SOFT, align: "center" });
    if (i === 0) dot(dx, y + 362, 15, INK);
    text(String(17 + i > 30 ? 17 + i - 30 : 17 + i), dx, y + 368, { size: 16, weight: i === 0 ? 700 : 400, color: i === 0 ? CARD : INK, align: "center" });
    const mark = { 1: BROWN, 3: GREY, 7: GREY, 8: BROWN, 10: GREY }[i];
    if (mark) box(dx - 9, y + 386, 18, 6, 3, mark);
    if (i === 3 || i === 10) box(dx - 9, y + 395, 18, 6, 3, YELLOW);
  }
  ctx.restore();
  ctx.restore();
}

/* 4. La carte : ce soir le bac marron, puis le camion */
function sCarte(t, d, cues) {
  fill(PAPER);
  title(S.hCard, seg(t, 0.1, 0.7));
  const a1 = at(cues, 1, 4.6), a2 = at(cues, 2, 6.7);
  const k = outCubic(seg(t, 0.4, 1.1));
  const now = seg(t, a2, d - 0.3);
  heroCard(80, 150, 600, t, now, k);
  const swap = seg(t, a2 + 0.1, a2 + 0.5);
  const show = seg(t, a1 - 0.2, a1 + 0.4);
  text(S.cardTonight, 110, 208, { size: 30, weight: 800, font: SORA, color: INK, alpha: k * show * (1 - swap) });
  text(S.cardTonightSub, 110, 242, { size: 18, color: "#6a5446", alpha: k * show * (1 - swap) });
  text(S.cardNow, 110, 208, { size: 30, weight: 800, font: SORA, color: INK, alpha: k * swap });
  text(S.cardNowSub, 110, 242, { size: 18, color: "#6a5446", alpha: k * swap });
  // à droite : la phrase, en grand
  const big = swap > 0.5 ? S.cardNow : S.cardTonight;
  const kb = swap > 0.5 ? seg(t, a2 + 0.3, a2 + 0.8) : show * (1 - seg(t, a2, a2 + 0.3));
  para(big, 740, 300, 460, { size: 46, lh: 54, weight: 800, font: SORA, color: INK, alpha: kb });
  box(740, 206, 86 * kb, 20, 8, BROWN, kb);
}

/* 5. Calendrier et guide du tri */
function sTri(t, d, cues) {
  fill(PAPER);
  title(S.hSort, seg(t, 0.1, 0.7));
  const a1 = at(cues, 1, 2.9), a2 = at(cues, 2, 5.4);
  const k = outCubic(seg(t, 0.3, 0.9));
  panel(80, 150 + (1 - k) * 24, 520, 420, { r: 20, fill: CARD, stroke: LINE, alpha: k });
  text(S.month, 112, 200, { size: 26, weight: 800, font: SORA, color: INK, alpha: k });
  for (let c = 0; c < 7; c += 1) text(S.wd[c], 134 + c * 68, 240, { size: 14, color: SOFT, align: "center", alpha: k });
  for (let n = 1; n <= 30; n += 1) {
    const idx = n + 5; // le 1er novembre 2026 est un dimanche
    const cx = 134 + (idx % 7) * 68, cy = 282 + Math.floor(idx / 7) * 56;
    const wd = idx % 7;
    if (n === 17) dot(cx, cy - 6, 17, INK, k);
    text(String(n), cx, cy, { size: 18, weight: n === 17 ? 700 : 400, color: n === 17 ? CARD : n < 17 ? "#aaa397" : INK, align: "center", alpha: k });
    const marks = wd === 1 ? [GREY] : wd === 2 ? [BROWN] : wd === 4 ? [GREY, YELLOW] : [];
    marks.forEach((color, i) => {
      const km = outBack(seg(t, 0.7 + n * 0.05, 1.0 + n * 0.05));
      box(cx - (marks.length * 16 - 2) / 2 + i * 16, cy + 10, 14 * km, 6, 3, color, km);
    });
  }
  // guide du tri
  const k1 = outCubic(seg(t, a1 - 0.3, a1 + 0.3));
  panel(660, 150 + (1 - k1) * 24, 540, 420, { r: 20, fill: CARD, stroke: LINE, alpha: k1 });
  text(S.guide, 692, 200, { size: 26, weight: 800, font: SORA, color: INK, alpha: k1 });
  box(692, 226, 476, 60, 14, "#efe9dc", k1);
  ring(722, 255, 9, SOFT, 2.4, k1); line([[729, 262], [737, 270]], SOFT, 2.4, k1);
  const shown = typed(S.search, seg(t, a1 + 0.9, a1 + 2.0));
  text(shown, 754, 264, { size: 24, weight: 500, color: INK, alpha: k1 });
  if (k1 > 0 && t < a2 && Math.floor(t * 2.5) % 2 === 0) box(756 + measure(shown, 24, 500, INTER), 241, 2, 28, 1, INK);
  const k2 = outCubic(seg(t, a2, a2 + 0.6));
  box(692, 318 + (1 - k2) * 16, 476, 110, 16, "#fbf1cf", k2);
  dot(734, 373 + (1 - k2) * 16, 22, GREEN, k2); check(734, 373 + (1 - k2) * 16, 10, CARD, seg(t, a2 + 0.3, a2 + 0.7));
  text(S.result, 776, 364 + (1 - k2) * 16, { size: 26, weight: 700, font: SORA, color: INK, alpha: k2 });
  box(776, 384 + (1 - k2) * 16, 22, 8, 3, YELLOW, k2);
  text(S.goes, 808, 394 + (1 - k2) * 16, { size: 18, color: "#5c4d16", alpha: k2 });
  bin(1090, 552, 1.5 * outBack(seg(t, a2 + 0.5, a2 + 1.1)), YELLOW, { open: Math.max(0, Math.sin((t - a2) * 3)) * 0.6 * seg(t, a2 + 1, a2 + 1.3) });
}

/* 6. Déchèteries : plan centré sur la maison, liste classée */
function sPlaces(t, d, cues) {
  fill(PAPER);
  title(S.hPlaces, seg(t, 0.1, 0.7));
  const a1 = at(cues, 1, 4.2);
  const cx = 330, cy = 380;
  [70, 140, 210].forEach((r, i) => {
    const k = seg(t, 0.3 + i * 0.2, 0.9 + i * 0.2);
    ctx.save(); ctx.setLineDash([3, 8]); ring(cx, cy, r * outCubic(k), "#bdb5a4", 1.6, k); ctx.restore();
    text(`${(i + 1) * 2} km`, cx + 6, cy - r - 6, { size: 13, font: MONO, color: SOFT, alpha: k });
  });
  box(cx - 15, cy - 6, 30, 22, 3, INK); ctx.fillStyle = INK;
  ctx.beginPath(); ctx.moveTo(cx - 20, cy - 4); ctx.lineTo(cx, cy - 22); ctx.lineTo(cx + 20, cy - 4); ctx.closePath(); ctx.fill();
  const pins = [[36, 44, true], [-44, 48, true], [12, -136, false], [176, -66, true]];
  const more = [[-150, -120], [-190, 60], [120, 170], [-70, 190], [200, 120], [-210, -30], [60, -200], [-120, 150], [220, -160], [150, -190]];
  more.forEach(([dx, dy], i) => dot(cx + dx, cy + dy, 6 * outBack(seg(t, 1.2 + i * 0.12, 1.6 + i * 0.12)), "#b9b0a3"));
  pins.forEach(([dx, dy, open], i) => {
    const k = outBack(seg(t, 0.9 + i * 0.3, 1.4 + i * 0.3));
    if (k <= 0) return;
    line([[cx, cy], [cx + dx * k, cy + dy * k]], "#c9c1b2", 1.6);
    const state = seg(t, a1 + i * 0.25, a1 + 0.4 + i * 0.25);
    dot(cx + dx, cy + dy, 17 * k, state ? (open ? GREEN : CARD) : CARD);
    ring(cx + dx, cy + dy, 17 * k, state ? (open ? GREEN : RED) : SOFT, 2.6);
    text(String(i + 1), cx + dx, cy + dy + 6, { size: 17, weight: 700, color: state && open ? CARD : INK, align: "center", alpha: k });
  });
  const kc = seg(t, 1.0, 2.6);
  text(String(Math.round(14 * outCubic(kc))), 80, 590, { size: 64, weight: 800, font: SORA, color: "#a8432b", alpha: seg(t, 1.0, 1.4) });
  text(S.countLabel, 170, 584, { size: 20, color: SOFT, alpha: seg(t, 1.2, 1.7) });
  [[S.d1, "1,5 km", true], [S.d2, "1,7 km", true], [S.d3, "3,7 km", false], [S.d4, "5,5 km", true]].forEach(([name, dist, open], i) => {
    const k = outCubic(seg(t, 1.4 + i * 0.3, 2.0 + i * 0.3));
    const y = 160 + i * 102, x = 640 + (1 - k) * 40;
    panel(x, y, 560, 86, { r: 16, fill: CARD, stroke: LINE, alpha: k });
    const state = seg(t, a1 + i * 0.25, a1 + 0.4 + i * 0.25);
    dot(x + 40, y + 43, 17, state && open ? GREEN : CARD, k); ring(x + 40, y + 43, 17, state ? (open ? GREEN : RED) : SOFT, 2.6, k);
    text(String(i + 1), x + 40, y + 49, { size: 17, weight: 700, color: state && open ? CARD : INK, align: "center", alpha: k });
    text(name, x + 74, y + 38, { size: 23, weight: 700, font: SORA, color: INK, alpha: k });
    text(open ? S.open : S.closed, x + 74, y + 66, { size: 17, weight: 700, color: open ? GREEN : RED, alpha: k * state });
    if (open) text(S.until, x + 74 + measure(S.open, 17, 700, INTER) + 8, y + 66, { size: 17, color: SOFT, alpha: k * state });
    text(dist, x + 536, y + 38, { size: 19, color: SOFT, align: "right", alpha: k });
    const kr = seg(t, a1 + 1.6 + i * 0.15, a1 + 2.0 + i * 0.15);
    text(S.route + " →", x + 536, y + 66, { size: 17, weight: 600, color: "#2a6fc9", align: "right", alpha: k * kr });
  });
}

/* 7. Le rappel : la notification, la lampe */
function sRappel(t, d, cues) {
  fill(NIGHT);
  title(S.hRemind, seg(t, 0.1, 0.7), "#f6f2e9");
  const a1 = at(cues, 1, 2.9);
  // téléphone
  const k = outCubic(seg(t, 0.3, 1.0));
  ctx.save(); ctx.translate(0, (1 - k) * 40); ctx.globalAlpha *= k;
  box(150, 170, 330, 470, 44, "#0a0d12"); box(162, 182, 306, 446, 34, "#222b3a");
  box(270, 194, 90, 20, 10, "#0a0d12");
  text("19:00", 315, 310, { size: 64, weight: 300, font: SORA, color: "#f6f2e9", align: "center" });
  ctx.restore();
  const kn = outBack(seg(t, a1, a1 + 0.6));
  if (kn > 0) {
    ctx.save(); ctx.globalAlpha *= clamp(kn); ctx.translate(0, (1 - kn) * -30);
    box(176, 360, 278, 118, 20, "#f6f2e9");
    bin(206, 404, 0.42, YELLOW, { body: INK });
    text(S.notifApp, 226, 392, { size: 13, weight: 600, color: SOFT });
    text(S.notifTitle, 196, 426, { size: 20, weight: 800, font: SORA, color: INK });
    para(S.notifBody, 196, 450, 240, { size: 15, lh: 20, color: "#39424c" });
    ctx.restore();
  }
  // lampe
  const a = at(cues, 1, 2.9) + 2.2;
  const glow = seg(t, a, a + 0.9);
  const lx = 880, ly = 330;
  if (glow > 0) {
    const g = ctx.createRadialGradient(lx, ly, 10, lx, ly, 330);
    g.addColorStop(0, `rgba(242,187,12,${0.5 * glow})`); g.addColorStop(1, "rgba(242,187,12,0)");
    ctx.fillStyle = g; ctx.fillRect(lx - 340, ly - 340, 680, 680);
  }
  line([[lx, 150], [lx, ly - 70]], "#5b6672", 4, seg(t, 0.5, 1));
  const ka = seg(t, 0.5, 1.1);
  ctx.save(); ctx.globalAlpha *= ka;
  ctx.fillStyle = "#39424c"; ctx.beginPath(); ctx.moveTo(lx - 40, ly - 70); ctx.lineTo(lx + 40, ly - 70); ctx.lineTo(lx + 78, ly + 4); ctx.lineTo(lx - 78, ly + 4); ctx.closePath(); ctx.fill();
  ctx.restore();
  dot(lx, ly + 16, 34, mix("#6c7684", YELLOW, glow), ka);
  text(S.lamp, lx, ly + 110, { size: 20, color: "#a3acb6", align: "center", alpha: ka });
  bin(lx, 610, 1.9, YELLOW, { alpha: seg(t, a + 0.2, a + 0.8), open: Math.max(0, Math.sin((t - a) * 3)) * 0.5 });
}

/* 8. Fin : ne ratez plus jamais le camion */
function sFin(t, d, cues) {
  fill(YELLOW);
  skyline(600, YDEEP, 1);
  kerb(600, INK, YELLOW);
  const a1 = at(cues, 1, 4);
  const pop = outBack(seg(t, 0.2, 0.9));
  bin(190, 300, 2.8 * pop, YELLOW, { body: INK });
  text(S.name, 310, 240, { size: 96, weight: 800, font: SORA, color: INK, alpha: seg(t, 0.3, 0.9) });
  text(S.free, 314, 296, { size: 28, weight: 600, color: "#3a3320", alpha: seg(t, 1.0, 1.6) });
  const k = outCubic(seg(t, a1, a1 + 0.7));
  box(310, 350 + (1 - k) * 14, measure(S.last, 40, 800, SORA) + 56, 78, 16, INK, k);
  text(S.last, 338, 403 + (1 - k) * 14, { size: 40, weight: 800, font: SORA, color: YELLOW, alpha: k });
  text(S.url, 314, 478, { size: 20, font: MONO, color: INK, alpha: seg(t, a1 + 1.0, a1 + 1.6) });
  const drive = seg(t, a1 + 0.2, d + 0.6);
  truck(lerp(1480, 560, outCubic(drive)), 622, 2.1, GREY);
  [GREY, YELLOW, BROWN].forEach((color, i) => bin(120 + i * 78, 602, 1.05, color, { open: seg(t, a1 + 1.4 + i * 0.2, a1 + 1.8 + i * 0.2) * 0.9 }));
}

VIDEO.create({
  title: { fr: "MEL Collecte", en: "MEL Collecte" },
  kicker: { fr: "Présentation en une minute", en: "Présentation en une minute" },
  langs: ["fr"],
  theme: { bg: INK, bg2: NIGHT, ink: "#f6f2e9", soft: "#c9cfd6", accent: YELLOW, accent2: BROWN, good: GREEN, bad: RED },
  strings: STR,
  background: () => fill(INK),
  poster: "intro",
  scenes: { doute: sDoute, intro: sIntro, installation: sInstall, carte: sCarte, tri: sTri, decheteries: sPlaces, rappel: sRappel, fin: sFin },
});
