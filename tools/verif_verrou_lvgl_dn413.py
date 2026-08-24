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


def ctrl(ok, libelle, detail=""):
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
    for nom in sorted(publiques):
        if nom not in fonctions:
            continue  # définie ailleurs (dn_widget.c, etc.)
        ligne, corps, statique = fonctions[nom]
        if statique:
            continue  # V3 : nommée dans un commentaire d'en-tête, pas publique
        chemin = chemin_vers_lvgl(nom, fonctions)
        if chemin is None:
            if "lvgl_port_lock" not in corps:
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
            else:
                verrou_hors_lvgl.append((nom, ligne))
            continue
        motif = exemption(brut_lignes, ligne)
        if motif and len(motif) >= MOTIF_MIN:
            exemptees.append((nom, ligne, motif))
        else:
            fautes.append((nom, ligne, chemin, motif))
    return (fautes, exemptees, protegees, verrou_hors_lvgl, publiques, fonctions)


def temoin_negatif(src_brut, hdr_brut):
    """On CASSE, une par une, chaque protection, et on exige un ROUGE.

    ⛔ Deux mutations distinctes, parce qu'elles ne prouvent pas la même chose :
       M1 retirer le verrou d'une fonction protégée   ⇒ la gate doit la voir
       M2 vider le motif d'une exemption existante    ⇒ la gate doit la voir
    """
    print("\n── TÉMOIN NÉGATIF — on retire les protections une par une ─────────")
    _, exemptees, protegees, hors, _, _ = auditer(src_brut, hdr_brut, bavard=False)
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
        fautes, _, _, _, _, _ = auditer("\n".join(mut), hdr_brut, bavard=False)
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
        fautes, _, _, _, _, _ = auditer("\n".join(mut), hdr_brut, bavard=False)
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
        fautes, _, _, _, _, _ = auditer("\n".join(mut), hdr_brut, bavard=False)
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
     fonctions) = auditer(src, hdr)
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

    print("\n── EXEMPTIONS MOTIVÉES ────────────────────────────────────────────")
    if not exemptees:
        print("  (aucune)")
    for nom, ligne, motif in exemptees:
        ctrl(True, "exemption motivée : %s" % nom,
             "dn_ui.c:%d — %s" % (ligne, motif[:60]))

    print("\n── CONTRÔLE PRINCIPAL ─────────────────────────────────────────────")
    for nom, ligne, chemin, motif in fautes:
        raison = "motif trop court (%d < %d c.)" % (len(motif), MOTIF_MIN) \
            if motif else "aucune exemption"
        ctrl(False, "sans verrou : %s" % nom,
             "dn_ui.c:%d — %s — %s" % (ligne, chemin, raison))
    ctrl(not fautes, "ZÉRO publique touche LVGL sans verrou",
         "%d faute(s)" % len(fautes))

    if "--temoin-negatif" in sys.argv:
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
