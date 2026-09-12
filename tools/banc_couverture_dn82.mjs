// -*- mode: javascript -*-
// ============================================================================
//  tools/banc_couverture_dn82.mjs — CE QUE LE BANC TOUCHE VRAIMENT   (dn8-2)
// ============================================================================
//
//  🔴 CE FICHIER NE JUGE PAS UNE PAGE : IL MESURE UN **INSTRUMENT**. Le banc
//     `tools/banc_langue_dalle_dn73.mjs` EXECUTE le `<script>` de
//     `installeur/index.html` ; ce releve-ci dit COMBIEN de ce script a
//     reellement ete traverse, fonction par fonction et bloc par bloc.
//
//  🔴 POURQUOI IL EXISTE. L'EXISTENCE D'UN BANC ⛔ NE VAUT PAS COUVERTURE.
//     MESURE DU 2026-09-11, avant `dn8-2` : le banc jouait 27 cas et rendait
//     `27 OK, 0 KO` — pendant que **21 des 93 fonctions** du script de la page
//     n'etaient JAMAIS entrees et que **54 des 141 blocs** internes des
//     fonctions vivantes n'etaient JAMAIS atteints.
//
//  🔴 ⚠️ ET CE QU'IL NE DIT **PAS**, ECRIT EN TETE PLUTOT QU'EN NOTE : UNE
//     COUVERTURE QUI MONTE PROUVE QU'UNE LIGNE A TOURNE, ⛔ PAS QU'UNE FAUTE SUR
//     CETTE LIGNE SERAIT VUE. Mesure du 2026-09-12 : l'essai qui a fait passer
//     les fonctions mortes de 21 a 5 restait VERT sur onze inversions REELLES de
//     la page. ⇒ ce releve est un GARDE-FOU DE POPULATION, et le jugement, lui,
//     vit dans les cas de `tools/verif_banc_langue_dn73.py`.
//
//  ── L'INSTRUMENT, ET POURQUOI IL EST HONNETE ──────────────────────────────
//
//  La couverture V8 **TRAVERSE `vm.runInContext`** (verifie le 2026-09-11 :
//  deux contextes jouant la MEME source rendent UNE entree dont les comptes
//  sont ADDITIONNES). C'est ce qui rend la mesure possible du tout.
//
//  ⚠️ LES DECALAGES SONT EN **UNITES UTF-16**, ⛔ PAS EN POINTS DE CODE — et
//     ce n'est pas un detail de forme : le script de cette page porte des
//     emoji (🔴 ⛔ ⚠️), qui comptent DEUX unites chacun. MESURE DU 2026-09-11 :
//     une conversion naive (offset lu comme un index de point de code, ce que
//     fait Python par defaut) attribuait la fonction morte de la l.1515 a la
//     **l.1518** — c'est-a-dire au gestionnaire de `b-dalle-FR` au lieu de
//     celui de `b-dalle-EN`, l'exact contraire du fait. ⇒ ce releve est ecrit
//     en JavaScript PARCE QUE les chaines de JavaScript SONT en UTF-16 : la
//     conversion est juste par construction, ⛔ pas par precaution.
//
//  ⚠️ ET LE `<script>` EST EXTRAIT **PAR LE BANC**, ⛔ pas re-extrait ici : ce
//     releve demande au banc l'offset de la fenetre (`--offset-script`) et
//     tranche la page dessus. Recopier la regle d'extraction en ferait une
//     seconde source de verite, qui pourrirait le jour ou la page change.
//
//  ── ⛔ UN CHIFFRE PRIS SUR UN BANC ROUGE N'EST PAS UNE MESURE ─────────────
//
//  🔴 CORRECTIF DE REVUE DU 2026-09-12, ET IL ETAIT DEMONTRE : ce releve
//     publiait ses comptes et sortait **0** alors que le banc qu'il lance avait
//     rendu `rc != 0`. Une couverture relevee sur une liste de cas TRONQUEE
//     decrit ce qui a tourne avant la panne, ⛔ pas ce que l'instrument couvre.
//     ⇒ le verdict du banc est juge **AVANT** les seuils : `rc = 0` **et** une
//     ligne `BANC : n OK, 0 KO`. Sinon ⇒ **rc=3**, et ⛔ AUCUN chiffre n'est
//     publie comme une mesure.
//
//  ── LE SEUIL EST UN ENGAGEMENT, ⛔ PAS UN VŒU ──────────────────────────────
//
//  🔴 IL EST ECRIT **DANS CE FICHIER** ET IL **MONTE** : un seuil qu'on abaisse
//     pour reverdir est une gate qu'on debranche. Les deux bornes d'entree
//     (2026-09-11, avant `dn8-2`) sont **72/93 fonctions** et **87/141 blocs** ;
//     tout seuil ecrit ici doit leur etre STRICTEMENT SUPERIEUR, et
//     `tools/verif_banc_langue_dn73.py` **(c15)** le RELIT — puis LANCE le
//     temoin ci-dessous, qui joue la DECISION sur des comptes forces.
//
//  🔴 ⚠️ ET LE SEUIL PORTE SUR LE **NUMERATEUR**, ⛔ PAS SUR UN RATIO — C'EST
//     UNE PROPRIETE MESUREE DE L'INSTRUMENT, ⛔ pas une commodite. V8 n'emet
//     les blocs internes d'une fonction QUE LORSQU'ELLE A ETE COMPILEE : le
//     DENOMINATEUR MONTE donc avec la couverture. Mesure a source de page
//     **INCHANGEE** : **93 fonctions / 141 blocs** declares AVANT `dn8-2`,
//     **100 / 190** apres (2026-09-12, SANS base — le seul tir qu'un appelant
//     committe rejoue). ⚠️ CES DEUX COUPLES SONT LES SEULS PUBLIES ICI : un
//     chiffre « avec le serveur reel » n'aurait ⛔ AUCUN producteur committe —
//     ⛔ rien dans ce depot ne passe `--base` a ce relevé. Un seuil
//     ecrit en pourcentage baisserait tout seul a mesure qu'on couvre mieux —
//     c'est-a-dire qu'il se debrancherait lui-meme.
//
//  Emploi :
//      node tools/banc_couverture_dn82.mjs
//      node tools/banc_couverture_dn82.mjs --base http://127.0.0.1:<port>/
//      node tools/banc_couverture_dn82.mjs --temoin-decision
//      node tools/banc_couverture_dn82.mjs --temoin-comptage
//
//  Codes : 0 les deux seuils sont tenus · 1 un seuil est SOUS sa borne ·
//          2 le banc n'a pas pu etre joue, ou n'a rendu AUCUNE couverture ·
//          3 LE BANC LUI-MEME EST ROUGE (⛔ aucun chiffre n'est une mesure).
// ============================================================================

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const RACINE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const BANC = path.join(RACINE, "tools", "banc_langue_dalle_dn73.mjs");
const PAGE = path.join(RACINE, "installeur", "index.html");
const URL_SCRIPT = "installeur/index.html<script>";

// 🔴 LES DEUX SEUILS DECLARES, ET LEURS DEUX BORNES D'ENTREE DATEES.
//    ⛔ Ils ⛔ ne se passent PAS en argument : un seuil reglable a la ligne de
//    commande est un seuil que le prochain tir baissera.
const BORNE_FONCTIONS = 72;      // mesure du 2026-09-11, AVANT `dn8-2`
const BORNE_BLOCS = 87;          // mesure du 2026-09-11, AVANT `dn8-2`
// 🔴 MESURE DU 2026-09-12, APRES `dn8-2`, **SANS BASE** — c'est-a-dire le
//    chiffre que la CI rejoue, ⛔ pas celui d'un lanceur jetable. ⚠️ UN CHIFFRE
//    « AVEC LE SERVEUR REEL » N'EST **PAS** PUBLIE ICI, et le motif est
//    mecanique : ⛔ AUCUN appelant committe de ce depot ne passe `--base` a ce
//    relevé. Il n'aurait donc aucun producteur, et un chiffre que personne ne
//    rejoue est un chiffre a croire sur parole.
//    Les seuils sont poses SOUS cette mesure, ⛔ pas au ras, et le motif est
//    ECRIT — DEUX sources de bruit, ⛔ aucune sous notre controle :
//      · le nombre de blocs que V8 declare depend de la VERSION du moteur, et
//        la CI ⛔ n'epingle PAS la sienne ;
//      · un runner plus lent que ce poste peut faire rougir un cas serre — mais
//        ⛔ plus en silence : un cas perdu rend le banc ROUGE, donc rc=3.
// 🔬 MESURE DU 2026-09-12, SANS BASE (le tir que la CI rejoue) : **96/100
//    fonctions** et **131/190 blocs**, 4 fonctions encore mortes et 59 blocs
//    morts. Les seuils sont poses SOUS cette mesure — 4 fonctions et 11 blocs de
//    marge —, ⛔ pas au ras, et ⛔ pas au-dessus : un seuil au ras rougirait sur
//    du BRUIT de version de V8. ⚠️ Ils sont publies a l'identique dans
//    `mesures/dn8-2/T1-couverture-avant-apres.txt` : ⛔ aucun seuil n'est abaisse
//    apres coup, c'est le defaut que la revue du 2026-09-11 a epingle.
const SEUIL_FONCTIONS = 92;      // ⇒ doit rester > BORNE_FONCTIONS (72)
const SEUIL_BLOCS = 120;         // ⇒ doit rester > BORNE_BLOCS (87)
// Le DENOMINATEUR de la borne d'entree — ⛔ ecrit UNE fois : les blocs morts de
// l'entree s'en DERIVENT (`BLOCS_DECLARES_ENTREE - BORNE_BLOCS`), et un 141
// recopie dans une phrase se perime le jour ou il compte.
const BLOCS_DECLARES_ENTREE = 141;

// Les deux attentes que la gate passe deja au banc — ⛔ pas les valeurs
// genereuses du banc seul : ce releve doit couter ce que coute un tir de gate.
const DELAI_PAGE = 40;
const DELAI_CAS = 1500;

const RC_SOUS_SEUIL = 1;
const RC_MESURE_ABSENTE = 2;
const RC_BANC_ROUGE = 3;

function offsetDuScript() {
  // ⛔ ON NE RE-EXTRAIT PAS : on DEMANDE au banc ou commence sa fenetre.
  const r = spawnSync(process.execPath, [BANC, "--offset-script"],
                      { encoding: "utf8" });
  const m = /^OFFSET (\d+) LONGUEUR (\d+)$/m.exec(r.stdout || "");
  if (!m) { return null; }
  return { debut: parseInt(m[1], 10), longueur: parseInt(m[2], 10) };
}

function jouerLeBancSousCouverture(base) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "dn82-cov-"));
  const argv = [BANC, "--delai", String(DELAI_PAGE),
                "--delai-cas", String(DELAI_CAS)];
  if (base) { argv.push("--base", base); }
  const r = spawnSync(process.execPath, argv, {
    encoding: "utf8",
    env: Object.assign({}, process.env, { NODE_V8_COVERAGE: dir })
  });
  return { dir, rc: r.status, sortie: (r.stdout || "") + (r.stderr || "") };
}

function lireCouverture(dir) {
  // ⚠️ PLUSIEURS FICHIERS SONT POSSIBLES (un par processus) : on les ADDITIONNE
  //    par intervalle plutot que de garder le dernier. Garder le dernier est le
  //    genre de repli muet qui rend une mesure fausse sans rien dire.
  const par = new Map();
  let vu = false;
  for (const f of fs.readdirSync(dir)) {
    if (!f.endsWith(".json")) { continue; }
    let j = null;
    try { j = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")); }
    catch (e) { continue; }
    for (const e of (j.result || [])) {
      if (String(e.url).indexOf(URL_SCRIPT) < 0) { continue; }
      vu = true;
      for (const fn of e.functions) {
        for (let i = 0; i < fn.ranges.length; i++) {
          const r = fn.ranges[i];
          const cle = fn.functionName + "|" + r.startOffset + "|" + r.endOffset
                    + "|" + i;
          const p = par.get(cle);
          if (p) { p.count += r.count; }
          else {
            par.set(cle, { nom: fn.functionName, rang: i, count: r.count,
                           debut: r.startOffset });
          }
        }
      }
    }
  }
  return vu ? [...par.values()] : null;
}

// 🔴 **LA** DECISION, DANS UNE SEULE FONCTION — et c'est elle que le temoin
//    joue. ⛔ Une decision ecrite en ligne dans le corps principal ne peut etre
//    exercee QU'EN rejouant le banc entier : personne ne l'aurait jamais jouee
//    sous le seuil, et « il sort en non-zero sous son seuil » serait resté une
//    PROMESSE ECRITE. Mesure du 2026-09-12 : avec `principal()` appelee sans
//    `exitCode` et un seuil a 99, ce releve sortait **0**.
function decider(mesure, banc, compte) {
  const m = /^BANC : (\d+) OK, (\d+) KO$/m.exec(banc.sortie || "");
  const bancSain = banc.rc === 0 && !!m && m[2] === "0";
  const sousF = compte.nFe < SEUIL_FONCTIONS;
  const sousB = compte.nBe < SEUIL_BLOCS;
  // 🔴 LE CODE 2 EST DECIDE **ICI** (correctif de revue du 2026-09-12). Decide
  //    HORS de cette fonction, il etait INATTEIGNABLE au temoin et vise par
  //    ⛔ AUCUN mutant : la table des codes de l'en-tete publiait un code que
  //    ⛔ rien ne rendait falsifiable.
  if (!mesure.fenetre || !mesure.entrees) {
    return { code: RC_MESURE_ABSENTE, motif:
      "⛔ MESURE ABSENTE : "
      + (!mesure.fenetre ? "la fenetre `<script>` n'a pas ete rendue par le banc"
                         : "⛔ aucune entree de couverture pour « " + URL_SCRIPT
                           + " »")
      + " — ⛔ ce n'est PAS « zero couverture », c'est une mesure QUI MANQUE." };
  }
  if (!bancSain) {
    return { code: RC_BANC_ROUGE, motif:
      "⛔ LE BANC LUI-MEME EST ROUGE (rc=" + banc.rc + ", bilan "
      + (m ? m[0] : "ABSENT") + ") — ⛔ AUCUN chiffre releve ici n'est une "
      + "mesure : une couverture prise sur une liste TRONQUEE decrit ce qui a "
      + "tourne avant la panne." };
  }
  if (sousF || sousB) {
    return { code: RC_SOUS_SEUIL, motif:
      "⛔ SOUS LE SEUIL DECLARE : "
      + (sousF ? "fonctions " + compte.nFe + " < " + SEUIL_FONCTIONS + " " : "")
      + (sousB ? "blocs " + compte.nBe + " < " + SEUIL_BLOCS : "") };
  }
  return { code: 0, motif: "les deux seuils sont tenus" };
}

// ── LE TEMOIN DE LA DECISION — ⛔ IL NE REJOUE PAS LE BANC ─────────────────
// 🔴 HUIT SCENARIOS SUR DES COMPTES **FORCES** : c'est ce qui rend la decision
//    falsifiable sans payer un tir de banc par scenario, et c'est `(c15)` de
//    `tools/verif_banc_langue_dn73.py` qui LANCE ce temoin et confronte les six
//    codes. ⛔ Un seuil dont la decision n'est jouee par personne est un seuil
//    qu'on croit avoir.
const BANC_SAIN = { rc: 0, sortie: "BANC : 42 OK, 0 KO" };
const MESURE_LA = { fenetre: true, entrees: true };
const AU_SEUIL = { nFe: SEUIL_FONCTIONS, nBe: SEUIL_BLOCS };
const SCENARIOS = [
  // ⇒ LES DEUX SCENARIOS DU CODE 2 : la table d'en-tete les publie, et ⛔ rien
  //   ne pouvait les atteindre avant le 2026-09-12.
  ["fenetre-absente", { fenetre: false, entrees: true }, BANC_SAIN, AU_SEUIL],
  ["couverture-absente", { fenetre: true, entrees: false }, BANC_SAIN, AU_SEUIL],
  ["banc-rouge", MESURE_LA, { rc: 1, sortie: "BANC : 41 OK, 1 KO" }, AU_SEUIL],
  ["banc-muet", MESURE_LA, { rc: 0, sortie: "(⛔ aucune ligne de bilan)" },
   AU_SEUIL],
  ["banc-un-ko", MESURE_LA, { rc: 0, sortie: "BANC : 41 OK, 1 KO" }, AU_SEUIL],
  ["sous-fonctions", MESURE_LA, BANC_SAIN,
   { nFe: SEUIL_FONCTIONS - 1, nBe: SEUIL_BLOCS }],
  ["sous-blocs", MESURE_LA, BANC_SAIN,
   { nFe: SEUIL_FONCTIONS, nBe: SEUIL_BLOCS - 1 }],
  ["au-seuil", MESURE_LA, BANC_SAIN, AU_SEUIL]
];

function temoinDeDecision() {
  console.log("TEMOIN DE DECISION — ⛔ le banc n'est PAS rejoue ici.");
  console.log("seuils declares : fonctions " + SEUIL_FONCTIONS + " · blocs "
    + SEUIL_BLOCS);
  for (const [nom, mesure, banc, compte] of SCENARIOS) {
    const d = decider(mesure, banc, compte);
    console.log("TEMOIN " + nom.padEnd(16) + " code=" + d.code + "  " + d.motif);
  }
  return 0;
}

// 🔴 LA BOUCLE DE COMPTAGE, SORTIE DANS **UNE** FONCTION — ⛔ ET CE N'EST PAS UN
//    RANGEMENT : tant qu'elle vivait dans le corps principal, ⛔ **RIEN** ne
//    l'observait. DEMONTRE le 2026-09-12 : remplacer les deux `e.count > 0` par
//    `true` (une mutation qui COMPILE) rendait **100/100 fonctions, 190/190
//    blocs, 0 bloc mort, rc=0**, et `tools/verif_banc_langue_dn73.py` restait a
//    `76 OK / 0 KO` — le plancher 92/120 cessait d'etre un plancher SANS QUE
//    RIEN NE BOUGE. ⇒ une couverture FIXTURE aux comptes CONNUS la traverse
//    desormais, et `(c15)` de la gate du banc LANCE ce temoin.
function compter(entrees, src) {
  const ligneDe = (off) => src.slice(0, off).split("\n").length;
  let nF = 0, nFe = 0, nB = 0, nBe = 0;
  const morts = [];
  for (const e of entrees) {
    if (e.rang === 0) {
      nF++;
      if (e.count > 0) { nFe++; }
      else {
        // ⚠️ LE NOM NE SUFFIT PAS : la plupart de ces fonctions sont ANONYMES,
        //    et DEUX peuvent commencer sur la MEME ligne. ⇒ on imprime aussi
        //    les premiers caracteres de la fonction, qui la DESIGNENT.
        morts.push([ligneDe(e.debut), e.nom || "(anonyme)",
                    src.slice(e.debut, e.debut + 52).split("\n")[0]]);
      }
    } else {
      nB++;
      if (e.count > 0) { nBe++; }
    }
  }
  morts.sort((a, b) => a[0] - b[0]);
  return { nF, nFe, nB, nBe, morts };
}

// ── LE TEMOIN DE **COMPTAGE** : UNE COUVERTURE FIXTURE, AUX COMPTES CONNUS ──
// ⚠️ ELLE EST AU FORMAT DE V8, et elle traverse `lireCouverture` **PUIS**
//    `compter` : c'est la CHAINE ENTIERE qui est observee, ⛔ pas une addition
//    refaite a cote. Elle porte EXPRES **une fonction morte** et **un bloc mort**.
const FIXTURE = { result: [{ scriptId: "1", url: URL_SCRIPT, functions: [
  { functionName: "vivante",
    ranges: [{ startOffset: 0, endOffset: 40, count: 3 },
             { startOffset: 10, endOffset: 20, count: 0 }],
    isBlockCoverage: true },
  { functionName: "morte",
    ranges: [{ startOffset: 50, endOffset: 80, count: 0 }],
    isBlockCoverage: true },
  { functionName: "vivante2",
    ranges: [{ startOffset: 90, endOffset: 99, count: 1 }],
    isBlockCoverage: true }
] }] };
const ATTENDU_FIXTURE = { nF: 3, nFe: 2, nB: 1, nBe: 0, morts: 1 };

function temoinDeComptage() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "dn82-fixture-"));
  let entrees = null;
  try {
    fs.writeFileSync(path.join(dir, "fixture.json"), JSON.stringify(FIXTURE));
    entrees = lireCouverture(dir);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
  if (!entrees) {
    console.log("TEMOIN COMPTAGE ⛔ LA FIXTURE N'A PAS ETE LUE par lireCouverture");
    return 1;
  }
  const c = compter(entrees, "x\n".repeat(200));
  const vu = { nF: c.nF, nFe: c.nFe, nB: c.nB, nBe: c.nBe, morts: c.morts.length };
  const ok = JSON.stringify(vu) === JSON.stringify(ATTENDU_FIXTURE);
  console.log("TEMOIN COMPTAGE fn=" + vu.nFe + "/" + vu.nF + " blk=" + vu.nBe
    + "/" + vu.nB + " morts=" + vu.morts
    + (ok ? "  (attendu)"
          : "  ⛔ ATTENDU fn=" + ATTENDU_FIXTURE.nFe + "/" + ATTENDU_FIXTURE.nF
            + " blk=" + ATTENDU_FIXTURE.nBe + "/" + ATTENDU_FIXTURE.nB
            + " morts=" + ATTENDU_FIXTURE.morts));
  return ok ? 0 : 1;
}

function principal() {
  const args = process.argv.slice(2);
  if (args.includes("--temoin-decision")) { return temoinDeDecision(); }
  if (args.includes("--temoin-comptage")) { return temoinDeComptage(); }
  const iB = args.indexOf("--base");
  const base = (iB >= 0 && args[iB + 1]) ? args[iB + 1] : null;

  const fen = offsetDuScript();
  if (!fen) {
    console.log("⛔ LE BANC N'A PAS RENDU L'OFFSET DE SA FENETRE `<script>`.");
    console.log("   ⇒ sans elle, ⛔ aucune ligne ne peut etre nommee. Geste :");
    console.log("     node tools/banc_langue_dalle_dn73.mjs --offset-script");
    return decider({ fenetre: false, entrees: true }, { rc: 0, sortie: "" },
                   { nFe: 0, nBe: 0 }).code;
  }
  const page = fs.readFileSync(PAGE, "utf8");
  const src = page.slice(fen.debut, fen.debut + fen.longueur);

  const { dir, rc, sortie } = jouerLeBancSousCouverture(base);
  let entrees = null;
  try { entrees = lireCouverture(dir); }
  finally { fs.rmSync(dir, { recursive: true, force: true }); }

  console.log("=".repeat(78));
  console.log("COUVERTURE dn8-2 — LE SCRIPT DE LA PAGE, MESURE PENDANT QU'IL "
    + "S'EXECUTE");
  console.log("=".repeat(78));
  console.log("banc      : tools/banc_langue_dalle_dn73.mjs (rc=" + rc + ")");
  console.log("base HTTP : " + (base || "(aucune — le trajet HTTP n'est PAS joue)"));

  if (!entrees) {
    console.log("⛔ AUCUNE ENTREE DE COUVERTURE pour « " + URL_SCRIPT + " ».");
    console.log("   Le banc n'a pas evalue la page, ou NODE_V8_COVERAGE n'a");
    console.log("   rien ecrit. ⛔ Ce n'est PAS « zero couverture » : c'est une");
    console.log("   MESURE ABSENTE, et elle sort en 2. Derniers octets du banc :");
    console.log("   " + sortie.trim().slice(-200).replace(/\n/g, "\n   "));
    return decider({ fenetre: true, entrees: false }, { rc, sortie },
                   { nFe: 0, nBe: 0 }).code;
  }

  // 🔴 LA LIGNE D'UN DECALAGE — ⛔ EN UTF-16, COMME V8 LES COMPTE, ET
  //    **RELATIF AU `<script>`**, ⛔ pas a la page : `vm.runInContext(src, …)`
  //    compile le SCRIPT SEUL, donc l'origine des decalages est le debut de la
  //    fenetre, ⛔ pas le debut du fichier. Mesure du 2026-09-11 : soustraire
  //    l'offset de la fenetre faisait tomber les sept fonctions mortes DANS DES
  //    COMMENTAIRES — des lignes plausibles et FAUSSES.
  const { nF, nFe, nB, nBe, morts } = compter(entrees, src);

  const verdict = decider(MESURE_LA, { rc, sortie }, { nFe, nBe });

  console.log("-".repeat(78));
  // ⛔ SUR UN BANC ROUGE, LES CHIFFRES SORTENT **MARQUES**, ⛔ pas publies comme
  //    une mesure : c'est le defaut que la revue a demontre.
  const prefixe = verdict.code === RC_BANC_ROUGE ? "⛔ [BANC ROUGE — ⛔ PAS UNE MESURE] " : "";
  console.log(prefixe + "fonctions : " + nFe + "/" + nF + " exercees   (seuil "
    + "declare : " + SEUIL_FONCTIONS + " · borne d'entree 2026-09-11 : "
    + BORNE_FONCTIONS + ")");
  console.log(prefixe + "blocs     : " + nBe + "/" + nB + " atteints   (seuil "
    + "declare : " + SEUIL_BLOCS + " · borne d'entree 2026-09-11 : "
    + BORNE_BLOCS + ")");
  console.log("blocs MORTS : " + (nB - nBe) + "   (borne d'entree 2026-09-11 : "
    + (BLOCS_DECLARES_ENTREE - BORNE_BLOCS) + " sur "
    + BLOCS_DECLARES_ENTREE + ")");
  if (morts.length) {
    console.log("FONCTIONS ENCORE MORTES (" + morts.length + ") — la ligne est "
      + "celle du `<script>`, ⛔ pas de la page :");
    for (const [l, n, txt] of morts) {
      console.log("  l." + String(l).padEnd(6) + (n || "(anonyme)").padEnd(20)
        + txt);
    }
  }
  // 🔴 CE QUE CES DEUX FRACTIONS **NE SONT PAS**, DIT EN PROPRE ET A CHAQUE TIR.
  console.log("-".repeat(78));
  console.log("⚠️ ⛔ CES DENOMINATEURS NE SONT PAS DES POPULATIONS : V8 n'emet ni");
  console.log("   les fonctions imbriquees dans une fonction JAMAIS COMPILEE, ni");
  console.log("   les blocs qui comptent comme leur parent. ⇒ le compte total");
  console.log("   MONTE quand la couverture monte (mesure a source INCHANGEE :");
  console.log("   93 ⇒ 100 fonctions et " + BLOCS_DECLARES_ENTREE + " ⇒ 190 "
    + "« blocs » declares, SANS base), et un");
  console.log("   seuil ecrit en POURCENTAGE se debrancherait tout seul. C'est");
  console.log("   pourquoi les deux seuils portent sur le NUMERATEUR.");
  console.log("⚠️ ET UNE COUVERTURE QUI MONTE ⛔ NE PROUVE PAS QU'UNE FAUTE SERAIT");
  console.log("   VUE : le jugement vit dans les cas de la gate du banc, ⛔ pas");
  console.log("   dans ce compte. Mesure : 21 ⇒ 5 fonctions mortes ET onze");
  console.log("   inversions reelles restees VERTES, le meme jour.");
  console.log("-".repeat(78));

  if (verdict.code !== 0) {
    console.log(verdict.motif);
    if (verdict.code === RC_SOUS_SEUIL) {
      console.log("⛔ ⛔ LE GESTE N'EST PAS D'ABAISSER LE SEUIL : un seuil qu'on");
      console.log("   baisse pour reverdir est une gate qu'on debranche. Le geste");
      console.log("   est de rendre au banc le cas qu'il a perdu.");
    } else {
      console.log("   Derniers octets du banc : "
        + sortie.trim().slice(-160).replace(/\n/g, " · "));
    }
    return verdict.code;
  }
  console.log("COUVERTURE : " + nFe + "/" + nF + " fonctions, " + nBe + "/" + nB
    + " blocs — les deux seuils sont tenus.");
  return 0;
}

process.exitCode = principal();
