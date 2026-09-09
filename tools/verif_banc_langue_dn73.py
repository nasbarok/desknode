#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn7-3 — LE BANC DE LA POSE DE LANGUE EST **JOUE**, ⛔ PAS SEULEMENT ECRIT.

======================= CE QUE CETTE GATE GARDE, ET POURQUOI ================

`tools/banc_langue_dalle_dn73.mjs` EXECUTE le JavaScript de
`installeur/index.html` contre un port bidon, et juge **DIX-HUIT** chemins : les
NEUF lignes de la matrice d'entrees-sorties de `dn7-3`, et NEUF de plus que deux
revues ont nommes. Cette gate existe pour UNE raison, et
elle est ecrite plutot que supposee :

  🔴 UN INSTRUMENT QUI A TOURNE **UNE FOIS** NE GARDE **RIEN** DEMAIN. Le banc
     avait d'abord ete joue a la main, hors de l'arbre, et son releve verse. Ce
     releve prouvait l'etat d'un jour, ⛔ pas une propriete. Documenter un piege
     ne protege de rien ; seul le REJOUER protege. ⇒ le banc entre au depot, et
     cette gate le LANCE — decouverte par le glob de `tools/run_gates.sh` et
     rejouee mutant par mutant par `tools/verif_campagne_dn56.py`.

  🔴 ET UNE GATE VERTE SUR UN BANC QUI N'A PAS TOURNE SERAIT **PIRE QUE PAS DE
     GATE**. `node` est un prerequis : s'il manque, cette gate rend **`rc=4`**
     avec son motif, et `tools/run_gates.sh` la declare NON-JOUABLE sur un
     temoin derive de `command -v node`. ⛔ Elle ne sort JAMAIS verte sans avoir
     joue le banc.

── CE QU'ELLE GARDE, LIGNE A LIGNE ─────────────────────────────────────────

  1. **LE BANC TOURNE**, et il rend son bilan. Une sortie sans `BANC :` est la
     signature d'un banc MORT — le meme discriminant que `BILAN` pour une gate.
  2. **LES NEUF LIGNES DE LA MATRICE SONT JOUEES, NOMMEMENT.** Un cas qui
     disparait retrecirait la population SANS RIEN DIRE. Les NEUF autres sont
     comptees, ⛔ pas nommees ici : la matrice fait autorite, ⛔ pas la liste.
  3. **LE BANC JOUE TOUS LES CAS QU'IL DECLARE** — le compte emis egale le
     compte attendu.
  4. **TOUT CAS REND OK.**
  5. **LE BANC EXECUTE LA PAGE, ⛔ IL NE LA RECOPIE PAS.** Un harnais qui
     rejoue une logique recopiee ne mesure que lui-meme.
  6. **LE BANC JUGE LA SUITE DES ISSUES, ⛔ PAS L'ETAT FINAL.** Mesure : un
     succes annonce trop tot puis ECRASE laisse l'ecran final correct, et le
     banc sortait VERT sur du code FAUX.

── CE QU'ELLE NE PROUVE ⛔ PAS, ECRIT PLUTOT QUE TU ─────────────────────────

⛔ Elle n'ouvre AUCUN port serie et ne parle a AUCUNE carte : le banc joue une
   carte BIDON. Que la langue soit VRAIMENT posee, et qu'elle survive a une
   coupure, se lit AU BANDEAU DE LA DALLE — seance carte, portee au ledger.
⛔ Elle ne remplace ⛔ pas `tools/verif_langue_dalle_dn73.py`, qui garde la
   STRUCTURE : les deux se partagent le travail, et le partage est ECRIT. Le
   relachement du verrou d'ecriture sur le chemin d'ECHEC, par exemple, n'est
   PAS exerce ici — ce chemin ne se produit pas contre un port bidon — et c'est
   `(c9)` de la gate statique, avec son mutant, qui le garde.
⛔ Elle ne dit RIEN de la lisibilite de la page.

Emploi :
    python3 tools/verif_banc_langue_dn73.py
    python3 tools/verif_banc_langue_dn73.py --liste-mutants
    python3 tools/verif_banc_langue_dn73.py --mutant <n>

Sortie : 0 si tout passe · 1 sur un vrai defaut · 2 sur un mutant inconnu ·
         3 si le mutant demande est PERIME (il n'a rien change) ·
         4 si `node` est introuvable — prerequis DECLARE, ⛔ pas un rouge.
"""

import argparse
import ast
import copy
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "installeur/index.html"
BANC = "tools/banc_langue_dalle_dn73.mjs"
FIXES = (PAGE, BANC)

# ⚠️ LE DELAI EST LARGE ET DECLARE : le banc joue dix scenarios, chacun avec des
#    attentes armees. Un `rc is None` de depassement est la mesure de CETTE
#    GATE, ⛔ pas le verdict du banc — et il se rend en KO, ⛔ jamais en vert.
DELAI_BANC = 120
# 🔴 LE TEMOIN DE CHAINE A **SA PROPRE BORNE, ET ELLE EST COURTE** — mesure :
#    le mutant qui RETIRE le filet global du banc faisait payer les 120 s
#    ci-dessus a CHAQUE tir, une fois par mutant dans la campagne (121,5 s pour
#    ce seul mutant). Le temoin ne joue AUCUN cas : il ne doit durer que le
#    temps du filet, et son depassement EST le rouge attendu.
DELAI_TEMOIN = 8
# ⚠️ LA BORNE D'UN CAS DU BANC, PASSEE EXPLICITEMENT : un cas normal coute
#    ~130 ms ; un cas qui ne se resout pas paye cette borne EN ENTIER, une fois
#    par mutant. ⛔ On ne la laisse donc pas a la valeur GENEREUSE du banc.
DELAI_CAS = 1500
# ⚠️ CE QUE LA **PAGE** ATTENDRA PENDANT LE BANC. ⛔ Ce n'est PAS une valeur de
#    produit : c'est le reglage que le banc REPOSE apres avoir evalue le script,
#    et il existe parce que la campagne rejoue ce banc UNE FOIS PAR MUTANT.
DELAI_PAGE = 40

# ── LES NEUF LIGNES DE LA MATRICE D'ENTREES-SORTIES DU DOSSIER ────────────
# 🔴 NOMMEES, ⛔ PAS COMPTEES : un compte ne dit pas LAQUELLE a disparu, et
#    c'est toujours celle qu'on n'aurait pas remarquee.
CAS_MATRICE = (
    "defaut-structurel",
    "pose-nominale",
    "deja-en-francais",
    "refus-de-la-carte",
    "pas-d-invite",
    "sans-reponse",
    "port-tenu-par-l-agent",
    "double-clic",
    "pas-d-acces-serie",
)
# ⚠️ QUATRE CAS HORS MATRICE, ET AUCUN N'EST UN SUPPLEMENT DE CONFORT :
#  · `relecture-sans-le-code` — la carte accepte sans le dire, puis la relecture
#    rend une AUTRE langue. Le dossier ne le nomme pas ; il est classe `refusee`
#    par un arbitrage ecrit au journal des changements de la story ;
#  · `pose-par-le-selecteur` — le chemin post-flash ORDINAIRE : le port n'est pas
#    deja ouvert, il s'obtient PAR LE SELECTEUR, et la pose va au bout. C'est LA
#    ligne de code livre que cette marche a changee, et rien ne l'exercait ;
#  · `nvs-refusee` — la CINQUIEME issue : la dalle a change A CHAUD, et ⛔ elle
#    ne gardera pas ce changement ;
#  · `selecteur-deja-en-vol` — un clic qui n'ecrit rien ET n'affiche rien se lit
#    comme une page cassee : la page doit NOMMER ce qui s'est passe.
CAS_HORS_MATRICE = ("relecture-sans-le-code", "pose-par-le-selecteur",
                    "nvs-refusee", "selecteur-deja-en-vol", "selecteur-annule",
                    "clic-reel-sur-francais", "flash-revele-arme-le-geste",
                    "module-absent-desarme-le-geste",
                    "ecriture-qui-rejette-en-vol")
CAS_ATTENDUS = len(CAS_MATRICE) + len(CAS_HORS_MATRICE)

RE_CAS = re.compile(r"^CAS (\S+)\s+(OK|KO)\s*(.*)$", re.M)
RE_BILAN_BANC = re.compile(r"^BANC : (\d+) OK, (\d+) KO$", re.M)

# ── CE QUI FAIT DU BANC UN BANC, ET ⛔ PAS UNE COPIE ──────────────────────
# 🔴 IL DOIT **LIRE LA PAGE ET L'EVALUER**. Un harnais qui redefinirait
#    `poserLangueDalle` chez lui sortirait vert sur une page cassee.
ANCRES_EXECUTION = ("readFileSync", '"<script>', "vm.runInContext")
ANCRE_RECOPIE = "function poserLangueDalle"
# 🔴 ET IL DOIT JUGER LA **SUITE** DES ISSUES : `langue.posee` au plus UNE fois,
#    et EN DERNIER. Mesure : sans ca, un succes annonce trop tot puis ecrase
#    laissait le banc VERT.
ANCRES_SUITE = ("suite.push(cle)", "r.suite[r.suite.length - 1]")
# 🔴 LE BANC DOIT SORTIR EN NON-ZERO QUAND SA CHAINE NE SE RESOUT PAS, ET CA SE
#    JOUE : `--temoin-chaine` REPLANTE le cas, et cette gate exige rc != 0 SANS
#    ligne de bilan. ⛔ Un banc qui rend 0 sur une liste tronquee annonce un
#    succes qu'il n'a pas mesure.
DRAPEAU_TEMOIN = "--temoin-chaine"
# 🔴 ET LE TEMOIN SE JUGE SUR **DEUX** CHOSES, ⛔ pas sur « non nul » : un
#    `Traceback` sort non nul et sans bilan, EXACTEMENT comme un filet qui a
#    joue. ⇒ on exige le code que le filet DECLARE, et la ligne qu'il imprime.
RC_FILET = 3
SIGNATURE_FILET = "BANC ⛔ CHAINE NON RESOLUE"
# 🔴 ET IL DOIT **REPOSER** LES ATTENTES DE LA PAGE : la campagne rejoue ce banc
#    une fois par mutant, et deux attentes de six secondes figees l'ont portee a
#    93 % de son plafond. ⛔ Se rabattre en silence sur la valeur du produit
#    serait pire que l'echec : il ECHOUE FERME.
ANCRES_DELAIS = ("ctx.DELAI_INVITE = DELAI_PAGE;",
                 "ctx.DELAI_REPONSE = DELAI_PAGE;",
                 'typeof ctx.DELAI_INVITE !== "number"')

LARGEUR_LIBELLE = 58

ok_total = [0]
ko_total = [0]
ids_emis = []

MUTANTS = {}                      # ⛔ AU NIVEAU MODULE — sinon `--liste-mutants`
CIBLES = {}                       # ⛔ AU NIVEAU MODULE — matiere de (c9)

MUTANTS[1] = ("PAGE : efface la garde du defaut anglais ⇒ des octets "
              "partent sur le port pour un choix qui n'ecrit rien")
CIBLES[1] = ("c4",)
MUTANTS[2] = ("PAGE : annonce le succes AVANT la relecture ⇒ un succes "
              "prouve par ce qu'on a tape")
CIBLES[2] = ("c4",)
MUTANTS[3] = ("PAGE : ECHANGE « refusee » et « sans reponse » ⇒ une "
              "ignorance publiee comme un constat")
CIBLES[3] = ("c4",)
MUTANTS[4] = ("PAGE : retire l'attente de l'invite ⇒ l'ordre part sur "
              "une carte qui n'a jamais repondu")
CIBLES[4] = ("c4",)
MUTANTS[5] = ("PAGE : retire la garde de re-entrance ⇒ deux clics "
              "envoient DEUX suites d'ordres sur le meme port")
CIBLES[5] = ("c4",)
MUTANTS[6] = ("PAGE : ne relache plus le verrou d'ecriture au succes ⇒ "
              "la fermeture du port partirait en rejet")
CIBLES[6] = ("c4",)
MUTANTS[7] = ("PAGE : rend le geste MUET quand le port n'est pas venu "
              "⇒ un clic qui n'ecrit rien ET n'affiche rien")
CIBLES[7] = ("c4",)
MUTANTS[8] = ("BANC : recopie la logique au lieu d'EVALUER la page ⇒ "
              "un harnais qui ne mesure plus que lui-meme")
CIBLES[8] = ("c4", "c5")
MUTANTS[9] = ("BANC : ne juge plus que l'etat FINAL ⇒ un succes "
              "annonce trop tot puis ECRASE redevient invisible")
CIBLES[9] = ("c6",)
MUTANTS[10] = ("BANC : retire un cas de la matrice ⇒ la population "
               "retrecit, et le banc sortirait VERT sur moins")
CIBLES[10] = ("c2", "c3")
MUTANTS[11] = ("replante une SORTIE ANTICIPEE NON DECLAREE : le bilan "
               "retrecit, et il sortirait VERT")
CIBLES[11] = ("z",)
MUTANTS[12] = ("declare un mutant dont le CORPS LEVE ⇒ un mutant MORT, "
               "qui sortirait en Traceback SANS `BILAN`")
CIBLES[12] = ("c0",)
MUTANTS[13] = ("retire une cible de `CIBLES` ⇒ un controle garde par "
               "ZERO mutant, le risque deja paye ailleurs")
CIBLES[13] = ("c9",)
MUTANTS[14] = ("declare dans `CIBLES` un controle INEXISTANT ⇒ une "
               "cible PERIMEE, que « N mutants, N rouges » ne voit pas")
CIBLES[14] = ("c10",)
MUTANTS[15] = ("declare une cible pour un mutant qui N'EXISTE PAS")
CIBLES[15] = ("c11",)
MUTANTS[16] = ("BANC : le rend MUET — il ne rend plus son bilan, la "
               "signature exacte d'un banc mort")
CIBLES[16] = ("c1",)
MUTANTS[17] = ("PAGE : rend l'ouverture du port bloquante jusqu'a la "
               "MORT du lien ⇒ la pose attend ce qu'elle veut utiliser")
CIBLES[17] = ("c4",)
MUTANTS[18] = ("PAGE : classe l'echec d'ecriture NVS comme un REFUS ⇒ "
               "la page dit l'INVERSE de ce que la carte imprime")
CIBLES[18] = ("c4",)
MUTANTS[19] = ("PAGE : renomme le delai d'invite ⇒ le banc ⛔ ne peut "
               "plus le regler, et il doit ECHOUER FERME")
CIBLES[19] = ("c4",)
MUTANTS[20] = ("BANC : retire le filet global ⇒ une chaine non resolue "
               "sortirait en 0 sur une liste TRONQUEE")
CIBLES[20] = ("c7",)
MUTANTS[21] = ("BANC : cesse de REPOSER les attentes de la page ⇒ la "
               "campagne repaie six secondes par tir")
CIBLES[21] = ("c8",)
MUTANTS[22] = ("PAGE : ECHANGE les deux gestionnaires de clic du choix "
               "⇒ cliquer « francais » enverrait `langue en`")
CIBLES[22] = ("c4",)
MUTANTS[23] = ("PAGE : INVERSE la polarite de l'armement ⇒ le geste "
               "s'offre justement quand le flash est impossible")
CIBLES[23] = ("c4",)
MUTANTS[24] = ("PAGE : dit TOUJOURS que le port est tenu ⇒ la phrase "
               "cesse d'etre une mesure et devient un ornement")
CIBLES[24] = ("c4",)
MUTANTS[25] = ("PAGE : le filet ne rend plus le geste ⇒ le bouton "
               "reste MORT jusqu'au rechargement de la page")
CIBLES[25] = ("c4",)
MUTANTS[26] = ("PAGE : revele le relais meme VIDE ⇒ un cadre vide "
               "donne a croire qu'on a lu quelque chose")
CIBLES[26] = ("c4",)
MUTANTS[27] = ("PAGE : ecrit une charge VIDE ⇒ trois appels pour "
               "ZERO octet, et « zero octet » cesse de vouloir dire")
CIBLES[27] = ("c4",)
MUTANTS[28] = ("BANC : le filet sort non nul SANS sa signature ⇒ un "
               "`Traceback` serait pris pour un filet qui a joue")
CIBLES[28] = ("c7",)

# ⚠️ LE COMPTE DU CHEMIN NORMAL : 1 pre-vol + un controle par mutant + les 11
#    controles numerotes. Il se PERIME si on ajoute un controle sans le mettre
#    a jour — et c'est voulu : c'est ce qui rend (z) FALSIFIABLE.
CONTROLES_PREVUS = 40

_MUTANT = 0

RE_ID_CTRL = re.compile(r"\((\w+)\)")


def ctrl(ok, libelle, detail=""):
    """UNE assertion, UNE ligne, UN identifiant. ⛔ Aucun controle muet."""
    assert len(libelle) < LARGEUR_LIBELLE, (
        "libelle de %d colonnes (max %d) : %r"
        % (len(libelle), LARGEUR_LIBELLE - 1, libelle))
    m = RE_ID_CTRL.match(libelle)
    ids_emis.append(m.group(1) if m else "?")
    if ok:
        ok_total[0] += 1
    else:
        ko_total[0] += 1
    print("  [%s] %-58s %s" % ("OK " if ok else "KO ", libelle, detail))
    return ok


def bilan(rc, anticipee=""):
    """TOUT CHEMIN QUI REND UN VERDICT passe ici. Une gate qui sort sans
    `BILAN` est indiscernable d'une gate MORTE.

    ⚠️ TROIS SORTIES NE PASSENT PAS ICI, ET C'EST ECRIT PLUTOT QUE PROMIS :
       · `--liste-mutants`, qui n'emet AUCUN controle et ne rend AUCUN verdict ;
       · le mutant INCONNU, qui est une ERREUR D'APPEL et rend 2 ;
       · `node` INTROUVABLE, qui est un PREREQUIS DECLARE et rend 4 — ⛔ pas un
         rouge, et ⛔ surtout pas un vert."""
    emis = ok_total[0] + ko_total[0]
    if not anticipee and emis != CONTROLES_PREVUS:
        ctrl(False, "(z) tout controle prevu est EMIS",
             "⛔ %d emis pour %d prevus — une gate qui joue MOINS de controles "
             "qu'annonce sort VERTE sur une population RETRECIE, ⛔ sans le "
             "declarer" % (emis, CONTROLES_PREVUS))
        rc = 1
    print("\n" + "=" * 78)
    if anticipee:
        print("⛔ SORTIE ANTICIPEE — %d controle(s) emis sur %d prevus : %s"
              % (ok_total[0] + ko_total[0], CONTROLES_PREVUS, anticipee))
    print("BILAN : %d OK, %d KO" % (ok_total[0], ko_total[0]))
    print("=" * 78)
    return rc


def lire(chemin):
    try:
        with io.open(os.path.join(RACINE, chemin), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


# ═══════════ LES PREDICATS — DES FONCTIONS DU PRODUIT ══════════════════════

def jouer_le_banc(fichiers, extra=(), delai=None):
    """ECRIT la page et le banc dans un repertoire JETABLE, hors du depot, et
    LANCE le banc dessus.

    🔴 ⛔ AUCUNE ECRITURE DANS L'ARBRE, JAMAIS — pas meme pour un mutant. La
       page mutee vit dans un temporaire que cette fonction detruit elle-meme.
    ⚠️ `rc is None` est un DEPASSEMENT DE DELAI **ou un lancement impossible**,
       ⛔ pas un verdict du banc : il remonte tel quel, et l'appelant le rend en
       KO. Les deux motifs sont DISTINGUES dans le texte — un moteur present mais
       non executable ⛔ n'est PAS « trop lent », et confondre les deux enverrait
       chercher un banc trop long la ou il y a un droit manquant."""
    # 🔴 LA PREPARATION ECHOUE **FERME**, AVEC SON MOTIF. Un `OSError` nu ici
    #    (disque plein, `TMPDIR` illisible, droits) sortirait en `Traceback`
    #    SANS `BILAN` — la signature exacte d'une gate MORTE, que ce depot a
    #    deja nommee. ⇒ il remonte comme un depassement : `rc is None`, et
    #    l'appelant le rend en KO.
    try:
        tmp = tempfile.mkdtemp(prefix="dn73-banc-")
    except OSError as e:
        return None, "⛔ REPERTOIRE JETABLE IMPOSSIBLE A CREER : %s" % e
    try:
        try:
            os.makedirs(os.path.join(tmp, "installeur"))
            os.makedirs(os.path.join(tmp, "tools"))
            for rel, texte in fichiers.items():
                with io.open(os.path.join(tmp, rel), "w", encoding="utf-8") as fh:
                    fh.write(texte)
        except (OSError, UnicodeError) as e:
            return None, "⛔ PREPARATION DU BANC IMPOSSIBLE : %s" % e
        argv = ["node", os.path.join(tmp, BANC),
                "--page", os.path.join(tmp, PAGE),
                "--delai", str(DELAI_PAGE),
                "--delai-cas", str(DELAI_CAS)] + list(extra)
        borne = DELAI_BANC if delai is None else delai
        try:
            r = subprocess.run(argv, cwd=tmp, timeout=borne,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            return r.returncode, r.stdout.decode("utf-8", "replace")
        except subprocess.TimeoutExpired as e:
            sortie = (e.output or b"").decode("utf-8", "replace")
            return None, sortie + "\n⛔ DEPASSEMENT DE DELAI (%d s)" % borne
        except OSError as e:
            # ⛔ UN MOTEUR PRESENT MAIS NON EXECUTABLE N'EST **PAS** UN BANC
            #    TROP LENT : le rapporter comme un depassement enverrait
            #    chercher une lenteur la ou il y a un droit ou un binaire casse.
            return None, ("⛔ LANCEMENT IMPOSSIBLE (⛔ pas un depassement) : "
                          "%s: %s" % (type(e).__name__, e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def le_banc_a_rendu_son_bilan(sortie):
    """Le banc a-t-il rendu son bilan ? ⛔ Une sortie sans `BANC :` est la
    signature d'un banc MORT, ⛔ pas d'un banc vert."""
    m = RE_BILAN_BANC.search(sortie or "")
    if not m:
        return False, None
    return True, (int(m.group(1)), int(m.group(2)))


def les_cas_de_la_matrice_sont_joues(sortie):
    """Les NEUF lignes de la matrice sont-elles jouees, NOMMEMENT ?"""
    joues = {m.group(1) for m in RE_CAS.finditer(sortie or "")}
    manquants = [c for c in CAS_MATRICE if c not in joues]
    return not manquants, (manquants, len(joues))


def le_banc_joue_tous_ses_cas(sortie):
    """Le compte emis egale-t-il le compte attendu ?"""
    n = len(RE_CAS.findall(sortie or ""))
    return n == CAS_ATTENDUS, n


def tout_cas_rend_ok(sortie):
    """Rend `(ok, [cas rouges avec leur motif])`."""
    rouges = [(m.group(1), m.group(3).strip())
              for m in RE_CAS.finditer(sortie or "") if m.group(2) == "KO"]
    return not rouges, rouges


def le_banc_execute_la_page(banc):
    """Le banc LIT-il la page et l'EVALUE-t-il, plutot que de la recopier ?"""
    absentes = [a for a in ANCRES_EXECUTION if a not in (banc or "")]
    recopie = ANCRE_RECOPIE in (banc or "")
    return not absentes and not recopie, (absentes, recopie)


def le_banc_sort_ferme(fichiers):
    """Le banc SORT-IL EN NON-ZERO quand sa chaine ne se resout pas ?

    🔴 C'EST JOUE, ⛔ PAS LU : `--temoin-chaine` REPLANTE le cas — une chaine
       qui ne se resout jamais — et on exige rc != 0 **et** ⛔ AUCUNE ligne de
       bilan. Un banc qui rend 0 sur une liste tronquee annonce un succes qu'il
       n'a pas mesure."""
    rc, sortie = jouer_le_banc(fichiers, (DRAPEAU_TEMOIN,), DELAI_TEMOIN)
    a_bilan = RE_BILAN_BANC.search(sortie or "") is not None
    signe = SIGNATURE_FILET in (sortie or "")
    return (rc == RC_FILET and signe and not a_bilan), (rc, a_bilan, signe, sortie)


def le_banc_regle_les_attentes(banc):
    """Le banc REPOSE-t-il les attentes de la page, et echoue-t-il FERME ?"""
    absentes = [a for a in ANCRES_DELAIS if a not in (banc or "")]
    return not absentes, absentes


def le_banc_juge_la_suite(banc):
    """Le banc juge-t-il la SUITE des issues, ⛔ pas seulement la derniere ?"""
    absentes = [a for a in ANCRES_SUITE if a not in (banc or "")]
    return not absentes, absentes


# ═══════════════════════════ LES MUTANTS ═══════════════════════════════════

def muter(etat):
    """REPLANTE une faute DANS L'ETAT — ⛔ jamais dans un fichier du depot.

    🔴 SEPT MUTANTS SUR SEIZE MUTENT **LA PAGE**, ⛔ pas la gate ni ses
       predicats : ce que ce banc garde, c'est le COMPORTEMENT DU PRODUIT, et
       une faute replantee ailleurs ne le prouverait pas.
    ⚠️ Tout corps VERIFIE son ancre d'abord et rend `e` INCHANGE : un corps qui
       LEVE serait rendu en `rc=1` + `BILAN` + `[KO ]` — mot pour mot le contrat
       que la campagne appelle « sain », et un mutant PERIME passerait pour un
       gardien vivant. ⛔ Le mutant 12 leve EXPRES : il est le temoin de ce cas.
    """
    e = copy.deepcopy(etat)
    p, r = e["fichiers"], e["regles"]

    if _MUTANT == 1:
        a = ('  if (code === LANGUE_DALLE_DEFAUT) {\n'
             '    blocMot("etat-langue", "langue.defaut-anglais");\n'
             '    languePort("langue.defaut-anglais");\n'
             '    return null;\n'
             '  }\n')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 2:
        a = ("            var relue = "
             "langueArmer(RE_INVITE_CARTE, DELAI_REPONSE, r2.reste);")
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '            blocMot("etat-langue", "langue.posee");\n' + a, 1)
    elif _MUTANT == 3:
        # 🔴 ON ECHANGE LES **SITES D'APPEL**, ⛔ PAS LES CLES DE LA TABLE.
        #    MESURE : un echange GLOBAL emportait aussi les deux entrees de
        #    `MOTS` — les textes suivaient leurs cles, rien ne changeait a
        #    l'ecran, et le mutant sortait VERT en ayant pourtant change des
        #    octets. ⛔ Un no-op DEGUISE echappe a la garde du no-op.
        t = p.get(PAGE, "")
        a = 'blocMot("etat-langue", "langue.refusee")'
        b = 'blocMot("etat-langue", "langue.sans-reponse")'
        if a not in t or b not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t.replace(a, "@@X@@").replace(b, a).replace("@@X@@", b)
    elif _MUTANT == 4:
        a = ('    var invite = langueArmer(RE_INVITE_CARTE, DELAI_INVITE, "");\n'
             '    var reveil = consoleEcrire("");\n'
             '    return reveil.then(function () { return invite; })')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '    var reveil = consoleEcrire("");\n'
               '    return reveil.then(function () '
               '{ return { texte: "", vu: true, reste: "" }; })', 1)
    elif _MUTANT == 5:
        a = "  if (langueEnVol) { return null; }\n"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 6:
        a = ('  return w.write(new TextEncoder().encode(ligne + "\\n"))'
             '.then(function () {\n'
             '    w.releaseLock();\n'
             '    return null;\n'
             '  }, function (err) {')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  return w.write(new TextEncoder().encode(ligne + "\\n"))'
               '.then(function () {\n'
               '    return null;\n'
               '  }, function (err) {', 1)
    elif _MUTANT == 7:
        # 🔴 LA FAUTE REPLANTEE A CHANGE AVEC LE PRODUIT, ET C'EST ECRIT PLUTOT
        #    QUE TU. Sa 1re redaction retirait `langueMasquer()` pour laisser le
        #    « ⏳ en cours » a cote du refus — ⛔ PERIMEE : depuis que ce chemin
        #    ANNONCE quelque chose, `blocMot` ecrase le temoin de toute facon, et
        #    le mutant etait devenu un NO-OP DEGUISE. ⇒ il replante desormais le
        #    defaut que la revue a trouve : le geste se TAIT quand le port n'est
        #    pas venu, et trois issues laissent le cadre VIDE.
        a = ('    blocMot("etat-langue", "langue.port-indisponible");\n'
             '    languePort("langue.port-indisponible");\n')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "", 1)
    elif _MUTANT == 8:
        # 🔴 IL **RECOPIE POUR DE VRAI**, ⛔ IL NE CITE PAS LE JETON DANS UN
        #    COMMENTAIRE. MESURE : la version d'avant posait
        #    `function poserLangueDalle` dans un COMMENTAIRE — `(c5)` rougissait
        #    sur la CHAINE pendant que le banc continuait d'evaluer la page et
        #    rendait `10 OK, 0 KO`. Ca prouvait un `grep`, ⛔ pas la propriete.
        #    ⇒ ici, l'evaluation de la page DISPARAIT et le harnais se donne sa
        #      propre logique : la faute est REPLANTEE, et le banc en rougit.
        a = ('  vm.runInContext(src, ctx, { filename: '
             '"installeur/index.html<script>" });\n  return { ctx, els };')
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(
            a, "  ctx.blocMot = function () { return null; };\n"
               "  ctx.consoleEcrire = function () "
               "{ return Promise.resolve(null); };\n"
               "  ctx.poserLangueDalle = function poserLangueDalle() "
               "{ return null; };\n"
               "  return { ctx, els };", 1)
    elif _MUTANT == 9:
        a = "      const succesJuste = posees === 0\n" \
            "        || (posees === 1 && r.suite[r.suite.length - 1] === \"langue.posee\");"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, "      const succesJuste = true;", 1)
    elif _MUTANT == 10:
        # 🔴 IL **RETIRE** LE CAS, ⛔ IL NE LE RENOMME PAS. MESURE : le renommer
        #    ne faisait rougir que `(c2)` — le banc emettait toujours DIX cas,
        #    donc `(c3)` restait VERT alors que ce mutant le declare pour cible.
        #    ⇒ `(c3)` etait garde par un mutant qui ⛔ NE LE FAISAIT PAS ROUGIR,
        #      et la reciproque `(c7)` ⛔ ne peut PAS voir ca : elle verifie
        #      qu'un controle est NOMME par un mutant, ⛔ pas qu'il ROUGIT.
        #      C'est le trou exact que ce depot a deja nomme : « N mutants, N
        #      vus rougir » prouve `mutant ⇒ rouge`, ⛔ jamais
        #      `controle ⇒ couvert`.
        t = p.get(BANC, "")
        a = '    nom: "sans-reponse",'
        if a not in t:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        i = t.rindex("  {", 0, t.index(a))
        j = t.index("  },", i) + len("  },\n")
        p[BANC] = t[:i] + t[j:]
    elif _MUTANT == 11:
        r["sortie_anticipee"] = True
    elif _MUTANT == 12:
        raise RuntimeError("mutant 12 : corps qui LEVE — c'est son role")
    elif _MUTANT == 13:
        # ⚠️ ON RETIRE LA CIBLE D'UN MUTANT **SEUL SUR SON CONTROLE**. MESURE :
        #    viser le mutant 1 ne prouvait RIEN — six autres mutants gardent
        #    `(c4)`, donc le controle restait couvert et `(c7)` restait VERT.
        e["cibles"][8] = ()
    elif _MUTANT == 14:
        e["cibles"][15] = tuple(e["cibles"][15]) + ("c99",)
    elif _MUTANT == 15:
        e["cibles"][99] = ("c1",)      # une cible pour un mutant INEXISTANT
    elif _MUTANT == 16:
        a = '    console.log("BANC : " + ok + " OK, " + ko + " KO");'
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, '    void ok; void ko;', 1)
    elif _MUTANT == 17:
        # 🔴 LA SEULE LIGNE DE CODE LIVRE QUE `dn7-3` A CHANGEE, REPLANTEE :
        #    `consoleOuvrir()` rendait sa promesse a la MORT du lien. Un
        #    appelant qui a besoin du port attendait alors la fin de ce qu'il
        #    voulait utiliser. MESURE : sans le cas `pose-par-le-selecteur`,
        #    cette regression laissait TOUTES les gates vertes.
        a = "      consoleLire();\n      return true;"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "      return consoleLire();", 1)
    elif _MUTANT == 18:
        a = "if (RE_NVS_REFUSEE.test(r2.texte)) {"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "if (false && RE_NVS_REFUSEE.test(r2.texte)) {", 1)
    elif _MUTANT == 19:
        a = "var DELAI_INVITE = 6000;"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "var DELAI_INVITE_MS = 6000;", 1)
    elif _MUTANT == 20:
        a = "  }, PLAFOND);"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, "  }, 24 * 3600 * 1000);", 1)
    elif _MUTANT == 21:
        a = "  ctx.DELAI_INVITE = DELAI_PAGE;\n  ctx.DELAI_REPONSE = DELAI_PAGE;"
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, "", 1)
    elif _MUTANT == 22:
        # ⚠️ IL ECHANGE LES **GESTIONNAIRES**, ⛔ pas les identifiants : la gate
        #    STATIQUE reste verte (les deux boutons appellent toujours
        #    `poserDalle`) — c'est exactement le trou que ce cas comble.
        t2 = p.get(PAGE, "")
        a = 'bDalleEn.addEventListener("click", function () { poserDalle("en"); });'
        b = 'bDalleFr.addEventListener("click", function () { poserDalle("fr"); });'
        if a not in t2 or b not in t2:
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = t2.replace(
            a, 'bDalleEn.addEventListener("click", function () { poserDalle("fr"); });', 1
        ).replace(
            b, 'bDalleFr.addEventListener("click", function () { poserDalle("en"); });', 1)
    elif _MUTANT == 23:
        a = ("  bLanguePoser.disabled = "
             "!(blocInstaller && blocInstaller.hidden === false);")
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, "  bLanguePoser.disabled = "
               "!!(blocInstaller && blocInstaller.hidden === false);", 1)
    elif _MUTANT == 24:
        a = ('  e.appendChild(portConsole ? paire("langue.port-tenu", undefined, true)\n'
             '                            : paire("langue.port-libre", undefined, true));')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '  e.appendChild(paire("langue.port-tenu", undefined, true));', 1)
    elif _MUTANT == 25:
        a = ("    relacher();\n    langueDesarmer();\n"
             '    blocMot("etat-langue", "langue.sans-reponse");')
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, '    langueDesarmer();\n'
               '    blocMot("etat-langue", "langue.sans-reponse");', 1)
    elif _MUTANT == 26:
        a = "  e.hidden = (txt === \"\" || txt === undefined || txt === null);"
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(a, "  e.hidden = false;", 1)
    elif _MUTANT == 27:
        a = 'w.write(new TextEncoder().encode(ligne + "\\n"))'
        if a not in p.get(PAGE, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[PAGE] = p[PAGE].replace(
            a, 'w.write(new TextEncoder().encode(""))', 1)
    elif _MUTANT == 28:
        a = '    console.log("BANC ⛔ CHAINE NON RESOLUE apres " + PLAFOND + " ms — "'
        if a not in p.get(BANC, ""):
            return e                      # ancre disparue ⇒ NO-OP ⇒ rc=3
        p[BANC] = p[BANC].replace(a, '    console.log("BANC interrompu — "', 1)
    else:
        raise AssertionError("mutant %d declare mais SANS CORPS" % _MUTANT)
    return e


# ═══════════════════════════ LA RECIPROQUE ═════════════════════════════════

def _texte_litteral(n):
    """La partie LITTERALE d'un libelle, meme construit par formatage."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Add)):
        return _texte_litteral(n.left)
    if isinstance(n, ast.JoinedStr) and n.values:
        return _texte_litteral(n.values[0])
    return None


def ids_par_ast():
    """Les identifiants de TOUS les controles de CE fichier, lus A L'AST."""
    try:
        with io.open(os.path.abspath(__file__), encoding="utf-8") as fh:
            arbre = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    out = set()
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "ctrl" and len(n.args) >= 2):
            m = RE_ID_CTRL.match(_texte_litteral(n.args[1]) or "")
            if m:
                out.add(m.group(1))
    return out or None


def main():
    global _MUTANT
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--mutant", type=int, default=None,
                    help="REPLANTE une faute EN MEMOIRE pour prouver que le "
                         "controle correspondant sait ROUGIR")
    ap.add_argument("--liste-mutants", action="store_true",
                    help="dit ce que chaque mutant replante, et sort")
    args = ap.parse_args()
    if args.mutant is not None and args.mutant not in MUTANTS:
        print("MUTANT %d INCONNU : il n'est pas declare. ⛔ Un mutant qui "
              "n'existe pas ne prouve RIEN — ⛔ ne pas conclure que le "
              "controle est vert." % args.mutant, file=sys.stderr)
        return 2
    _MUTANT = args.mutant or 0

    if args.liste_mutants:
        for n in sorted(MUTANTS):
            print("  %2d  [%s]  %s"
                  % (n, ",".join(CIBLES.get(n, ())) or "—", MUTANTS[n]))
        return 0

    print("=" * 78)
    print("dn7-3 — LE BANC DE LA POSE EST JOUE, ⛔ PAS SEULEMENT ECRIT"
          + ("   [MUTANT %d]" % _MUTANT if _MUTANT else ""))
    print("=" * 78)

    # ── LE PREREQUIS : `node`. ⛔ PAS UN ROUGE, ⛔ PAS UN VERT ────────────
    # 🔴 UNE GATE VERTE SUR UN BANC QUI N'A PAS TOURNE SERAIT PIRE QUE PAS DE
    #    GATE. ⇒ absence de `node` = rc=4, DECLARE, et `tools/run_gates.sh`
    #    porte la ligne qui l'attend sur un temoin derive de `command -v node`.
    node = shutil.which("node")
    if not node:
        print("⛔ PREREQUIS ABSENT : `node` est introuvable dans le PATH.")
        print("   Ce banc EXECUTE le JavaScript de `%s` ; sans moteur, il n'y" % PAGE)
        print("   a rien a jouer. ⛔ Cette gate ⛔ NE SORT PAS VERTE pour")
        print("   autant : elle rend 4, et `tools/run_gates.sh` la declare")
        print("   NON-JOUABLE avec ce motif. Le geste : installer Node.js.")
        return 4
    print("moteur     : %s" % node)
    print("cibles     : %s" % " · ".join(FIXES))
    print("⛔ CETTE GATE N'OUVRE AUCUN PORT ET NE PARLE A AUCUNE CARTE : le banc")
    print("   joue une carte BIDON. Que la langue soit VRAIMENT posee se lit AU")
    print("   BANDEAU DE LA DALLE — seance carte, portee au ledger.")

    # ── (c0) LE PRE-VOL ─────────────────────────────────────────────────
    print("\n── (c0) LE PRE-VOL — ⛔ AUCUN CONTROLE SUR DU VIDE ────────────────")
    fichiers = {}
    illisibles = []
    for c in FIXES:
        t = lire(c)
        if t is None:
            illisibles.append(c)
        else:
            fichiers[c] = t
    if not ctrl(not illisibles, "(c0) tout fichier attendu est LISIBLE",
                "%d fichier(s) lus" % len(fichiers) if not illisibles
                else "⛔ ILLISIBLE(S) : %s" % " ".join(illisibles)):
        return bilan(1, "un fichier attendu est illisible")

    for n in sorted(MUTANTS):
        if not ctrl(bool(CIBLES.get(n)) and bool(MUTANTS.get(n)),
                    "(c0) le mutant %d a une CIBLE et un LIBELLE" % n,
                    "→ %s" % ",".join(CIBLES.get(n, ()))
                    if CIBLES.get(n) else "⛔ cible ou libelle manquant"):
            return bilan(1, "un mutant est declare a moitie")

    etat = {"fichiers": fichiers,
            "regles": {"sortie_anticipee": False},
            "cibles": dict(CIBLES)}

    try:
        neuf = muter(etat) if _MUTANT else etat
    except Exception as exc:                              # noqa: BLE001
        ctrl(False, "(c0) le mutant %d a une CIBLE et un CORPS" % _MUTANT,
             "⛔ %s: %s — la faute est dans le MUTANT, ⛔ pas dans la gate"
             % (type(exc).__name__, str(exc)[:80]))
        return bilan(1, "le mutant %d n'a pas pu s'appliquer" % _MUTANT)
    if _MUTANT and neuf == etat:
        ctrl(False, "(c0) le mutant %d a bien un EFFET" % _MUTANT,
             "⛔ SANS EFFET — son ancre litterale a disparu de la cible. "
             "⛔ Ce n'est PAS un controle vert : rc=3, mutant PERIME.")
        return bilan(3, "le mutant %d n'a eu aucun effet" % _MUTANT)

    regles = neuf["regles"]
    cibles = neuf["cibles"]

    # ── (c1)…(c4) LE BANC TOURNE, ET IL REND SES CAS ────────────────────
    print("\n── (c1)…(c4) LE BANC TOURNE, ET CHAQUE CAS REND SON VERDICT ──────")
    rc_banc, sortie = jouer_le_banc(neuf["fichiers"])
    ok, compte = le_banc_a_rendu_son_bilan(sortie)
    # ⚠️ `rc is None` EST LA MESURE DE **CETTE GATE** (depassement, lancement
    #    impossible), ⛔ pas le verdict du banc. Les deux sont distingues.
    ctrl(ok and rc_banc is not None, "(c1) le banc TOURNE, et il rend son bilan",
         "BANC : %d OK, %d KO (rc=%s)" % (compte[0], compte[1], rc_banc)
         if ok and rc_banc is not None
         else "⛔ %s — une sortie sans `BANC :` est la signature d'un banc MORT, "
              "⛔ pas d'un banc vert"
              % ("le banc n'a pas pu etre lance ou a depasse son delai : %s"
                 % sortie.strip()[-90:] if rc_banc is None
                 else "aucune ligne `BANC :` dans %d octet(s) de sortie"
                      % len(sortie or "")))

    ok, (manquants, joues) = les_cas_de_la_matrice_sont_joues(sortie)
    ctrl(ok, "(c2) les NEUF lignes de la matrice sont JOUEES",
         "%d cas joues, dont les %d de la matrice" % (joues, len(CAS_MATRICE))
         if ok
         else "⛔ ligne(s) de matrice NON JOUEE(S) : %s — un cas qui disparait "
              "retrecit la population SANS RIEN DIRE, et c'est toujours celui "
              "qu'on n'aurait pas remarque" % " ".join(manquants))

    ok, n = le_banc_joue_tous_ses_cas(sortie)
    ctrl(ok, "(c3) le banc joue TOUS les cas qu'il declare",
         "%d cas emis pour %d attendus" % (n, CAS_ATTENDUS) if ok
         else "⛔ %d cas emis pour %d attendus — le compte est la seule chose "
              "qui voit un cas ajoute sans etre declare, ou retire sans etre "
              "dit" % (n, CAS_ATTENDUS))

    ok, rouges = tout_cas_rend_ok(sortie)
    ctrl(ok, "(c4) tout cas du banc rend OK",
         "%d cas, aucun rouge" % n if ok
         else "⛔ %d cas ROUGE(S) : %s"
              % (len(rouges), " · ".join("%s (%s)" % (c, m[:60])
                                         for c, m in rouges[:3])))

    # ── (c5)(c6) CE QUI FAIT DU BANC UN BANC ────────────────────────────
    print("\n── (c5)(c6) LE BANC EXECUTE LA PAGE, ET IL JUGE LA SUITE ─────────")
    banc = neuf["fichiers"].get(BANC, "")
    ok, (absentes, recopie) = le_banc_execute_la_page(banc)
    ctrl(ok, "(c5) le banc EXECUTE la page, ⛔ il ne la recopie pas",
         "il lit le `<script>` et l'evalue" if ok
         else "⛔ %s — un harnais qui rejoue une logique recopiee ne mesure que "
              "lui-meme, et il sortirait VERT sur une page cassee"
              % ("il redefinit chez lui ce qu'il devrait appeler" if recopie
                 else "ancre(s) d'execution absente(s) : %s" % " ".join(absentes)))

    ok, absentes = le_banc_juge_la_suite(banc)
    ctrl(ok, "(c6) le banc juge la SUITE des issues, ⛔ pas la fin",
         "« posee » au plus UNE fois, et EN DERNIER" if ok
         else "⛔ ancre(s) absente(s) : %s — un succes annonce trop tot puis "
              "ECRASE laisse l'ecran final correct et le defaut INVISIBLE ; "
              "c'est mesure, ⛔ pas suppose" % " ".join(absentes))

    # ── (c7)(c8) LE BANC SORT FERME, ET IL REGLE SES ATTENTES ───────────
    print("\n── (c7)(c8) UNE CHAINE NON RESOLUE N'EST PAS UN SUCCES ───────────")
    ok, (rc_t, a_bilan, signe, sortie_t) = le_banc_sort_ferme(neuf["fichiers"])
    ctrl(ok, "(c7) chaine non resolue ⇒ le FILET joue, et il le dit",
         "temoin joue : rc=%d, sa signature imprimee, ⛔ aucun bilan" % RC_FILET
         if ok
         else "⛔ %s — un banc qui rend 0 sur une liste TRONQUEE annonce un "
              "succes qu'il n'a pas mesure, et un `Traceback` sort non nul SANS "
              "bilan exactement comme un filet qui a joue"
              % ("le temoin n'a pas pu etre lance : %s"
                 % (sortie_t or "").strip()[-80:] if rc_t is None
                 else "le temoin a rendu un BILAN alors que sa chaine ⛔ ne "
                      "s'est PAS resolue" if a_bilan
                 else "rc=%s au lieu de %d" % (rc_t, RC_FILET)
                 if rc_t != RC_FILET
                 else "⛔ la SIGNATURE du filet est absente : rc=%d ne prouve "
                      "pas QUI a mis fin au banc" % RC_FILET))

    ok, absentes = le_banc_regle_les_attentes(neuf["fichiers"].get(BANC, ""))
    ctrl(ok, "(c8) le banc REPOSE les attentes de la page",
         "les deux delais sont reposes, et l'absence ECHOUE FERME" if ok
         else "⛔ ancre(s) absente(s) : %s — la campagne rejoue ce banc UNE "
              "FOIS PAR MUTANT, et deux attentes de six secondes figees l'ont "
              "portee a 93 %% de son plafond" % " ".join(absentes))

    if regles["sortie_anticipee"]:
        return bilan(0)

    # ── (c9)(c10)(c11) LA RECIPROQUE, MECANIQUE ─────────────────────────
    print("\n── (c9)(c10)(c11) AUCUN CONTROLE GARDE PAR ZERO MUTANT ───────────")
    lus_ast = ids_par_ast()
    reels = set(ids_emis) | (lus_ast or set())
    vises = set()
    for v in cibles.values():
        vises.update(v)
    nus = sorted(reels - vises, key=lambda s: (len(s), s))
    ctrl(not nus and lus_ast is not None,
         "(c9) chaque controle est vise par >= 1 mutant",
         "%d controle(s) lu(s) a l'AST, %d cible(s) declaree(s)"
         % (len(reels), len(vises)) if not nus and lus_ast is not None
         else ("⛔ %d CONTROLE(S) GARDE(S) PAR RIEN : %s"
               % (len(nus), " · ".join(nus)) if nus
               else "⛔ LA SOURCE NE S'ANALYSE PAS A L'AST — la population de "
                    "ce controle est INCONNUE, ⛔ pas vide"))
    perimees = sorted(vises - reels, key=lambda s: (len(s), s))
    ctrl(not perimees, "(c10) chaque cible de mutant est un controle REEL",
         "%d cible(s) confrontee(s)" % len(vises) if not perimees
         else "⛔ %d CIBLE(S) PERIMEE(S) : %s — un mutant qui vise un controle "
              "inexistant ⛔ ne garde rien"
              % (len(perimees), " · ".join(perimees)))
    orph = sorted(set(cibles) - set(MUTANTS))
    sans_cible = sorted(set(MUTANTS) - set(cibles))
    ctrl(not orph and not sans_cible,
         "(c11) `CIBLES` et `MUTANTS` se correspondent",
         "%d mutant(s), %d cible(s), cle a cle" % (len(MUTANTS), len(cibles))
         if not orph and not sans_cible
         else "⛔ cible(s) SANS mutant : %s · mutant(s) SANS cible : %s"
              % (orph or "—", sans_cible or "—"))

    print("\n⛔ CE QUE CETTE GATE NE PROUVE PAS : que la langue soit VRAIMENT")
    print("   posee dans une carte. Le banc joue une carte BIDON ; le bandeau")
    print("   est SUR LA DALLE, et il se lit A L'ŒIL. Et le relachement du")
    print("   verrou sur le chemin d'ECHEC n'est pas exerce ici : c'est la")
    print("   gate STATIQUE qui le garde, avec son mutant.")
    return bilan(1 if ko_total[0] else 0)


if __name__ == "__main__":
    sys.exit(main())
