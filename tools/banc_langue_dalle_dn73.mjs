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
//                                             [--delai-cas <ms>]
//      node tools/banc_langue_dalle_dn73.mjs --liste-cas
//      node tools/banc_langue_dalle_dn73.mjs --temoin-chaine
//
//  ⚠️ `--page` sert a la gate `tools/verif_banc_langue_dn73.py`, qui MUTE la
//     page dans une COPIE JETABLE et rejoue le banc dessus. ⛔ Le banc n'ecrit
//     JAMAIS dans le depot.
//
//  Sortie : une ligne `CAS <nom> <OK|KO> …` par cas, puis `BANC : n OK, m KO`.
//  Codes  : 0 tout passe · 1 au moins un cas rouge · 2 la page ne se lit pas ·
//           3 la chaine ne s'est PAS resolue (⛔ pas un succes : une ignorance).
// ============================================================================

import fs from "node:fs";
import path from "node:path";
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
let DELAI_CAS = 4000;       // la borne d'UN cas — au-dela il est ROUGE, ⛔ pas vert
let PLAFOND = 30000;        // le filet global — au-dela le banc SORT EN 3

function litLeScript(chemin) {
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
  return brut.slice(i + "<script>\n".length, j);
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

function faireContexte(src, choix) {
  const els = {};
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
    window: { isSecureContext: true, addEventListener() {},
              setTimeout: detache, clearTimeout },
    location: { hostname: "127.0.0.1", protocol: "http:", host: "127.0.0.1:1", pathname: "/" },
    navigator: { serial: {} },
    fetch: () => Promise.reject(new Error("hors banc")),
    TextEncoder, TextDecoder,
    setTimeout: detache, clearTimeout, setInterval: detacheI, clearInterval,
    console, Promise, Date, JSON, Error
  };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(src, ctx, { filename: "installeur/index.html<script>" });
  return { ctx, els };
}

// ── LE PORT BIDON ──────────────────────────────────────────────────────────
//    `ouverture` decide si `open()` reussit ; `repond` decide ce que la carte
//    rend pour chaque ligne recue. Le compte d'octets ECRITS est la mesure de
//    « rien n'est ecrit », et ⛔ pas une declaration.
function jouer(src, cas) {
  const { ctx, els } = faireContexte(src, cas.choix);
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
      return Object.assign({}, vide, { temoins: lire(), armes, bandeaux: bandeaux() });
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
      () => Object.assign({}, vide, { temoins: lire(), armes, bandeaux: bandeaux() }));
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
  }
];

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
  // 🔴 LE PLAFOND EST **DERIVE DU NOMBRE DE CAS**, ⛔ pas une constante : une
  //    valeur figee se perime au cas suivant, et un plafond franchi par la
  //    LISTE, ⛔ pas par une chaine bloquee, tuerait le banc en plein travail et
  //    ferait passer un banc SAIN pour un banc mort.
  PLAFOND = temoin ? 400 : CAS.length * (DELAI_CAS + 600) + 3000;

  const i = args.indexOf("--page");
  const chemin = (i >= 0 && args[i + 1]) ? args[i + 1] : PAGE_DEFAUT;

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

  console.log("=".repeat(78));
  console.log("BANC dn7-3 — LE SCRIPT DE LA PAGE, **EXECUTE** CONTRE UN PORT BIDON");
  console.log("=".repeat(78));
  console.log("page jouee : " + chemin + " (" + Buffer.byteLength(src, "utf8") + " octets de script)");
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
      + joues + " cas sur " + CAS.length + " (" + ok + " OK, " + ko + " KO)");
    console.log("⛔ SORTIE FERMEE EN 3 : une liste tronquee n'est PAS un succes,");
    console.log("   et ⛔ aucune ligne `BANC : n OK, m KO` n'est rendue.");
    process.exit(3);
  }, PLAFOND);

  let chaine = Promise.resolve();
  // ⛔ EN MODE TEMOIN, ⛔ AUCUN CAS N'EST JOUE : ce qu'on replante est « la
  //    chaine ne se resout jamais », ⛔ pas « un cas est lent ». Jouer la liste
  //    d'abord ne prouverait rien de plus et couterait a la campagne.
  for (const c of (temoin ? [] : CAS)) {
    chaine = chaine.then(() => jouerBorne(src, c).then(r => {
      joues++;
      const vuLangue = c.attendLangueVide
        ? r.etatLangue === ""
        : r.etatLangue.includes(c.attendLangue);
      const vuConsole = !c.attendConsole || r.etatConsole.includes(c.attendConsole);
      const vuRelais = !c.attendRelais || r.relais.includes(c.attendRelais);
      const oct = r.ecrits.length === c.ecritures;
      // 🔴 LES **OCTETS**, ⛔ PAS LES APPELS : « zero octet » est ce que trois
      //    surfaces de ce depot publient, et un `write()` de longueur nulle
      //    aurait satisfait un compte d'appels.
      const zero = (r.octets === 0) === (c.ecritures === 0);
      // 🔴 CE QUE LA PAGE DIT DU PORT — les deux phrases sont OPPOSEES.
      const dit = !c.attendPort || (r.etatLangue.includes(c.attendPort)
        && !r.etatLangue.includes(c.attendPort === PORT_TENU ? PORT_LIBRE : PORT_TENU));
      // 🔴 LA POLARITE DU GESTE, LUE SUR LE VRAI BOUTON.
      const arme = c.attendDesarme === undefined || r.poserDesarme === c.attendDesarme;
      // 🔴 CE QUI EST REELLEMENT PARTI SUR LE PORT.
      const parti = !c.attendEcrit || r.ecrits.some((x) => x.trim() === c.attendEcrit);
      // ⛔ ET UN RELAIS **VIDE** N'EST PAS REVELE : un cadre vide donne a croire
      //    qu'on a lu quelque chose.
      const relaisJuste = r.relais !== "" || r.relaisCache === true;
      // 🔴 OU LE TRANSCRIPT S'EST POSE (`dn7-4`) — une CHAINE, ⛔ pas un booleen :
      //    « pas a la bonne place » doit DIRE ou il est.
      const placeJuste = !c.attendPlace || r.place === c.attendPlace;
      const transcritJuste = !c.attendPlaces
        || JSON.stringify(r.places || []) === JSON.stringify(c.attendPlaces);
      // ⛔ ET UN BLOC NE DOIT PAS PORTER CE QUI APPARTIENT A L'AUTRE : sans
      //    cette exclusion, deux blocs ECHANGES passaient le cas
      //    `pas-d-acces-serie`, qui attendait la MEME chaine des deux cotes.
      const consoleSans = !c.attendConsoleSans
        || !r.etatConsole.includes(c.attendConsoleSans);
      // 🔴 LE TEMOIN DE CHAQUE ETAPE, ET LE MOTIF DE CHAQUE DESARMEMENT
      //    (`dn7-6`) — DES CHAINES, ⛔ pas des booleens : « pas le bon etat »
      //    doit DIRE lequel il porte, sinon le KO envoie chercher a l'aveugle.
      const temoinsJustes = !c.attendTemoins
        || JSON.stringify(r.temoins || []) === JSON.stringify(c.attendTemoins);
      const armesJustes = !c.attendArmes
        || JSON.stringify(r.armes || []) === JSON.stringify(c.attendArmes);
      const bandeauxJustes = !c.attendBandeaux
        || JSON.stringify(r.bandeaux || [])
           === JSON.stringify(c.attendBandeaux);
      // 🔴 LE VERROU D'ECRITURE EST RENDU **A CHAQUE ECRITURE**, ⛔ pas « en
      //    general » : un verrou garde fait partir `port.close()` en REJET, et
      //    le port reste tenu EN SILENCE. MESURE : sans cette ligne, retirer
      //    le `releaseLock()` du chemin de succes laissait le banc VERT.
      //    ⚠️ Le chemin d'ECHEC, lui, ⛔ n'est PAS exerce ici — un port bidon
      //       n'echoue pas a l'ecriture — et c'est la gate STATIQUE qui le
      //       garde, avec son mutant. Le partage est ECRIT, ⛔ pas suppose.
      const verrou = r.verrouRendu === r.ecrits.length;
      // ⛔ « posee » N'APPARAIT QU'UNE FOIS, ET SEULEMENT EN DERNIER.
      const posees = r.suite.filter(k => k === "langue.posee").length;
      const succesJuste = posees === 0
        || (posees === 1 && r.suite[r.suite.length - 1] === "langue.posee");
      const bon = vuLangue && vuConsole && vuRelais && oct && zero && dit && arme
        && parti && relaisJuste && verrou && !r.enVol && succesJuste
        && placeJuste && transcritJuste && consoleSans
        && temoinsJustes && armesJustes && bandeauxJustes;
      if (bon) { ok++; } else { ko++; }
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
        motifs.push("⛔ PLACE : « " + r.place + " » au lieu de « "
          + c.attendPlace + " »");
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
      console.log("CAS " + c.nom.padEnd(28) + " " + (bon ? "OK " : "KO ")
        + " ecritures=" + r.ecrits.length + "/" + c.ecritures + " octets=" + r.octets
        + (motifs.length ? "  " + motifs.join(" · ") : ""));
    }, e => {
      joues++;
      ko++;
      console.log("CAS " + c.nom.padEnd(28) + " KO  ⛔ LEVE : "
        + String(e && e.message).slice(0, 90));
    }));
  }
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
