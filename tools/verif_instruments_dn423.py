#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-23 / AC8 — LES INSTRUMENTS DISENT QUAND ILS MENTENT, ET C'EST GARDÉ.
Jouable depuis WSL, ⛔ SANS CARTE.

======================= CE QUE CET OUTIL FAIT ==============================

Il garde les DEUX ÉTAGES de la chaîne, parce que le défaut est de FAMILLE et
qu'il vit sur les deux :

  · **l'hôte** (`tools/dn_console.py`, `tools/dn_injecteur.py`) — le pilote ne
    lisait NI le refus NI la perte de lignes ; deux fenêtres de 90 s ont rendu
    **0** sur un stimulus qui n'a JAMAIS tourné ;
  · **la carte** (`firmware/desknode/main/dn_console.c`) — la commande RÉCITAIT
    au lieu de RELIRE (`6 × 35 100 px` sur une aire de 36 675), ou BLOQUAIT ce
    qu'elle mesure (`cpu N` publiait 0,8 % sous trafic contre 0,9 % au repos).

⇒ **Les deux se gardent ensemble ou pas du tout** : un compteur de lignes
  imprimé par la carte ne sert à rien si le pilote ne le lit pas, et
  réciproquement. Le contrôle du MIROIR (`bloc_miroir`) est celui-là.

============ LES QUATRE RÈGLES QUE CETTE GATE S'APPLIQUE À ELLE-MÊME =========

(1) 🔴 **CHAQUE CONTRÔLE DOIT POUVOIR ROUGIR.** La question posée de chaque
    ligne est *« qu'est-ce qui la ferait rougir ? »*. Si rien, elle ne compte
    pas. ⛔ Un `N OK / 0 KO` peut épingler du code FAUX — mesuré **trois fois**
    sur cette base de code. Les mutants sont au PV : `mesures/dn4-23/T8-mutants.txt`.

(2) ⛔ **NE PAS CODER EN DUR CE QUI SE GARDE GÉNÉRIQUEMENT.** `dn4-16` a payé
    exactement ça : une gate qui exigeait SA propre clé rendait « SANS
    DISPOSITION » sur la première entrée d'un autre auteur — un rouge au
    diagnostic FAUX. Ici les bornes de `k_metriques[]` sont **RELUES** de
    `dn_link.c`, le format du compteur est **EXTRAIT** du `printf` du firmware,
    et la règle du `35 100` est une **forme** (« etait 35 100 a … »), ⛔ pas une
    liste de lignes.

(3) ⛔ **NE PAS COMPARER UN TOTAL.** Un contrôle qui teste `count(motif) == 3`
    est satisfait par une ligne fabriquée n'importe où. Ici tout se **localise**
    dans une FONCTION ou dans une BRANCHE (`corps_fonction`, `branche_argv1`),
    et le mutant le démontre.

(4) ⛔ **`grep -c` sort en 1 quand le compte est 0** — d'où le Python pur, sans
    dépendance.

Sortie : `[OK ]` / `[KO ]`, `BILAN : n OK, m KO`, rc 0 / 1.
Option : `--racine <chemin>` — joue la gate sur un ARBRE MUTÉ (c'est ainsi que
le PV des mutants est produit). Défaut : le dépôt qui la contient.
"""

import argparse
import os
import re
import subprocess
import sys

OK = [0]
KO = [0]


def ctrl(bon, libelle, detail=""):
    if bon:
        OK[0] += 1
        print("  [OK ] %-58s %s" % (libelle, detail))
    else:
        KO[0] += 1
        print("  [KO ] %-58s %s" % (libelle, detail))
    return bon


def lire(chemin):
    try:
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        # ⛔ Un contrôle qui ne peut pas LIRE ne dit PAS « rien à signaler ».
        print("  [KO ] fichier ILLISIBLE : %s" % chemin)
        print("        %s" % e)
        KO[0] += 1
        return None


# ── LOCALISATION : ⛔ on ne cherche JAMAIS dans le fichier entier ────────────
def corps_fonction(src, signature):
    """Le corps `{ … }` de la fonction dont la SIGNATURE est donnée (le texte
    exact qui précède l'accolade ouvrante). ⛔ Comptage d'accolades naïf : il
    suffit ici parce qu'aucune de ces fonctions ne porte d'accolade dans une
    chaîne — et la gate le VÉRIFIE en exigeant que le corps se referme."""
    i = src.find(signature)
    if i < 0:
        return None
    j = src.find("{", i)
    if j < 0:
        return None
    prof, k = 0, j
    while k < len(src):
        if src[k] == "{":
            prof += 1
        elif src[k] == "}":
            prof -= 1
            if prof == 0:
                return src[j:k + 1]
        k += 1
    return None


def corps_python(src, signature):
    """Le corps d'une fonction PYTHON, par INDENTATION.

    🔴 PREMIÈRE RÉDACTION FAUSSE, ET ELLE A ÉTÉ VUE ROUGIR : cette gate
       appliquait `corps_fonction()` (comptage d'ACCOLADES, écrit pour le C) à
       `dn_console.py`. Sur du Python, la première `{` rencontrée est un dict —
       le « corps » extrait était donc un littéral, et **onze contrôles
       rougissaient sur du code JUSTE**. ⛔ C'est « une gate `N OK / 0 KO` peut
       épingler du code FAUX », dans l'autre sens : un ROUGE au diagnostic FAUX.
    """
    m = re.search(r"^" + re.escape(signature), src, re.M)
    if not m:
        return None
    lignes = src[m.start():].split("\n")
    out = [lignes[0]]
    for l in lignes[1:]:
        if l.strip() and not l.startswith((" ", "\t")):
            break
        out.append(l)
    return "\n".join(out)


def printfs(src):
    """Les LITTÉRAUX que le firmware IMPRIME — ⛔ pas ses commentaires.

    🔴 MOTIF PAYÉ PAR CE DÉPÔT : *« le jeton d'exemption d'une gate n'a aucun
       échappement — le citer dans un commentaire l'accorde »*. Le symétrique
       est vrai : un contrôle qui cherche dans le fichier entier ROUGIT sur le
       commentaire qui EXPLIQUE le correctif. Vu ici sur `dn3-3` : le message
       est retiré, et le commentaire qui dit pourquoi le nommait encore.
    """
    return re.findall(r'printf\(\s*"((?:[^"\\]|\\.)*)"', src)


def branche_argv1(src, fonction_sig, mot, argc=None):
    """Le corps d'une branche `if (… strcmp(argv[1], "<mot>") == 0)` DANS une
    fonction donnée. C'est l'unité de localisation des sous-commandes : sans
    elle, un contrôle sur `widget piste` serait satisfait par n'importe quelle
    autre branche du même fichier de 11 000 lignes."""
    corps = corps_fonction(src, fonction_sig)
    if corps is None:
        return None
    motif = r'strcmp\(argv\[1\],\s*"%s"\)\s*==\s*0' % re.escape(mot)
    for m in re.finditer(motif, corps):
        if argc is not None:
            # remonter au `if (` de la branche pour lire sa garde d'argc
            deb = corps.rfind("if (", 0, m.start())
            tete = corps[deb:m.start()]
            if ("argc == %d" % argc) not in tete and \
               ("argc >= %d" % argc) not in tete:
                continue
        j = corps.find("{", m.end())
        if j < 0:
            continue
        prof, k = 0, j
        while k < len(corps):
            if corps[k] == "{":
                prof += 1
            elif corps[k] == "}":
                prof -= 1
                if prof == 0:
                    return corps[j:k + 1]
            k += 1
    return None


def sans_commentaires_c(src):
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def joue(argv, cwd):
    """Joue un témoin en SOUS-PROCESSUS et rend (rc, sortie)."""
    try:
        p = subprocess.run([sys.executable] + argv, cwd=cwd,
                           capture_output=True, text=True, timeout=300)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:      # noqa: BLE001 — on veut le MOTIF, pas le type
        return 99, "exception : %s" % e


# ═══════════════════════════════════════════════════════════════════════════
def bloc_refus(py):
    """AC1 — LE REFUS EST LU, ET IL ARME LE CODE DE RETOUR."""
    print("\n── AC1 : un harnais qui pose une commande LIT LE REFUS ─────────")
    exiges = ["Unrecognized command", "non-zero error code", "ESP_ERR_",
              "Internal error"]
    tbl = re.search(r"MOTIFS_REFUS\s*=\s*\((.*?)\n\)", py, re.S)
    ctrl(tbl is not None, "`MOTIFS_REFUS` est une table LOCALISABLE",
         "⛔ pas des `in` dispersés")
    corps = tbl.group(1) if tbl else ""
    for mot in exiges:
        ctrl(mot in corps, "…et elle porte « %s »" % mot,
             "REPL ESP-IDF" if mot != "ESP_ERR_" else "esp_err_to_name")
    ctrl(re.search(r'refus\(\?:\S*\)\\s\*:', corps) is not None
         or r"\s*:" in corps,
         "…et le motif français EXIGE le « : »",
         "⛔ sinon « (refuse hors bornes) » est un refus")

    res = corps_python(py, "def _resultat(")
    ctrl(res is not None, "`_resultat()` est localisable", "")
    res = res or ""
    ctrl("chercher_refus(" in res,
         "`_resultat()` APPELLE `chercher_refus`", "⛔ pas seulement défini")
    ctrl('"refus"' in res and '"refus_motifs"' in res,
         "…et pose `refus` (LE MOTIF) et `refus_motifs`",
         "⛔ pas un booléen nu")
    ctrl("completude(" in res, "…et `completude()` y est appelée aussi",
         "AC2.2 : un compteur non lu ne compte pas")

    mn = corps_python(py, "def main(")
    ctrl(mn is not None, "`main()` est localisable", "")
    mn = mn or ""
    ctrl(re.search(r'if r\["refus"\][^\n]*\n\s*code = 1', mn) is not None
         or re.search(r'if r\["refus"\].*?:\s*\n\s*code = 1', mn, re.S) is not None,
         "…et un refus ARME le code de retour dans `main()`",
         "au même titre qu'une invite non rendue")
    ctrl('r["completude"]["etat"] == "PERTE"' in mn and "code = 1" in mn,
         "…et une PERTE de lignes l'arme aussi", "⛔ pas les étrangères")
    ctrl('--refus-tolere' in mn and 'default=[]' in mn,
         "`--refus-tolere` existe et vaut `[]` PAR DÉFAUT",
         "⛔ jamais désarmé par défaut")
    # AC1.4 — le refus est imprimé EN TÊTE : l'ordre dans le source fait foi.
    i_ref = mn.find('print("🔴 REFUS')
    i_sor = mn.find('print(r["sortie"])')
    ctrl(0 <= i_ref < i_sor,
         "AC1.4 : le refus s'imprime AVANT la sortie",
         "⛔ pas noyé dans 90 s de capture")


def bloc_completude(py, c):
    """AC2 — LA COMPLÉTUDE EST VISIBLE, DES DEUX CÔTÉS."""
    print("\n── AC2 : l'instrument dit s'il a TOUT lu ───────────────────────")
    tr = corps_fonction(c, "static int dn_cmd_tracer(")
    ctrl(tr is not None, "le firmware a un shim `dn_cmd_tracer()`", "")
    tr = tr or ""
    ctrl("lignes emises" in tr, "…qui imprime le compteur en FIN de commande",
         "l'invariant par capture")
    # ⛔ Le compteur DOIT être lu AVANT de s'imprimer lui-même.
    i_lu = tr.find("= s_lignes_cmd;")
    i_pr = tr.find("lignes emises")
    ctrl(0 <= i_lu < i_pr,
         "…et il LIT `s_lignes_cmd` AVANT de l'imprimer",
         "⛔ sinon il se compterait lui-même")
    pf = corps_fonction(c, "static int dn_console_printf(const char *fmt, ...)\n{")
    ctrl(pf is not None, "`dn_console_printf()` existe", "")
    pf = pf or ""
    ctrl("'\\n'" in pf and "s_lignes_cmd++" in pf,
         "…et il compte les passages à la ligne", "⛔ pas les appels")
    ctrl("#define printf dn_console_printf" in c,
         "…et TOUT `printf` du fichier passe par lui",
         "⛔ pas 32 branches à instrumenter")
    st = corps_fonction(c, "esp_err_t dn_console_start(void)")
    ctrl(st is not None, "`dn_console_start()` est localisable", "")
    st = st or ""
    ctrl("s_shims[i]" in st and "s_cmd_reelle[i]" in st,
         "…et il enregistre le SHIM à la place de la commande",
         "toute commande est instrumentée")
    ctrl("_Static_assert" in st,
         "…avec un `_Static_assert` sur le nombre de shims",
         "⛔ échoue à la COMPILATION, pas au boot")

    cp = corps_python(py, "def completude(")
    ctrl(cp is not None, "l'hôte a `completude()`", "")
    cp = cp or ""
    for etat in ("PERTE", "LIGNES_ETRANGERES", "SANS_COMPTEUR"):
        ctrl('"%s"' % etat in cp, "…et il distingue l'état %s" % etat,
             "⛔ « pas de compteur » ≠ « 0 perte »")
    ctrl("coupees_avant_echo" in cp,
         "AC2.3 : ce que `nettoyer()` coupe AVANT l'écho est compté",
         "le SECOND mécanisme candidat")
    ctrl("VIDE_NE_PROUVE_RIEN" in py and py.count("VIDE_NE_PROUVE_RIEN") >= 2,
         "AC2.5 : la règle « vide ≠ muet » est POSÉE ET UTILISÉE",
         "⛔ pas un commentaire de dossier")
    ctrl(re.search(r"(?i)parade.{0,80}dn4-2.{0,400}insuffisan", py, re.S)
         is not None
         or re.search(r"(?i)dn4-2.{0,200}INSUFFISANTE", py, re.S) is not None,
         "AC2.4 : la parade `dn4-2` est dite INSUFFISANTE dans le pilote",
         "la perte existe AUSSI en solo (1/7)")
    ctrl(re.search(r"(?i)(2 A/B|30 passes).{0,200}(reproduit|reproduction)",
                   py, re.S) is not None,
         "AC2.6 : la cause est déclarée NON INSTRUITE",
         "⛔ ne pas inventer un mécanisme")


def bloc_miroir(py, c):
    """🎯 LE MIROIR — LE CONTRÔLE QUI TIENT LES DEUX BOUTS DU PROTOCOLE.

    ⛔ ANGLE MORT CONNU DE CE DÉPÔT : une gate qui lit UN SEUL fichier laisse
       passer un désaccord de format entre deux fichiers. Ici on EXTRAIT le
       `printf` du firmware, on FABRIQUE la ligne qu'il produirait, et on la
       passe à la regex de l'hôte. Un des deux qui bouge ⇒ rouge.
    """
    print("\n── LE MIROIR : le format du compteur, des DEUX côtés ───────────")
    m = re.search(r'printf\("(--- fin : [^"]*?)"', c)
    ctrl(m is not None, "le format du compteur est EXTRAIT du firmware",
         "⛔ pas recopié dans la gate")
    fmt = m.group(1) if m else ""
    exemple = (fmt.replace("%u", "12").replace("%s", "").replace("\\n", "")
               .strip())
    rx = re.search(r'RE_COMPTEUR\s*=\s*re\.compile\(r"([^"]+)"\)', py)
    ctrl(rx is not None, "…et la regex de l'hôte est EXTRAITE du pilote", "")
    if fmt and rx:
        try:
            mm = re.compile(rx.group(1)).match(exemple)
        except re.error as e:
            mm = None
            print("        regex illisible : %s" % e)
        ctrl(mm is not None and mm.group(1) == "12",
             "🎯 la ligne du FIRMWARE est lue par la regex de l'HÔTE",
             repr(exemple)[:34])
        # …et le cas « COMPTE NON FIABLE », l'autre branche du même printf.
        ex2 = exemple.replace(" ---", "") + \
            " (COMPTE NON FIABLE : sortie tronquee) ---"
        try:
            m2 = re.compile(rx.group(1)).match(ex2)
        except re.error:
            m2 = None
        ctrl(m2 is not None, "…y compris quand la carte déclare son compte faux",
             "l'autre branche du même printf")


def bloc_injecteur(racine, inj):
    """AC3 — L'INJECTEUR A UN JEU QUI VARIE, ET IL DÉCLARE LES JEUX FIXES."""
    print("\n── AC3 : le jeu variable, et la bannière des jeux FIXES ────────")
    ctrl("JEUX_RAMPES" in inj, "`JEUX_RAMPES` existe", "")
    ctrl(re.search(r'"rampe"', inj) is not None
         and 'choices=sorted(list(JEUX) + ["rampe"])' in inj,
         "…et `--jeu rampe` est offert", "")
    for j in ("pire", "reel", "nominal", "trou"):
        ctrl(re.search(r'^\s{4}"%s":\s*\{' % j, inj, re.M) is not None,
             "⛔ le jeu témoin « %s » est INTACT" % j,
             "il ne remplace aucun jeu")
    b = corps_python(inj, "def banniere_jeu(")
    ctrl(b is not None, "`banniere_jeu()` existe", "")
    b = b or ""
    ctrl("FIXE" in b and ("94 645" in b or "128 613" in b) and "108" in b,
         "…et elle NOMME la conséquence, chiffrée",
         "36 % de stimulus en moins, ×108")
    mn = corps_python(inj, "def main(")
    ctrl(mn is not None and "banniere_jeu(" in (mn or ""),
         "…et `main()` l'APPELLE", "⛔ pas seulement définie")
    ctrl("bornes_relues(" in inj and "dn_link.c" in inj,
         "les bornes sont RELUES de `dn_link.c`",
         "⛔ jamais recopiées dans l'outil")
    inject = corps_python(inj, "def injecter(")
    ctrl(inject is not None and "valeurs_rampes(" in (inject or ""),
         "…et le tir CALCULE les valeurs à chaque cycle",
         "⛔ pas un dict figé de plus")
    rc, out = joue(["tools/dn_injecteur.py", "--temoin-negatif"], racine)
    ctrl(rc == 0 and re.search(r"BILAN : \d+ OK, 0 KO", out) is not None,
         "🔴 LE TÉMOIN DE L'INJECTEUR PASSE (joué, ⛔ pas supposé)",
         out.strip().splitlines()[-1][:30] if out.strip() else "rc=%d" % rc)


def bloc_cpu(c):
    """AC4 — `cpu` MESURE SANS BLOQUER LE TRANSPORT QU'IL MESURE."""
    print("\n── AC4 : `cpu` ne bloque plus son propre transport ─────────────")
    d = corps_fonction(c, "static int cpu_delta(void)")
    ctrl(d is not None, "`cpu_delta()` existe", "")
    d = d or ""
    ctrl("vTaskDelay" not in d,
         "🔴 …et il ne contient AUCUN `vTaskDelay`",
         "⛔ le REPL EST le transport")
    dep = corps_fonction(c, "static int cpu_depart(void)")
    ctrl(dep is not None and "vTaskDelay" not in (dep or ""),
         "…ni `cpu_depart()`", "")
    ctrl("DN_CPU_DELTA_HORIZON_US" in d and "REFUS DE PUBLIER" in d,
         "…et le rebouclage ~71 min est GARDÉ, pas commenté",
         "il REFUSE plutôt que de publier faux")
    i_g = d.find("DN_CPU_DELTA_HORIZON_US")
    i_p = d.find("charge CPU sur la SESSION")
    ctrl(0 <= i_g < i_p, "…et la garde tombe AVANT toute publication", "")
    cm = corps_fonction(c, "static int cmd_cpu(int argc, char **argv)\n{\n    if (argc >= 2 && strcmp(argv[1], \"brut\")")
    ctrl(cm is not None, "`cmd_cpu()` (variante instrumentée) est localisable", "")
    cm = cm or ""
    ctrl('"depart"' in cm and '"delta"' in cm,
         "…et il route `depart` / `delta`", "")
    i_dit = cm.find("CETTE COMMANDE BLOQUE LE REPL")
    i_dort = cm.find("vTaskDelay")
    ctrl(0 <= i_dit < i_dort,
         "AC4.3 : `cpu N` dit ce qu'il ne peut pas mesurer AVANT de dormir",
         "⛔ après, l'opérateur a déjà son chiffre")
    ctrl("0,8" in cm and "0,9" in cm,
         "…et il NOMME le symptôme qui l'a trahi",
         "0,8 % sous trafic vs 0,9 % au repos")


def bloc_sorties(c):
    """AC5 — TROIS SORTIES CESSENT DE MESURER AUTRE CHOSE."""
    print("\n── AC5 : relire au lieu de réciter, et mesurer ce qu'on annonce ─")
    col = corps_fonction(c, "static void colonnes(const char *s, int largeur)")
    ctrl(col is not None, "`colonnes()` est localisable", "")
    col = col or ""
    ctrl("0xC0" in col and "0x80" in col,
         "…et elle raisonne en octets de TÊTE UTF-8",
         "⛔ jamais couper au milieu d'une séquence")
    ctrl(re.search(r"cols > largeur", col) is not None and "return;" in col,
         "🔴 …et elle TRONQUE quand `cols > largeur`",
         "le défaut qu'elle existe pour fermer")
    ctrl('">"' in col or '">"' in col or '%.*s>' in col,
         "…et la coupe se VOIT (dernier caractère « > »)",
         "⛔ tronquer en silence est un autre mensonge")

    # 🎯 LA RÈGLE DU `35 100` EST UNE **FORME**, ⛔ PAS UNE LISTE DE LIGNES :
    #    « etait 35 100 a … » est un REPÈRE DATÉ (le patron du fichier) ; toute
    #    autre occurrence est une CONSIGNE D'ACTION qui récite une géométrie.
    #    Deux formes de REPÈRE DATÉ existent dans ce fichier, et les deux sont
    #    légitimes : « (etait 35 100 a 156) » et « (35 100 -> 36 675 px) ».
    #    Toute autre occurrence IMPRIMÉE est une consigne d'action qui envoie
    #    l'opérateur vérifier un nombre que la géométrie ne rend plus.
    #    ⛔ On regarde les LITTÉRAUX IMPRIMÉS : les commentaires historiques du
    #      fichier citent `35 100` et ont le DROIT de le faire — les réécrire
    #      referait la faute que `dn4-15` a nommée (« une réfutation ne vaut que
    #      son périmètre »).
    recitees = [t for t in printfs(c)
                if re.search(r"35\s?100", t)
                and not re.search(r"etait\s+35\s?100|35\s?100\s*->", t)]
    ctrl(not recitees,
         "🔴 aucune AIRE RÉCITÉE dans un printf hors REPÈRE DATÉ",
         "fautifs : %s" % ((recitees[0][:26] if recitees else "aucun")))
    ctrl(len([t for t in printfs(c) if re.search(r"35\s?100", t)]) >= 2,
         "…et les REPÈRES DATÉS, eux, sont TOUJOURS LÀ",
         "⛔ on ne réécrit pas les comptes rendus")
    for mot, argc in (("rafale", 2), ("barre", 3)):
        br = branche_argv1(c, "static int cmd_widget(", mot, argc)
        ctrl(br is not None, "la branche `widget %s` est localisable" % mot, "")
        ctrl(br is not None and "dn_ui_case_dim(" in br,
             "…et elle RELIT l'aire par `dn_ui_case_dim()`" ,
             "⛔ ni 35 100 ni 36 675 ne sont écrivables")
    br = branche_argv1(c, "static int cmd_widget(", "barre", 3)
    ctrl(br is not None and "6334" in br and "/ aire_b" in br,
         "…et `widget barre` CALCULE son pourcentage",
         "18 % récité valait 17,3 %")

    fl = corps_fonction(c, "static void largeur_drapeau_repl(const char *recu)")
    ctrl(fl is not None, "AC5.3 : `largeur_drapeau_repl()` existe", "")
    fl = fl or ""
    ctrl("0x80" in fl and "largeur_original_probable(" in fl,
         "…et il NOMME l'original probable, ⛔ pas seulement la règle",
         "`RÉSEAU` privé de ses octets ≥ 0x80")
    op = corps_fonction(c, "static bool largeur_original_probable(")
    ctrl(op is not None and "dn_ui_metrique_nom(" in (op or "")
         and "dn_ui_barre_date_forme(" in (op or ""),
         "…sur un vocabulaire ENGENDRÉ, ⛔ pas une table locale",
         "métriques + formes de date")
    cw = corps_fonction(c, "static int cmd_widget(")
    ctrl(cw is not None and (cw or "").count("largeur_drapeau_repl(argv[2])") == 2,
         "…et les DEUX branches de `widget largeur` l'appellent",
         "argc==3 ET argc==4")


def bloc_leviers(c, w):
    """AC6 — LES LEVIERS À CHAUD DISENT CE QU'ILS CASSENT."""
    print("\n── AC6 : les leviers à chaud, et le verdict de contraste ───────")
    br = branche_argv1(c, "static int cmd_widget(", "piste", 3)
    ctrl(br is not None, "la branche `widget piste` est localisable", "")
    br = br or ""
    ctrl("SI LA CARTE EST EN VEILLE" in br,
         "🔴 …et elle AVERTIT `veille off` comme ses trois voisines",
         "la jauge se pose 27 px trop haut")
    # ⛔ ON CHERCHE DANS CE QUI EST **IMPRIMÉ**, pas dans le fichier : le
    #    commentaire qui EXPLIQUE le correctif nomme forcément `dn3-3`, et un
    #    contrôle naïf rougirait sur sa propre documentation. Vu, ici même.
    dits = " ".join(printfs(br))
    ctrl("dn3-3" not in dits,
         "🔴 …et le renvoi vers `dn3-3` (`done`) n'est plus IMPRIMÉ",
         "⛔ un renvoi mort est un instrument qui ment")
    ctrl("dn4-29" in dits,
         "…redirigé vers le porteur VIVANT `dn4-29`",
         "statut vérifié au tracker")

    vc = corps_fonction(c, "static void verdict_contraste(void)")
    ctrl(vc is not None, "`verdict_contraste()` existe", "")
    vc = vc or ""
    ctrl("dn_widget_piste()" in vc and "dn_widget_amb_case_bg()" in vc,
         "…et il RELIT la piste ET l'aplat", "⛔ aucune copie locale")
    ctrl("dn_widget_desaturer(" in vc and "dn_ui_case_couleur(" in vc,
         "…et l'accent par la MÊME fonction que l'écran",
         "⛔ pas une copie de la formule")
    cb = corps_fonction(c, "static const char *contraste_bande(int ecart)") or ""
    ctrl("ecart == 0" in cb and "ECART NUL" in cb,
         "…et l'écart NUL est une bande À PART",
         "certitude ARITHMÉTIQUE, aucun œil requis")
    ctrl("DN_CONTRASTE_REPERE" in cb,
         "…et le repère 24 est NOMMÉ, ⛔ pas écrit en dur",
         "emprunté à `bloc_gris`")
    ctrl("ON NE REFUSE PAS" in vc,
         "…et le verdict AVERTIT, ⛔ ne refuse pas",
         "doctrine explicite de ces commandes")
    for mot, sig, argc in (("piste", "static int cmd_widget(", 3),
                           ("couleur", "static int cmd_widget(", 4),
                           ("opa", None, None),
                           ("case", "static int cmd_veille(", None)):
        if mot == "opa":
            corps = corps_fonction(c, "static int cmd_widget(") or ""
            m = re.search(r'strcmp\(argv\[1\], "opa"\) == 0.*?return 0;\n    \}',
                          corps, re.S)
            trouve = m is not None and "verdict_contraste()" in m.group(0)
        else:
            b = branche_argv1(c, sig, mot, argc)
            trouve = b is not None and "verdict_contraste()" in b
        ctrl(trouve, "…et la branche `%s` l'APPELLE" % mot,
             "⛔ un verdict non appelé ne garde rien")

    tr = branche_argv1(c, "static int cmd_touch(", "reset")
    ctrl(tr is not None, "AC6.3 : la branche `touch reset` est localisable", "")
    tr = tr or ""
    ctrl("s_base_consommes" in tr and "veille" in tr,
         "…et elle AVERTIT qu'elle casse le compteur de `veille`",
         "« reveils : 3 » à côté de « CONSOMMES : 0 »")

    # ── AC8.7 : LA GATE LIT `W_COL_PISTE_DEFAUT` **ET** `s_piste` ───────────
    #    C'est l'écart déclaré de `dn4-29` : « aucun des 22 verif_*.py ne les
    #    lit ». Elle les lit, et elle en CALCULE le contraste par défaut.
    print("\n── AC8.7 : la paire piste ↔ fond, que RIEN ne gardait ──────────")
    mp = re.search(r"#define W_COL_PISTE_DEFAUT\s+0x([0-9A-Fa-f]{6})", w)
    ms = re.search(r"static uint32_t s_piste\s*=\s*(\w+);", w)
    mb = re.search(r"#define W_AMB_CASE_BG\s+0x([0-9A-Fa-f]{6})", w)
    ctrl(mp is not None, "`W_COL_PISTE_DEFAUT` est LU dans `dn_widget.c`",
         "0x%s" % (mp.group(1) if mp else "?"))
    ctrl(ms is not None and ms.group(1) == "W_COL_PISTE_DEFAUT",
         "…et `s_piste` en dérive", ms.group(1) if ms else "?")
    ctrl(mb is not None, "`W_AMB_CASE_BG` est LU aussi",
         "0x%s" % (mb.group(1) if mb else "?"))
    if mp and mb:
        def lum(h):
            v = int(h, 16)
            return ((v >> 16 & 255) * 77 + (v >> 8 & 255) * 150 +
                    (v & 255) * 29) >> 8
        lp, lf = lum(mp.group(1)), lum(mb.group(1))
        e = abs(lp - lf)
        ctrl(e != 0,
             "🔴 la paire LIVRÉE piste ↔ aplat n'est PAS de l'écart NUL",
             "lum %d vs %d ⇒ écart %d" % (lp, lf, e))
        print("        ⚠️ écart %d — SOUS le repère 24 emprunté à `bloc_gris`, qui"
              % e)
        print("           gouverne LES TROIS GRIS DE RÉGIME entre eux et ⛔ ne se")
        print("           transpose pas. Éprouvé À L'ŒIL sur la carte le 2026-08-31")
        print("           (« oui, une barre vert foncé ») ⇒ FAIT CONSIGNÉ, ⛔ pas")
        print("           un défaut ouvert. Seul l'écart NUL est un rouge ici.")


def bloc_latence(py, inj):
    """AC7 — LA DISPERSION AVANT TOUT DELTA."""
    print("\n── AC7 : la latence publie sa dispersion, et refuse le delta ───")
    vd = corps_python(py, "def verdict_delta(")
    ctrl(vd is not None, "`verdict_delta()` existe", "")
    vd = vd or ""
    ctrl("LATENCE_FENETRES_MIN" in vd and "REFUS" in vd,
         "🔴 …et il REFUSE un delta sur UNE fenêtre",
         "⛔ pas un commentaire déconseillant")
    ctrl("chevauche" in vd,
         "…et il refuse aussi deux étendues qui SE CHEVAUCHENT",
         "le delta serait dans le bruit")
    ctrl("dn4-2" in vd,
         "AC7.4 : la conséquence rétroactive NOMME `dn4-2`",
         "ses écarts sur fenêtre unique aussi")
    d = corps_python(py, "def dispersion(")
    ctrl(d is not None and "etendue" in (d or "") and "ecart_type" in (d or ""),
         "`dispersion()` publie étendue ET écart-type",
         "⛔ jamais une moyenne seule")
    ctrl(re.search(r"(?i)225/225.{0,300}(DÉMOLIE|demolie)", py, re.S) is not None,
         "AC7.3 : la règle réfutée est ÉCRITE comme réfutée",
         "la 5ᵉ fenêtre l'a démolie")
    ctrl(re.search(r"(?i)(RÉFUTÉ|REFUTE).{0,200}(tas LVGL|fragmentation)",
                   py, re.S) is not None,
         "AC7.5 : les deux hypothèses réfutées sont NOMMÉES",
         "⛔ ne pas les rejouer")
    mn = corps_python(inj, "def main(") or ""
    ctrl("--latence exige --firmware" in mn or
         ("a.latence and not a.firmware" in mn),
         "…et `--latence` EXIGE `--firmware`",
         "un relevé sans binaire ne se compare à rien")
    ctrl("campagne_latence(" in mn,
         "…et la campagne joue N fenêtres CONSÉCUTIVES", "")


def bloc_latence_execute(racine):
    """🔴 AC7.2 **EXÉCUTÉ**, ⛔ PAS LU.

    LE MUTANT QUI A OUVERT CE BLOC : `LATENCE_FENETRES_MIN = 1` passait la gate
    en VERT. Les contrôles d'AC7 étaient TEXTUELS — ils vérifiaient que le refus
    est ÉCRIT, pas qu'il a lieu. ⛔ *« Demande-toi de chaque ligne : qu'est-ce
    qui la ferait rougir ? »* — celles-là, rien.
    ⇒ On IMPORTE le pilote de l'arbre sous test et on lui POSE la question.
    """
    print("\n── AC7 : le refus du delta, EXÉCUTÉ sur l'arbre sous test ──────")
    prog = (
        "import sys; sys.path.insert(0, 'tools'); import dn_console as d\n"
        "u = d.dispersion([10]); v = d.dispersion([300, 310, 305, 299])\n"
        "r1, _ = d.verdict_delta(u, v)\n"
        "r2, _ = d.verdict_delta(d.dispersion([86, 138, 220, 86, 260]),\n"
        "                        d.dispersion([90, 250, 130]))\n"
        "r3, _ = d.verdict_delta(d.dispersion([10, 12, 11, 13, 10]),\n"
        "                        d.dispersion([300, 310, 305, 299, 302]))\n"
        "print('R', int(r1), int(r2), int(r3))\n")
    import tempfile
    fd, chemin = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(prog)
        rc, out = joue([chemin], racine)
    finally:
        os.unlink(chemin)
    m = re.search(r"^R (\d) (\d) (\d)$", out, re.M)
    ctrl(m is not None, "le pilote sous test s'importe et répond",
         (out.strip().splitlines() or ["rc=%d" % rc])[-1][:30])
    if m:
        ctrl(m.group(1) == "0",
             "🔴 UNE fenêtre, étendues DISJOINTES ⇒ REFUSÉ",
             "⛔ le chevauchement ne rattrape pas ce cas")
        ctrl(m.group(2) == "0",
             "🔴 étendues qui SE CHEVAUCHENT ⇒ REFUSÉ", "delta dans le bruit")
        ctrl(m.group(3) == "1",
             "✅ …et un delta LISIBLE reste recevable",
             "⛔ une gate qui refuse tout ne garde rien")


def bloc_temoin_pilote(racine):
    print("\n── LE TÉMOIN DU PILOTE, JOUÉ (⛔ pas supposé) ──────────────────")
    rc, out = joue(["tools/dn_console.py", "--temoin-negatif"], racine)
    ctrl(rc == 0 and re.search(r"BILAN : \d+ OK, 0 KO", out) is not None,
         "🔴 `dn_console.py --temoin-negatif` PASSE",
         (out.strip().splitlines() or ["rc=%d" % rc])[-1][:30])
    # ⛔ Et il doit être NON TRIVIAL : un témoin à 3 contrôles ne prouve rien.
    m = re.search(r"BILAN : (\d+) OK", out)
    ctrl(m is not None and int(m.group(1)) >= 20,
         "…et il joue au moins 20 contrôles",
         "%s contrôles" % (m.group(1) if m else "?"))


# ═══════════════════════════════════════════════════════════════════════════
# AC8.6 — LES MUTANTS : **CETTE GATE A ÉTÉ VUE ROUGIR**
# ═══════════════════════════════════════════════════════════════════════════
#
# 🔴 *« Une gate qu'aucun test n'a vue échouer est décorative »*. ⛔ Et un
#    `N OK / 0 KO` peut épingler du code FAUX — mesuré TROIS fois sur cette base
#    de code. La falsification vit donc DANS la gate, ⛔ pas dans un compte rendu
#    qu'on ne rejoue jamais.
#
# Chaque mutant remet le défaut D'ORIGINE de son AC, sur un ARBRE COPIÉ (⛔ le
# dépôt n'est jamais modifié), et la gate doit **sortir en 1**.
FICHIERS_MUTABLES = (
    "tools/dn_console.py",
    "tools/dn_injecteur.py",
    "firmware/desknode/main/dn_console.c",
    "firmware/desknode/main/dn_widget.c",
    "firmware/desknode/main/dn_link.c",
)

MUTANTS = (
    ("AC1", "le motif REPL universel est retiré de la table",
     "tools/dn_console.py",
     '    ("REPL: commande inconnue", re.compile(r"Unrecognized command")),\n',
     ""),
    ("AC1", "un refus n'arme plus le code de retour",
     "tools/dn_console.py",
     'if r["refus"] and not refus_tolere(cmd, args.refus_tolere):\n                    code = 1',
     'if False:\n                    code = 1'),
    ("AC2", "le compteur de lignes est retiré du firmware",
     "firmware/desknode/main/dn_console.c",
     'printf("--- fin : %u lignes emises%s ---\\n", (unsigned)n,',
     'printf("fin%s%s\\n", "", (const char *)'),
    ("AC2", "l'hôte ne distingue plus la PERTE",
     "tools/dn_console.py",
     '        r["etat"] = "PERTE"',
     '        r["etat"] = "OK"'),
    ("AC3", "le jeu « variable » redevient FIXE (rampe plate)",
     "tools/dn_injecteur.py",
     '"cpu": [(30, 1000, 7), (20, 57, 11), (30, 1000, 13), (300, 900, 17)],\n'
     '    "gpu": [(0, 1000, 19)',
     '"cpu": [(30, 30, 7), (20, 57, 11), (30, 1000, 13), (300, 900, 17)],\n'
     '    "gpu": [(0, 1000, 19)'),
    ("AC4", "`vTaskDelay` est réintroduit dans `cpu_delta`",
     "firmware/desknode/main/dn_console.c",
     "    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;\n"
     "    TaskStatus_t *apres = calloc(capacite, sizeof(TaskStatus_t));",
     "    vTaskDelay(pdMS_TO_TICKS(1000));\n"
     "    UBaseType_t capacite = uxTaskGetNumberOfTasks() + 8;\n"
     "    TaskStatus_t *apres = calloc(capacite, sizeof(TaskStatus_t));"),
    ("AC5", "une constante de géométrie est replantée dans une consigne",
     "firmware/desknode/main/dn_console.c",
     'printf("   delta vaut %u flushes pour UN SEUL cycle (et %u x %d px,\\n",',
     'printf("   delta vaut %u flushes pour UN SEUL cycle (et %u x 35 100 px,%d\\n",'),
    ("AC6", "l'avertissement `veille off` est retiré de `widget piste`",
     "firmware/desknode/main/dn_console.c",
     '        printf("⛔ SI LA CARTE EST EN VEILLE : `veille off` D\'ABORD. Une scene\\n");\n'
     '        printf("   reconstruite en Ambient pose la jauge 27 px TROP HAUT, et\\n");\n'
     '        printf("   AUCUN compteur ne le dit (ledger, 2026-08-29).\\n");\n'
     '        /* 🔴 dn4-23 / AC6.1 — LE RENVOI ETAIT MORT.',
     '        /* 🔴 dn4-23 / AC6.1 — LE RENVOI ETAIT MORT.'),
    ("AC6", "le verdict de contraste disparaît de `veille case`",
     "firmware/desknode/main/dn_console.c",
     "        verdict_contraste();\n        return 0;\n    }\n\n    if (strcmp(argv[1], \"unite\")",
     "        return 0;\n    }\n\n    if (strcmp(argv[1], \"unite\")"),
    ("AC6", "la piste par défaut retombe sur l'aplat (écart NUL)",
     "firmware/desknode/main/dn_widget.c",
     "#define W_COL_PISTE_DEFAUT 0x141820",
     "#define W_COL_PISTE_DEFAUT 0x000000"),
    ("AC7", "un delta sur UNE SEULE fenêtre redevient publiable",
     "tools/dn_console.py",
     "LATENCE_FENETRES_MIN = 2",
     "LATENCE_FENETRES_MIN = 1"),
)


def jouer_mutants(racine, sortie_pv):
    import shutil
    import tempfile
    lignes_pv = []

    def dire(t=""):
        print(t)
        lignes_pv.append(t)

    dire("=" * 78)
    dire("dn4-23 / AC8.6 — LES MUTANTS, VUS ROUGIR")
    dire("=" * 78)
    dire("⛔ Le dépôt n'est JAMAIS modifié : chaque mutant vit dans un arbre")
    dire("   COPIÉ, et la gate y est rejouée telle quelle.")
    dire("")
    moi = os.path.abspath(__file__)
    rc_ref, out_ref = joue([moi, "--racine", racine], racine)
    dire("TÉMOIN POSITIF — l'arbre LIVRÉ : rc=%d   %s"
         % (rc_ref, (out_ref.strip().splitlines() or ["?"])[-1]))
    if rc_ref != 0:
        dire("⛔ L'arbre livré n'est pas vert : ⛔ aucun mutant n'est concluant.")
        with open(sortie_pv, "w", encoding="utf-8") as f:
            f.write("\n".join(lignes_pv) + "\n")
        return 1
    dire("")
    n_ok = n_rate = 0
    for ac, quoi, fichier, avant, apres in MUTANTS:
        tmp = tempfile.mkdtemp(prefix="dn423-mutant-")
        try:
            for rel in FICHIERS_MUTABLES:
                dst = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(os.path.join(racine, rel), dst)
            cible = os.path.join(tmp, fichier)
            with open(cible, encoding="utf-8") as f:
                txt = f.read()
            if txt.count(avant) != 1:
                dire("[RATÉ ] %-4s %-52s ancre introuvable (%d)"
                     % (ac, quoi, txt.count(avant)))
                n_rate += 1
                continue
            with open(cible, "w", encoding="utf-8") as f:
                f.write(txt.replace(avant, apres, 1))
            rc, out = joue([moi, "--racine", tmp], tmp)
            kos = [l.strip() for l in out.splitlines() if "[KO ]" in l]
            bilan = ([l for l in out.splitlines() if l.startswith("BILAN")]
                     or ["(pas de bilan)"])[-1]
            if rc == 1 and kos:
                dire("[ROUGE] %-4s %-52s rc=1  %s" % (ac, quoi, bilan))
                for k in kos[:3]:
                    dire("          ↳ %s" % k[:96])
                if len(kos) > 3:
                    dire("          ↳ … et %d autre(s)" % (len(kos) - 3))
                n_ok += 1
            else:
                dire("[VERT!] %-4s %-52s rc=%d  %s" % (ac, quoi, rc, bilan))
                dire("          ⛔ CE CONTRÔLE NE GARDE RIEN — le défaut passe.")
                n_rate += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    dire("")
    dire("BILAN MUTANTS : %d vus ROUGIR, %d non concluant(s) sur %d"
         % (n_ok, n_rate, len(MUTANTS)))
    dire("⛔ CE QUE CE PV NE PROUVE PAS : que la gate attrape TOUS les défauts.")
    dire("   Il prouve que chacun de ces onze-là ne passe plus. Une gate se juge")
    dire("   à ce qu'elle a été vue REFUSER, ⛔ pas à son compte de contrôles.")
    os.makedirs(os.path.dirname(sortie_pv), exist_ok=True)
    with open(sortie_pv, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes_pv) + "\n")
    print("\nPV écrit : %s" % sortie_pv)
    return 0 if n_rate == 0 else 1


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--racine", default=None,
                   help="jouer sur un ARBRE MUTÉ (production du PV des mutants)")
    p.add_argument("--mutants", action="store_true",
                   help="AC8.6 — remet le défaut d'origine de chaque AC sur un "
                        "arbre COPIÉ et EXIGE que la gate sorte en 1. ⛔ Le "
                        "dépôt n'est jamais modifié.")
    p.add_argument("--pv", default=None, metavar="FICHIER",
                   help="où écrire le PV des mutants "
                        "(défaut : mesures/dn4-23/T8-mutants.txt)")
    a = p.parse_args()
    racine = a.racine or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if a.mutants:
        return jouer_mutants(
            racine,
            a.pv or os.path.join(racine, "mesures", "dn4-23", "T8-mutants.txt"))

    print("=" * 78)
    print("dn4-23 / AC8 — LES INSTRUMENTS DE LA CONSOLE, GARDÉS SUR LES DEUX ÉTAGES")
    print("=" * 78)
    print("  racine : %s" % racine)

    py = lire(os.path.join(racine, "tools", "dn_console.py"))
    inj = lire(os.path.join(racine, "tools", "dn_injecteur.py"))
    c = lire(os.path.join(racine, "firmware", "desknode", "main", "dn_console.c"))
    w = lire(os.path.join(racine, "firmware", "desknode", "main", "dn_widget.c"))
    if None in (py, inj, c, w):
        print("\nBILAN : %d OK, %d KO" % (OK[0], KO[0]))
        return 1

    bloc_refus(py)
    bloc_completude(py, c)
    bloc_miroir(py, c)
    bloc_injecteur(racine, inj)
    bloc_cpu(c)
    bloc_sorties(c)
    bloc_leviers(c, w)
    bloc_latence(py, inj)
    bloc_latence_execute(racine)
    bloc_temoin_pilote(racine)

    print("\n" + "=" * 78)
    print("⛔ CE QUE CETTE GATE NE SOLDE PAS, ET C'EST ÉCRIT : elle ne parle pas à")
    print("   la carte. Elle prouve que les INSTRUMENTS ne peuvent plus conclure")
    print("   sur du vide — ⛔ pas qu'une perte réelle a été attrapée, ⛔ pas que le")
    print("   jeu variable atteint le régime réel, ⛔ pas que le contraste est")
    print("   lisible à l'œil. Ces cinq constats-là se tirent EN SÉANCE.")
    print("BILAN : %d OK, %d KO" % (OK[0], KO[0]))
    return 0 if KO[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
