#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-16 / AC6 — LE LEDGER DIT CE QUI RESTE, ET A QUI.

======================= CE QUE CET OUTIL FAIT, ET POURQUOI ==================

Le 2026-08-25, l'epic `dn4` publiait : « 388 entrees, dont 160 ouvertes cote
DeskNode, et 27 adressees a des stories deja `done` ». Cinq jours plus tard,
AUCUN de ces chiffres n'a pu etre reproduit — ⛔ PAS parce qu'ils etaient faux,
mais parce que LA CONVENTION DE COMPTAGE N'ETAIT ECRITE NULLE PART. Trois
passes du cadrage ont rendu 233 / 240 / 258 selon la regle de decoupe : l'ecart
entre deux conventions non ecrites vaut 10 %.

⇒ CETTE GATE EST LA CONVENTION. Elle ne CITE pas un nombre : elle le PRODUIT.
   Le manifeste `dn4-16-arbitrage-ledger.md` cite CE script, jamais l'inverse.
   Motif mesure (`dn4-14-2` / `W_SEC_H`) : un nombre ECRIT a cote d'un nombre
   CALCULE finit par diverger.

Et elle exige, pour CHAQUE entree DeskNode ouverte, une LIGNE DE DISPOSITION :

    ⇒ [dn4-16 AAAA-MM-JJ] <VERDICT> · porteur : <...> · preuve : <motif>

------------------------------------------------------------------------------
── ⛔ CE QUE CETTE GATE NE VOIT PAS, ET C'EST ECRIT PLUTOT QUE TU (AC6.9) ─────
------------------------------------------------------------------------------

  🔴 ELLE EXIGE UN VERDICT. ELLE NE PEUT PAS JUGER S'IL EST JUSTE.
     Elle verifie qu'une ligne de disposition existe, que son verdict est l'un
     des CINQ, que son porteur est VIVANT et que sa preuve est un MOTIF. Elle
     ne lit pas le code cite, ne rejoue aucun constat, et ne sait pas si
     `CLOSE` a ete pose sur une entree encore vraie. Le verdict est un acte de
     lecture humaine, consigne au manifeste. ⇒ Elle EXIGE un arbitrage, elle
     ne le REND pas.

  🔴 ELLE NE COMPTE PAS DES BORNES, ET C'EST LE POINT (AC6.6).
     Mesure du 2026-08-30 : les 240 entrees ouvertes citent 192 adresses
     `fichier:ligne` ; **ZERO** tombe hors de son fichier. Un controle « la
     ligne existe-t-elle ? » sortirait `192 OK / 0 KO` sur un ledger
     INTEGRALEMENT DERIVE — et `dn_ui.c:3733`, cite comme designant
     `dn_ui_icone_alt()`, porte aujourd'hui `desc_effectif()`, du code sans
     rapport. La correction de l'epic (`:7346`) a derive a son tour en cinq
     jours (`:9948` le 2026-08-30). ⇒ CETTE GATE NE VALIDE AUCUNE ADRESSE
     `fichier:ligne`. Elle REFUSE une preuve qui n'est QU'un numero.
     A rapprocher de « une gate `N OK / 0 KO` peut epingler du code FAUX ».

  🔴 ELLE NE DIT RIEN DES ENTREES KIDSAT — 174 sur 443, hors perimetre PAR
     CONSTRUCTION. Ce n'est pas un oubli : `dn4-16` ne les compte pas, ne les
     arbitre pas, ne les deplace pas. Une passe KidSat aura sa propre story.

  🔴 ELLE NE JUGE PAS LA VIVACITE D'UN `clos par :` NI D'UN `bloquee par :`.
     ⚠️ ECART DECLARE AVEC UNE LECTURE LITTERALE D'AC6.5 : celui-ci exige que
     « le porteur soit vivant ». Or AC3.4 exige qu'une entree `CLOSE` dise
     POURQUOI elle se ferme — et ce qui l'a fermee est, PAR DEFINITION, dans
     le passe (une story `done`, un commit). Exiger qu'un fossoyeur soit
     vivant serait une contradiction. ⇒ La regle appliquee est : **tout
     porteur qui designe du TRAVAIL A VENIR doit etre vivant** (`PORTEE`,
     `RE-HEBERGEE`, et la part story d'une `BLOQUEE`) ; un `clos par :`
     designe du passe et n'est pas soumis a la vivacite. C'est ECRIT ici
     plutot que resolu en silence.

  ⚠️ ELLE NE VOIT PAS LES AUTRES ECRIVAINS DU LEDGER. `bmad-code-review`
     (step-04) est corrige par AC4 ; `bmad-dev-auto` et `bmad-quick-dev`
     ecrivent aussi au ledger par d'autres chemins et NE SONT PAS couverts.

  ⚠️ ELLE NE SAIT PAS QU'UN SECOND FORMAT EXISTE. `bmad-loop-sweep` definit
     `### DW-<n>:` pour CE MEME FICHIER, et son `--migrate` exige ZERO prose
     residuelle ⇒ il detruirait les 443 entrees en prose et les 14 fichiers
     thematiques qu'il ne connait pas. La collision est DECLAREE en tete du
     ledger ; ⛔ elle n'est pas tranchee ici.

------------------------------------------------------------------------------
── LA CONVENTION, ET C'EST DU CODE (AC1.3) ───────────────────────────────────
------------------------------------------------------------------------------

  (1) UNE ENTREE = une puce de PREMIER NIVEAU (`^- `, zero indentation) dans
      une section `## Deferred from: ...`. Son texte court jusqu'a la puce de
      premier niveau suivante, le prochain titre `^#`, ou la fin du fichier.
      ⇒ Les puces INDENTEES (`^  - `) sont des CONTINUATIONS, ⛔ pas des
        entrees. C'est cette regle-la qui separe 240 de 258.
      ⇒ Une puce hors section `## Deferred from:` (index, legende, bandeau)
        n'est PAS une entree. C'est cette regle-la qui separe 443 de 484.

  (2) PERIMETRE DESKNODE = l'entree porte le tag `[DeskNode]` DANS son texte,
      OU le titre de sa section cite `dnN-M` / contient `desknode` (insensible
      a la casse). ⛔ Le contenu technique n'entre pas dans la regle : un
      constat sur `dn_ui.c` range dans une section KidSat resterait KidSat.

  (3) UNE ENTREE OUVERTE = une entree dont la puce NE COMMENCE PAS par `✅`
      (apres `- ` et espaces). Le `✅` est la marque de solde du depot.
      ⚠️ La ligne de disposition NE ferme PAS l'entree : une entree arbitree
        `CLOSE` reste OUVERTE au sens du compte. Motif : si l'arbitrage
        retirait les entrees du perimetre, la gate cesserait de les surveiller
        et le compte deviendrait non reproductible d'un tir a l'autre.

  (4) LE MARQUEUR = le PREMIER glyphe de marqueur EN TETE de puce, apres `- `,
      les espaces, un `**` d'ouverture et un tag `[DeskNode]`. Sinon `(sans)`.
      🔴 MESURE : un glyphe compte PARTOUT DANS LA LIGNE rend 45 🔴 / 23 ⚠️ /
      15 🆕 ; EN TETE il rend 42 🔴 / 14 ⚠️ / 2 🆕 — soit exactement le releve
      du 2026-08-25. La regle « en tete » est donc celle de l'epic, et elle
      n'avait jamais ete ecrite.

------------------------------------------------------------------------------
Usage :
    python3 tools/verif_ledger_dn416.py [--cockpit CHEMIN] [--compte]
                                        [--manifeste] [--sortie F]

  (defaut)     : la GATE. Exige une disposition valide sur chaque entree
                 ouverte. Sort en 1 des qu'un controle rougit.
  --compte     : mode COMPTE SEUL (T0). N'exige aucune disposition ; imprime
                 la convention, les totaux et l'histogramme des marqueurs.
                 ⚠️ Il sort quand meme en 1 si un controle STRUCTUREL rougit
                 (depot absent, ledger illisible) — ⛔ jamais un 0 inconditionnel.
  --manifeste  : emet le TABLEAU du manifeste (une ligne par entree ouverte),
                 pour que `dn4-16-arbitrage-ledger.md` ne recopie AUCUN chiffre.
==============================================================================
"""

import argparse
import io
import os
import re
import sys

DESKNODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCKPIT_DEFAUT = os.path.expanduser("~/projects/compagnon_project")

REL_LEDGER = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRACKER = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
REL_MANIFESTE = "_bmad-output/implementation-artifacts/dn4-16-arbitrage-ledger.md"

VERDICTS = ("PORTEE", "RE-HEBERGEE", "CLOSE", "BLOQUEE", "CONNAISSANCE")

# Les verdicts qui designent du TRAVAIL A VENIR ⇒ leur porteur doit etre VIVANT.
VERDICTS_A_VENIR = ("PORTEE", "RE-HEBERGEE", "BLOQUEE")

STATUTS_VIVANTS = ("backlog", "in-progress", "ready-for-dev", "review", "blocked")
STATUTS_MORTS = ("done", "superseded")

MARQUEURS = ("🔴", "🟠", "⚪", "🟢", "🟡", "⚠️", "🆕", "🎯", "⚫", "🔵",
             "🧹", "📋", "🗺️", "✅")

ok_total = [0]
ko_total = [0]


def ctrl(ok, libelle, detail=""):
    """Un controle, imprime, compte. ⛔ Jamais un skip silencieux."""
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-62s %s" % (libelle[:62], detail[:60]))
    else:
        ko_total[0] += 1
        print("  [KO ] %-62s %s" % (libelle[:62], detail[:60]))
    return ok


def sans_accents(s):
    """PORTÉE == PORTEE, RE-HÉBERGÉE == RE-HEBERGEE, BLOQUÉE == BLOQUEE."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


# ═══════════════════════════════════════════════════════════════════════════
#  LA CONVENTION, IMPLEMENTEE  (AC1.3 / AC6.3)
# ═══════════════════════════════════════════════════════════════════════════

def decoupe(texte):
    """Convention (1) : sections `## Deferred from:` + puces de PREMIER niveau."""
    lignes = texte.split("\n")
    sections = []
    cur = None
    for i, l in enumerate(lignes):
        if l.startswith("## Deferred from:"):
            cur = {"titre": l[len("## Deferred from:"):].strip(),
                   "ligne": i + 1, "entrees": []}
            sections.append(cur)
        elif l.startswith("## "):
            cur = None
        elif cur is not None and re.match(r"^- ", l):
            j = i
            while (j + 1 < len(lignes)
                   and not re.match(r"^- ", lignes[j + 1])
                   and not lignes[j + 1].startswith("#")):
                j += 1
            cur["entrees"].append({
                "ligne": i + 1,
                "txt": "\n".join(lignes[i:j + 1]),
                "tete": l,
                "sec": cur["titre"],
                "sec_ligne": cur["ligne"],
            })
    return sections


def est_desknode(e):
    """Convention (2)."""
    return ("[DeskNode]" in e["txt"]
            or re.search(r"\bdn\d|desknode", e["sec"], re.I) is not None)


def est_ouverte(e):
    """Convention (3)."""
    return re.match(r"^-\s*✅", e["txt"]) is None


def marqueur(e):
    """Convention (4) : le PREMIER glyphe EN TETE de puce."""
    t = e["tete"][2:]
    t = re.sub(r"^\s*", "", t)
    t = re.sub(r"^\*\*", "", t)
    t = re.sub(r"^\[DeskNode\]\s*", "", t)
    t = re.sub(r"^\*\*", "", t)
    t = re.sub(r"^\s*", "", t)
    for m in MARQUEURS:
        if t.startswith(m):
            return m
    return "(sans)"


def titre_court(e, n=58):
    """Le libelle de l'entree, nettoye — pour le manifeste. ⛔ Jamais une preuve."""
    t = e["tete"][2:]
    t = re.sub(r"^\s*", "", t)
    for m in MARQUEURS:
        t = t.replace(m, "")
    t = t.replace("[DeskNode]", "")
    t = re.sub(r"[*`«»\"]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n]


# ═══════════════════════════════════════════════════════════════════════════
#  LA LIGNE DE DISPOSITION  (AC3.1)
# ═══════════════════════════════════════════════════════════════════════════

RE_DISPO = re.compile(
    r"^\s*⇒\s*\[dn4-16\s+(\d{4}-\d{2}-\d{2})\]\s*"
    r"([A-ZÀ-ÿ\-]+)\s*·\s*"
    r"porteur\s*:\s*(.*?)\s*·\s*"
    r"preuve\s*:\s*(.*?)\s*$",
    re.M)

# Une preuve qui n'est QU'une adresse `fichier:123` (ou `fichier:12-34`) est
# REFUSEE — AC6.6. Motif mesure : 0 adresse sur 192 tombe hors fichier.
RE_PREUVE_NUE = re.compile(r"^[`'\"]?[\w./+-]+:\d+(?:[-–]\d+)?[`'\"]?$")

RE_STORY = re.compile(r"\b(dn\d+-\d+(?:-\d+)?)\b", re.I)


def dispo(e):
    """Retourne la disposition de l'entree, ou None."""
    m = RE_DISPO.search(e["txt"])
    if not m:
        return None
    return {"date": m.group(1),
            "verdict": sans_accents(m.group(2)).upper(),
            "verdict_brut": m.group(2),
            "porteur": m.group(3).strip(),
            "preuve": m.group(4).strip()}


def porteurs_a_venir(d):
    """Les cles de story que la disposition designe comme TRAVAIL A VENIR.

    ⛔ Un `clos par :` designe le PASSE ⇒ exclu de la vivacite (voir l'en-tete).
    """
    if d["verdict"] not in VERDICTS_A_VENIR:
        return []
    p = d["porteur"]
    if re.match(r"^\s*clos par\s*:", p, re.I):
        return []
    return [x.lower() for x in RE_STORY.findall(p)]


# ═══════════════════════════════════════════════════════════════════════════
#  LE TRACKER
# ═══════════════════════════════════════════════════════════════════════════

def lit_tracker(chemin):
    st = {}
    try:
        txt = io.open(chemin, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    for l in txt.split("\n"):
        m = re.match(r"^  ([a-z0-9\-]+):\s*([a-z\-]+)", l)
        if m:
            c = re.match(r"^(dn\d+-\d+(?:-\d+)?)", m.group(1))
            if c:
                st.setdefault(c.group(1).lower(), m.group(2))
    return st


# ═══════════════════════════════════════════════════════════════════════════

def imprime_convention():
    print("\n── LA CONVENTION QUE CE SCRIPT IMPLEMENTE (AC1.3) ────────────────")
    print("   (1) entree   = puce `^- ` de PREMIER niveau, en section"
          " `## Deferred from:`")
    print("       (les puces indentees sont des CONTINUATIONS ⇒ 240, pas 258)")
    print("   (2) DeskNode = tag `[DeskNode]` dans le texte OU `dnN-M`/`desknode`"
          " au titre de section")
    print("   (3) ouverte  = la puce ne commence PAS par `✅`")
    print("       ⚠️ une entree arbitree `CLOSE` reste OUVERTE au sens du compte")
    print("   (4) marqueur = premier glyphe EN TETE de puce (⛔ pas ailleurs"
          " dans la ligne)")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--cockpit", default=COCKPIT_DEFAUT)
    ap.add_argument("--compte", action="store_true")
    ap.add_argument("--manifeste", action="store_true")
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()

    print("=" * 78)
    print("dn4-16 / AC6 — CHAQUE ENTREE OUVERTE PORTE UN VERDICT ET UN PORTEUR")
    print("=" * 78)
    print("\ndepot code    : %s" % DESKNODE)
    print("depot cockpit : %s" % a.cockpit)

    # ── 0. LES DEUX DEPOTS (AC6.7) — ⛔ jamais un skip silencieux ────────────
    print("\n── 0. LES DEUX DEPOTS SONT LA (AC6.7) ────────────────────────────")
    dn_ok = ctrl(os.path.isdir(DESKNODE), "le depot code est atteignable",
                 DESKNODE[-58:])
    ck_ok = ctrl(os.path.isdir(a.cockpit), "le depot cockpit est atteignable",
                 a.cockpit[-58:] if os.path.isdir(a.cockpit)
                 else "⛔ ABSENT — une gate scopee epingle VERT le meme defaut ailleurs")
    p_led = os.path.join(a.cockpit, REL_LEDGER)
    p_trk = os.path.join(a.cockpit, REL_TRACKER)
    led_ok = ctrl(ck_ok and os.path.isfile(p_led), "le ledger est lisible",
                  REL_LEDGER if ck_ok and os.path.isfile(p_led) else "⛔ ABSENT")
    trk_ok = ctrl(ck_ok and os.path.isfile(p_trk), "le tracker est lisible",
                  REL_TRACKER if ck_ok and os.path.isfile(p_trk) else "⛔ ABSENT")
    if not (dn_ok and ck_ok and led_ok and trk_ok):
        print("\n" + "=" * 78)
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("⛔ ARRET : un depot ou un fichier manque. ⛔ JAMAIS un skip.")
        print("=" * 78)
        return 1

    texte = io.open(p_led, encoding="utf-8", errors="replace").read()
    tracker = lit_tracker(p_trk)

    # ── 1. LE COMPTE, PRODUIT ICI (AC1.2 / AC6.3) ───────────────────────────
    imprime_convention()
    sections = decoupe(texte)
    toutes = [e for s in sections for e in s["entrees"]]
    dn = [e for e in toutes if est_desknode(e)]
    ouvertes = [e for e in dn if est_ouverte(e)]
    sec_dn = [s for s in sections
              if re.search(r"\bdn\d|desknode", s["titre"], re.I)]

    print("\n── 1. LE COMPTE — ⛔ AUCUN CHIFFRE N'EST RECOPIE (AC1.2) ──────────")
    print("     ledger              : %s (%d lignes)"
          % (REL_LEDGER, texte.count("\n") + 1))
    print("     sections            : %4d   dont DeskNode : %d (%.0f %%)"
          % (len(sections), len(sec_dn), 100.0 * len(sec_dn) / max(1, len(sections))))
    print("     entrees             : %4d   dont DeskNode : %d (%.0f %%)"
          % (len(toutes), len(dn), 100.0 * len(dn) / max(1, len(toutes))))
    print("     DeskNode OUVERTES   : %4d   <= LE PERIMETRE DE CETTE GATE"
          % len(ouvertes))
    print("     KidSat (hors champ) : %4d" % (len(toutes) - len(dn)))

    hist = {}
    for e in ouvertes:
        hist[marqueur(e)] = hist.get(marqueur(e), 0) + 1
    print("     marqueurs (regle 4) : %s"
          % "  ".join("%s %d" % (k, v)
                      for k, v in sorted(hist.items(), key=lambda x: -x[1])))
    ctrl(len(ouvertes) > 0, "le perimetre n'est pas vide",
         "%d entree(s) ouverte(s)" % len(ouvertes))

    # ── mode COMPTE SEUL ────────────────────────────────────────────────────
    if a.compte:
        print("\n" + "=" * 78)
        print("MODE --compte : aucune disposition n'est exigee.")
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
        print("=" * 78)
        return 1 if ko_total[0] else 0

    # ── mode MANIFESTE ──────────────────────────────────────────────────────
    if a.manifeste:
        flux = (io.open(a.sortie, "w", encoding="utf-8") if a.sortie
                else sys.stdout)
        flux.write("| ligne | section d'origine | marq. | titre court |"
                   " verdict | porteur | preuve |\n")
        flux.write("|---:|---|:-:|---|---|---|---|\n")
        for e in ouvertes:
            d = dispo(e)
            flux.write("| %d | `%s` | %s | %s | %s | %s | %s |\n"
                       % (e["ligne"], e["sec"][:46], marqueur(e),
                          titre_court(e).replace("|", "\\|"),
                          ("**%s**" % d["verdict_brut"]) if d else "⛔ ABSENT",
                          (d["porteur"].replace("|", "\\|")) if d else "⛔ ABSENT",
                          (d["preuve"].replace("|", "\\|")) if d else "⛔ ABSENT"))
        if a.sortie:
            flux.close()
            print("\n     manifeste ecrit : %s (%d lignes de tableau)"
                  % (a.sortie, len(ouvertes)))
        return 0

    # ── 2. CHAQUE ENTREE OUVERTE PORTE UNE DISPOSITION (AC6.4) ──────────────
    print("\n── 2. CHAQUE ENTREE OUVERTE PORTE UNE DISPOSITION (AC6.4) ────────")
    sans_dispo = []
    mauvais_verdict = []
    sans_porteur = []
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            sans_dispo.append(e)
            continue
        if d["verdict"] not in VERDICTS:
            mauvais_verdict.append((e, d["verdict_brut"]))
        if not d["porteur"]:
            sans_porteur.append(e)

    ctrl(not sans_dispo,
         "toute entree ouverte a une ligne de disposition",
         ("%d entree(s) arbitree(s)" % len(ouvertes)) if not sans_dispo
         else "⛔ %d SANS DISPOSITION : l.%s"
              % (len(sans_dispo),
                 ", l.".join(str(e["ligne"]) for e in sans_dispo[:8])
                 + (" …" if len(sans_dispo) > 8 else "")))
    ctrl(not mauvais_verdict,
         "tout verdict est l'un des CINQ",
         (" · ".join(VERDICTS)) if not mauvais_verdict
         else "⛔ %d HORS LISTE : %s"
              % (len(mauvais_verdict),
                 ", ".join("l.%d `%s`" % (e["ligne"], v)
                           for e, v in mauvais_verdict[:5])))
    # ── L'HISTOGRAMME DES VERDICTS — produit ICI, cite par le manifeste ──────
    hv = {}
    for e in ouvertes:
        d = dispo(e)
        hv[d["verdict_brut"] if d else "⛔ ABSENT"] = \
            hv.get(d["verdict_brut"] if d else "⛔ ABSENT", 0) + 1
    print("     verdicts (AC2.2)    : %s"
          % "  ".join("%s %d" % (k, v)
                      for k, v in sorted(hv.items(), key=lambda x: -x[1])))
    porteurs = {}
    for e in ouvertes:
        d = dispo(e)
        for cle in porteurs_a_venir(d) if d else []:
            porteurs[cle] = porteurs.get(cle, 0) + 1
    print("     porteurs A VENIR    : %d story(s) distincte(s) pour %d entree(s)"
          % (len(porteurs), sum(porteurs.values())))
    print("       %s" % "  ".join("%s:%d" % (k, v)
                                  for k, v in sorted(porteurs.items(),
                                                     key=lambda x: -x[1])))

    ctrl(not sans_porteur,
         "tout porteur est non vide",
         "aucun champ porteur vide" if not sans_porteur
         else "⛔ %d VIDE(S) : l.%s"
              % (len(sans_porteur),
                 ", l.".join(str(e["ligne"]) for e in sans_porteur[:8])))

    # ── 3. LE PORTEUR EST VIVANT (AC6.5) ────────────────────────────────────
    print("\n── 3. LE PORTEUR EST VIVANT (AC6.5) ──────────────────────────────")
    print("     ⚠️ un `clos par :` designe le PASSE ⇒ non soumis (voir en-tete)")
    morts = []
    inconnus = []
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            continue
        for cle in porteurs_a_venir(d):
            st = tracker.get(cle)
            if st is None:
                inconnus.append((e, cle))
            elif st in STATUTS_MORTS:
                morts.append((e, cle, st))
    ctrl(not morts,
         "aucun porteur A VENIR n'est `done`/`superseded`",
         "tracker : %d story(s) connue(s)" % len(tracker) if not morts
         else "⛔ %d MORT(S) : %s"
              % (len(morts),
                 ", ".join("l.%d→%s(%s)" % (e["ligne"], c, s)
                           for e, c, s in morts[:5])))
    ctrl(not inconnus,
         "tout porteur A VENIR existe au tracker",
         "sprint-status-desknode.yaml" if not inconnus
         else "⛔ %d INCONNU(S) : %s"
              % (len(inconnus),
                 ", ".join("l.%d→%s" % (e["ligne"], c)
                           for e, c in inconnus[:5])))

    # ── 4. LA PREUVE EST UN MOTIF, ⛔ PAS UN NUMERO (AC6.6) ──────────────────
    print("\n── 4. LA PREUVE EST UN MOTIF, ⛔ PAS UN NUMERO DE LIGNE (AC6.6) ───")
    print("     motif mesure : 0 adresse sur 192 tombe hors fichier ⇒ un")
    print("     controle de bornes rendrait `192 OK / 0 KO` sur du derive")
    nues = []
    vides = []
    for e in ouvertes:
        d = dispo(e)
        if d is None:
            continue
        if not d["preuve"]:
            vides.append(e)
        elif RE_PREUVE_NUE.match(d["preuve"]):
            nues.append((e, d["preuve"]))
    ctrl(not vides, "tout champ preuve est non vide",
         "aucun champ preuve vide" if not vides
         else "⛔ %d VIDE(S) : l.%s"
              % (len(vides), ", l.".join(str(e["ligne"]) for e in vides[:8])))
    ctrl(not nues,
         "aucune preuve n'est un PUR `fichier:ligne`",
         "aucune adresse nue" if not nues
         else "⛔ %d ADRESSE(S) NUE(S) : %s"
              % (len(nues),
                 ", ".join("l.%d `%s`" % (e["ligne"], p) for e, p in nues[:5])))

    # ── 5. LE MANIFESTE EXISTE ET CITE CE SCRIPT ────────────────────────────
    print("\n── 5. LE MANIFESTE EXISTE ET NE RECOPIE AUCUN CHIFFRE ────────────")
    p_man = os.path.join(a.cockpit, REL_MANIFESTE)
    man_ok = ctrl(os.path.isfile(p_man), "le manifeste d'arbitrage est livre",
                  REL_MANIFESTE if os.path.isfile(p_man) else "⛔ ABSENT")
    if man_ok:
        man = io.open(p_man, encoding="utf-8", errors="replace").read()
        ctrl("verif_ledger_dn416.py" in man,
             "le manifeste cite le script qui produit son compte",
             "⇒ un seul compte, ⛔ pas deux qui divergent")
        n_lig = len(re.findall(r"^\| *\d+ *\|", man, re.M))
        ctrl(n_lig == len(ouvertes),
             "le manifeste couvre 100 %% des entrees ouvertes (AC2.7)",
             "%d ligne(s) de tableau pour %d entree(s)" % (n_lig, len(ouvertes)))

    # ── 6. BILAN ────────────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS :")
    print("   · elle EXIGE un verdict, elle ne peut pas juger s'il est JUSTE ;")
    print("   · elle ne valide AUCUNE adresse `fichier:ligne` — par decision ;")
    print("   · elle ignore les %d entrees KidSat, hors perimetre ;"
          % (len(toutes) - len(dn)))
    print("   · elle ne couvre ni `bmad-dev-auto` ni `bmad-quick-dev`, qui")
    print("     ecrivent aussi au ledger par d'autres chemins.")
    print("=" * 78)
    if ko_total[0]:
        print("⛔ %d ECHEC(S) sur %d controles."
              % (ko_total[0], ok_total[0] + ko_total[0]))
    else:
        print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return 1 if ko_total[0] else 0


if __name__ == "__main__":
    sys.exit(main())
