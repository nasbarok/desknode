// -*- mode: javascript -*-
// ============================================================================
//  tools/banc_langue_dalle_dn73.mjs — LE BANC DE LA POSE DE LANGUE   (dn7-3)
// ============================================================================
//
//  🔴 IL **EXECUTE** LE JAVASCRIPT DE `installeur/index.html`, ⛔ IL NE LE
//     REJOUE PAS. Le `<script>` de la page est EXTRAIT du fichier et evalue
//     dans un contexte isole ; les fonctions appelees ensuite — `poserLangueDalle`,
//     `consoleEcrire`, `consoleAjouter` — sont **CELLES DE LA PAGE**. Un
//     harnais qui rejouerait une logique recopiee ne mesurerait que lui-meme,
//     et c'est un piege que ce depot a deja paye.
//
//  🔴 POURQUOI CE BANC EXISTE. Aucune gate de ce depot n'executait le
//     JavaScript de cette page, et `dn7-3` y a ajoute de la matiere d'une
//     nature NEUVE : jusque-la, la page ne faisait que **LIRE** le port ; elle
//     **ECRIT** maintenant — prise d'un verrou d'ecriture, encodage, envoi,
//     relachement sur deux chemins, attente armee sur un motif, et trois
//     aller-retours avec la carte. La gate statique
//     `tools/verif_langue_dalle_dn73.py` prouve la STRUCTURE ; celle-ci prouve
//     le COMPORTEMENT.
//
//  ── CE QU'IL MESURE, ET CE QU'IL NE MESURE PAS ────────────────────────────
//
//  ✅ Les **NEUF** lignes de la matrice d'entrees-sorties du dossier, chacune
//     jouee contre un DOM bidon et un port bidon, plus les TROIS chemins que la
//     revue a nommes : l'ouverture du port **par le selecteur** suivie d'une
//     pose complete, la reponse « posee A CHAUD mais NON PERSISTEE », et la
//     relecture qui ne porte pas le code envoye.
//  ⚠️ ANNOTE LE 2026-09-11 (`dn8-2`) — ⛔ LES LIGNES CI-DESSUS NE SONT PAS
//     EFFACEES, MAIS LEUR COMPTE EST **PERIME** : la liste a grandi a chaque
//     marche (`dn7-4`, `dn7-6`, puis `dn8-2`). Le compte qui fait foi est
//     `--liste-cas`, ⛔ pas cette phrase — un nombre ecrit dans un commentaire
//     se perime le jour ou il compte. Releve du 2026-09-11 : **27 cas** AVANT
//     `dn8-2`.
//  🔴 CE QUE `dn8-2` AJOUTE, ET POURQUOI. MESURE SOUS `NODE_V8_COVERAGE` le
//     2026-09-11 : sur les **93 fonctions** du script de la page, **21**
//     n'etaient JAMAIS entrees et **54 des 141 blocs** internes des fonctions
//     vivantes n'etaient JAMAIS atteints. L'existence d'un banc ⛔ NE VAUT PAS
//     couverture. ⇒ trois choses entrent ici :
//       · une ASSERTION DE DOM NON DEGENERE, jouee **AVANT** `runInContext` —
//         `dn7-4` a mesure que deux branches de `montrerSortie()` etaient
//         MORTES parce que le DOM bidon n'avait ni `parentNode`, ni
//         `nextSibling`, ni `insertBefore`, et que le banc rendait quand meme
//         `18 OK, 0 KO`. Le temoin `--temoin-dom` REPLANTE ce cas ;
//       · un **VRAI SERVEUR** derriere `--base` : sans lui, `fetch` rejette
//         toujours, et une INVERSION dans le routage de `do_POST` passerait
//         VERTE. ⛔ Le serveur est lie par la GATE, ⛔ jamais par ce banc ;
//       · les cas qui entrent dans les surfaces MORTES : la console serie, la
//         langue de la PAGE, les verbes qu'aucun clic n'atteignait.
//  🔴 AMENDE LE 2026-09-12 (boucle de revue 1 de `dn8-2`) — **EXECUTER N'EST PAS
//     JUGER, ET C'EST MESURE.** 19 sondes de mutation jouees sur une copie
//     jetable ont laisse ce banc VERT sur ONZE inversions REELLES — dont
//     l'avertissement hors Windows que le ledger demontrait le 2026-09-09. Une
//     couverture qui monte prouve qu'une ligne a tourne, ⛔ pas qu'une faute sur
//     cette ligne serait vue. ⇒ quatre choses de plus, et chacune ferme un
//     constat DEMONTRE :
//       · CHAQUE BLOC D'AFFICHAGE CONDITIONNEL est OBSERVE dans ses DEUX etats,
//         par un VECTEUR compare EN ENTIER (`etat-hors-windows`,
//         `etat-orphelin`, `etat-port-tenu`, `etat-cdn`, `etat-inactif`,
//         `etat-not-allowed`, `etat-unsupported`, le bloc d'installation,
//         `etat-charge`, `etat-deps`, `etat-lhm`) ⛔ pas par un booleen ;
//       · LE PORT BIDON MODELISE LES VERROUS : `close()` REJETTE tant qu'un
//         lecteur ou un ecrivain tient le flux, comme le navigateur. Une
//         fermeture jouee dans le MAUVAIS ORDRE se voit donc, et une fermeture
//         qui ECHOUE publie `console.non-rendue`, ⛔ jamais « port rendu » ;
//       · LES VERBES SONT ARMES PAR **LA FONCTION DE LA PAGE**
//         (`rafraichirEtat` puis `appliquerFlash`), ⛔ jamais cliques DESARMES,
//         et l'etat des quatre boutons APRES un verbe qui ECHOUE est compare a
//         celui d'AVANT — le `.catch` de `jouer` est ce qui les rend ;
//       · LE PONT IMITE LE NAVIGATEUR : un POST porte `Origin`, et le vrai
//         `fetch` n'est donne QU'AUX cas HTTP.
//  ⚠️ ET DEUX ETATS DE DEPART CESSENT D'APPARTENIR AU BANC : l'etat initial des
//     QUATRE boutons de choix est **LU DANS LE BALISAGE** (⛔ plus
//     `en=null fr=null`), et la version attendue du cas HTTP est **LUE DANS LE
//     MANIFESTE** (⛔ plus un `40be2c8` grave ici, que `dn8-7` ferait mentir).
//  🔴 `asserterDom` JUGE DES **VALEURS** — le conteneur, le frere suivant —, ⛔
//     plus la seule PRESENCE des trois capacites : un getter qui rend toujours
//     `null` porte la cle et ⛔ ne dit rien de juste.
//  ⚠️ LES CAS SE JOUENT EN **PARALLELE BORNE** (8 a la fois), ⛔ plus un par un.
//     MESURE DU 2026-09-12 : construire un contexte et evaluer la page coute
//     **1,9 ms**, tout le reste etant de l'ATTENTE armee. La campagne rejoue ce
//     banc UNE FOIS PAR MUTANT, et c'est cette mesure-la qui paie les mutants
//     neufs. ⛔ Les lignes `CAS` restent imprimees DANS L'ORDRE DE LA LISTE, ⛔
//     jamais dans l'ordre d'arrivee : un ordre d'arrivee rendrait la sortie non
//     reproductible, donc illisible a la comparaison.
//  🔴 Et il mesure la **SUITE** des issues annoncees, ⛔ pas seulement la
//     derniere : une annonce de succes POSEE PUIS ECRASEE par le verdict juste
//     laisse l'ecran final correct et le defaut INVISIBLE. MESURE : sans ce
//     releve, le temoin « succes annonce AVANT la relecture » sortait VERT.
//     ⇒ `langue.posee` ⛔ ne peut apparaitre qu'UNE fois, et EN DERNIER.
//  🔴 ET IL SORT EN **NON-ZERO** QUAND SA CHAINE NE SE RESOUT PAS. Un banc qui
//     rend 0 sur une liste tronquee annonce un succes qu'il n'a pas mesure :
//     chaque cas est borne, et un plafond global le tue en dernier ressort. Le
//     drapeau `--temoin-chaine` REPLANTE ce cas et se joue.
//  ⛔ Il ne parle a AUCUNE carte. Un port bidon rend les litteraux que le
//     firmware imprime ; ⛔ il ne prouve pas que la carte les imprime vraiment,
//     ni que la langue survive a une coupure d'alimentation. Cette moitie-la se
//     lit AU BANDEAU DE LA DALLE, a l'oeil, en seance carte.
//  ⛔ Il ne rend AUCUN verdict sur la lisibilite de la page.
//
//  ── LE COUT EST UNE CONTRAINTE, ⛔ PAS UN EFFET DE BORD ────────────────────
//
//  🔴 `tools/verif_campagne_dn56.py` rejoue chaque gate UNE FOIS PAR MUTANT, et
//     elle doit rester sous 60 % du plafond de `tools/run_gates.sh`. MESURE : ce
//     banc paye DEUX attentes par tir ; laissees a leur valeur de produit
//     (6 000 ms), elles ont porte la campagne a 93 % de son plafond. ⇒ les
//     deux delais de la page sont **REPOSES** ici apres evaluation, et le banc
//     ECHOUE FERME s'il ne les trouve pas : un banc qui ne peut pas les regler
//     ⛔ ne doit PAS se rabattre en silence sur six secondes.
//
//  Emploi :
//      node tools/banc_langue_dalle_dn73.mjs [--page <chemin>] [--delai <ms>]
//                                             [--delai-cas <ms>] [--base <url>]
//      node tools/banc_langue_dalle_dn73.mjs --liste-cas
//      node tools/banc_langue_dalle_dn73.mjs --temoin-chaine
//      node tools/banc_langue_dalle_dn73.mjs --temoin-dom
//      node tools/banc_langue_dalle_dn73.mjs --offset-script
//
//  ⚠️ `--base` EST **OPTIONNELLE, ET SON ABSENCE NE CHANGE RIEN** : sans elle,
//     `fetch` rejette comme avant et les cas HTTP ⛔ ne sont PAS joues. Ce banc
//     ⛔ ne lie AUCUN port lui-meme, et il ⛔ n'en fermera donc aucun : le
//     serveur vit dans `tools/verif_banc_langue_dn73.py`, qui le lie sur
//     `127.0.0.1:0` et le ferme dans son `finally`.
//  🔴 ET L'URL DE LA PAGE EST **RELATIVE** (`fetch("api/agent/stop")`) : la
//     resoudre contre la base est le travail du NAVIGATEUR, et c'est pour ca
//     que `new URL(u, BASE)` vit dans le pont — l'ecrire dans un cas ferait
//     mesurer le pont au lieu de la page.
//
//  ⚠️ `--page` sert a la gate `tools/verif_banc_langue_dn73.py`, qui MUTE la
//     page dans une COPIE JETABLE et rejoue le banc dessus. ⛔ Le banc n'ecrit
//     JAMAIS dans le depot.
//
//  Sortie : une ligne `CAS <nom> <OK|KO> …` par cas, puis `BANC : n OK, m KO`.
//  Codes  : 0 tout passe · 1 au moins un cas rouge · 2 la page ne se lit pas ·
//           3 la chaine ne s'est PAS resolue (⛔ pas un succes : une ignorance) ·
//           4 le DOM du banc est DEGENERE — ⛔ rendu SEULEMENT par le temoin
//             `--temoin-dom`, qui REPLANTE la faute de `dn7-4`.
// ============================================================================

import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const RACINE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const PAGE_DEFAUT = path.join(RACINE, "installeur", "index.html");

// ── LES REPONSES QUE LA CARTE BIDON REND ───────────────────────────────────
// ⚠️ ELLES SONT RECOPIEES DU FIRMWARE, ET C'EST ASSUME : ce banc joue une
//    carte, ⛔ il n'en mesure pas une. Ce qui garantit qu'elles sont encore
//    celles du firmware est le controle `(c16)` de
//    `tools/verif_langue_dalle_dn73.py`, qui les RELIT dans `firmware/`.
const R_INVITE = "\ndesknode> ";
const R_SUCCES = "langue : FR   (scene reconstruite)\ndesknode> ";
const R_NOOP = "rien a faire : la langue est DEJA FR.\n(aucune ecriture NVS, aucune reconstruction)\ndesknode> ";
const R_REFUS = "\u{1F534} REFUS : « fr » n'est pas une langue connue.\nCommand returned non-zero error code\ndesknode> ";
// 🔴 LA CINQUIEME ISSUE, ET ELLE EST LA RAISON DE LA RE-DERIVATION : la carte
//    imprime SON avertissement, PUIS reconstruit la scene, PUIS imprime la
//    ligne de succes, et rend un code NON NUL. Les deux moities tombaient dans
//    le meme motif ⇒ la page annoncait l'inverse de ce que la carte disait.
const R_NVS = "⚠️ ECRITURE NVS REFUSEE (ESP_ERR_NVS_NOT_ENOUGH_SPACE) — la langue est posee A CHAUD mais ⛔ elle NE survivra PAS au reboot.\nlangue : FR   (scene reconstruite)\nCommand returned non-zero error code\ndesknode> ";
const R_LUE_FR = "langue de l'ecran : FR   (⛔ defaut = EN)\nusage : langue <en|fr>\ndesknode> ";
const R_LUE_EN = "langue de l'ecran : EN   (⛔ defaut = EN)\nusage : langue <en|fr>\ndesknode> ";
// ⛔ CE QUE LA CARTE DIT **SANS RAPPORT** AVEC LA LANGUE, ET QUI PORTE `REFUS`.
//    C'est la raison pour laquelle le classement s'ancre sur les litteraux de
//    `cmd_langue`, ⛔ pas sur un motif qui traverse tout le flux : ce journal-ci
//    est REEL, et il tombe dans la fenetre de demarrage a froid ou ce geste se
//    joue. Il est melange a la reponse du no-op, et le verdict doit rester
//    « posee ».
const R_BRUIT = "E (2317) dn_capteurs: ouverture REFUSEE : le bus I2C n'existe pas\n";
// 🔴 CE QUE LA PAGE DIT DU PORT — ⛔ un port tenu EN SILENCE empeche l'agent de
//    repartir, et c'est `dn7-2` qui l'a nomme. Les deux phrases sont OPPOSEES,
//    donc une seule des deux peut etre vraie a la fois : c'est ce qui en fait
//    une mesure et ⛔ pas une presence.
const PORT_TENU = "This page still holds the serial port";
const PORT_LIBRE = "This page does ⛔ not hold the serial port";

// ── LES DEUX BORNES DE TEMPS DU BANC ───────────────────────────────────────
// ⚠️ ELLES SE REGLENT, PARCE QUE LA CAMPAGNE LES REJOUE UNE FOIS PAR MUTANT.
let DELAI_PAGE = 40;        // ce que la PAGE attendra (repose apres evaluation)
// 🔴 LA BASE HTTP — `null` PAR DEFAUT, ET C'EST LA PROPRIETE : ⛔ sans elle, ce
//    banc se comporte EXACTEMENT comme avant `dn8-2`.
let BASE = null;
// 🔴 LE TEMOIN DE DOM : il DEGRADE un element monte, et l'assertion doit le
//    dire AVANT que la moindre ligne de la page ne s'evalue.
let TEMOIN_DOM = false;
const SIGNATURE_DOM = "DOM DEGENERE";
const RC_DOM = 4;
let DELAI_CAS = 4000;       // la borne d'UN cas — au-dela il est ROUGE, ⛔ pas vert
let PLAFOND = 30000;        // le filet global — au-dela le banc SORT EN 3

// 🔴 COMBIEN DE CAS A LA FOIS — ⛔ PAS UNE COMMODITE, UN BUDGET (voir l'en-tete).
//    ⚠️ BORNEE, ⛔ pas « tous » : les bornes de cas (`DELAI_CAS`) demarrent quand
//       l'ouvrier prend le cas, et lacher 45 evaluations d'un coup ferait expirer
//       des bornes AVANT que le premier cas n'ait ete joue.
const CONCURRENCE = 8;
// Le manifeste de la charge — la version ATTENDUE par le cas HTTP y est **LUE**.
// ⛔ Elle n'est PAS ecrite en dur : `dn8-7` reconstruira cette charge, et un
//    chiffre grave ici rougirait ce jour-la sans rien apprendre a personne.
let MANIFESTE = path.join(RACINE, "installeur", "charge", "manifest.json");
let VERSION_MANIFESTE = null;
// Les quatre boutons dont l'etat de depart est LU DANS LE BALISAGE, ⛔ pas pose.
const BOUTONS_DE_CHOIX = ["b-langue-en", "b-langue-fr", "b-dalle-en", "b-dalle-fr"];
let ARIA_INITIAL = {};

// 🔴 LA FENETRE DU `<script>`, ⛔ CALCULEE UNE SEULE FOIS ET EN UN SEUL
//    ENDROIT. `tools/banc_couverture_dn82.mjs` la DEMANDE (`--offset-script`)
//    plutot que de la recalculer : deux extractions, c'est deux sources de
//    verite, et la seconde pourrit le jour ou la page change.
function fenetreDuScript(chemin) {
  const brut = fs.readFileSync(chemin, "utf8");
  const i = brut.indexOf("<script>\n");
  const j = brut.indexOf("</script>", i);
  if (i < 0 || j < 0) {
    return null;
  }
  // 🔴 ⛔ ON ECHOUE **FERME** SUR UNE FENETRE DOUTEUSE. Cette extraction coupe a
  //    la PREMIERE balise fermante : le jour ou la page porte cette chaine dans
  //    un litteral JavaScript, le script serait TRONQUE — et un script tronque
  //    s'evalue peut-etre encore, en ayant perdu la moitie de ce qu'on mesure.
  //    ⇒ une seule fermante apres l'ouvrante, ⛔ sinon on ne joue rien.
  let n = 0;
  for (let k = brut.indexOf("</script>", i); k >= 0; k = brut.indexOf("</script>", k + 1)) { n++; }
  if (n !== 1) {
    return null;
  }
  const debut = i + "<script>\n".length;
  return { brut, debut, longueur: j - debut };
}

function litLeScript(chemin) {
  const f = fenetreDuScript(chemin);
  return f ? f.brut.slice(f.debut, f.debut + f.longueur) : null;
}

// 🔴 L'ETAT INITIAL DES QUATRE BOUTONS DE CHOIX, **LU DANS LE BALISAGE** (dn8-2).
//    ⛔ CE BANC N'INVENTE PLUS CET ETAT. Avant ce jour, `langue-de-la-page`
//    epinglait `en=null fr=null` : un etat de depart qui n'appartenait qu'au
//    banc, alors que la page porte `aria-pressed` SUR CES QUATRE BOUTONS et que
//    le defaut anglais tient PAR CE BALISAGE — exactement comme le defaut de la
//    dalle tient par l'ABSENCE d'ecriture en NVS.
// ⚠️ LA FENETRE EST LE BALISAGE **AVANT** LE `<script>` : le script CITE ces
//    identifiants pour les chercher, et lire le fichier entier ferait tomber sur
//    la citation plutot que sur la balise.
// ⚠️ ET CE N'EST ⛔ PAS LA SEULE LECTURE DE CES ATTRIBUTS : `verif_entree_dn82.py`
//    les relit avec `html.parser` et confronte « anglais presse ». Deux lectures
//    INDEPENDANTES d'un meme fait, qui rougissent chacune de son cote.
function ariaDuBalisage(balisage) {
  const out = {};
  for (const id of BOUTONS_DE_CHOIX) {
    const i = balisage.indexOf('id="' + id + '"');
    if (i < 0) { out[id] = null; continue; }
    const deb = balisage.lastIndexOf("<", i);
    const fin = balisage.indexOf(">", i);
    const balise = (deb >= 0 && fin > i) ? balisage.slice(deb, fin + 1) : "";
    const m = /\saria-pressed="(true|false)"/.exec(balise);
    out[id] = m ? m[1] : null;
  }
  return out;
}

// ── UN DOM BIDON, ⛔ PAS UN MOTEUR DE RENDU ────────────────────────────────
//    Il repond a ce que le script de la page demande VRAIMENT, et a rien de
//    plus. Tout ce qu'il ne sait pas faire est INERTE, ⛔ jamais simule.
//
// 🔴 AJOUTE LE 2026-09-10 (`dn7-4`) — UN ARBRE **MINIMAL**, ET C'EST UNE MESURE,
//    ⛔ pas du confort. Sans `parentNode`, `nextSibling` ni `insertBefore`, LES
//    DEUX BRANCHES de `montrerSortie()` etaient MORTES dans le seul instrument
//    qui execute cette page : remplacer `ancre.parentNode` par `sortieParent`
//    faisait lever `NotFoundError` a chaque clic de verbe — les deux boutons
//    devenaient MUETS — et le banc rendait quand meme `18 OK, 0 KO`.
//    ⇒ un conteneur ordonne, et rien de plus : ⛔ pas de rendu, ⛔ pas de style.
function faireConteneur(nom) {
  const p = {
    nom, enfants: [],
    retirer(n) {
      const i = p.enfants.indexOf(n);
      if (i >= 0) { p.enfants.splice(i, 1); n.parent = null; }
    },
    // ⛔ LA MEME REGLE QUE LE NAVIGATEUR : un noeud de reference qui n'est PAS
    //    un enfant de ce parent fait LEVER. C'est ce que la page doit eviter,
    //    et c'est donc ce que le banc doit pouvoir reproduire.
    insertBefore(n, ref) {
      if (ref && p.enfants.indexOf(ref) < 0) {
        throw new Error("NotFoundError: the node before which the new node is "
          + "to be inserted is not a child of this node.");
      }
      // ⚠️ LA REGLE DU DOM, ⛔ PAS UNE COMMODITE : « si le noeud de reference EST
      //    le noeud insere, la reference devient son frere suivant » — sinon
      //    replacer un noeud DEJA a sa place le renvoie EN QUEUE. Mesure du
      //    2026-09-10 : sans cette ligne, le second `montrerSortie(bouton)`
      //    d'un meme clic deplacait le transcript APRES le bloc voisin, et le
      //    banc accusait la PAGE d'un defaut qui etait CELUI DU STUB.
      if (ref === n) { ref = n.nextSibling; }
      if (n.parent) { n.parent.retirer(n); }
      const i = ref ? p.enfants.indexOf(ref) : -1;
      if (i < 0) { p.enfants.push(n); } else { p.enfants.splice(i, 0, n); }
      n.parent = p;
      return n;
    }
  };
  return p;
}

// Ou vit un element, dit en UNE chaine : le conteneur, et ce qui le PRECEDE.
function placeDe(el) {
  if (!el || !el.parent) { return "⛔ ORPHELIN"; }
  const p = el.parent;
  const i = p.enfants.indexOf(el);
  return p.nom + " apres " + (i > 0 ? (p.enfants[i - 1].id || "?") : "(tete)");
}

function faireElement(id) {
  return {
    id, hidden: true, textContent: "", className: "", disabled: false,
    attrs: {}, enfants: [], clics: [], scrollTop: 0, scrollHeight: 0,
    parent: null,
    get parentNode() { return this.parent; },
    get nextSibling() {
      const p = this.parent;
      if (!p) { return null; }
      const i = p.enfants.indexOf(this);
      return (i >= 0 && i + 1 < p.enfants.length) ? p.enfants[i + 1] : null;
    },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; },
    appendChild(n) { this.enfants.push(n); this.textContent += (n.txt || ""); },
    // 🔴 LES GESTIONNAIRES DE CLIC SONT **GARDES** : c'est la seule facon de
    //    dispatcher un VRAI clic et de mesurer la liaison bouton ⇄ code.
    addEventListener(t, f) { if (t === "click" && typeof f === "function") { this.clics.push(f); } },
    scrollIntoView() {}
  };
}

// ── L'ASSERTION DE NON-DEGENERESCENCE DU DOM ─────────────── (dn8-2) ──
// 🔴 ELLE SE JOUE **AVANT** `runInContext`, ET C'EST TOUTE SA VALEUR. `dn7-4` a
//    MESURE le cas : sans `parentNode`, `nextSibling` ni `insertBefore`, LES
//    DEUX BRANCHES de `montrerSortie()` etaient MORTES — les deux boutons de
//    verbe devenaient MUETS — et le banc rendait quand meme `18 OK, 0 KO`. Les
//    trois capacites ont ete AJOUTEES ce jour-la ; ⛔ RIEN ne garantissait
//    qu'elles RESTENT. C'est ce « rien » que cette assertion remplace.
// ⛔ ELLE NE REPARE RIEN, ET ELLE NE SE CONTENTE PAS DE COMPTER : elle LEVE, en
//    nommant l'ELEMENT et la CAPACITE — un banc qui dirait « DOM incomplet »
//    enverrait chercher a l'aveugle.
const POURQUOI_DOM = {
  parentNode: "la branche qui replace le transcript SOUS le bouton clique "
            + "serait MORTE, et ce banc VERT dessus",
  nextSibling: "le retour du transcript A SA PLACE D'ORIGINE serait MORT, et "
             + "ce banc VERT dessus",
  insertBefore: "⛔ aucun deplacement du transcript ne serait possible, et "
              + "`montrerSortie()` leverait a chaque clic"
};

// 🔴 ELLE JUGE DES **VALEURS**, ⛔ PLUS UNE PRESENCE (correctif de revue,
//    2026-09-12). La 1re redaction testait `cap in el` : un getter qui rend
//    TOUJOURS `null` porte la cle et passait donc — et le motif d'un ORPHELIN
//    disait « SANS insertBefore », c'est-a-dire le mauvais defaut sur le bon
//    element. ⇒ le parent doit ETRE le conteneur, et le frere suivant doit ETRE
//    celui du conteneur (ou `null` en queue).
function asserterDom(montes) {
  for (const [conteneur, el] of montes) {
    const ou = "« " + (el.id || "?") + " » monte dans « " + conteneur.nom + " »";
    const i = conteneur.enfants.indexOf(el);
    const nomDe = (n) => String(n && n.id ? n.id : n);
    const parent = el.parentNode;
    // ⛔ UN ORPHELIN SE DIT **ORPHELIN**, et c'est son propre motif.
    if (!parent) {
      throw new Error(SIGNATURE_DOM + " : " + ou + " est ⛔ ORPHELIN — "
        + "« parentNode » rend " + String(parent) + " — " + POURQUOI_DOM.parentNode);
    }
    if (parent !== conteneur) {
      throw new Error(SIGNATURE_DOM + " : " + ou + " ⛔ « parentNode » ne rend "
        + "PAS son conteneur mais « " + String(parent.nom) + " » — "
        + POURQUOI_DOM.parentNode);
    }
    if (typeof parent.insertBefore !== "function") {
      throw new Error(SIGNATURE_DOM + " : " + ou + " ⛔ SANS « insertBefore » "
        + "APPELABLE — " + POURQUOI_DOM.insertBefore);
    }
    const attendu = (i >= 0 && i + 1 < conteneur.enfants.length)
      ? conteneur.enfants[i + 1] : null;
    if (el.nextSibling !== attendu) {
      throw new Error(SIGNATURE_DOM + " : " + ou + " ⛔ « nextSibling » rend "
        + nomDe(el.nextSibling) + " au lieu de " + nomDe(attendu) + " — "
        + POURQUOI_DOM.nextSibling);
    }
  }
  return montes.length;
}

// La forme VIDE d'un resultat de cas — ⛔ une seule fois, pour que les chemins
// ne divergent pas les uns des autres.
function resultatVide() {
  return {
    etatLangue: "", etatConsole: "", relais: "", relaisCache: true,
    classe: "", poserDesarme: undefined, ecrits: [], octets: 0, suite: [],
    enVol: false, verrouRendu: 0
  };
}

// 🔴 ELLE PREND LE **CAS ENTIER** (dn8-2) : le contexte du navigateur
//    (`isSecureContext`, `navigator.serial`) se decide PENDANT l'evaluation, et
//    deux blocs de la page en dependent. Le poser apres coup ⛔ ne peut pas les
//    atteindre : ils seraient verts par construction.
function faireContexte(src, cas) {
  const choix = cas.choix;
  const cx = cas.contexte || {};
  const els = {};
  // Les URL demandees par la page, RELEVEES telles qu'elle les ecrit — ⛔ pas
  // telles que le pont les resout : c'est la PAGE qu'on mesure.
  const traces = [];
  const doc = {
    documentElement: {
      attrs: { "data-langue": "en", lang: "en" },
      setAttribute(k, v) { this.attrs[k] = v; },
      getAttribute(k) { return this.attrs[k] ?? null; }
    },
    getElementById(id) { return (els[id] = els[id] || faireElement(id)); },
    createElement() {
      return {
        lang: "", txt: "",
        set textContent(v) { this.txt = v; },
        get textContent() { return this.txt; },
        set innerHTML(v) { this.txt = v; },
        appendChild() {}
      };
    },
    createDocumentFragment() {
      return { txt: "", enfants: [], appendChild(n) { this.enfants.push(n); this.txt += n.txt; } };
    },
    createTextNode(t) { return { txt: t }; },
    addEventListener() {}
  };
  // 🔴 L'ARBRE EST MONTE **AVANT** `runInContext`, ET C'EST LA PROPRIETE : la
  //    page LIT `sortie.parentNode` / `sortie.nextSibling` AU CHARGEMENT. Monte
  //    apres, la place d'origine serait `null` et les deux branches de
  //    `montrerSortie()` resteraient mortes — exactement ce que ce banc existe
  //    pour ne plus laisser passer.
  //    ⚠️ TROIS CONTENEURS SUFFISENT, et ils MIMENT le document : `#sortie` est
  //       le dernier bloc de sa section (avec un frere APRES lui, pour que le
  //       retour a la maison ne se joue pas sur le seul cas `null`), `b-stop`
  //       vit dans le GESTE 1, `b-retirer` en SECTION 4.
  const maison = faireConteneur("sec-suite");
  const geste1 = faireConteneur("geste-1");
  const section4 = faireConteneur("sec-agent");
  maison.insertBefore(doc.getElementById("sortie"), null);
  maison.insertBefore(doc.getElementById("bas-de-section"), null);
  geste1.insertBefore(doc.getElementById("b-stop"), null);
  geste1.insertBefore(doc.getElementById("etat-port-tenu"), null);
  section4.insertBefore(doc.getElementById("b-retirer"), null);
  section4.insertBefore(doc.getElementById("apres-retirer"), null);
  // 🔴 LES ELEMENTS DE `dn7-6` SONT MONTES **AVANT** `runInContext`, ET POUR LA
  //    MEME RAISON QUE CEUX DE `dn7-4` : le script LIT ses boutons AU
  //    CHARGEMENT. ⚠️ Le fichier documente deja le cas vecu — un element non
  //    monte avant l'execution rend le banc VERT sur des branches MORTES —, et
  //    `dn7-5` en avait laisse le residu : son `poserMot("v-lhm", …)` n'etait
  //    traverse par AUCUN harnais.
  //    ⚠️ QUATRE TEMOINS D'ETAPE, un par `<li>` du workflow, et ils vivent
  //       CHACUN DANS SON GESTE — les entasser dans un seul conteneur ferait
  //       mesurer une page qui n'existe pas.
  const entete = faireConteneur("sec-suite-entete");
  const geste2 = faireConteneur("geste-2");
  const geste3 = faireConteneur("geste-3");
  const geste4 = faireConteneur("geste-4");
  entete.insertBefore(doc.getElementById("etat-deps"), null);
  entete.insertBefore(doc.getElementById("etat-lhm"), null);
  entete.insertBefore(doc.getElementById("b-deps"), null);
  entete.insertBefore(doc.getElementById("b-deps-raison"), null);
  geste1.insertBefore(doc.getElementById("v-etape-arret"), null);
  geste2.insertBefore(doc.getElementById("v-etape-flash"), null);
  geste3.insertBefore(doc.getElementById("v-etape-langue"), null);
  geste3.insertBefore(doc.getElementById("b-langue-poser"), null);
  geste3.insertBefore(doc.getElementById("b-langue-poser-raison"), null);
  geste4.insertBefore(doc.getElementById("v-etape-console"), null);
  section4.insertBefore(doc.getElementById("b-agent-poser"), null);
  section4.insertBefore(doc.getElementById("b-agent-poser-raison"), null);

  // 🔴 LE CHOIX VIT DANS L'ATTRIBUT, EXACTEMENT COMME DANS LE DOCUMENT : le
  //    banc le POSE ici parce qu'il n'a pas de HTML, mais la page le LIT par
  //    `langueDalleChoisie()`, qui est SA fonction, ⛔ pas la notre.
  // 🔴 D'ABORD LE BALISAGE — les quatre boutons de choix partent de l'etat que
  //    le DOCUMENT porte, ⛔ pas d'un etat que ce banc aurait choisi.
  for (const id of BOUTONS_DE_CHOIX) {
    if (ARIA_INITIAL[id] !== null && ARIA_INITIAL[id] !== undefined) {
      doc.getElementById(id).setAttribute("aria-pressed", ARIA_INITIAL[id]);
    }
  }
  // ⚠️ PUIS LE CHOIX DE **DALLE** DU CAS, parce que c'est lui que le cas mesure.
  doc.getElementById("b-dalle-fr").setAttribute("aria-pressed", choix === "fr" ? "true" : "false");
  doc.getElementById("b-dalle-en").setAttribute("aria-pressed", choix === "fr" ? "false" : "true");

  // 🔴 LES MINUTEURS DE LA PAGE SONT **DETACHES DE LA BOUCLE**, ET C'EST UNE
  //    MESURE : la page arme au chargement une sonde a 10 000 ms (« le module
  //    distant est-il arrive ? »). Treize contextes ⇒ node restait vivant DIX
  //    SECONDES apres le dernier cas, et le banc coutait 11,2 s au lieu de 1,3 s
  //    — une fois PAR MUTANT dans la campagne. ⛔ On ne les supprime PAS (ils
  //    doivent pouvoir se declencher : l'attente d'invite en est un) ; on leur
  //    retire le droit de TENIR la boucle ouverte. Ce qui la tient est le filet
  //    global de ce banc, ⛔ et lui seul.
  const detache = (f, d) => {
    const h = setTimeout(f, d);
    if (h && typeof h.unref === "function") { h.unref(); }
    return h;
  };
  const detacheI = (f, d) => {
    const h = setInterval(f, d);
    if (h && typeof h.unref === "function") { h.unref(); }
    return h;
  };
  const ctx = {
    document: doc,
    // 🔴 LES ECOUTEURS DE FENETRE SONT **GARDES** (`dn8-2`) : avec un
    //    `addEventListener()` vide, le `pagehide` qui rend le port — le filet
    //    de celui qui ferme l'onglet — etait INJOIGNABLE, donc MORT dans le
    //    seul instrument qui execute cette page (mesure V8 du 2026-09-11).
    // 🔴 LE CONTEXTE VIENT DU CAS : `etat-not-allowed` (⛔ pas un contexte
    //    securise, ou une adresse qui ne convient pas) et `etat-unsupported`
    //    (⛔ pas d'acces serie) se decident A L'EVALUATION, et rien ne pouvait
    //    les atteindre tant que ce contexte etait une constante.
    window: { isSecureContext: cx.securise !== false, ecouteurs: {},
              addEventListener(nom, f) {
                if (typeof f !== "function") { return; }
                (this.ecouteurs[nom] = this.ecouteurs[nom] || []).push(f);
              },
              setTimeout: detache, clearTimeout },
    location: { hostname: "127.0.0.1", protocol: "http:", host: "127.0.0.1:1", pathname: "/" },
    navigator: cx.serie === false ? {} : { serial: {} },
    // 🔴 LE PONT HTTP — ⛔ RESERVE AUX CAS `http`, ET C'EST UN CORRECTIF DE
    //    REVUE (2026-09-12). Avant, TOUT cas recevait le vrai `fetch` des que la
    //    gate passait `--base` : les cas anciens couraient alors contre le VRAI
    //    serveur, et une reponse d'etat arrivant EN PLEIN CAS etait une fenetre
    //    de course (mesure : `/api/etat` a 175,2 ms median sous les doubles,
    //    2,2 ms une fois `dependance_presente` doublee). ⇒ le vrai `fetch` ne
    //    part QUE pour les cas HTTP, et ⛔ pour personne d'autre.
    // ⚠️ ET IL **IMITE LE NAVIGATEUR** : un POST porte `Origin`. MESURE DU
    //    2026-09-11 : le `fetch` de node n'envoie AUCUN `Origin` (valeur recue :
    //    `null`), si bien que le refus `Origin` du produit ⛔ n'etait jamais joue
    //    comme la PAGE le declenche — `_origines_permises` faussee laissait la
    //    gate VERTE alors qu'un navigateur aurait ete refuse sur TOUS les verbes.
    // ⚠️ `new URL(u, BASE)` EST LE TRAVAIL DU NAVIGATEUR, ⛔ pas une
    //    complaisance : la page ecrit `fetch("api/agent/stop")`, une URL
    //    RELATIVE, et le `fetch` de node exige un absolu. L'ecrire ailleurs que
    //    dans le pont ferait mesurer le pont.
    fetch: (BASE && cas.http !== undefined)
      ? (u, o) => {
          traces.push(String(u));
          const opts = Object.assign({}, o || {});
          if (String(opts.method || "GET").toUpperCase() !== "GET") {
            opts.headers = Object.assign({}, opts.headers || {},
                                         { Origin: new URL(BASE).origin });
          }
          return globalThis.fetch(new URL(String(u), BASE), opts);
        }
      // ⚠️ LE SERVEUR **DE PAPIER** D'UN CAS DE BLOCS : il repond EN MEMOIRE et
      //    ⛔ ne parle a PERSONNE. C'est ce qui permet d'observer les blocs
      //    d'affichage dans leurs DEUX etats — la branche de SUCCES du
      //    chargement, que le `fetch` qui rejette ⛔ ne peut pas atteindre —
      //    sans donner a ces cas-la le vrai serveur, ⛔ donc sans course.
      : (cas.serveurDePapier
          ? serveurDePapier(cas.serveurDePapier, traces)
          : () => Promise.reject(new Error("hors banc"))),
    TextEncoder, TextDecoder,
    setTimeout: detache, clearTimeout, setInterval: detacheI, clearInterval,
    console, Promise, Date, JSON, Error
  };
  // ⛔ LE TEMOIN **REPLANTE** LA FAUTE, ⛔ IL NE DEBRANCHE PAS LA GARDE :
  //    l'element perd VRAIMENT sa capacite, exactement comme avant `dn7-4`.
  if (TEMOIN_DOM) { delete doc.getElementById("sortie").nextSibling; }

  // 🔴 ET C'EST **ICI** QUE L'ASSERTION SE JOUE : apres tous les montages, et
  //    AVANT que la moindre ligne de la page ne s'evalue. Jouee apres, elle
  //    constaterait un DOM sur lequel la page a DEJA lu ce qu'elle avait a
  //    lire — c'est-a-dire trop tard.
  const montes = [];
  for (const c of [maison, geste1, section4, entete, geste2, geste3, geste4]) {
    for (const e of c.enfants) { montes.push([c, e]); }
  }
  asserterDom(montes);

  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(src, ctx, { filename: "installeur/index.html<script>" });
  return { ctx, els, traces };
}

// ── LE PORT BIDON ──────────────────────────────────────────────────────────
//    `ouverture` decide si `open()` reussit ; `repond` decide ce que la carte
//    rend pour chaque ligne recue. Le compte d'octets ECRITS est la mesure de
//    « rien n'est ecrit », et ⛔ pas une declaration.
function jouer(src, cas) {
  const { ctx, els, traces } = faireContexte(src, cas);
  const ecrits = [];
  const suite = [];
  // 🔴 LES **OCTETS**, ⛔ PAS LES APPELS : trois surfaces de ce depot publient
  //    « zero octet », et compter des appels a `write()` ne mesure pas ca.
  let octets = 0;

  // 🔴 LES DEUX DELAIS DE LA PAGE SONT **REPOSES**, ET LE BANC ECHOUE FERME
  //    S'IL NE LES TROUVE PAS. Se rabattre en silence sur six secondes ferait
  //    payer a la campagne de mutants un plafond qu'elle a deja frole.
  if (typeof ctx.DELAI_INVITE !== "number" || typeof ctx.DELAI_REPONSE !== "number") {
    return Promise.reject(new Error("les delais de la page ne sont pas reglables"));
  }
  ctx.DELAI_INVITE = DELAI_PAGE;
  ctx.DELAI_REPONSE = DELAI_PAGE;

  // 🔴 LES CAS DE **VERBE** NE PASSENT PAS PAR LE GESTE DE LANGUE (`dn7-4`).
  //    Ils mesurent OU LE TRANSCRIPT SE TROUVE, et rien d'autre : c'est la
  //    seule propriete de `AC7.4.1` qu'une machine puisse tenir.
  if (cas.verbe !== undefined) { return jouerVerbe(ctx, els, cas); }

  // 🔴 LES CAS DE **PRECONDITION** NE PASSENT PAS NON PLUS PAR LE GESTE DE
  //    LANGUE (`dn7-6`). Ils mesurent ce que la page fait d'un ETAT DE MACHINE :
  //    quel temoin porte chaque etape, et quel geste se DESARME — avec quel
  //    motif. C'est la moitie d'`AC7.6.2` qu'une machine puisse tenir ; l'autre
  //    — un bouton REELLEMENT grise sous les yeux de quelqu'un — se ferme
  //    cote Windows, a l'œil.
  if (cas.etatMachine !== undefined) { return jouerPrecondition(ctx, els, cas); }

  // ── LES QUATRE CHEMINS NEUFS DE `dn8-2` ────────────────────────────────
  // 🔴 CHACUN ENTRE DANS UNE SURFACE QUE LA COUVERTURE V8 A RELEVEE **MORTE**
  //    le 2026-09-11 — ⛔ pas dans une surface qu'on suppose faible.
  if (cas.langues !== undefined) { return jouerLanguePage(ctx, els, cas); }
  if (cas.console !== undefined) { return jouerConsole(ctx, els, cas); }
  if (cas.verbes !== undefined) { return jouerVerbes(ctx, els, cas); }
  if (cas.http !== undefined) { return jouerHttp(ctx, els, cas, traces); }
  if (cas.blocs !== undefined) { return jouerBlocs(ctx, els, cas); }

  // 🔴 ON RELEVE LA **SUITE** DES ISSUES ANNONCEES, ⛔ PAS SEULEMENT LA
  //    DERNIERE. `blocMot` est l'unique fabrique par laquelle le geste annonce
  //    une issue : on l'enveloppe, on ⛔ ne la remplace pas.
  const vraiBloc = ctx.blocMot;
  ctx.blocMot = function (id, cle, sfx) { suite.push(cle); return vraiBloc(id, cle, sfx); };

  const port = {
    writable: {
      getWriter: () => ({
        write(o) {
          ecrits.push(Buffer.from(o).toString("utf8"));
          octets += (o && o.byteLength !== undefined) ? o.byteLength : 0;
          // ⛔ UN PORT QUI DISPARAIT **EN VOL** : la carte se debranche entre
          //    deux lignes, ou un autre programme reprend le port. C'est le seul
          //    chemin qui exerce le filet du geste.
          if (cas.rejetteAu !== undefined && ecrits.length === cas.rejetteAu) {
            return Promise.reject(new Error("The device has been lost."));
          }
          return Promise.resolve();
        },
        releaseLock() { port.verrouRendu++; }
      })
    },
    readable: { getReader: () => ({ read: () => new Promise(() => {}), cancel: () => Promise.resolve(), releaseLock() {} }) },
    open: () => (cas.ouverture === false
      ? Promise.reject(new Error("Failed to execute 'open' on 'SerialPort'"))
      : Promise.resolve()),
    close: () => Promise.resolve(),
    verrouRendu: 0
  };

  if (cas.serie === false) {
    // ⛔ PAS D'ACCES SERIE DU TOUT : la page doit le dire AVANT, et n'ecrire rien.
    delete ctx.navigator.serial;
  }
  if (cas.parSelecteur) {
    // Le port passe par le VRAI chemin d'ouverture de la page — celui que la
    // console livre par `dn7-2-2` — et ⛔ pas par une affectation directe.
    // ⚠️ Sans acces serie il n'y a RIEN a brancher : c'est tout l'objet du cas,
    //    et la page doit s'arreter AVANT d'avoir un port a demander.
    if (ctx.navigator.serial) {
      ctx.navigator.serial.requestPort = () => (cas.selecteur === false
        ? Promise.reject(new Error("No port selected"))
        : Promise.resolve(port));
    }
  } else {
    ctx.portConsole = port;
  }
  if (cas.reveler) {
    // 🔴 LA **POLARITE** DE `langueOffrir()`, LUE SUR LE VRAI BOUTON : la page
    //    revele son bloc d'installation quand l'etat de la machine est connu, et
    //    le geste doit s'armer AVEC lui. ⛔ On ne lit pas la fonction : on
    //    l'appelle par le chemin du produit et on relit `.disabled`.
    ctx.reveler();
  }
  if (cas.moduleAbsent) {
    ctx.reveler();
    ctx.moduleAbsent("cdn.delai");
  }
  // ⚠️ LA POLARITE SE RELEVE **ICI**, juste apres le geste qui la pose, ⛔ pas a
  //    la fin du cas : la page rearme et desarme ce bouton a chaque fois qu'elle
  //    apprend quelque chose de la machine, et l'echec de `api/etat` — normal sur
  //    un banc — repasserait par la apres coup. On mesure la POLARITE, ⛔ pas le
  //    dernier etat d'une page qui n'a pas de serveur.
  const poserDesarme = (els["b-langue-poser"] || {}).disabled;
  if (cas.selecteurEnVol) {
    // ⛔ UN SELECTEUR DEJA EN VOL : `consoleOuvrir()` rend `null` SANS RIEN
    //    DIRE. La page doit alors nommer ce qui s'est passe elle-meme — un clic
    //    qui n'ecrit rien ET n'affiche rien se lit comme une page cassee.
    ctx.consoleOuvertureEnVol = true;
  }

  // La carte repond PAR L'ENTONNOIR DE LECTURE DE LA PAGE (`consoleAjouter`),
  // ⛔ pas par un second chemin : c'est la ou l'attente est branchee.
  const vraiEcrire = ctx.consoleEcrire;
  ctx.consoleEcrire = function (l) {
    return vraiEcrire(l).then(() => {
      const r = cas.repond(l);
      if (r !== null && r !== undefined) { setTimeout(() => ctx.consoleAjouter(r), 5); }
      return null;
    });
  };

  // 🔴 LE CLIC EST **DISPATCHE SUR LE VRAI BOUTON** quand le cas le demande :
  //    c'est la seule facon de mesurer la liaison BOUTON ⇄ CODE. Poser
  //    l'attribut a la main prouverait le lecteur, ⛔ pas le gestionnaire.
  if (cas.cliqueDalle) { els[cas.cliqueDalle].clics.forEach((f) => f()); }
  const p = ctx.poserLangueDalle();
  // Le double clic : le SECOND appel doit etre IGNORE par la garde de la page.
  if (cas.doubleClic) { ctx.poserLangueDalle(); }
  return Promise.resolve(p)
    .then(() => new Promise(r => setTimeout(r, 80)))
    .then(() => ({
      etatLangue: (els["etat-langue"] || {}).textContent || "",
      etatConsole: (els["etat-console"] || {}).textContent || "",
      relais: (els["langue-relais"] || {}).textContent || "",
      relaisCache: (els["langue-relais"] || {}).hidden,
      classe: (els["etat-langue"] || {}).className || "",
      poserDesarme,
      ecrits, octets, suite, enVol: ctx.langueEnVol, verrouRendu: port.verrouRendu
    }));
}

// ── LE VERBE, ET LA PLACE DE SON VERDICT ───────────────────────────────────
// 🔴 CE QUE CE CHEMIN MESURE, ⛔ ET CE QU'IL NE MESURE PAS. Il dit OU se trouve
//    `#sortie` apres coup — sous le bouton clique, ou a sa place d'origine.
//    ⛔ Il ⛔ ne dit RIEN de ce que l'œil voit : ni defilement, ni rendu, ni
//    lisibilite. `AC7.4.3` se ferme A L'ŒIL DE L'OWNER, ⛔ pas ici.
function jouerVerbe(ctx, els, cas) {
  // ⚠️ LE FAIT DE **PAGE** SE PRODUIT AU CHARGEMENT, ⛔ on ne le simule pas :
  //    `rafraichirEtat()` part sur un `fetch` qui rejette (« hors banc »), et
  //    c'est SA branche `.catch` qui ecrit `sortie.pas-de-serveur` SANS ancre.
  const vide = {
    etatLangue: "", etatConsole: "", relais: "", relaisCache: true,
    classe: "", poserDesarme: undefined, ecrits: [], octets: 0, suite: [],
    enVol: false, verrouRendu: 0
  };
  // 🔴 ON RELEVE LA **SUITE** DES PLACES, ⛔ PAS SEULEMENT LA DERNIERE — meme
  //    raison que pour la suite des issues : une place JUSTE a la fin peut
  //    suivre un aller-retour a la maison que personne ne verrait.
  //    `montrerSortie` est ENVELOPPEE, ⛔ pas remplacee.
  const places = [];
  const vraiMontrer = ctx.montrerSortie;
  ctx.montrerSortie = function (ancre) {
    const r = vraiMontrer(ancre);
    places.push(placeDe(els["sortie"]));
    return r;
  };
  return new Promise((r) => setTimeout(r, 80)).then(() => {
    if (cas.verbe === null) {
      return Object.assign({}, vide, { place: placeDe(els["sortie"]), places });
    }
    // ⛔ LE `fetch` DU VERBE EST STUBBE **APRES** LE CHARGEMENT : avant, il
    //    ferait aussi repondre `api/etat`, et le fait de page ne se produirait
    //    jamais. Ici, SEUL `api/agent/<verbe>` repond.
    ctx.fetch = (url) => (String(url).indexOf("api/agent/") >= 0
      ? Promise.resolve({ json: () => Promise.resolve(cas.reponse) })
      : Promise.reject(new Error("hors banc")));
    // 🔴 UN **VRAI** CLIC, dispatche sur le bouton : poser la sortie a la main
    //    prouverait le lecteur, ⛔ pas le gestionnaire.
    els[cas.bouton].clics.forEach((f) => f());
    return new Promise((r) => setTimeout(r, 150)).then(
      () => Object.assign({}, vide, {
        place: placeDe(els["sortie"]), places
      }));
  });
}

// ── LES PRECONDITIONS, ET LE GESTE QUI SE DESARME ────────────── (dn7-6) ──
// 🔴 CE QUE CE CHEMIN MESURE, ⛔ ET CE QU'IL NE MESURE PAS. Il dit quel MOT et
//    quelle FORME chaque etape porte apres un etat de machine donne, et quel
//    geste est arme ou grise, AVEC SA RAISON. ⛔ Il ⛔ ne dit RIEN de ce que
//    l'œil voit : ni rendu, ni contraste, ni lisibilite. `AC7.6.1` se ferme A
//    L'ŒIL DE L'OWNER, ⛔ pas ici.
// ⚠️ LA FABRIQUE DE DESARMEMENT EST **ENVELOPPEE**, ⛔ JAMAIS REMPLACEE : la
//    remplacer ferait mesurer le banc lui-meme, et la page pourrait etre
//    cassee sans que rien ne bouge.
function jouerPrecondition(ctx, els, cas) {
  const vide = {
    etatLangue: "", etatConsole: "", relais: "", relaisCache: true,
    classe: "", poserDesarme: undefined, ecrits: [], octets: 0, suite: [],
    enVol: false, verrouRendu: 0
  };
  const armes = [];
  const vraiArmer = ctx.armerGeste;
  ctx.armerGeste = function (id, permis, cle) {
    const r = vraiArmer(id, permis, cle);
    armes.push(id + (permis ? " ARME" : " GRISE=" + cle));
    return r;
  };
  const TEMOINS = ["v-etape-arret", "v-etape-flash", "v-etape-langue",
                   "v-etape-console"];
  // 🔴 LE MOT **ET** LA FORME, DANS LA MEME MESURE — ⛔ pas l'un sans l'autre :
  //    un mot juste sous une forme perimee est exactement le defaut que la
  //    page se garde de commettre, et il serait invisible a qui ne mesure
  //    qu'une moitie.
  const forme = (e) => {
    const c = (e.className || "?").replace("val ", "");
    const t = e.textContent || "";
    const mot = t.includes("ready") ? "prete"
      : t.includes("BLOCKED") ? "bloquee"
        : t.includes("not testable") ? "non-testable"
          : t.includes("unknown") ? "inconnu" : "?";
    return c + ":" + mot;
  };
  const lire = () => TEMOINS.map((id) => forme(els[id] || {}));
  // 🔴 LA VISIBILITE DES DEUX BANDEAUX, MESUREE (`dn7-6`, correctif de revue).
  //    ⚠️ ELLE NE SE DEDUIT ⛔ PAS DE L'ARMEMENT : `#b-deps` vit DANS
  //       `#etat-deps`, donc le banc pouvait relever « b-deps ARME » sur un
  //       bouton que la page venait de RENDRE INVISIBLE. Et inverser
  //       `afficher("etat-lhm", …)` laissait HUIT gates vertes — le bandeau
  //       de LHM s'affichant sur une machine SAINE et se taisant sur une
  //       machine ou le pre-vol de l'agent REFUSERA.
  const bandeaux = () => ["etat-deps", "etat-lhm"].map(
    (id) => id + ((els[id] || {}).hidden === false ? " VU" : " CACHE"));
  // ⚠️ ON ATTEND LE CHARGEMENT : `rafraichirEtat()` part sur un `fetch` qui
  //    rejette (« hors banc »), et c'est SA branche `.catch` qui pose l'etat
  //    d'IGNORANCE. Le cas `serveur-muet` mesure EXACTEMENT ca, ⛔ il ne le
  //    simule pas.
  return new Promise((r) => setTimeout(r, 80)).then(() => {
    if (cas.etatMachine === null) {
      return Object.assign({}, vide, { temoins: lire(), armes,
                                       bandeaux: bandeaux(),
                                       blocs: lireBlocs(els) });
    }
    // ⛔ CE QUE LE BANC REMET, ET IL LE DIT : sans serveur, le chargement a
    //    deja refuse la charge locale (`charge/manifest.json` ne repond pas) —
    //    un fait du BANC, ⛔ pas de la page. Le laisser en place ferait juger
    //    l'etape 2 sur une panne que le cas ne decrit pas. ⇒ on rend a la page
    //    l'etat ou son serveur repond, PUIS on lui donne l'etat de machine du
    //    cas, et on ne releve que ce qui suit.
    ctx.chargeRefusee = false;
    armes.length = 0;
    ctx.appliquerFlash(cas.etatMachine);
    return new Promise((r) => setTimeout(r, 40)).then(
      () => Object.assign({}, vide, { temoins: lire(), armes,
                                      bandeaux: bandeaux(),
                                      blocs: lireBlocs(els) }));
  });
}

// ── LA LANGUE DE LA **PAGE** — ⛔ PAS CELLE DE LA DALLE ────── (dn8-2) ──
// 🔴 DEUX MECANISMES DISJOINTS, ET CE BANC N'EN EXERCAIT QU'UN. Mesure V8 du
//    2026-09-11 : `poserLangue()` (l.424 du `<script>`) et SES DEUX
//    GESTIONNAIRES DE CLIC (l.439, l.442) n'etaient JAMAIS entres — c'est-a-dire
//    la surface meme dont la LISIBILITE fait le sujet d'`AC8.2.6`.
// ⛔ CE QUE CE CHEMIN NE MESURE **PAS**, ET IL FAUT L'ECRIRE : que l'option
//    retenue se DISTINGUE a l'œil. Il n'y a ⛔ aucun rendu ici, et il n'y en
//    aura pas. Ce verdict-la se prend sur la page SERVIE, cote Windows, A
//    L'ŒIL DE L'OWNER — porteur `dn8-3`.
function jouerLanguePage(ctx, els, cas) {
  // 🔴 RELU **SUR LES VRAIS BOUTONS**, ⛔ pas sur une variable du banc : ce
  //    qu'on mesure est la liaison BOUTON ⇄ CODE, et poser l'attribut a la
  //    main prouverait le lecteur.
  const lu = () => {
    const e = els["b-langue-en"] || {};
    const f = els["b-langue-fr"] || {};
    return "en=" + (e.getAttribute ? e.getAttribute("aria-pressed") : "⛔ ABSENT")
      + " fr=" + (f.getAttribute ? f.getAttribute("aria-pressed") : "⛔ ABSENT")
      + " doc=" + ctx.document.documentElement.getAttribute("data-langue");
  };
  const langues = [];
  return new Promise((r) => setTimeout(r, 60)).then(() => {
    langues.push("depart " + lu());
    for (const id of cas.langues) {
      // ⛔ UN **VRAI** CLIC, dispatche sur le bouton du document.
      (els[id].clics || []).forEach((f) => f());
      langues.push(id + " ⇒ " + lu());
    }
    return Object.assign({}, resultatVide(), { langues });
  });
}

// ── LA CONSOLE SERIE — OUVERTURE, LECTURE, FIN DE LIEN, FERMETURE ─────────
// 🔴 SIX FONCTIONS MORTES SUR CE SEUL BLOC (mesure V8 du 2026-09-11 : l.1296,
//    1306, 1308, 1313 `consoleFinDeLien`, 1374 `consoleFermer`, 1417 le
//    `pagehide`). Le port etait bien branche pour le geste de LANGUE, ⛔ jamais
//    ouvert par le geste de CONSOLE — celui que `dn7-2-2` a livre.
// ⚠️ LE LECTEUR EST UN VRAI FLUX, ⛔ pas un tableau : son `read()` reste EN VOL
//    tant que la carte n'ecrit rien, et c'est `cancel()` qui le termine. Un
//    lecteur qui rendrait `done` de lui-meme ferait jouer la fin de lien a
//    chaque fermeture, et la distinction — voulue par la page — disparaitrait.
function jouerConsole(ctx, els, cas) {
  const d = cas.console;
  const lignes = d.lignes || [];
  let i = 0;
  let attente = null;
  // 🔴 LE PORT MODELISE SES **VERROUS** (dn8-2, correctif de revue du
  //    2026-09-12) — ⛔ ET CE N'EST PAS UN RAFFINEMENT : un flux encore
  //    verrouille fait partir `close()` EN REJET, c'est la regle du navigateur,
  //    et c'est la SEULE chose qui rende observable une fermeture jouee dans le
  //    MAUVAIS ORDRE. MESURE : sans ce modele, fermer le port AVANT d'annuler et
  //    de relacher le lecteur laissait ce banc VERT — le port restait tenu EN
  //    SILENCE, ce que la matrice de `dn7-2-2` interdit mot pour mot.
  const port = {
    ferme: 0, tentees: 0, lecteurVerrouille: false, ecrivainVerrouille: false,
    readable: {
      getReader: () => {
        // ⛔ UN FLUX N'ADMET QU'UN SEUL LECTEUR — la regle du navigateur, jouee.
        if (port.lecteurVerrouille) {
          throw new TypeError("Failed to execute 'getReader' on 'ReadableStream'"
            + " : ReadableStream is locked");
        }
        port.lecteurVerrouille = true;
        return {
          read() {
            if (i < lignes.length) {
              return Promise.resolve({ value: new TextEncoder().encode(lignes[i++]),
                                       done: false });
            }
            if (d.finDeLien) {
              return Promise.resolve({ value: undefined, done: true });
            }
            if (d.lecteurRejette) {
              return Promise.reject(new Error("The device has been lost."));
            }
            return new Promise((r) => { attente = r; });
          },
          cancel() {
            if (attente) { attente({ value: undefined, done: true }); attente = null; }
            return Promise.resolve();
          },
          releaseLock() { port.lecteurVerrouille = false; }
        };
      }
    },
    writable: {
      getWriter: () => {
        port.ecrivainVerrouille = true;
        return { write: () => Promise.resolve(),
                 releaseLock() { port.ecrivainVerrouille = false; } };
      }
    },
    open: () => (d.ouverture === false
      ? Promise.reject(new Error("Failed to execute 'open' on 'SerialPort'"))
      : Promise.resolve()),
    close: () => {
      port.tentees++;
      if (port.lecteurVerrouille || port.ecrivainVerrouille) {
        return Promise.reject(new TypeError("Failed to execute 'close' on "
          + "'SerialPort': Cannot cancel a locked stream"));
      }
      // ⛔ UNE FERMETURE PEUT **ECHOUER** SANS QU'AUCUN VERROU NE SOIT TENU : la
      //    carte a disparu entre-temps. La page doit alors dire « ⛔ PAS rendu »
      //    et GARDER ses references — annoncer une restitution qui n'a pas eu
      //    lieu serait publier une ignorance comme un constat.
      if (d.fermetureEchoue) {
        return Promise.reject(new Error("NetworkError: Failed to close the "
          + "serial port."));
      }
      port.ferme++;
      return Promise.resolve();
    }
  };
  if (ctx.navigator.serial) {
    ctx.navigator.serial.requestPort = () => Promise.resolve(port);
  }
  // 🔴 QUATRE FAITS, ⛔ PAS TROIS : les deux boutons, le port REELLEMENT rendu
  //    (⛔ pas seulement « close appele » — d'ou `ferme/tentees`), et si la page
  //    a GARDE ses references. Les quatre ensemble disent si le port est revenu.
  const etat = () => {
    const o = els["b-console"] || {};
    const f = els["b-console-fermer"] || {};
    return ["b-console " + (o.disabled ? "GRISE" : "ARME"),
            "b-console-fermer " + (f.disabled ? "GRISE" : "ARME"),
            "port ferme=" + port.ferme + "/" + port.tentees,
            (ctx.portConsole === null && ctx.lecteurConsole === null)
              ? "references RENDUES" : "references GARDEES"];
  };
  return new Promise((r) => setTimeout(r, 30)).then(() => {
    (els["b-console"].clics || []).forEach((f) => f());
    return new Promise((r) => setTimeout(r, 45));
  }).then(() => {
    if (d.fermerPar === "bouton") {
      (els["b-console-fermer"].clics || []).forEach((f) => f());
    } else if (d.fermerPar === "pagehide") {
      // ⛔ PAR L'ECOUTEUR QUE LA PAGE A POSE, ⛔ pas en appelant sa fonction :
      //    ce qu'on mesure est que le filet SOIT BRANCHE.
      const h = (ctx.window.ecouteurs || {}).pagehide || [];
      h.forEach((f) => f());
    }
    return new Promise((r) => setTimeout(r, 45));
  }).then(() => Object.assign({}, resultatVide(), {
    consoleTexte: (els["console-sortie"] || {}).textContent || "",
    etatConsole: (els["etat-console"] || {}).textContent || "",
    gestes: etat()
  }));
}

// ── LES VERBES QU'AUCUN CLIC N'ATTEIGNAIT ───────────────────── (dn8-2) ──
// 🔴 TROIS GESTIONNAIRES MORTS (l.821 `b-retirer`, l.826 `b-deps`, l.829
//    `b-agent-poser`) ET LE `.catch` DE `jouer` (l.810). Un seul bouton sur
//    quatre etait clique, et c'est la SUITE DES PLACES du transcript qui le
//    disait — ⛔ pas une declaration.
// ⚠️ LE `fetch` EST STUBBE ICI, ET C'EST VOULU : ce chemin mesure la LIAISON
//    bouton ⇄ verbe et la place du verdict, ⛔ pas le trajet HTTP. Le trajet
//    reel a ses propres cas, et ils ⛔ ne se jouent que derriere `--base`.
const REPONSE_DE_PAPIER = {
  commande: "dn_agent_tour.ps1 <verbe>", sortie: "sortie de papier",
  rc: 0, rc_pose_par: "l'outil", verdict: "fait"
};

function jouerVerbes(ctx, els, cas) {
  const d = cas.verbes;
  const places = [];
  const routes = [];
  const armesVerbes = [];
  let avant = [], apres = [];
  const vraiMontrer = ctx.montrerSortie;
  ctx.montrerSortie = function (ancre) {
    const r = vraiMontrer(ancre);
    places.push(placeDe(els["sortie"]));
    return r;
  };
  const QUATRE = ["b-stop", "b-retirer", "b-deps", "b-agent-poser"];
  const lireBoutons = () => QUATRE.map(
    (id) => id + ((els[id] || {}).disabled ? " GRISE" : " ARME"));
  let etatCourant = null;
  let rejette = false;
  // ⚠️ `api/etat` REPOND TOUJOURS, et c'est voulu : c'est par lui que la PAGE
  //    arme ses boutons. Un verbe qui echoue ⛔ ne doit pas se confondre avec un
  //    etat perdu — ce sont deux faits, et deux branches differentes.
  ctx.fetch = (url) => {
    const u = String(url);
    if (u.indexOf("api/etat") >= 0) {
      // ⚠️ TANT QU'AUCUN ETAT N'EST ARME, IL **REJETTE** — ⛔ il ne rend pas
      //    `null`. C'est l'etat REEL du chargement d'un banc sans serveur (la
      //    branche `.catch`, qui grise les quatre boutons) ; rendre `null` ferait
      //    lever la page dans une branche que ⛔ personne ne decrit.
      if (etatCourant === null) {
        routes.push(u + " ⇒ REJET");
        return Promise.reject(new Error("hors banc"));
      }
      routes.push(u);
      return Promise.resolve({ json: () => Promise.resolve(etatCourant) });
    }
    if (rejette) {
      routes.push(u + " ⇒ REJET");
      return Promise.reject(new Error("hors banc"));
    }
    routes.push(u);
    return Promise.resolve({ json: () => Promise.resolve(REPONSE_DE_PAPIER) });
  };
  // 🔴 LA PAGE S'ARME **PAR SES PROPRES FONCTIONS** — `rafraichirEtat()` puis
  //    `appliquerFlash`, exactement la chaine de son chargement. Poser
  //    `disabled = false` a la main prouverait le banc, ⛔ pas la page.
  const armer = (etat) => {
    etatCourant = etat;
    return ctx.rafraichirEtat().then(ctx.appliquerFlash)
      .then(() => new Promise((r) => setTimeout(r, 20)));
  };
  // ⛔ ET ⛔ ON NE CLIQUE **JAMAIS** UN BOUTON DESARME. MESURE DU 2026-09-11 : le
  //    chargement sans serveur grise `b-deps` et `b-agent-poser` AVANT le premier
  //    clic, et les trois clics de la 1re redaction tombaient donc sur des
  //    boutons MORTS. Un clic sur un bouton grise ne mesure rien — et il le
  //    mesure en VERT.
  const cliquer = (id) => {
    const b = els[id] || {};
    if (b.disabled) {
      armesVerbes.push(id + " ⛔ DESARME — ⛔ PAS clique");
      return new Promise((r) => setTimeout(r, 5));
    }
    armesVerbes.push(id + " ARME");
    (b.clics || []).forEach((f) => f());
    return new Promise((r) => setTimeout(r, 55));
  };
  return new Promise((r) => setTimeout(r, 50))
    .then(() => armer(d.etatAvecManque))
    .then(() => cliquer("b-deps"))
    .then(() => armer(d.etatSain))
    .then(() => cliquer("b-agent-poser"))
    .then(() => cliquer("b-retirer"))
    .then(() => {
      // 🔴 L'ETAT D'AVANT EST RELEVE **JUSTE AVANT** LE VERBE QUI ECHOUE : c'est
      //    celui-la que le `.catch` de `jouer` doit rendre, ⛔ pas « tout arme ».
      avant = lireBoutons();
      rejette = true;
      return cliquer("b-retirer");
    })
    .then(() => {
      apres = lireBoutons();
      return Object.assign({}, resultatVide(), {
        places, routes, armesVerbes, boutonsAvant: avant, boutonsApres: apres,
        place: placeDe(els["sortie"])
      });
    });
}

// ── LE TRAJET HTTP REEL — LE PRODUIT EST **APPELE** ────────── (dn8-2) ──
// 🔴 CE QUE CE CHEMIN FERME. `verif_installeur_dn71.py` appelle le produit
//    **PAR IMPORT** : une INVERSION entre `ROUTE_DEPENDANCES` et le prefixe
//    `/api/agent/` dans `do_POST` passait donc VERTE. Ici la requete part pour
//    de vrai, elle traverse `_garde()`, `do_POST` et le routage, et le cas
//    NOMME LA ROUTE ATTEINTE — ⛔ pas seulement un `200`.
// ⛔ LE SERVEUR EST LIE PAR LA **GATE**, ⛔ jamais par ce banc : c'est ce qui
//    garde les deux proprietes a la fois — le banc reste jouable SEUL, et le
//    trajet n'existe que la ou quelqu'un a lie un port QU'IL FERME.
// ⚠️ ET LA GARDE `Host` ⛔ N'EST PAS JOIGNABLE PAR `fetch` : MESURE DU
//    2026-09-11 — node ACCEPTE de poser `Origin`, et IGNORE EN SILENCE un
//    `Host` fourni. ⇒ ce seul refus passe par `node:http`, et c'est DECLARE :
//    il mesure LE SERVEUR, ⛔ pas la page.
function requeteBrute(chemin, entetes, methode) {
  return new Promise((resoudre) => {
    const u = new URL(chemin, BASE);
    const req = http.request(
      { host: u.hostname, port: u.port, path: u.pathname,
        method: methode || "POST", headers: entetes || {} },
      (res) => {
        let b = "";
        res.on("data", (c) => { b += c; });
        res.on("end", () => resoudre({ code: res.statusCode, corps: b }));
      });
    req.on("error", (e) => resoudre({ code: -1, corps: String(e.message) }));
    req.end();
  });
}

function jouerHttp(ctx, els, cas, traces) {
  const d = cas.http;
  const codes = [];
  return new Promise((r) => setTimeout(r, d.attente || 140)).then(() => {
    if (!d.geste) { return null; }
    return d.geste(ctx, els, codes);
  }).then(() => new Promise((r) => setTimeout(r, d.repos || 140))).then(() => {
    const champ = (id) => (els[id] || {}).textContent || "";
    return Object.assign({}, resultatVide(), {
      routes: traces.slice(),
      codes,
      sortieTexte: champ("sortie"),
      champs: (d.champs || []).map((id) => id + "=" + champ(id).trim())
    });
  });
}

// L'ETAT DE MACHINE SAIN — la forme que `etat_machine()` rend REELLEMENT.
// ⚠️ Chaque cas en DERIVE le sien : recopier l'objet entier a chaque fois
//    ferait diverger les cas les uns des autres, et la difference — la seule
//    chose que le cas mesure — cesserait d'etre lisible.
const ETAT_SAIN = {
  windows: true, pilote: "C:\\dn\\tools\\dn_agent_tour.ps1",
  tache_presente: false, tache_runlevel: "Limited", tache_nom: "DeskNode agent",
  python_version: "3.13.0", psutil: true, pyserial: true,
  manquantes: [], non_testables: [], lhm: true, arbre_parent: true,
  port_serie: "COM3", port_nom: "", port_motif: "", charge: { complete: true }
};
const avec = (o) => Object.assign({}, ETAT_SAIN, o);
const QUATRE_PRETES = ["etat-prete:prete", "etat-prete:prete",
                       "etat-prete:prete", "etat-prete:prete"];

// ── LES BLOCS D'AFFICHAGE CONDITIONNELS, JUGES DANS LEURS DEUX ETATS ──────
// 🔴 POURQUOI CE VECTEUR EXISTE, ET C'EST DEMONTRE : l'inversion de
//    `afficher("etat-hors-windows", e.windows === false)` — la faute que le
//    ledger DEMONTRAIT le 2026-09-09 — laissait cette gate a `54 OK / 0 KO`.
//    Cinq autres inversions aussi. EXECUTER une ligne ⛔ ne prouve rien de ce
//    qu'elle affiche ; seul un JUGEMENT sur son resultat le fait.
// ⚠️ IL SE COMPARE **EN ENTIER** : un booleen par bloc ne dirait pas LEQUEL a
//    bouge, et onze booleens separes laisseraient passer celui qu'on n'aurait
//    pas pense a regarder.
const BLOCS = ["etat-hors-windows", "etat-orphelin", "etat-port-tenu",
               "etat-cdn", "etat-inactif", "etat-not-allowed",
               "etat-unsupported", "bloc-installer", "etat-charge",
               "etat-deps", "etat-lhm"];
const lireBlocs = (els) => BLOCS.map(
  (id) => id + ((els[id] || {}).hidden === false ? " VU" : " CACHE"));

// Ce que le serveur DE PAPIER rend pour le manifeste — ⛔ aucune charge n'est lue.
const MANIFESTE_DE_PAPIER = {
  name: "DeskNode", version: "papier-dn8-2",
  builds: [{ chipFamily: "ESP32-S3",
             parts: [{ path: "bootloader.bin", offset: 0 }] }]
};

// 🔴 UN SERVEUR **DE PAPIER**, ⛔ PAS UN VRAI — ET C'EST CE QUI OUVRE LA BRANCHE
//    DE SUCCES DU CHARGEMENT. Avec un `fetch` qui rejette toujours, la page ne
//    traverse QUE ses `.catch` : la moitie des blocs conditionnels ⛔ n'est alors
//    JAMAIS atteinte. Ce double repond EN MEMOIRE, aux deux seules adresses que
//    le chargement demande, et il ⛔ ne parle a PERSONNE — ⛔ donc aucune fenetre
//    de course avec le vrai serveur, qui reste reserve aux cas `http`.
function serveurDePapier(d, traces) {
  return (u) => {
    const s = String(u);
    traces.push(s);
    if (s.indexOf("charge/manifest.json") >= 0 && d.manifeste) {
      return Promise.resolve({ ok: true, status: 200,
                               json: () => Promise.resolve(d.manifeste) });
    }
    if (s.indexOf("api/etat") >= 0 && d.etat) {
      return Promise.resolve({ ok: true, status: 200,
                               json: () => Promise.resolve(d.etat) });
    }
    return Promise.reject(new Error("hors banc — le serveur de papier ne sert "
      + "pas " + s));
  };
}

function jouerBlocs(ctx, els, cas) {
  const d = cas.blocs;
  // ⚠️ LE CHARGEMENT EST CELUI DE LA PAGE, ⛔ PAS UNE SIMULATION : le script a
  //    lance lui-meme `afficherManifeste()` puis `rafraichirEtat().then(
  //    appliquerFlash)` a l'evaluation, et le serveur de papier lui a repondu.
  //    On attend, puis on joue les deux gestes qui masquent le bloc
  //    d'installation AILLEURS que dans `reveler()` — les trois sites qui
  //    decident de cette visibilite sont ainsi tous traverses.
  return new Promise((r) => setTimeout(r, 40)).then(() => {
    if (d.moduleAbsent) { ctx.moduleAbsent("cdn.delai"); }
    if (d.chargeInutilisable) { ctx.chargeInutilisable("charge.incomplete-muette"); }
    return new Promise((r) => setTimeout(r, 25));
  }).then(() => Object.assign({}, resultatVide(), { blocs: lireBlocs(els) }));
}

// 🔴 LA ROUTE **ATTEINTE**, LUE DANS CE QUE LA REPONSE PORTE (correctif de revue
//    du 2026-09-12) — ⛔ PAS LE CHEMIN DEMANDE. Un cas qui etiquette le chemin
//    demande ⛔ ne peut PAS voir une inversion de routage : sous l'echange de
//    `/api/dependances` et du prefixe `/api/agent/` dans `do_POST`, la ligne
//    « stop ⇒ 200 rc=0 » ⛔ ne bouge pas d'un caractere. Ce qui bouge, c'est la
//    COMMANDE que le serveur dit avoir jouee, et QUI a pose le code.
function routeAtteinte(corps) {
  let d = null;
  try { d = JSON.parse(corps); } catch (e) { return "⛔ corps NON JSON"; }
  const cmd = String(d.commande || "");
  const qui = String(d.rc_pose_par || "?");
  let route;
  if (cmd.indexOf("pip install") >= 0) { route = "dependances"; }
  else {
    const m = /-File\s+\S+\s+(\S+)/.exec(cmd);
    route = m ? "verbe " + m[1]
              : (cmd ? "⛔ commande inconnue" : "aucune commande");
  }
  return "atteint=" + route + " (" + qui + ")";
}

// ── LES NEUF LIGNES DE LA MATRICE, PLUS LES TROIS CHEMINS NOMMES ───────────
// ⚠️ CHAQUE CAS PORTE LE NOM DE SA LIGNE DANS LE DOSSIER, ⛔ pas un numero :
//    un numero se perime au premier reordonnancement.
const CAS = [
  {
    nom: "defaut-structurel",
    attendPort: PORT_TENU,
    quoi: "choix = anglais ⇒ ⛔ AUCUN octet n'est ecrit",
    choix: "en", repond: () => null,
    attendLangue: "Nothing to do", ecritures: 0
  },
  {
    nom: "pose-nominale",
    attendPort: PORT_TENU,
    quoi: "choix = francais ⇒ POSEE, et seulement apres relecture",
    choix: "fr",
    repond: (l) => (l === "" ? R_INVITE : (l === "langue fr" ? R_SUCCES : R_LUE_FR)),
    attendLangue: "carries this language now", ecritures: 3
  },
  {
    nom: "deja-en-francais",
    attendPort: PORT_TENU,
    quoi: "la carte rend « rien a faire » ⇒ POSEE, ⛔ pas une ecriture",
    choix: "fr",
    repond: (l) => (l === "" ? R_INVITE : (l === "langue fr" ? R_BRUIT + R_NOOP : R_LUE_FR)),
    attendLangue: "carries this language now", attendRelais: "rien a faire", ecritures: 3
  },
  {
    nom: "refus-de-la-carte",
    attendPort: PORT_TENU,
    quoi: "la carte REFUSE ⇒ REFUSEE, texte relaye TEL QUEL",
    choix: "fr",
    repond: (l) => (l === "" ? R_INVITE : R_REFUS),
    attendLangue: "REFUSED", attendRelais: "n'est pas une langue connue", ecritures: 2
  },
  {
    nom: "pas-d-invite",
    attendPort: PORT_TENU,
    quoi: "la carte ne rend pas son invite ⇒ PAS-D-INVITE, ⛔ pas « refusee »",
    choix: "fr", repond: () => null,
    attendLangue: "does not give its prompt", ecritures: 1
  },
  {
    nom: "sans-reponse",
    attendPort: PORT_TENU,
    quoi: "invite obtenue puis silence ⇒ SANS REPONSE, ⛔ rien de pose",
    choix: "fr",
    repond: (l) => (l === "" ? R_INVITE : null),
    attendLangue: "No usable answer", ecritures: 2
  },
  {
    nom: "relecture-sans-le-code",
    attendPort: PORT_TENU,
    quoi: "la relecture ne porte PAS le code ⇒ REFUSEE, ⛔ pas POSEE",
    choix: "fr",
    repond: (l) => (l === "" ? R_INVITE : (l === "langue fr" ? R_SUCCES : R_LUE_EN)),
    attendLangue: "REFUSED", ecritures: 3
  },
  // ── LES TROIS LIGNES QUE RIEN NE COUVRAIT ────────────────────────────────
  // 🔴 ATTENTE AMENDEE ET DATEE LE 2026-09-10 (`dn7-4`) — ⛔ LA VALEUR
  //    D'AVANT EST NOMMEE : ces TROIS cas attendaient ~~« could not be taken »~~,
  //    c'est-a-dire `langue.port-indisponible`, la SUPPOSITION. C'etait le
  //    DEFAUT lui-meme, ecrit dans l'instrument : la console NOMMAIT deja le
  //    fait exact dans le geste 4 pendant que le geste 3 affichait « le plus
  //    souvent, un selecteur est deja ouvert ». ⇒ l'attente porte desormais LE
  //    FAIT, et c'est CE BANC qui a vu les trois cas basculer.
  //    ⚠️ `selecteur-deja-en-vol`, lui, garde « could not be taken » : c'est le
  //       SEUL cas ou cette phrase est VRAIE, et il est CONSERVE.
  {
    nom: "port-tenu-par-l-agent",
    attendPort: PORT_LIBRE,
    quoi: "l'ouverture est REFUSEE ⇒ « port refuse », ⛔ jamais « aucune carte »",
    choix: "fr", parSelecteur: true, ouverture: false, repond: () => null,
    attendConsole: "port was refused",
    // 🔴 LA **QUEUE** DU TEXTE, ⛔ PAS SON EN-TETE : `console.port-refuse` FINIT
    //    sur « Measured reason : », et le motif arrive EN SUFFIXE. Attendre
    //    l'en-tete laissait passer un label VIDE — sur le cas du DEUXIEME
    //    LANCEMENT ORDINAIRE, celui ou l'agent tient le port.
    attendLangue: "Failed to execute 'open' on 'SerialPort'", ecritures: 0
  },
  {
    nom: "double-clic",
    attendPort: PORT_TENU,
    quoi: "le geste rejoue EN VOL est IGNORE ⇒ une seule suite d'ordres",
    choix: "fr", doubleClic: true,
    repond: (l) => (l === "" ? R_INVITE : (l === "langue fr" ? R_SUCCES : R_LUE_FR)),
    attendLangue: "carries this language now", ecritures: 3
  },
  {
    nom: "pas-d-acces-serie",
    attendPort: PORT_LIBRE,
    quoi: "⛔ pas de Web Serial ⇒ la page le DIT, et n'ecrit rien",
    choix: "fr", parSelecteur: true, serie: false, repond: () => null,
    attendConsole: "does not expose serial port access",
    attendLangue: "does not expose serial port access",
    // ⛔ CE QUI DISTINGUE LES DEUX BLOCS : seul celui de la LANGUE dit ce qu'il
    //    advient du port. Sans cette exclusion, le cas passait avec les deux
    //    contenus ECHANGES, puisqu'il attendait la meme chaine des deux cotes.
    attendConsoleSans: PORT_LIBRE, ecritures: 0
  },
  // ── LES TROIS CHEMINS QUE LA REVUE A NOMMES ──────────────────────────────
  {
    // 🔴 LE CHEMIN POST-FLASH ORDINAIRE : le port n'est PAS deja ouvert, il
    //    s'obtient PAR LE SELECTEUR, et la pose va jusqu'au bout. MESURE : sans
    //    ce cas, rendre `consoleOuvrir()` a nouveau bloquante jusqu'a la mort du
    //    lien laissait TOUTES les gates vertes pendant que le geste s'arretait a
    //    « ⏳ reveil de la console… » sans ecrire un octet.
    nom: "pose-par-le-selecteur",
    attendPort: PORT_TENU,
    quoi: "port obtenu PAR LE SELECTEUR puis pose complete ⇒ POSEE",
    choix: "fr", parSelecteur: true,
    repond: (l) => (l === "" ? R_INVITE : (l === "langue fr" ? R_SUCCES : R_LUE_FR)),
    attendLangue: "carries this language now", ecritures: 3
  },
  {
    // 🔴 LA CINQUIEME ISSUE : la dalle A change, et elle ⛔ ne gardera PAS ce
    //    changement. ⛔ Ni « refusee » (faux : elle a change), ⛔ ni « posee »
    //    (faux : ca ne survivra pas). Et la relecture ⛔ n'a PAS lieu — elle
    //    rendrait le code choisi que l'ecriture ait reussi ou non.
    nom: "nvs-refusee",
    attendPort: PORT_TENU,
    quoi: "ecriture NVS refusee ⇒ POSEE A CHAUD mais ⛔ NON PERSISTEE",
    choix: "fr",
    repond: (l) => (l === "" ? R_INVITE : R_NVS),
    attendLangue: "will NOT keep it", attendRelais: "ECRITURE NVS REFUSEE", ecritures: 2
  },
  {
    // ⛔ LE SELECTEUR EST **ANNULE** par le lecteur : le navigateur rejette sur
    //    « No port selected ». Ce chemin etait SUPPORTE par le port bidon et
    //    ⛔ regle par AUCUN cas — un chemin qu'on sait jouer et qu'on ne joue
    //    pas est un chemin garde par rien.
    nom: "selecteur-annule",
    attendPort: PORT_LIBRE,
    quoi: "le selecteur est ANNULE ⇒ la page le DIT, et n'ecrit rien",
    choix: "fr", parSelecteur: true, selecteur: false, repond: () => null,
    attendConsole: "No port selected",
    attendLangue: "picker was closed without selecting", ecritures: 0
  },
  {
    // 🔴 LA LIAISON **BOUTON ⇄ CODE**, MESUREE PAR UN VRAI CLIC. Le choix part
    //    du gestionnaire du produit, ⛔ pas d'un attribut pose a la main : sans
    //    ce cas, echanger les deux gestionnaires laissait tout vert.
    nom: "clic-reel-sur-francais",
    attendPort: PORT_TENU,
    quoi: "un VRAI clic sur « dalle en francais » ⇒ `langue fr` part",
    choix: "en", cliqueDalle: "b-dalle-fr",
    repond: (l) => (l === "" ? R_INVITE : (l === "langue fr" ? R_SUCCES : R_LUE_FR)),
    attendLangue: "carries this language now", attendEcrit: "langue fr", ecritures: 3
  },
  {
    // 🔴 LA **POLARITE** DE `langueOffrir()` : le bloc de flash est revele ⇒ le
    //    geste s'ARME. Inverser la condition laissait toutes les gates vertes.
    nom: "flash-revele-arme-le-geste",
    attendPort: PORT_TENU,
    quoi: "le bloc de flash est REVELE ⇒ le geste est ARME",
    choix: "fr", reveler: true,
    repond: (l) => (l === "" ? R_INVITE : (l === "langue fr" ? R_SUCCES : R_LUE_FR)),
    attendLangue: "carries this language now", attendDesarme: false, ecritures: 3
  },
  {
    // 🔴 ET L'AUTRE SENS : le module distant ne vient pas ⇒ le bloc est masque
    //    et le geste se DESARME. Un seul des deux sens ne prouve pas la polarite.
    nom: "module-absent-desarme-le-geste",
    attendPort: PORT_TENU,
    quoi: "le module distant manque ⇒ le geste est DESARME",
    choix: "en", reveler: true, moduleAbsent: true, repond: () => null,
    attendLangue: "Nothing to do", attendDesarme: true, ecritures: 0
  },
  {
    // 🔴 LE FILET : une ecriture qui REJETTE EN VOL. Sans lui, `langueEnVol`
    //    resterait VRAI et le bouton serait MORT jusqu'au rechargement.
    nom: "ecriture-qui-rejette-en-vol",
    attendPort: PORT_TENU,
    quoi: "`write()` rejette en vol ⇒ IGNORANCE publiee, et le geste est RENDU",
    choix: "fr", rejetteAu: 2,
    repond: (l) => (l === "" ? R_INVITE : R_SUCCES),
    attendLangue: "No usable answer", ecritures: 2
  },
  {
    // ⛔ LE SELECTEUR EST **DEJA EN VOL** : `consoleOuvrir()` rend `null` sans
    //    rien dire, et la console n'a rien annonce. La page doit nommer ce qui
    //    s'est passe elle-meme — sinon le clic n'ecrit rien ET n'affiche rien.
    nom: "selecteur-deja-en-vol",
    attendPort: PORT_LIBRE,
    quoi: "un selecteur est deja ouvert ⇒ la page NOMME le fait, ⛔ pas de silence",
    choix: "fr", parSelecteur: true, selecteurEnVol: true, repond: () => null,
    attendLangue: "could not be taken", ecritures: 0
  },
  // ── LES DEUX CAS DE **PLACE**, AJOUTES LE 2026-09-10 (`dn7-4`) ───────────
  {
    // 🔴 UN FAIT DE **PAGE** N'APPARTIENT A AUCUN BOUTON. `rafraichirEtat()`
    //    part au chargement, son `fetch` rejette, et le transcript doit revenir
    //    A SA PLACE D'ORIGINE — l'attribuer au dernier bouton clique publierait
    //    une CAUSE FAUSSE.
    // ⚠️ `sansServeur` A DISPARU DE CE CAS LE 2026-09-12, ET SON FAIT EST
    //    INTACT : le vrai `fetch` n'est plus donne QU'AUX cas `http`, donc le
    //    rejet est desormais le DEFAUT. Un drapeau qui ne distingue plus rien
    //    serait une garde qu'on croit avoir.
    nom: "fait-de-page-a-la-maison",
    quoi: "`sortie.pas-de-serveur` sans clic ⇒ le transcript rentre CHEZ LUI",
    choix: "en", verbe: null,
    attendLangueVide: true, ecritures: 0,
    attendPlace: "sec-suite apres (tete)",
    attendPlaces: ["sec-suite apres (tete)"]
  },
  {
    // 🔴 LE VERDICT D'UN VERBE S'ECRIT **SOUS LE BOUTON CLIQUE**. C'est le
    //    constat owner du 2026-09-10, et c'est la moitie de `AC7.4.1` qu'une
    //    machine peut tenir. ⚠️ Le rafraichissement qui SUIT le verbe echoue
    //    lui aussi (le banc n'a pas de serveur) : sans son ancre, il renverrait
    //    le verdict A LA MAISON — le defaut recree sur le clic qui le ferme.
    nom: "verdict-sous-le-bouton",
    quoi: "un clic sur `b-stop` ⇒ le transcript passe SOUS `b-stop`",
    choix: "en", verbe: "stop", bouton: "b-stop",
    reponse: { commande: "dn_agent_tour.ps1 stop", sortie: "agent arrete",
               rc: 0, rc_pose_par: "l'outil", verdict: "le port est rendu" },
    attendLangueVide: true, ecritures: 0,
    attendPlace: "geste-1 apres b-stop",
    // ⚠️ QUATRE ECRITURES, ET LA PREMIERE EST **A LA MAISON** : le fait de page
    //    du chargement. Les TROIS suivantes appartiennent au clic — « en
    //    cours », le verdict, puis le rafraichissement qui ECHOUE APRES un
    //    verbe REUSSI. C'est cette derniere qui, sans son ancre, renvoyait le
    //    verdict quatre gestes plus bas SUR LE CLIC QUI VENAIT DE LE FERMER.
    attendPlaces: ["sec-suite apres (tete)", "geste-1 apres b-stop",
                   "geste-1 apres b-stop", "geste-1 apres b-stop"]
  },
  // ── LES SIX CAS DE **PRECONDITION**, AJOUTES LE 2026-09-10 (`dn7-6`) ─────
  {
    // 🔴 TOUT EST LA : les quatre etapes sont PRETES, et « activer l'agent »
    //    est ARME. C'est la ligne de reference — sans elle, « grise » ne se
    //    distinguerait de rien.
    nom: "tout-est-la",
    quoi: "charge complete, modules et LHM presents ⇒ 4 etapes PRETES",
    choix: "en", etatMachine: ETAT_SAIN,
    attendLangueVide: true, ecritures: 0,
    attendBandeaux: ["etat-deps CACHE", "etat-lhm CACHE"],
    attendTemoins: QUATRE_PRETES,
    attendArmes: ["b-langue-poser ARME",
                  "b-deps GRISE=raison.deps-completes",
                  "b-agent-poser ARME"]
  },
  {
    // 🔴 LA LIGNE DE PARTAGE, ET ELLE N'EST PAS INTUITIVE : ⛔ LE FLASH N'EST
    //    **PAS** BLOQUE par une dependance de l'AGENT. Priver un inconnu du
    //    geste PRINCIPAL pour ca est le contresens que `dn7-5` a ecarte.
    nom: "psutil-manquant",
    quoi: "un module manque ⇒ l'agent est GRISE, ⛔ pas le flash",
    choix: "en", etatMachine: avec({ psutil: false, manquantes: ["psutil"] }),
    attendLangueVide: true, ecritures: 0,
    attendBandeaux: ["etat-deps VU", "etat-lhm CACHE"],
    attendTemoins: QUATRE_PRETES,
    attendArmes: ["b-langue-poser ARME", "b-deps ARME",
                  "b-agent-poser GRISE=raison.agent-deps"]
  },
  {
    // 🔴 LE TROU NEUF DE `dn7-5` : LHM est un prerequis DUR de l'agent, et la
    //    page SAVAIT qu'il etait absent sans s'en servir pour rien.
    nom: "lhm-absent",
    quoi: "LHM ne repond pas ⇒ l'activation est GRISEE, avec SON motif",
    choix: "en", etatMachine: avec({ lhm: false }),
    attendLangueVide: true, ecritures: 0,
    attendBandeaux: ["etat-deps CACHE", "etat-lhm VU"],
    attendTemoins: QUATRE_PRETES,
    attendArmes: ["b-langue-poser ARME",
                  "b-deps GRISE=raison.deps-completes",
                  "b-agent-poser GRISE=raison.agent-lhm"]
  },
  {
    // 🔴 UNE IGNORANCE ⛔ N'EST PAS UN VERDICT : « non testable ici » ⛔ n'est
    //    PAS « absent », et elle ⛔ NE BLOQUE PAS. C'est la faute que `dn7-1`
    //    a payee pour `psutil`, et elle ⛔ ne se rejoue pas.
    nom: "lhm-non-testable",
    quoi: "LHM NON TESTABLE ⇒ l'activation reste ARMEE, ⛔ pas grisee",
    choix: "en", etatMachine: avec({ lhm: null }),
    attendLangueVide: true, ecritures: 0,
    attendBandeaux: ["etat-deps CACHE", "etat-lhm CACHE"],
    attendTemoins: QUATRE_PRETES,
    attendArmes: ["b-langue-poser ARME",
                  "b-deps GRISE=raison.deps-completes",
                  "b-agent-poser ARME"]
  },
  {
    // ⛔ LA MACHINE N'A PAS REPONDU AU PLANIFICATEUR : l'etape 1 ⛔ n'est ni
    //    prete ni bloquee — elle est NON TESTABLE, et le dire autrement
    //    publierait une ignorance comme un constat.
    nom: "hors-windows",
    quoi: "le planificateur ne repond pas ⇒ etape 1 NON TESTABLE",
    choix: "en", etatMachine: avec({ tache_presente: null, windows: false }),
    attendLangueVide: true, ecritures: 0,
    attendBandeaux: ["etat-deps CACHE", "etat-lhm CACHE"],
    attendTemoins: ["etat-su-non:non-testable", "etat-prete:prete",
                    "etat-prete:prete", "etat-prete:prete"],
    attendArmes: ["b-langue-poser ARME",
                  "b-deps GRISE=raison.deps-completes",
                  "b-agent-poser GRISE=raison.agent-outil"]
  },
  {
    // 🔴 LE SERVEUR SE TAIT — ET C'EST LE CHARGEMENT REEL QUI LE PRODUIT, ⛔ pas
    //    une simulation : le `fetch` du banc rejette. TOUS les temoins repassent
    //    a l'ignorance ET LEUR FORME AVEC, et les deux gestes pilotes se
    //    desarment : « on ne sait pas » ⛔ n'est pas « c'est bon ».
    nom: "serveur-muet",
    quoi: "le serveur ne repond pas ⇒ temoins INCONNUS, gestes DESARMES",
    choix: "en", etatMachine: null,
    attendLangueVide: true, ecritures: 0,
    attendBandeaux: ["etat-deps CACHE", "etat-lhm CACHE"],
    // 🔴 LES BLOCS DE LA BRANCHE `.catch` (dn8-2) : quand le serveur se tait, la
    //    page REMET `etat-orphelin`, `etat-deps` et `etat-lhm` a CACHE et LEVE
    //    `etat-inactif` avec « sans serveur ». Ces trois sites-la ⛔ ne sont pas
    //    ceux de la branche de succes, et ⛔ aucun cas ne les regardait.
    attendBlocs: ["etat-hors-windows CACHE", "etat-orphelin CACHE",
                  "etat-port-tenu CACHE", "etat-cdn CACHE",
                  "etat-inactif VU", "etat-not-allowed CACHE",
                  "etat-unsupported CACHE", "bloc-installer CACHE",
                  "etat-charge VU", "etat-deps CACHE", "etat-lhm CACHE"],
    attendTemoins: ["etat-su-non:inconnu", "etat-su-non:inconnu",
                    "etat-su-non:inconnu", "etat-su-non:inconnu"],
    attendArmes: ["b-langue-poser GRISE=raison.flash-absent",
                  "b-deps GRISE=raison.sans-serveur",
                  "b-agent-poser GRISE=raison.sans-serveur"]
  },
  {
    // 🔴 L'ETAT DONT CETTE MARCHE PORTE LE NOM, ET ⛔ AUCUN HARNAIS NE L'AVAIT
    //    JAMAIS EXERCE (correctif de revue, 2026-09-10). Les six cas neufs
    //    attendaient QUATRE_PRETES, `non-testable` ou `inconnu` : la chaine
    //    `etat-bloquee:bloquee` n'apparaissait dans AUCUNE attente, donc la
    //    branche ⛔ n'etait jamais executee.
    // 🔬 CE QUE CA LAISSAIT PASSER, **DEMONTRE** : peindre `etape.bloquee`
    //    avec l'aplat de `prete` — c'est-a-dire « lire une position pour
    //    l'autre », la faute meme que `dn7-4` a corrigee a l'œil de l'owner —
    //    laissait HUIT gates vertes.
    // ⚠️ ET LE CAS MESURE LE MOT **ET** LA FORME : `etat-bloquee:bloquee`.
    nom: "outil-absent-etape-bloquee",
    quoi: "l'outil est absent ⇒ etape 1 BLOQUEE, mot ET aplat",
    choix: "en", etatMachine: avec({ pilote: "" }),
    attendLangueVide: true, ecritures: 0,
    attendBandeaux: ["etat-deps CACHE", "etat-lhm CACHE"],
    attendTemoins: ["etat-bloquee:bloquee", "etat-prete:prete",
                    "etat-prete:prete", "etat-prete:prete"],
    attendArmes: ["b-langue-poser ARME",
                  "b-deps GRISE=raison.deps-completes",
                  "b-agent-poser GRISE=raison.agent-outil"]
  },
  // ── LES SEPT CAS DE **SURFACE MORTE**, AJOUTES LE 2026-09-11 (`dn8-2`) ──
  // 🔴 CHACUN ENTRE DANS UNE FONCTION QUE LA COUVERTURE V8 A RELEVEE MORTE,
  //    ⛔ pas dans une surface qu'on suppose faible. La population visee est
  //    NOMMEE : l.424/439/442 (la langue de la PAGE), l.1515 (la dalle en
  //    ANGLAIS), l.810/821/826/829 (les verbes qu'aucun clic n'atteignait),
  //    l.1296/1306/1308/1313/1374/1417 (la console de `dn7-2-2`).
  {
    // 🔴 LE FRERE MANQUANT DE `clic-reel-sur-francais` : `b-dalle-fr` etait
    //    clique, `b-dalle-en` ⛔ JAMAIS — et son gestionnaire etait donc MORT
    //    dans le seul instrument qui execute cette page.
    nom: "clic-reel-sur-anglais",
    attendPort: PORT_TENU,
    quoi: "un VRAI clic sur « dalle en anglais » ⇒ ⛔ AUCUN octet",
    choix: "fr", cliqueDalle: "b-dalle-en", repond: () => null,
    attendLangue: "Nothing to do", ecritures: 0
  },
  {
    // 🔴 LA LANGUE DE LA **PAGE** — ⛔ PAS CELLE DE LA DALLE. `aria-pressed` est
    //    relu SUR LES VRAIS BOUTONS : c'est la moitie d'`AC8.2.6` qu'une
    //    machine puisse tenir. ⛔ L'autre moitie — l'option retenue se
    //    DISTINGUE-t-elle a l'œil — ⛔ ne se ferme PAS ici.
    nom: "langue-de-la-page",
    quoi: "clics REELS sur « fr » puis « en » ⇒ `aria-pressed` bascule",
    choix: "en", repond: () => null,
    langues: ["b-langue-fr", "b-langue-en"],
    attendLangueVide: true, ecritures: 0,
    // 🔴 LE DEPART EST CELUI DU **BALISAGE** (corrige le 2026-09-12) : la page
    //    porte `aria-pressed="true"` sur `b-langue-en` et `"false"` sur
    //    `b-langue-fr`. ⛔ L'ancienne attente — ~~`en=null fr=null`~~ — epinglait
    //    un etat de depart qui n'appartenait QU'AU BANC, sur la surface meme dont
    //    la lisibilite fait le sujet d'`AC8.2.6`.
    attendLangues: ["depart en=true fr=false doc=en",
                    "b-langue-fr ⇒ en=false fr=true doc=fr",
                    "b-langue-en ⇒ en=true fr=false doc=en"]
  },
  {
    // 🔴 TROIS VERBES QU'AUCUN CLIC N'ATTEIGNAIT, ET LE `.catch` DE `jouer`.
    //    Le QUATRIEME geste REJETTE : sans lui, la branche d'echec — celle qui
    //    REND les boutons — restait morte, et un bouton qui ne se rearme pas
    //    est un geste mort jusqu'au rechargement.
    nom: "verbes-non-cliques",
    quoi: "`b-deps`, `b-agent-poser`, `b-retirer` ARMES, puis un verbe qui ECHOUE",
    choix: "en", repond: () => null,
    verbes: { etatAvecManque: avec({ psutil: false, manquantes: ["psutil"] }),
              etatSain: ETAT_SAIN },
    attendLangueVide: true, ecritures: 0,
    attendArmesVerbes: ["b-deps ARME", "b-agent-poser ARME", "b-retirer ARME",
                        "b-retirer ARME"],
    // ⚠️ LA PREMIERE LIGNE EST LE **CHARGEMENT** : la page demande son etat AVANT
    //    qu'aucun etat ne soit arme, et elle part donc dans sa branche `.catch` —
    //    exactement ce qu'un banc sans serveur produit. Les deux `api/etat` qui
    //    suivent chaque verbe sont le RE-SONDAGE que `jouer` enchaine.
    attendRoutes: ["api/etat ⇒ REJET", "api/etat", "api/dependances", "api/etat",
                   "api/etat", "api/agent/poser", "api/etat",
                   "api/agent/retirer", "api/etat",
                   "api/agent/retirer ⇒ REJET"],
    // 🔴 ET L'ETAT DES QUATRE BOUTONS EST COMPARE **AVANT / APRES** LE VERBE QUI
    //    ECHOUE : c'est le `.catch` de `jouer` qui les rend, et sans ce jugement
    //    le priver de sa restitution laissait la gate VERTE sur quatre boutons
    //    MORTS jusqu'au rechargement de la page.
    attendBoutonsAvant: ["b-stop ARME", "b-retirer ARME", "b-deps GRISE",
                         "b-agent-poser ARME"],
    attendRestitution: true
  },
  {
    // 🔴 LA CONSOLE DE `dn7-2-2`, OUVERTE PAR SON BOUTON, LUE, PUIS RENDUE PAR
    //    LE SIEN. ⛔ Pas en appelant `consoleOuvrir()` : ce qu'on mesure est la
    //    liaison bouton ⇄ code, et le port RENDU (`port ferme=1`).
    nom: "console-ouverte-lue-fermee",
    quoi: "ouvrir · lire une ligne · fermer par le bouton ⇒ le port est RENDU",
    choix: "en", repond: () => null,
    console: { lignes: ["desknode> pret\n"], fermerPar: "bouton" },
    attendLangueVide: true, ecritures: 0,
    attendConsoleContient: ["console open at 115200", "desknode> pret",
                            "port closed and handed back"],
    // ⛔ UNE FERMETURE **VOULUE** N'EST PAS UNE FIN DE LIEN : sans cette
    //    exclusion, `consoleFinDeLien` prive de sa garde annoncait « la carte a
    //    cesse d'ecrire » sur un debranchement QUI N'A PAS EU LIEU, et le cas
    //    restait VERT.
    attendConsoleSans2: ["the board stopped writing", "the read stopped"],
    attendGestes: ["b-console ARME", "b-console-fermer GRISE",
                   "port ferme=1/1", "references RENDUES"]
  },
  {
    // 🔴 LE FLUX QUI SE TERMINE DE LUI-MEME (carte debranchee, remise a zero) :
    //    ⛔ personne n'a clique, et le port doit etre rendu QUAND MEME. Sans
    //    ce chemin, « Ouvrir » restait GRISE et « Fermer » ACTIF sur un port
    //    MORT — deux boutons qui mentent tous les deux.
    nom: "console-fin-de-lien",
    quoi: "la carte cesse d'ecrire ⇒ le lien FINIT, et le port est rendu",
    choix: "en", repond: () => null,
    console: { lignes: ["boot\n"], finDeLien: true },
    attendLangueVide: true, ecritures: 0,
    attendConsoleContient: ["the board stopped writing",
                            "port closed and handed back"],
    attendConsoleSans2: ["the read stopped"],
    attendGestes: ["b-console ARME", "b-console-fermer GRISE",
                   "port ferme=1/1", "references RENDUES"]
  },
  {
    // ⛔ UNE LECTURE QUI **ECHOUE** N'EST PAS UNE FIN DE LIEN ORDINAIRE : la
    //    page doit NOMMER le motif, ⛔ pas publier une ignorance comme un
    //    constat. Les deux cles sont DISTINCTES, et c'est mesure ici.
    nom: "console-lien-perdu",
    quoi: "la lecture LEVE ⇒ « the read stopped », ⛔ pas « stopped writing »",
    choix: "en", repond: () => null,
    console: { lignes: [], lecteurRejette: true },
    attendLangueVide: true, ecritures: 0,
    attendConsoleContient: ["the read stopped", "port closed and handed back"],
    attendConsoleSans2: ["the board stopped writing"],
    attendGestes: ["b-console ARME", "b-console-fermer GRISE",
                   "port ferme=1/1", "references RENDUES"]
  },
  {
    // 🔴 LE FILET DE CELUI QUI FERME L'ONGLET : l'ecouteur `pagehide` rend le
    //    port. Il etait INJOIGNABLE tant que la fenetre du banc avait un
    //    `addEventListener()` VIDE — c'est-a-dire mort, et vert.
    nom: "console-pagehide-rend-le-port",
    quoi: "l'onglet part sans clic ⇒ le port est rendu quand meme",
    choix: "en", repond: () => null,
    console: { lignes: ["x\n"], fermerPar: "pagehide" },
    attendLangueVide: true, ecritures: 0,
    attendConsoleContient: ["port closed and handed back"],
    attendConsoleSans2: ["the board stopped writing", "the read stopped"],
    attendGestes: ["b-console ARME", "b-console-fermer GRISE",
                   "port ferme=1/1", "references RENDUES"]
  },
  {
    // 🔴 UNE FERMETURE QUI **ECHOUE** — LE CAS QUE LE PORT BIDON NE POUVAIT PAS
    //    JOUER AVANT LE 2026-09-12. La page doit publier `console.non-rendue`,
    //    GARDER ses references et laisser « Fermer » ACTIF pour qu'on ressaie.
    //    ⛔ « le port est rendu » sur une fermeture qui a echoue serait une
    //    IGNORANCE publiee comme un constat.
    nom: "console-fermeture-qui-echoue",
    quoi: "`close()` REJETTE ⇒ « ⛔ pas rendu », references GARDEES, Fermer ACTIF",
    choix: "en", repond: () => null,
    console: { lignes: ["x\n"], fermerPar: "bouton", fermetureEchoue: true },
    attendLangueVide: true, ecritures: 0,
    attendConsoleContient: ["the port could NOT be handed back",
                            "Failed to close the serial port"],
    attendConsoleSans2: ["port closed and handed back",
                         "the board stopped writing", "the read stopped"],
    attendGestes: ["b-console GRISE", "b-console-fermer ARME",
                   "port ferme=0/1", "references GARDEES"]
  },
  // ── LES QUATRE CAS DE **BLOCS D'AFFICHAGE**, AJOUTES LE 2026-09-12 ───────
  // 🔴 ILS FERMENT SIX CONSTATS **DEMONTRES** : l'inversion de
  //    `etat-hors-windows`, celle d'`etat-orphelin`, celle d'`etat-port-tenu`,
  //    `etat-cdn` qui ne se leve plus, `etat-inactif` jamais masque et
  //    `etat-not-allowed` muet laissaient TOUTES la gate a `54 OK / 0 KO`.
  // ⚠️ CHAQUE BLOC EST VU DANS SES **DEUX** ETATS, et les quatre cas se
  //    partagent ce travail : `saine` porte les CACHE, `en-defaut` les VU de
  //    l'etat de machine, `contexte-refuse` ceux du contexte du navigateur,
  //    `sans-web-serial` le dernier et la charge qui devient inutilisable.
  {
    nom: "blocs-machine-saine",
    quoi: "machine SAINE ⇒ ⛔ aucun bandeau, et le bloc d'installation est OFFERT",
    choix: "en", repond: () => null,
    serveurDePapier: { manifeste: MANIFESTE_DE_PAPIER, etat: ETAT_SAIN },
    blocs: {},
    attendLangueVide: true, ecritures: 0,
    attendBlocs: ["etat-hors-windows CACHE", "etat-orphelin CACHE",
                  "etat-port-tenu CACHE", "etat-cdn CACHE",
                  "etat-inactif CACHE", "etat-not-allowed CACHE",
                  "etat-unsupported CACHE", "bloc-installer VU",
                  "etat-charge CACHE", "etat-deps CACHE", "etat-lhm CACHE"]
  },
  {
    nom: "blocs-machine-en-defaut",
    quoi: "hors Windows, orpheline, agent pose, charge abimee, modules et LHM absents",
    choix: "en", repond: () => null,
    serveurDePapier: { manifeste: MANIFESTE_DE_PAPIER,
                       etat: avec({ windows: false, arbre_parent: false,
                                    tache_presente: true, psutil: false,
                                    manquantes: ["psutil"], lhm: false,
                                    charge: { complete: false,
                                              asset: "⛔ CRC32 FAUX" } }) },
    blocs: {},
    attendLangueVide: true, ecritures: 0,
    attendBlocs: ["etat-hors-windows VU", "etat-orphelin VU",
                  "etat-port-tenu VU", "etat-cdn CACHE",
                  "etat-inactif CACHE", "etat-not-allowed CACHE",
                  "etat-unsupported CACHE", "bloc-installer CACHE",
                  "etat-charge VU", "etat-deps VU", "etat-lhm VU"]
  },
  {
    nom: "blocs-contexte-refuse",
    quoi: "⛔ pas de contexte securise + outil absent + module distant absent",
    choix: "en", repond: () => null,
    contexte: { securise: false },
    serveurDePapier: { manifeste: MANIFESTE_DE_PAPIER,
                       etat: avec({ pilote: "" }) },
    blocs: { moduleAbsent: true },
    attendLangueVide: true, ecritures: 0,
    attendBlocs: ["etat-hors-windows CACHE", "etat-orphelin CACHE",
                  "etat-port-tenu CACHE", "etat-cdn VU",
                  "etat-inactif VU", "etat-not-allowed VU",
                  "etat-unsupported CACHE", "bloc-installer CACHE",
                  "etat-charge CACHE", "etat-deps CACHE", "etat-lhm CACHE"]
  },
  {
    nom: "blocs-sans-web-serial",
    quoi: "⛔ pas d'acces serie, puis la charge devient INUTILISABLE",
    choix: "en", repond: () => null,
    contexte: { serie: false },
    serveurDePapier: { manifeste: MANIFESTE_DE_PAPIER, etat: ETAT_SAIN },
    blocs: { chargeInutilisable: true },
    attendLangueVide: true, ecritures: 0,
    attendBlocs: ["etat-hors-windows CACHE", "etat-orphelin CACHE",
                  "etat-port-tenu CACHE", "etat-cdn CACHE",
                  "etat-inactif CACHE", "etat-not-allowed CACHE",
                  "etat-unsupported VU", "bloc-installer CACHE",
                  "etat-charge VU", "etat-deps CACHE", "etat-lhm CACHE"]
  }
];

// ── LES CAS **HTTP** — ⛔ JOUES SEULEMENT DERRIERE `--base` ──── (dn8-2) ──
// 🔴 POURQUOI ILS VIVENT DANS UNE LISTE A PART : sans serveur, ils ne
//    mesureraient RIEN, et un cas qui ne mesure rien est un OK de plus dans un
//    bilan — c'est-a-dire un mensonge. ⇒ sans `--base`, ce banc joue
//    EXACTEMENT les cas qu'il jouait avant `dn8-2`, ⛔ ni plus ni moins.
// ⛔ LE SERVEUR EST LIE PAR `tools/verif_banc_langue_dn73.py`, ⛔ jamais par ce
//    fichier : c'est ce qui garde le banc jouable SEUL.
const CAS_HTTP = [
  {
    // 🔴 LE CHARGEMENT SUR UN VRAI SERVEUR : `afficherManifeste()` PUIS
    //    `rafraichirEtat()` ABOUTISSENT — leurs branches de succes (l.944/948
    //    et l.690/691) etaient MORTES parce que le `fetch` du banc rejetait
    //    TOUJOURS. Puis un verbe part VRAIMENT, et traverse `_garde()`,
    //    `do_POST` et le prefixe `/api/agent/` du produit.
    nom: "http-page-chargee-et-verbe-abouti",
    quoi: "la page charge d'un VRAI serveur, puis `b-stop` part pour de vrai",
    choix: "en", repond: () => null,
    attendLangueVide: true, ecritures: 0,
    http: {
      attente: 180, repos: 180, champs: ["v-version"],
      geste: (ctx, els) => { (els["b-stop"].clics || []).forEach((f) => f()); }
    },
    attendRoutes: ["charge/manifest.json", "api/etat", "api/agent/stop",
                   "api/etat"],
    // 🔴 LA VERSION ATTENDUE EST **LUE DANS LE MANIFESTE**, ⛔ plus gravee ici :
    //    `dn8-7` reconstruira cette charge, et `40be2c8` ecrit en dur aurait
    //    rougi ce jour-la sans rien apprendre a personne.
    attendVersionDuManifeste: true,
    attendSortieContient: ["dn_agent_tour.ps1 stop", "sortie de papier",
                           "exit code: 0"]
  },
  {
    // 🔴 LE ROUTAGE, NOMME ROUTE PAR ROUTE. Une INVERSION entre
    //    `ROUTE_DEPENDANCES` et le prefixe `/api/agent/` dans `do_POST`
    //    passait VERTE tant que le produit n'etait appele que PAR IMPORT.
    // ⚠️ `rc=2` SUR UN VERBE INCONNU EST POSE PAR LE SERVEUR, ⛔ pas par
    //    l'outil : c'est ce que la page relaie en « posé par CETTE PAGE ».
    nom: "http-routes-du-serveur",
    quoi: "stop ⇒ rc=0 · inconnu ⇒ rc=2 · dependances ⇒ 200, NOMMEES",
    choix: "en", repond: () => null,
    attendLangueVide: true, ecritures: 0,
    http: {
      attente: 150, repos: 40,
      geste: (ctx, els, codes) => requeteBrute("api/agent/stop").then((r) => {
        codes.push("api/agent/stop ⇒ " + r.code + " rc=" + rcDe(r.corps)
          + " " + routeAtteinte(r.corps));
        return requeteBrute("api/agent/inconnu");
      }).then((r) => {
        codes.push("api/agent/inconnu ⇒ " + r.code + " rc=" + rcDe(r.corps)
          + " " + routeAtteinte(r.corps));
        return requeteBrute("api/dependances");
      }).then((r) => {
        codes.push("api/dependances ⇒ " + r.code + " rc=" + rcDe(r.corps)
          + " " + routeAtteinte(r.corps));
      })
    },
    attendCodesHttp: ["api/agent/stop ⇒ 200 rc=0 atteint=verbe stop (l'outil)",
                      "api/agent/inconnu ⇒ 200 rc=2 atteint=aucune commande (la page)",
                      "api/dependances ⇒ 200 rc=0 atteint=dependances (l'outil)"]
  },
  {
    // 🔴 LES DEUX REFUS, RELEVES A **403** ET AVEC LEUR MOTIF. ⛔ Ni 200, ni
    //    404 : un 404 dirait « il n'y a rien la », alors que ce qui se passe
    //    est un REFUS NOMME.
    // ⚠️ `Host` PASSE PAR `node:http` : node IGNORE EN SILENCE un `Host` pose
    //    sur `fetch` (mesure du 2026-09-11). C'est DECLARE, ⛔ pas contourne.
    nom: "http-refus-host-et-origine",
    quoi: "`Host` menteur et `Origin` etrangere ⇒ 403, avec leur motif",
    choix: "en", repond: () => null,
    attendLangueVide: true, ecritures: 0,
    http: {
      attente: 150, repos: 40,
      geste: (ctx, els, codes) => requeteBrute(
        "api/agent/stop", { Host: "attaquant.example:1" }).then((r) => {
          codes.push("Host menteur ⇒ " + r.code
            + (r.corps.indexOf("`Host` refuse") >= 0 ? " motif Host"
                                                     : " ⛔ SANS motif"));
          return requeteBrute("api/agent/stop",
                              { Origin: "http://ailleurs.example" });
        }).then((r) => {
          codes.push("Origin etrangere ⇒ " + r.code
            + (r.corps.indexOf("`Origin` refuse") >= 0 ? " motif Origin"
                                                       : " ⛔ SANS motif"));
        })
    },
    attendCodesHttp: ["Host menteur ⇒ 403 motif Host",
                      "Origin etrangere ⇒ 403 motif Origin"]
  }
];

// Le `rc` d'une reponse JSON du serveur — ⛔ « ? » plutot qu'une supposition.
function rcDe(corps) {
  try { return String(JSON.parse(corps).rc); } catch (e) { return "⛔"; }
}

// ── CE QUE `dn8-2` COMPARE EN PLUS, ET COMMENT ──────────────────────────
// 🔴 DES **CHAINES**, ⛔ PAS DES BOOLEENS : « pas la bonne chose » doit DIRE ce
//    qu'il a lu, sinon le KO envoie chercher a l'aveugle. Deux familles, et
//    elles ne se confondent pas : une SUITE se compare EN ENTIER (l'ordre est
//    la moitie du fait), un TEXTE se compare par INCLUSION (il porte aussi les
//    deux langues du document, et les exiger toutes rendrait le cas illisible).
const EGALITES = [["attendLangues", "langues"], ["attendGestes", "gestes"],
                  ["attendRoutes", "routes"], ["attendCodesHttp", "codes"],
                  ["attendChamps", "champs"],
                  // ── CE QUE LA BOUCLE DE REVUE 1 A AJOUTE (2026-09-12) ──
                  ["attendBlocs", "blocs"],
                  ["attendArmesVerbes", "armesVerbes"],
                  ["attendBoutonsAvant", "boutonsAvant"]];
const INCLUSIONS = [["attendConsoleContient", "consoleTexte"],
                    ["attendSortieContient", "sortieTexte"]];
const EXCLUSIONS = [["attendConsoleSans2", "consoleTexte"]];

function ecartsDeSurface(c, r) {
  const out = [];
  for (const [a, k] of EGALITES) {
    if (c[a] && JSON.stringify(r[k] || []) !== JSON.stringify(c[a])) {
      out.push("⛔ " + k.toUpperCase() + " : " + JSON.stringify(r[k] || [])
        + " au lieu de " + JSON.stringify(c[a]));
    }
  }
  for (const [a, k] of INCLUSIONS) {
    if (!c[a]) { continue; }
    const abs = c[a].filter((x) => String(r[k] || "").indexOf(x) < 0);
    if (abs.length) {
      out.push("⛔ " + k.toUpperCase() + " SANS " + JSON.stringify(abs)
        + " — lu : " + String(r[k] || "(vide)").replace(/\s+/g, " ").slice(0, 110));
    }
  }
  for (const [a, k] of EXCLUSIONS) {
    if (!c[a]) { continue; }
    const vus = c[a].filter((x) => String(r[k] || "").indexOf(x) >= 0);
    if (vus.length) {
      out.push("⛔ " + k.toUpperCase() + " PORTE " + JSON.stringify(vus)
        + ", qui appartient a l'AUTRE issue");
    }
  }
  return out;
}

// 🔴 LE JUGEMENT D'UN CAS VIT DANS **UNE** FONCTION (dn8-2) : les cas se jouent
//    en parallele borne, et la ligne `CAS` doit s'imprimer DANS L'ORDRE DE LA
//    LISTE. Juge en ligne dans la chaine, l'ordre aurait ete celui des arrivees.
function juger(c, r) {
  const vuLangue = c.attendLangueVide
    ? r.etatLangue === ""
    : r.etatLangue.includes(c.attendLangue);
  const vuConsole = !c.attendConsole || r.etatConsole.includes(c.attendConsole);
  const vuRelais = !c.attendRelais || r.relais.includes(c.attendRelais);
  const oct = r.ecrits.length === c.ecritures;
  // 🔴 LES **OCTETS**, ⛔ PAS LES APPELS : « zero octet » est ce que trois
  //    surfaces de ce depot publient, et un `write()` de longueur nulle aurait
  //    satisfait un compte d'appels.
  const zero = (r.octets === 0) === (c.ecritures === 0);
  // 🔴 CE QUE LA PAGE DIT DU PORT — les deux phrases sont OPPOSEES.
  const dit = !c.attendPort || (r.etatLangue.includes(c.attendPort)
    && !r.etatLangue.includes(c.attendPort === PORT_TENU ? PORT_LIBRE : PORT_TENU));
  // 🔴 LA POLARITE DU GESTE, LUE SUR LE VRAI BOUTON.
  const arme = c.attendDesarme === undefined || r.poserDesarme === c.attendDesarme;
  const parti = !c.attendEcrit || r.ecrits.some((x) => x.trim() === c.attendEcrit);
  // ⛔ ET UN RELAIS **VIDE** N'EST PAS REVELE : un cadre vide donne a croire
  //    qu'on a lu quelque chose.
  const relaisJuste = r.relais !== "" || r.relaisCache === true;
  const placeJuste = !c.attendPlace || r.place === c.attendPlace;
  const transcritJuste = !c.attendPlaces
    || JSON.stringify(r.places || []) === JSON.stringify(c.attendPlaces);
  const consoleSans = !c.attendConsoleSans
    || !r.etatConsole.includes(c.attendConsoleSans);
  const temoinsJustes = !c.attendTemoins
    || JSON.stringify(r.temoins || []) === JSON.stringify(c.attendTemoins);
  const armesJustes = !c.attendArmes
    || JSON.stringify(r.armes || []) === JSON.stringify(c.attendArmes);
  const bandeauxJustes = !c.attendBandeaux
    || JSON.stringify(r.bandeaux || []) === JSON.stringify(c.attendBandeaux);
  // 🔴 LE VERROU D'ECRITURE EST RENDU **A CHAQUE ECRITURE**, ⛔ pas « en
  //    general » : un verrou garde fait partir `port.close()` en REJET.
  const verrou = r.verrouRendu === r.ecrits.length;
  // ⛔ « posee » N'APPARAIT QU'UNE FOIS, ET SEULEMENT EN DERNIER.
  const posees = r.suite.filter(k => k === "langue.posee").length;
  const succesJuste = posees === 0
    || (posees === 1 && r.suite[r.suite.length - 1] === "langue.posee");
  // 🔴 LA RESTITUTION DES QUATRE BOUTONS APRES UN VERBE QUI ECHOUE (dn8-2) :
  //    l'etat d'APRES doit etre CELUI D'AVANT. Un bouton qui ne se rearme pas
  //    est un geste mort jusqu'au rechargement de la page.
  const restitue = !c.attendRestitution
    || JSON.stringify(r.boutonsAvant || []) === JSON.stringify(r.boutonsApres || []);
  const ecarts = ecartsDeSurface(c, r);
  const bon = vuLangue && vuConsole && vuRelais && oct && zero && dit && arme
    && parti && relaisJuste && verrou && !r.enVol && succesJuste
    && placeJuste && transcritJuste && consoleSans
    && temoinsJustes && armesJustes && bandeauxJustes && restitue
    && ecarts.length === 0;
  const motifs = [];
  if (!vuLangue) { motifs.push("issue lue : " + (r.etatLangue.slice(0, 70) || "(vide)")); }
  if (!vuConsole) { motifs.push("console lue : " + (r.etatConsole.slice(0, 70) || "(vide)")); }
  if (!vuRelais) { motifs.push("relais sans « " + c.attendRelais + " »"); }
  if (!oct) { motifs.push("ecritures=" + r.ecrits.length + " au lieu de " + c.ecritures); }
  if (!zero) { motifs.push("⛔ OCTETS=" + r.octets + " pour " + c.ecritures + " ecriture(s)"); }
  if (!dit) { motifs.push("⛔ LE PORT N'EST PAS DIT : attendu « " + c.attendPort + " »"); }
  if (!arme) { motifs.push("⛔ GESTE desarme=" + r.poserDesarme + " au lieu de " + c.attendDesarme); }
  if (!parti) { motifs.push("⛔ « " + c.attendEcrit + " » n'est PAS parti : " + JSON.stringify(r.ecrits)); }
  if (!relaisJuste) { motifs.push("⛔ RELAIS VIDE REVELE"); }
  if (!verrou) {
    motifs.push("⛔ VERROU NON RENDU : " + r.verrouRendu + " restitution(s) pour "
      + r.ecrits.length + " ecriture(s)");
  }
  if (r.enVol) { motifs.push("⛔ LE GESTE RESTE EN VOL"); }
  if (!succesJuste) { motifs.push("⛔ SUCCES HORS RELECTURE : " + r.suite.join(">")); }
  if (!placeJuste) {
    motifs.push("⛔ PLACE : « " + r.place + " » au lieu de « " + c.attendPlace + " »");
  }
  if (!transcritJuste) {
    motifs.push("⛔ SUITE DES PLACES : " + JSON.stringify(r.places || [])
      + " au lieu de " + JSON.stringify(c.attendPlaces));
  }
  if (!consoleSans) {
    motifs.push("⛔ LE BLOC CONSOLE PORTE « " + c.attendConsoleSans
      + " », qui appartient au bloc de langue");
  }
  if (!bandeauxJustes) {
    motifs.push("⛔ BANDEAUX " + JSON.stringify(r.bandeaux)
      + " au lieu de " + JSON.stringify(c.attendBandeaux));
  }
  if (!temoinsJustes) {
    motifs.push("⛔ TEMOINS : " + JSON.stringify(r.temoins || [])
      + " au lieu de " + JSON.stringify(c.attendTemoins));
  }
  if (!armesJustes) {
    motifs.push("⛔ ARMEMENT : " + JSON.stringify(r.armes || [])
      + " au lieu de " + JSON.stringify(c.attendArmes));
  }
  if (!restitue) {
    motifs.push("⛔ BOUTONS NON RENDUS APRES L'ECHEC : "
      + JSON.stringify(r.boutonsApres || []) + " au lieu de "
      + JSON.stringify(r.boutonsAvant || []));
  }
  for (const e of ecarts) { motifs.push(e); }
  return { bon, ligne: "CAS " + c.nom.padEnd(28) + " " + (bon ? "OK " : "KO ")
    + " ecritures=" + r.ecrits.length + "/" + c.ecritures + " octets=" + r.octets
    + (motifs.length ? "  " + motifs.join(" · ") : "") };
}

// ⚠️ LE PLAFOND D'UN CAS EST UNE MESURE DE **CE BANC**, ⛔ pas un verdict de la
//    page : un cas qui ne se resout pas est ROUGE et NOMME, et la chaine
//    continue — sinon un seul defaut emporterait la liste entiere en silence.
function jouerBorne(src, cas) {
  return new Promise((resoudre, rejeter) => {
    let fini = false;
    const t = setTimeout(() => {
      if (fini) { return; }
      fini = true;
      rejeter(new Error("CAS NON RESOLU en " + DELAI_CAS + " ms"));
    }, DELAI_CAS);
    Promise.resolve().then(() => jouer(src, cas)).then(r => {
      if (fini) { return; }
      fini = true; clearTimeout(t); resoudre(r);
    }, e => {
      if (fini) { return; }
      fini = true; clearTimeout(t); rejeter(e);
    });
  });
}

function principal() {
  const args = process.argv.slice(2);
  if (args.includes("--liste-cas")) {
    for (const c of CAS) { console.log("  " + c.nom.padEnd(30) + "  " + c.quoi); }
    // ⚠️ LES CAS HTTP SONT **NOMMES ET MARQUES**, ⛔ pas caches : une gate qui
    //    les compte doit pouvoir dire lesquels ⛔ ne se jouent PAS sans base.
    for (const c of CAS_HTTP) {
      console.log("  " + c.nom.padEnd(30) + "  [--base] " + c.quoi);
    }
    return Promise.resolve(0);
  }
  // ⛔ UNE VALEUR DE DELAI INVALIDE EST **REFUSEE**, ⛔ pas ignoree en silence :
  //    ignoree, elle ferait payer la valeur de PRODUIT a chaque mutant de la
  //    campagne, et personne ne saurait pourquoi la passe a ralenti.
  const nombre = (v, quoi) => {
    const n = parseInt(v, 10);
    if (!Number.isFinite(n) || String(n) !== String(v).trim() || n <= 0) {
      console.log("BANC ⛔ ARGUMENT REFUSE : " + quoi + " = " + JSON.stringify(v)
        + " — un entier strictement positif est attendu.");
      return null;
    }
    return n;
  };
  const iD = args.indexOf("--delai");
  if (iD >= 0) {
    const v = nombre(args[iD + 1], "--delai");
    if (v === null) { return Promise.resolve(2); }
    DELAI_PAGE = v;
  }
  // ⚠️ LA BORNE D'UN CAS SE REGLE AUSSI, ET POUR LA MEME RAISON : un cas qui ne
  //    se resout pas la paye EN ENTIER, une fois PAR MUTANT. La valeur par
  //    defaut reste GENEREUSE pour une main qui lance le banc ; la gate, elle,
  //    en passe une plus serree parce qu'elle sait ce qu'un cas coute.
  const iC = args.indexOf("--delai-cas");
  if (iC >= 0) {
    const v = nombre(args[iC + 1], "--delai-cas");
    if (v === null) { return Promise.resolve(2); }
    DELAI_CAS = v;
  }
  // 🔴 LE TEMOIN DE LA CHAINE : il REPLANTE le cas « la chaine ne se resout
  //    jamais » et exige que ce banc SORTE EN NON-ZERO sans rendre de bilan.
  //    ⛔ Sans lui, « le banc sort en non-zero » serait une promesse ecrite que
  //    rien ne joue — et c'est exactement ce que ce depot appelle une regle qui
  //    pourrira.
  const temoin = args.includes("--temoin-chaine");
  // 🔴 LE TEMOIN DE **DOM** : il DEGRADE un element MONTE et exige que
  //    l'assertion le dise AVANT que la moindre ligne de la page ne s'evalue.
  //    ⛔ Il ne debranche rien : il REPLANTE la faute de `dn7-4`.
  const temoinDom = args.includes("--temoin-dom");
  // 🔴 LE PLAFOND EST **DERIVE DU NOMBRE DE CAS**, ⛔ pas une constante : une
  //    valeur figee se perime au cas suivant, et un plafond franchi par la
  //    LISTE, ⛔ pas par une chaine bloquee, tuerait le banc en plein travail et
  //    ferait passer un banc SAIN pour un banc mort.
  PLAFOND = temoin ? 400 : 0;   // ⚠️ derive de la LISTE JOUEE, plus bas

  // 🔴 LA BASE HTTP — REFUSEE SI ELLE N'EST PAS UNE URL ABSOLUE. Une base
  //    relative ferait lever `new URL` a chaque cas, et le banc accuserait la
  //    PAGE d'un defaut qui serait CELUI DE SON APPELANT.
  const iU = args.indexOf("--base");
  if (iU >= 0) {
    const v = args[iU + 1];
    // ⛔ VALIDEE PAR `new URL`, ⛔ PAS PAR UN MOTIF — correctif de revue du
    //    2026-09-12 : `--base "http://"` passait `^https?://` et n'avait ⛔ AUCUN
    //    HOTE. `new URL(u, BASE)` levait alors PAR CAS, et le banc rendait
    //    `39 OK, 3 KO` en accusant la PAGE (« Invalid URL ») d'une faute de SON
    //    APPELANT. ⇒ une base qu'on ne peut pas resoudre est un ARGUMENT REFUSE,
    //    comme les deux delais.
    let hoteBase = null;
    try { hoteBase = new URL(String(v)).hostname; } catch (e) { hoteBase = null; }
    if (!v || !/^https?:\/\//.test(String(v)) || !hoteBase) {
      console.log("BANC ⛔ ARGUMENT REFUSE : --base = " + JSON.stringify(v)
        + " — une URL ABSOLUE **ET RESOLUBLE** (http://hote:port/) est attendue.");
      return Promise.resolve(2);
    }
    BASE = String(v);
  }

  const i = args.indexOf("--page");
  const chemin = (i >= 0 && args[i + 1]) ? args[i + 1] : PAGE_DEFAUT;
  // 🔴 LE MANIFESTE DE LA CHARGE — passe par la GATE, qui sait ou vit l'arbre
  //    reel. ⚠️ La page mutee, elle, vit dans un temporaire SANS `charge/`.
  const iN = args.indexOf("--manifeste");
  if (iN >= 0) {
    if (!args[iN + 1]) {
      console.log("BANC ⛔ ARGUMENT REFUSE : --manifeste sans chemin.");
      return Promise.resolve(2);
    }
    MANIFESTE = String(args[iN + 1]);
  }

  // 🔴 L'OFFSET DE LA FENETRE `<script>` — DEMANDE PAR
  //    `tools/banc_couverture_dn82.mjs`, qui ⛔ ne la recalcule PAS : deux
  //    extractions, c'est deux sources de verite.
  if (args.includes("--offset-script")) {
    let f = null;
    try { f = fenetreDuScript(chemin); } catch (e) { f = null; }
    if (!f) {
      console.log("BANC ⛔ ILLISIBLE : aucune fenetre `<script>` dans " + chemin);
      return Promise.resolve(2);
    }
    console.log("OFFSET " + f.debut + " LONGUEUR " + f.longueur);
    return Promise.resolve(0);
  }

  let src = null;
  try {
    src = litLeScript(chemin);
  } catch (e) {
    console.log("BANC ⛔ ILLISIBLE : " + String(e.message).slice(0, 120));
    return Promise.resolve(2);
  }
  if (!src) {
    console.log("BANC ⛔ ILLISIBLE : aucun `<script>` dans " + chemin);
    return Promise.resolve(2);
  }

  // 🔴 L'ETAT INITIAL DES QUATRE BOUTONS DE CHOIX, **LU DANS LE BALISAGE** —
  //    avant tout cas, et avant le temoin de DOM.
  try {
    const fb = fenetreDuScript(chemin);
    ARIA_INITIAL = fb ? ariaDuBalisage(fb.brut.slice(0, fb.debut)) : {};
  } catch (e) { ARIA_INITIAL = {}; }

  if (temoinDom) {
    TEMOIN_DOM = true;
    try {
      faireContexte(src, { choix: "en" });
    } catch (e) {
      const m = String(e && e.message);
      if (m.indexOf(SIGNATURE_DOM) === 0) {
        console.log("BANC ⛔ " + m);
        console.log("⛔ SORTIE FERMEE EN " + RC_DOM + " : l'assertion a joue");
        console.log("   AVANT `runInContext`, et ⛔ aucun cas n'a ete tente.");
        return Promise.resolve(RC_DOM);
      }
      console.log("BANC ⛔ LE TEMOIN DOM A LEVE POUR UN AUTRE MOTIF : " + m.slice(0, 120));
      return Promise.resolve(1);
    }
    console.log("BANC ⛔ LE TEMOIN DOM N'A PAS ROUGI : un element PRIVE de sa");
    console.log("   capacite est passe, et l'assertion ⛔ ne garde donc RIEN.");
    return Promise.resolve(1);
  }

  // ⛔ LES CAS HTTP NE SE JOUENT QUE DERRIERE `--base` : sans serveur ils ne
  //    mesureraient rien, et un cas qui ne mesure rien est un OK de plus.
  const LISTE = BASE ? CAS.concat(CAS_HTTP) : CAS;

  // 🔴 LA VERSION ATTENDUE DU CAS HTTP EST **LUE DANS LE MANIFESTE**, et le banc
  //    ECHOUE FERME s'il ne peut pas la lire : inventer cette valeur ferait
  //    mesurer le banc, et l'ecrire en dur ferait rougir `dn8-7`.
  if (BASE) {
    try {
      VERSION_MANIFESTE = JSON.parse(fs.readFileSync(MANIFESTE, "utf8")).version
                          || null;
    } catch (e) { VERSION_MANIFESTE = null; }
    if (!VERSION_MANIFESTE) {
      console.log("BANC ⛔ MANIFESTE ILLISIBLE (ou sans `version`) : " + MANIFESTE);
      console.log("   ⇒ la version que la page doit afficher ⛔ ne s'invente pas.");
      return Promise.resolve(2);
    }
    for (const c of CAS_HTTP) {
      if (c.attendVersionDuManifeste) {
        c.attendChamps = ["v-version=" + VERSION_MANIFESTE];
      }
    }
  }

  console.log("=".repeat(78));
  console.log("BANC dn7-3 — LE SCRIPT DE LA PAGE, **EXECUTE** CONTRE UN PORT BIDON");
  console.log("=".repeat(78));
  console.log("page jouee : " + chemin + " (" + Buffer.byteLength(src, "utf8") + " octets de script)");
  // 🔴 LE PLAFOND EST DERIVE DE LA **LISTE JOUEE**, ⛔ pas de `CAS` : depuis
  //    `dn8-2` la liste change avec `--base`, et un plafond derive de la
  //    mauvaise longueur tuerait un banc SAIN en plein travail.
  if (!temoin) { PLAFOND = LISTE.length * (DELAI_CAS + 600) + 3000; }
  console.log("base HTTP  : " + (BASE || "(aucune — les cas HTTP ⛔ ne sont PAS joues)"));
  console.log("boutons    : "
    + BOUTONS_DE_CHOIX.map((id) => id + "=" + ARIA_INITIAL[id]).join(" ")
    + "   (LUS dans le balisage, ⛔ pas poses par ce banc)");
  console.log("concurrence: " + CONCURRENCE + " cas a la fois, lignes dans "
    + "l'ordre de la LISTE");
  console.log("delais     : page=" + DELAI_PAGE + " ms · cas=" + DELAI_CAS
    + " ms · plafond=" + PLAFOND + " ms");
  console.log("⛔ AUCUNE CARTE N'EST TOUCHEE, et ⛔ aucun port reel n'est ouvert.");
  console.log("-".repeat(78));

  let ok = 0, ko = 0;
  let joues = 0;
  // 🔴 LE FILET GLOBAL. ⛔ Un banc dont la chaine ne se resout pas laisserait le
  //    processus mourir avec un code de SUCCES et une liste TRONQUEE : un
  //    succes annonce sur ce qui n'a pas ete mesure.
  const filet = setTimeout(() => {
    console.log("-".repeat(78));
    console.log("BANC ⛔ CHAINE NON RESOLUE apres " + PLAFOND + " ms — "
      + joues + " cas sur " + LISTE.length + " (" + ok + " OK, " + ko + " KO)");
    console.log("⛔ SORTIE FERMEE EN 3 : une liste tronquee n'est PAS un succes,");
    console.log("   et ⛔ aucune ligne `BANC : n OK, m KO` n'est rendue.");
    process.exit(3);
  }, PLAFOND);

  // 🔴 LES CAS SE JOUENT EN **PARALLELE BORNE** — ⛔ ni un par un, ni tous a la
  //    fois. MESURE DU 2026-09-12 : construire un contexte ET evaluer la page
  //    coute **1,9 ms** ; tout le reste d'un cas est de l'ATTENTE armee. Un par
  //    un, les cas coutaient ~4 s A CHAQUE TIR — et la campagne rejoue ce banc
  //    UNE FOIS PAR MUTANT, ce qui est precisement ce qui paie les mutants que
  //    la boucle de revue 1 a exiges. ⛔ Tous a la fois, en revanche, les bornes
  //    de cas (`DELAI_CAS`) expireraient pendant que les derniers attendent leur
  //    tour : un banc SAIN declare mort.
  // ⚠️ ET LES LIGNES SORTENT **DANS L'ORDRE DE LA LISTE**, ⛔ pas des arrivees :
  //    une sortie non reproductible ne se compare pas d'un tir a l'autre.
  const JOUEE = temoin ? [] : LISTE;
  const lignes = new Array(JOUEE.length);
  let prochain = 0;
  const ouvrier = () => {
    if (prochain >= JOUEE.length) { return Promise.resolve(); }
    const k = prochain++;
    const c = JOUEE[k];
    return jouerBorne(src, c).then((r) => {
      joues++;
      const v = juger(c, r);
      if (v.bon) { ok++; } else { ko++; }
      lignes[k] = v.ligne;
    }, (e) => {
      joues++;
      ko++;
      lignes[k] = "CAS " + c.nom.padEnd(28) + " KO  ⛔ LEVE : "
        + String(e && e.message).slice(0, 90);
    }).then(ouvrier);
  };
  let chaine = Promise.all(
    Array.from({ length: Math.max(1, Math.min(CONCURRENCE, JOUEE.length)) },
               () => ouvrier())
  ).then(() => { for (const l of lignes) { console.log(l); } });
  if (temoin) {
    // ⛔ LA CHAINE QUI NE SE RESOUT JAMAIS, ET RIEN D'AUTRE. Le filet doit la
    //    tuer, imprimer ce qu'il sait, et sortir en 3 — ⛔ jamais en 0.
    chaine = chaine.then(() => new Promise(() => {}));
  }
  return chaine.then(() => {
    clearTimeout(filet);
    console.log("-".repeat(78));
    console.log("BANC : " + ok + " OK, " + ko + " KO");
    console.log("⛔ CE BANC NE PROUVE PAS que la langue soit VRAIMENT posee dans une");
    console.log("   carte, ni qu'elle survive a une coupure : le bandeau est SUR LA");
    console.log("   DALLE, et il se lit A L'ŒIL. Seance carte, portee au ledger.");
    return ko ? 1 : 0;
  });
}

principal().then(rc => { process.exitCode = rc; });
