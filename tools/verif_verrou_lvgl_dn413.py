#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-13 / AC1.3 — « ZÉRO fonction publique de `dn_ui.h` ne touche un objet LVGL
sans verrou », JOUABLE DEPUIS WSL SANS CARTE.

======================= POURQUOI CET OUTIL EXISTE ===========================

La revue du 2026-08-24 a trouvé DEUX fonctions publiques qui lisaient un objet
LVGL hors `lvgl_port_lock` (`dn_ui_detail_courbe_axes`, `dn_ui_garde_hauteur`).
⛔ CORRIGER LES DEUX NOMMÉES ET LAISSER UNE TROISIÈME EST EXACTEMENT LE DÉFAUT
   QU'ON SOLDE : un correctif ponctuel ne prouve rien sur le reste du fichier.
   [Leçon du dépôt : « une gate scopée à UNE fonction peut épingler VERT le même
   défaut ailleurs ».]

⇒ Cet outil ne relit PAS les deux fonctions nommées. Il relit **TOUTES** les
  fonctions publiques déclarées dans `dn_ui.h`, suit leurs appels **de proche en
  proche** dans `dn_ui.c`, et rend ROUGE dès qu'un chemin atteint un `lv_*()`
  sans qu'aucun maillon n'ait pris le verrou.

🎯 CE QU'IL SAIT VOIR, ET QUE LE `grep` NE VOIT PAS :

   V1  LE CHEMIN INDIRECT. `dn_ui_cpu_maj` ne touche aucun `lv_*` : elle appelle
       `dn_ui_pc_maj`, qui appelle `case_poser`, qui en touche. Un `grep lv_`
       sur le corps la déclare saine ; elle ne l'est que parce que `dn_ui_pc_maj`
       verrouille. C'est la chaîne qu'il faut lire, pas la fonction.

   V2  LE CODE CITÉ DANS UN COMMENTAIRE. Ce dépôt écrit `lv_indev_reset()` et
       `lv_timer_enable(true)` DANS des commentaires. Un `grep` nu les compte
       comme du code et fabrique deux faux positifs — des rouges plausibles,
       la pire espèce. Les commentaires sont retirés AVANT toute analyse.

   V3  LE `static` QUI SE FAIT PASSER POUR PUBLIC. `dn_ui_flush` est nommée dans
       `dn_ui.h`... à l'intérieur d'un commentaire. Elle est `static` dans le
       `.c`. Elle n'est donc PAS une fonction publique, et l'exiger sous verrou
       serait exiger un interblocage : LVGL l'appelle en tenant déjà le verrou.

⚖️ L'EXEMPTION EXISTE, MAIS ELLE SE PAIE EN ÉCRIT. Une fonction publique peut
   légitimement toucher LVGL sans verrou (rappel LVGL, chemin de flush...). Elle
   doit alors porter, dans le commentaire qui la précède immédiatement, le jeton

       VERROU-LVGL-EXEMPT: <motif d'au moins 40 caractères>

   ⛔ Le jeton SEUL ne suffit pas : un motif vide ou télégraphique est REFUSÉ.
      Une exemption non motivée est une garde décorative, et ce dépôt en solde
      justement une famille (AC8).

🔴 TÉMOIN NÉGATIF INTÉGRÉ — `--temoin-negatif`. On retire, une par une, l'appel
   `lvgl_port_lock` de chaque fonction publique aujourd'hui protégée, et on
   VÉRIFIE QUE LA GATE ROUGIT. Une gate qu'aucun test n'a vue échouer est
   décorative (AC7.5) ; celle-ci se voit échouer autant de fois qu'il y a de
   verrous à protéger.

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES
(piège n°11 : un `.pyc` périmé a déjà fait conclure ROUGE sur un arbre SAIN).
"""

import hashlib
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(RACINE, "firmware", "desknode", "main")
DN_UI_C = os.path.join(MAIN, "dn_ui.c")
DN_UI_H = os.path.join(MAIN, "dn_ui.h")

JETON_EXEMPT = "VERROU-LVGL-EXEMPT:"
MOTIF_MIN = 40

ok_total = [0]
ko_total = [0]


def lire(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    return brut.decode("utf-8"), hashlib.sha256(brut).hexdigest()[:16]


# 🔴 dn4-40 / AC40.7.c — L'INSTRUMENT DE CAMPAGNE, ⛔ PAS UN CHANGEMENT DE
# FORMAT. Import DEFENSIF : une gate reste jouable si son instrument manque.
# Sans `DN_TRACE_CTRL`, la console sort a l'octet pres comme avant.
try:
    import dn_trace
except ImportError:                                  # pragma: no cover
    dn_trace = None


def ctrl(ok, libelle, detail=""):
    if dn_trace is not None:
        dn_trace.trace(ok, libelle)
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return ok


def decommenter(txt):
    """Retire commentaires C et littéraux chaîne EN PRÉSERVANT LES LIGNES.

    ⛔ Le remplacement conserve les `\\n` : sans ça, tout numéro de ligne publié
       par cet outil désignerait une autre ligne du fichier — un instrument qui
       ment sur l'endroit vaut moins que pas d'instrument."""

    def blanchir(m):
        return re.sub(r"[^\n]", " ", m.group(0))

    txt = re.sub(r"/\*.*?\*/", blanchir, txt, flags=re.S)
    txt = re.sub(r"//[^\n]*", blanchir, txt)
    txt = re.sub(r'"(?:\\.|[^"\\\n])*"', blanchir, txt)
    return txt


def corps_fonctions(code):
    """{nom: (ligne, corps, statique)} pour toute définition de `code`.

    `code` est DÉJÀ décommenté. On n'accepte qu'une définition ancrée en colonne
    0 (style du dépôt) et suivie d'un `{` : ça écarte les prototypes, les appels
    et les initialiseurs de table."""
    out = {}
    motif = re.compile(
        r"^(static\s+)?[A-Za-z_][A-Za-z0-9_ \*]*?\b([a-zA-Z_][a-zA-Z0-9_]*)\s*"
        r"\([^;{]*?\)\s*\{", re.M)
    for m in motif.finditer(code):
        nom = m.group(2)
        statique = m.group(1) is not None
        i = code.find("{", m.end() - 1)
        prof, j = 0, i
        while j < len(code):
            if code[j] == "{":
                prof += 1
            elif code[j] == "}":
                prof -= 1
                if prof == 0:
                    break
            j += 1
        ligne = code[:m.start()].count("\n") + 1
        if nom not in out:
            out[nom] = (ligne, code[i:j + 1], statique)
    return out


def declarations_publiques(entete_code):
    """Les `dn_ui_*` réellement DÉCLARÉES (prototype `;`) dans `dn_ui.h`."""
    return set(re.findall(r"\b(dn_ui_[a-z0-9_]+)\s*\([^;{]*?\)\s*;",
                          entete_code, re.S))


RE_LV = re.compile(r"\blv_[a-z0-9_]+\s*\(")
RE_APPEL = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")

# 🔴 REVUE DU 2026-08-25 — UN OBJET LVGL SE TOUCHE AUSSI PAR DÉRÉFÉRENCE.
#    `RE_LV` ne voyait que l'APPEL `lv_xxx(`. Or `dn_ui.c` lit `s_det_serie0->hidden`
#    — un champ de `lv_chart_private.h`, donc un objet LVGL — SANS aucun `lv_*()`.
#    Mutation jouée à la revue : retirer le verrou ET les deux
#    `lv_chart_get_series_color()` en laissant les `->hidden` ⇒ la gate rendait
#    `exit 0`, et la fonction n'était même pas NOMMÉE. Le motif « lire un champ
#    privé plutôt qu'appeler un getter » venait d'être introduit par `dn4-13` :
#    il est donc appelé à se reproduire.
RE_LV_PTR_DECL = re.compile(r"\blv_[a-z0-9_]+_t\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)")


def pointeurs_lvgl(code):
    """Les identifiants déclarés `lv_xxx_t *` quelque part dans le source."""
    return set(RE_LV_PTR_DECL.findall(code))


def acces_lvgl(corps, noms_lvgl):
    """Positions de CHAQUE accès à un objet LVGL — appel `lv_*(` ET `ptr->`."""
    pos = [m.start() for m in RE_LV.finditer(corps)]
    if noms_lvgl:
        rx = re.compile(r"\b(" + "|".join(sorted(re.escape(n) for n in noms_lvgl))
                        + r")\s*->")
        pos += [m.start() for m in rx.finditer(corps)]
    return sorted(pos)


def verrou_defauts(corps, noms_lvgl):
    """🔴 CE QUE LA **PRÉSENCE** DE `lvgl_port_lock` NE PROUVE PAS.

    La gate coupait la branche sur `if "lvgl_port_lock" in corps` — un test de
    SOUS-CHAÎNE. Trois mutations survivaient, toutes jouées à la revue du
    2026-08-25 :
      · lire `lv_screen_active()` AVANT le verrou      ⇒ 0 faute (défaut d'AC1.1)
      · `(void)lvgl_port_lock(1000);` au lieu du test  ⇒ vert   (défaut d'AC1.2)
      · retirer le `lvgl_port_unlock()` d'un `return`  ⇒ exit 0 (verrou FUITÉ,
        et un verrou fuité GÈLE LA TÂCHE LVGL ENTIÈRE — panne muette)
    ⚠️ LIMITE DÉCLARÉE : le test (a) reconnaît la forme directe
       `if (!lvgl_port_lock(...))`. La forme `bool ok = lvgl_port_lock(...);`
       suivie d'un `if (!ok)` plus loin n'est PAS reconnue — elle n'existe pas
       dans ce dépôt aujourd'hui, et la gate le DIT plutôt que de le taire.
    """
    d = []
    locks = [m.start() for m in re.finditer(r"\blvgl_port_lock\s*\(", corps)]
    if not locks:
        return d

    # (a) le RETOUR du verrou est-il TESTÉ ?
    if not re.search(r"if\s*\(\s*!?\s*lvgl_port_lock\s*\(", corps):
        d.append("retour de `lvgl_port_lock` IGNORÉ — un échec de verrou "
                 "poursuit et déréférence quand même")

    # (b) un objet LVGL touché AVANT la première prise ?
    for p in acces_lvgl(corps, noms_lvgl):
        if p < locks[0]:
            d.append("objet LVGL touché AVANT `lvgl_port_lock` — "
                     "« LE VERROU EST PRIS AVANT DE LIRE L'OBJET » (AC1.1)")
            break

    # (c) une sortie VERROU TENU ? Les `return` de la garde d'échec sont exempts.
    exempts = [(m.start(1), m.end(1)) for m in re.finditer(
        r"if\s*\(\s*!\s*lvgl_port_lock\s*\([^()]*\)\s*\)\s*"
        r"(\{[^{}]*\}|[^;{}]*;)", corps)]
    evts = [(m.start(), "L") for m in re.finditer(r"\blvgl_port_lock\s*\(", corps)]
    evts += [(m.start(), "U") for m in re.finditer(r"\blvgl_port_unlock\s*\(", corps)]
    evts += [(m.start(), "R") for m in re.finditer(r"\breturn\b", corps)]
    prof = 0
    for p, k in sorted(evts):
        if k == "L":
            prof += 1
        elif k == "U":
            prof -= 1
        elif prof > 0 and not any(a <= p < b for a, b in exempts):
            d.append("`return` atteint VERROU TENU — la tâche LVGL gèle "
                     "(libération sur TOUS les chemins de sortie, AC1.1)")
            break
    if prof > 0:
        d.append("fin de fonction VERROU TENU (%d prise(s) non libérée(s))" % prof)
    return d


def chemin_vers_lvgl(nom, fonctions, vus=None):
    """Le premier chemin `nom -> ... -> lv_xxx()` qui ne rencontre AUCUN verrou.

    Rend `None` si tout chemin est verrouillé (ou n'atteint jamais LVGL).
    ⚠️ Un maillon qui prend le verrou COUPE la branche : c'est lui qui protège,
       et exiger un second verrou en amont serait exiger un interblocage."""
    if vus is None:
        vus = set()
    if nom in vus or nom not in fonctions:
        return None
    vus = vus | {nom}
    _, corps, _ = fonctions[nom]
    if "lvgl_port_lock" in corps:
        return None
    m = RE_LV.search(corps)
    if m:
        return "%s [%s]" % (nom, m.group(0).rstrip("("))
    for appel in dict.fromkeys(RE_APPEL.findall(corps)):
        if appel == nom or appel not in fonctions:
            continue
        sous = chemin_vers_lvgl(appel, fonctions, vus)
        if sous:
            return "%s -> %s" % (nom, sous)
    return None


def exemption(brut_lignes, ligne_def):
    """Le motif d'exemption du bloc de commentaire qui PRÉCÈDE la définition.

    On remonte tant qu'on est dans du commentaire ou du vide ; on s'arrête sur
    la première ligne de code réel. ⇒ Un jeton posé 200 lignes plus haut, dans
    le commentaire d'une AUTRE fonction, ne peut pas couvrir celle-ci."""
    i = ligne_def - 2  # index 0-based de la ligne juste au-dessus
    bloc = []
    dans_bloc = False
    while i >= 0:
        t = brut_lignes[i].strip()
        if t.endswith("*/"):
            dans_bloc = True
        if dans_bloc or t.startswith("*") or t.startswith("/*") \
                or t.startswith("//") or t == "":
            bloc.append(brut_lignes[i])
            if t.startswith("/*"):
                dans_bloc = False
                if not t.endswith("*/"):
                    pass
            i -= 1
            continue
        break
    texte = "\n".join(reversed(bloc))
    k = texte.find(JETON_EXEMPT)
    if k < 0:
        return None
    motif = texte[k + len(JETON_EXEMPT):]
    motif = re.sub(r"[\n\r\*/]", " ", motif)
    motif = re.sub(r"\s+", " ", motif).strip()
    return motif


def auditer(src_brut, hdr_brut, bavard=True):
    """Rend la liste des (nom, ligne, chemin) publiques SANS verrou NI exemption."""
    code = decommenter(src_brut)
    hdr = decommenter(hdr_brut)
    fonctions = corps_fonctions(code)
    publiques = declarations_publiques(hdr)
    brut_lignes = src_brut.split("\n")

    fautes, exemptees, protegees, verrou_hors_lvgl = [], [], [], []
    # 🔴 REVUE 2026-08-25 — CE QUI ÉTAIT ÉCARTÉ EN SILENCE EST DÉSORMAIS COMPTÉ.
    #    71 des 111 publiques tombaient dans un `continue` muet, sans être même
    #    nommées — alors que la gate se félicitait de nommer les 5 autres.
    sans_lvgl = []
    noms_lvgl = pointeurs_lvgl(code)
    for nom in sorted(publiques):
        if nom not in fonctions:
            continue  # définie ailleurs (dn_widget.c, etc.)
        ligne, corps, statique = fonctions[nom]
        if statique:
            continue  # V3 : nommée dans un commentaire d'en-tête, pas publique
        chemin = chemin_vers_lvgl(nom, fonctions)
        if chemin is None:
            if "lvgl_port_lock" not in corps:
                # ⚠️ Pas de verrou et aucun chemin vers `lv_*()`. MAIS elle peut
                #    quand même toucher un objet LVGL PAR DÉRÉFÉRENCE.
                if acces_lvgl(corps, noms_lvgl):
                    fautes.append((nom, ligne,
                                   "%s [déréférence d'objet LVGL, SANS verrou "
                                   "et sans appel `lv_*()`]" % nom, None))
                else:
                    sans_lvgl.append((nom, ligne))
                continue
            # Elle verrouille. Mais protège-t-elle un OBJET LVGL, ou autre chose ?
            # On le tranche en RETIRANT le verrou dans une copie de travail : si
            # un chemin vers `lv_*` apparaît, le verrou couvrait bien LVGL.
            sans = dict(fonctions)
            sans[nom] = (ligne, corps.replace("lvgl_port_lock", "verrou_neutralise"),
                         statique)
            fin = ligne + corps.count("\n")
            if chemin_vers_lvgl(nom, sans):
                protegees.append((nom, ligne, fin))
                # 🔴 Elle VERROUILLE. Mais le verrou est-il pris AVANT l'objet,
                #    son retour TESTÉ, et libéré sur TOUS les chemins ?
                for defaut in verrou_defauts(corps, noms_lvgl):
                    fautes.append((nom, ligne, "%s [%s]" % (nom, defaut), None))
            else:
                verrou_hors_lvgl.append((nom, ligne))
            continue
        motif = exemption(brut_lignes, ligne)
        if motif and len(motif) >= MOTIF_MIN:
            exemptees.append((nom, ligne, motif))
        else:
            fautes.append((nom, ligne, chemin, motif))
    return (fautes, exemptees, protegees, verrou_hors_lvgl, publiques,
            fonctions, sans_lvgl)


def temoin_negatif(src_brut, hdr_brut):
    """On CASSE, une par une, chaque protection, et on exige un ROUGE.

    ⛔ Deux mutations distinctes, parce qu'elles ne prouvent pas la même chose :
       M1 retirer le verrou d'une fonction protégée   ⇒ la gate doit la voir
       M2 vider le motif d'une exemption existante    ⇒ la gate doit la voir
    """
    print("\n── TÉMOIN NÉGATIF — on retire les protections une par une ─────────")
    _, exemptees, protegees, hors, _, _, _ = auditer(src_brut, hdr_brut,
                                                     bavard=False)
    lignes = src_brut.split("\n")
    n_mut = 0

    print("  (%d hors périmètre — verrou sans objet LVGL — non mutées)"
          % len(hors))
    for nom, ligne, fin in protegees:
        # M1 : on neutralise TOUS les `lvgl_port_lock` du corps de `nom`.
        # ⛔ PAS SEULEMENT LE PREMIER — `dn_ui_bg_psram` en porte DEUX (un par
        #    branche). N'en casser qu'un laissait la fonction protégée, la gate
        #    restait verte À RAISON, et le témoin comptait ça comme un ÉCHEC DE
        #    LA GATE. C'était le témoin qui était faux, pas la gate : mesuré et
        #    corrigé le 2026-08-25.
        mut = list(lignes)
        cibles = [i for i in range(ligne - 1, min(fin + 1, len(mut)))
                  if "lvgl_port_lock" in mut[i]]
        if not cibles:
            continue
        for i in cibles:
            mut[i] = mut[i].replace("lvgl_port_lock", "verrou_neutralise")
        cible = cibles[0]
        fautes, _, _, _, _, _, _ = auditer("\n".join(mut), hdr_brut, bavard=False)
        n_mut += 1
        ctrl(any(f[0] == nom for f in fautes),
             "M1 sans verrou, `%s` ROUGIT" % nom,
             "%d verrou(x) neutralisé(s), l.%d" % (len(cibles), cible + 1))

    for nom, ligne, _motif in exemptees:
        # M2 : on vide le motif de l'exemption (le jeton reste).
        mut = list(lignes)
        cible = None
        for i in range(max(0, ligne - 60), ligne):
            if JETON_EXEMPT in mut[i]:
                cible = i
                break
        if cible is None:
            continue
        for i in range(cible, ligne - 1):
            mut[i] = " *" if JETON_EXEMPT not in mut[i] else \
                mut[i][:mut[i].find(JETON_EXEMPT) + len(JETON_EXEMPT)]
        fautes, _, _, _, _, _, _ = auditer("\n".join(mut), hdr_brut, bavard=False)
        n_mut += 1
        ctrl(any(f[0] == nom for f in fautes),
             "M2 motif vidé, `%s` ROUGIT" % nom, "ligne %d" % (cible + 1))

    n_mut += temoin_exemption(src_brut, hdr_brut, protegees)

    if n_mut == 0:
        ctrl(False, "le témoin négatif a MUTÉ QUELQUE CHOSE",
             "0 mutation jouée — la gate ne prouve rien")
    return n_mut


def temoin_exemption(src_brut, hdr_brut, protegees):
    """M3 — LA PORTE DE SORTIE EST ÉPROUVÉE DANS LES DEUX SENS.

    Le dépôt ne porte aujourd'hui AUCUNE exemption : le chemin `JETON_EXEMPT`
    n'est donc jamais exécuté par la gate en régime. ⛔ Un chemin qu'aucun test
    n'emprunte est décoratif — et c'est précisément la famille qu'AC7.5 solde.
    On le force donc sur un cas FABRIQUÉ, et on exige les TROIS réponses :
      A  verrou retiré, pas d'exemption      ⇒ ROUGE
      B  verrou retiré + exemption motivée   ⇒ VERT   (la porte s'ouvre)
      C  verrou retiré + jeton sans motif    ⇒ ROUGE  (elle ne s'ouvre pas seule)
    """
    print("\n── TÉMOIN NÉGATIF M3 — la porte d'exemption, dans les deux sens ───")
    cible = None
    for nom, ligne, fin in protegees:
        if nom == "dn_ui_detail_courbe_axes":
            cible = (nom, ligne, fin)
            break
    if cible is None:
        ctrl(False, "M3 a trouvé sa fonction cible", "dn_ui_detail_courbe_axes")
        return 0
    nom, ligne, fin = cible
    lignes = src_brut.split("\n")

    base = list(lignes)
    for i in range(ligne - 1, min(fin + 1, len(base))):
        base[i] = base[i].replace("lvgl_port_lock", "verrou_neutralise")

    def rouge(mut):
        fautes, _, _, _, _, _, _ = auditer("\n".join(mut), hdr_brut, bavard=False)
        return any(f[0] == nom for f in fautes)

    ctrl(rouge(base), "M3-A verrou retiré, sans exemption ⇒ ROUGE", nom)

    motif_long = ("appelée par LVGL elle-même, qui tient déjà le verrou — le "
                  "reprendre serait un interblocage")
    b = list(base)
    b.insert(ligne - 1, "/* %s %s */" % (JETON_EXEMPT, motif_long))
    ctrl(not rouge(b), "M3-B exemption MOTIVÉE (%d c.) ⇒ VERT" % len(motif_long),
         nom)

    c = list(base)
    c.insert(ligne - 1, "/* %s court */" % JETON_EXEMPT)
    ctrl(rouge(c), "M3-C jeton SANS motif suffisant ⇒ ROUGE", "5 c. < %d" % MOTIF_MIN)
    return temoin_negatif_m4(src_brut, hdr_brut, cible)


def temoin_negatif_m4(src_brut, hdr_brut, cible):
    """🔴 M4 — CE QUE LA **PRÉSENCE** DU VERROU NE PROUVAIT PAS.

    Ajouté par la revue de code du 2026-08-25. Les trois premières mutations
    sont EXACTEMENT celles que la revue a jouées à la main et qui SURVIVAIENT :
    la gate coupait sa branche sur `if "lvgl_port_lock" in corps`, un test de
    SOUS-CHAÎNE, donc l'ordre, le retour et la libération n'étaient jamais vus.
    ⛔ Sans ces quatre témoins, les contrôles ajoutés le 2026-08-25 seraient
       eux-mêmes DÉCORATIFS — c'est la famille que `dn4-13` solde.
    """
    print("\n── TÉMOIN NÉGATIF M4 — portée, ordre, libération, déréférence ─────")
    if cible is None:
        ctrl(False, "M4 a trouvé sa fonction cible", "aucune")
        return 0
    nom, ligne, fin = cible
    lignes = src_brut.split("\n")
    haut, bas = ligne - 1, min(fin + 1, len(lignes))

    def rouge(mut):
        fautes, _, _, _, _, _, _ = auditer("\n".join(mut), hdr_brut, bavard=False)
        return any(f[0] == nom for f in fautes)

    def muter(remplacements, inserer=None):
        m = list(lignes)
        for i in range(haut, bas):
            for a, b in remplacements:
                m[i] = m[i].replace(a, b)
        if inserer:
            for i in range(haut, bas):
                if "lvgl_port_lock" in m[i]:
                    m.insert(i, inserer)
                    break
        return m

    # M4-A — l'objet est LU AVANT la prise du verrou (le défaut d'AC1.1).
    ctrl(rouge(muter([], inserer="    lv_obj_invalidate(s_det_courbe);")),
         "M4-A objet LVGL lu AVANT le verrou ⇒ ROUGE", nom)

    # M4-B — le RETOUR du verrou n'est plus testé (le défaut d'AC1.2).
    ctrl(rouge(muter([("if (!lvgl_port_lock", "if (0 && !lvgl_port_lock")])),
         "M4-B retour de `lvgl_port_lock` IGNORÉ ⇒ ROUGE", nom)

    # M4-C — le verrou FUITE sur un chemin de sortie : la tâche LVGL gèle.
    ctrl(rouge(muter([("lvgl_port_unlock();", "/* fuite */")])),
         "M4-C `return` atteint VERROU TENU ⇒ ROUGE", nom)

    # M4-D — plus aucun appel `lv_*()`, plus de verrou, mais un `->` sur un
    #        objet LVGL : c'est le motif que `dn4-13` vient d'introduire.
    ctrl(rouge(muter([("lvgl_port_lock", "verrou_neutralise"),
                      ("lv_chart_get_series_color(", "zero_couleur(")])),
         "M4-D déréférence `ptr->` sans verrou ni `lv_*()` ⇒ ROUGE", nom)
    return 4
    return 3


def main():
    src, sha_c = lire(DN_UI_C)
    hdr, sha_h = lire(DN_UI_H)
    print("=" * 78)
    print("dn4-13 / AC1.3 — LE VERROU LVGL SUR TOUTE LA SURFACE PUBLIQUE")
    print("=" * 78)
    print("  dn_ui.c sha256[:16] = %s" % sha_c)
    print("  dn_ui.h sha256[:16] = %s" % sha_h)

    (fautes, exemptees, protegees, hors_lvgl, publiques,
     fonctions, sans_lvgl) = auditer(src, hdr)
    definies = [n for n in publiques if n in fonctions]
    print("\n  %d fonctions publiques déclarées dans dn_ui.h, %d définies ici."
          % (len(publiques), len(definies)))
    print("  %d touchent un objet LVGL SOUS VERROU — c'est la population que la"
          % len(protegees))
    print("     gate couvre, et le témoin négatif les casse une par une.")
    print("\n  ⚠️ %d AUTRES fonctions publiques prennent `lvgl_port_lock` SANS"
          % len(hors_lvgl))
    print("     jamais atteindre un `lv_*()` : leur verrou protège AUTRE CHOSE")
    print("     (un tuple de statiques écrit par la tâche LVGL, un cycle en vol).")
    print("     ⛔ CETTE GATE NE LES COUVRE PAS, et ne le prétend pas — le retrait")
    print("        de leur verrou ne produirait AUCUN rouge ici. Elles sont")
    print("        NOMMÉES plutôt que passées sous silence :")
    for nom, ligne in hors_lvgl:
        print("        · %-34s dn_ui.c:%d" % (nom, ligne))

    print("\n── ÉCARTÉES : NI VERROU, NI OBJET LVGL ────────────────────────────")
    print("     🔴 REVUE 2026-08-25 — ELLES SONT COMPTÉES, ⛔ PLUS AVALÉES.")
    print("        Elles tombaient dans un `continue` MUET : ni verrou, ni appel")
    print("        `lv_*()`, ni déréférence d'objet LVGL. La gate en écartait la")
    print("        MAJORITÉ sans les nommer, pendant qu'elle se félicitait de")
    print("        nommer les %d « hors périmètre ». Un audit qui ne dit pas ce" % len(hors_lvgl))
    print("        qu'il n'a PAS regardé ne se relit pas.")
    print("     %d publique(s) écartée(s) : %s"
          % (len(sans_lvgl), ", ".join(n for n, _ in sans_lvgl[:8])
             + (" …" if len(sans_lvgl) > 8 else "")))
    # ⛔ AUCUNE PUBLIQUE NE DOIT DISPARAÎTRE DU COMPTE : le total des quatre
    #    familles + les non-définies-ici doit retomber sur les déclarations.
    vues = (len(fautes) + len(exemptees) + len(protegees) + len(hors_lvgl)
            + len(sans_lvgl))
    ailleurs = sum(1 for n in publiques
                   if n not in fonctions or fonctions[n][2])
    ctrl(vues + ailleurs >= len(publiques),
         "AUCUNE publique ne disparaît du compte",
         "%d classées + %d définies ailleurs ⇒ %d déclarées"
         % (vues, ailleurs, len(publiques)))

    print("\n── EXEMPTIONS MOTIVÉES ────────────────────────────────────────────")
    if not exemptees:
        print("  (aucune)")

# ⚠️ dn4-40 / AC40.2 — CE N'ETAIT PAS UN CONTROLE. Un `ctrl(True, …)`
#    litteral qu'aucun arbre defaillant ne peut faire rougir ne GARDE rien :
#    il gonfle le bilan. Le tri (`tools/campagne_ctrl_dn440.py`) l'a classe
#    par MUTANT, ⛔ pas par raisonnement. Le fait qu'il publiait reste dit —
#    il est imprime, ⛔ il n'est plus compte.
    for nom, ligne, motif in exemptees:
        print("  exemption motivée : %-38s dn_ui.c:%d — %s"
              % (nom, ligne, motif[:60]))

    print("\n── CONTRÔLE PRINCIPAL ─────────────────────────────────────────────")
    for nom, ligne, chemin, motif in fautes:
        raison = "motif trop court (%d < %d c.)" % (len(motif), MOTIF_MIN) \
            if motif else "aucune exemption"
        ctrl(False, "sans verrou : %s" % nom,
             "dn_ui.c:%d — %s — %s" % (ligne, chemin, raison))
    ctrl(not fautes, "ZÉRO publique touche LVGL sans verrou",
         "%d faute(s)" % len(fautes))

    # 🔴 REVUE 2026-08-25 — LE TÉMOIN NÉGATIF N'EST PLUS OPTIONNEL.
    #    Il était derrière `if "--temoin-negatif" in sys.argv`, et `grep` sur
    #    TOUT le dépôt montrait qu'AUCUN runner ne passait le drapeau : en
    #    invocation nominale cette gate publiait UN SEUL contrôle, et ce contrôle
    #    n'avait JAMAIS été vu rougir. C'est la définition d'AC7.5 (« une gate
    #    qu'aucun test n'a vue échouer est décorative ») appliquée à AC1.3.
    temoin_negatif(src, hdr)

    print("\n" + "=" * 78)
    if ko_total[0] == 0:
        print("✅ %d contrôles passent, 0 échec." % ok_total[0])
        return 0
    print("⛔ %d ÉCHEC(S) sur %d contrôles."
          % (ko_total[0], ok_total[0] + ko_total[0]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
