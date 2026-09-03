# -*- coding: utf-8 -*-
"""dn4-40 / AC40.7 — LA CAMPAGNE PROUVE `controle ⇒ couvert`, ⛔ PAS `mutant ⇒ rouge`.

🔴 LE SENS DE LA PREUVE EST LE SUJET. Une campagne « N mutants, N vus rougir »
prouve `mutant ⇒ rouge` : elle dit que les mutants qu'on a ecrits sont
attrapes. Elle ⛔ NE DIT RIEN des controles que RIEN ne garde. Ce script
publie donc les DEUX faces :

  (1) chaque mutant REPLANTE une faute et doit etre vu rougir ;
  (2) le COMPTE DES CONTROLES GARDES PAR RIEN — ceux qu'aucun mutant de la
      campagne ne fait passer de OK a KO.

⛔ UN MUTANT QUI DEBRANCHE LA GARDE NE PROUVE QUE SON EXISTENCE. Tous les
mutants ci-dessous replantent la faute DANS LES DONNEES (ledger, tracker),
⛔ jamais dans le code de la gate.

⚠️ UN SEUL SITE A LA FOIS. Muter par remplacement global synchroniserait la
faute ET sa fixture : la gate verrait un monde coherent et resterait verte
pour la mauvaise raison.

⚠️ INDEXATION : sur le SITE D'APPEL du `ctrl()` (`dn_trace`), ⛔ jamais sur la
console — 4 libelles de KO y collident deja aujourd'hui (voir dn_trace.py).

⚠️ ⛔ AUCUNE ECRITURE DANS LE COCKPIT VIVANT. Chaque mutant travaille dans une
COPIE jetable, montee sous un repertoire temporaire.

Usage :
    python3 tools/campagne_dn440.py --cockpit ~/projects/compagnon_project
    python3 tools/campagne_dn440.py --liste
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
DESKNODE = os.path.dirname(ICI)
REL_LEDGER = "_bmad-output/implementation-artifacts/deferred-work.md"
REL_TRACKER = "_bmad-output/implementation-artifacts/sprint-status-desknode.yaml"
REL_MANIFESTE = "_bmad-output/implementation-artifacts/dn4-16-arbitrage-ledger.md"
GATE = os.path.join(ICI, "verif_ledger_dn416.py")
# ⚠️ `--gate` sert a jouer la MEME campagne contre la version d'AVANT le
# correctif (extraite par `git archive HEAD`). C'est le seul moyen de
# prouver le defaut « a vide » plutot que de l'affirmer : les mutants A et C
# doivent y sortir VERTS SANS avoir ete regardes.

# Une disposition TEMOIN, insérée en tete de la section DeskNode. ⛔ Elle
# n'existe que dans la copie.
# 🔴 dn4-40 / REVUE 2026-09-03 — LE TAG `[DeskNode]` EST POSE, ⛔ PLUS DEDUIT.
#    `est_desknode()` lit le tag DANS LA TETE de puce, sinon elle retombe sur
#    la SECTION. Tant que le temoin ne portait pas le tag, sa DeskNode-ite
#    dependait de l'endroit ou l'ancre etait tombee — un chemin non exerce
#    rendait les mutants VERTS pour rien. Le tag rend la chose VRAIE PAR
#    DECLARATION, ⛔ plus par inference.
TETE = ("- %s **[DeskNode] Entree TEMOIN de campagne dn4-40** — inseree par "
        "`campagne_dn440.py` dans une COPIE.\n")
DISPO = ("  ⇒ [dn4-40 %s] %s · porteur : %s · preuve : %s\n")
PREUVE_PAR_DEFAUT = "le motif `TEMOIN de campagne dn4-40`"


def ancre_desknode(txt):
    """L'offset de la puce d'une entree DeskNode OUVERTE — le site d'insertion.

    🔴 CE QUE CETTE FONCTION REPARE, ET QUI EST LE PIEGE N°1 D'UNE CAMPAGNE.
    Premiere version : on inserait avant la 1re puce `- ⚪ ` du fichier. Les
    14 mutants sortaient alors « KO neufs : aucun » — VERTS, et pour rien :
    la puce tombait HORS d'une section DeskNode, donc `est_desknode()` la
    rejetait et le mutant N'ATTEIGNAIT JAMAIS la garde qu'il pretend couvrir.
    ⛔ Un mutant vert sur un chemin non exerce ne prouve RIEN.

    ⇒ On ancre desormais sur une entree qui porte DEJA une disposition
      DeskNode : la section est alors la bonne PAR CONSTRUCTION.

    ⚠️ REVUE 2026-09-03 — `rindex` LEVAIT UN `ValueError` NON ATTRAPE quand la
    1re ligne `⇒` du fichier n'a aucune puce au-dessus d'elle (l'EXEMPLE DE
    FORMAT de l'en-tete est exactement ce cas). La campagne mourait au lieu de
    dire qu'elle n'a pas d'ancre. On rend None, et l'appelant sort en 1.
    """
    for m in re.finditer(r"^\s*⇒\s*\[dn\d", txt, re.M):
        j = txt.rfind("\n- ", 0, m.start())
        if j >= 0:
            return j + 1
    return None


def _mute_ledger(txt, ch, j):
    """Insere UNE entree temoin a l'offset `j`. ⛔ Un seul site."""
    bloc = TETE % ch.get("marqueur", "⚪")
    if ch.get("verdict") is not None:
        d = DISPO % (ch.get("date", "2026-09-02"), ch["verdict"], ch["porteur"],
                     ch.get("preuve", PREUVE_PAR_DEFAUT))
        bloc += d
        if ch.get("double"):
            bloc += d
    return txt[:j] + bloc + txt[j:]


# ── LES MUTANTS ──────────────────────────────────────────────────────────────
# `cible` = le controle que le mutant pretend couvrir (site d'appel resolu a
# l'execution par son LIBELLE lu au SOURCE, ⛔ pas a la console).
MUTANTS = [
    # ── Les trois du cadrage, rejoues ───────────────────────────────────────
    ("A-porteur-en-prose",
     "un porteur EN PROSE qui ne releve d'AUCUNE des cinq formes",
     dict(verdict="PORTEE", porteur="a traiter quand on aura le temps"),
     "tout porteur releve de l'UNE des CINQ formes"),
    ("C-porteur-epic",
     "un porteur `epic-*` — INVISIBLE avant dn4-40, donc a vide",
     dict(verdict="PORTEE", porteur="epic-dn4"),
     None),          # ⇒ doit rester VERT : `epic-dn4` est `in-progress`
    ("C2-porteur-epic-mort",
     "un porteur `epic-*` dont l'EPIC est clos ⇒ doit rougir",
     dict(verdict="PORTEE", porteur="epic-dn1"),
     "aucun porteur A VENIR n'est `done`/`superseded`"),
    ("B-incise-story-close",
     "une cle VIVANTE + une story CLOSE citee en incise",
     dict(verdict="BLOQUEE",
          porteur="bloquee par : le materiel decrit en dn4-1, absent du poste"),
     None),          # ⇒ doit rester VERT : l'incise n'est plus un porteur
    # ── Les temoins NEGATIFS : la segmentation ⛔ ne rend pas permissif ──────
    ("E1-bouchon-tbd",
     "un porteur bouchon `TBD`",
     dict(verdict="PORTEE", porteur="TBD"),
     "tout porteur DESIGNE quelqu'un (⛔ ni vide ni bouchon)"),
    ("E2-porteur-vide",
     "un champ porteur VIDE",
     dict(verdict="PORTEE", porteur=""),
     "tout porteur DESIGNE quelqu'un (⛔ ni vide ni bouchon)"),
    ("E3-story-done",
     "un porteur qui est une story `done`",
     dict(verdict="RE-HEBERGEE", porteur="dn4-16"),
     "aucun porteur A VENIR n'est `done`/`superseded`"),
    ("E4-story-inconnue",
     "un porteur absent du tracker",
     dict(verdict="PORTEE", porteur="dn9-99"),
     "tout porteur A VENIR existe au tracker"),
    # ── Les formes, une par une ─────────────────────────────────────────────
    ("F2-sans-cle",
     "une forme 2 dont l'argument n'est PAS une cle",
     dict(verdict="PORTEE", porteur="backlog nomme : une story a creer un jour"),
     "toute forme 2 `backlog nomme :` nomme UNE cle"),
    ("F3-fait-muet",
     "un `bloquee par :` dont le fait est un bouchon",
     dict(verdict="BLOQUEE", porteur="bloquee par : TBD"),
     "tout `bloquee par :` NOMME un fait (⛔ ni vide ni bouchon)"),
    ("F3-porteur-deguise",
     "un `bloquee par :` qui se REDUIT a une cle de story",
     dict(verdict="BLOQUEE", porteur="bloquee par : dn4-16"),
     "aucun fait bloquant ne se REDUIT a une cle de story"),
    ("F4-hors-close",
     "une forme 4 `clos par :` sur un verdict qui n'est pas CLOSE",
     dict(verdict="PORTEE", porteur="clos par : dn4-16, motif eteint"),
     "la forme 4 `clos par :` ne porte que le verdict CLOSE"),
    # ── Les deux controles POSES PAR LA REVUE DU 2026-09-03, avec leur mutant.
    #    ⛔ On ne livre pas un controle « garde par rien » : c'est le defaut
    #    meme que cette campagne existe pour compter.
    ("F4-fossoyeur-muet",
     "une forme 4 `clos par :` dont l'argument est un BOUCHON",
     dict(verdict="CLOSE", porteur="clos par : TBD"),
     "toute forme 4 `clos par :` NOMME ce qui a clos"),
    ("F2-cle-fantome-sous-close",
     "une forme 2 nommant une story qui n'existe NULLE PART, sous CLOSE",
     dict(verdict="CLOSE", porteur="backlog nomme : dn9-99"),
     "toute cle de porteur EXISTE au tracker (⛔ tous verdicts)"),
    ("F5-hors-connaissance",
     "une forme 5 `—` sur un verdict qui n'est pas CONNAISSANCE",
     dict(verdict="BLOQUEE", porteur="—"),
     "la forme 5 `—` est reservee a CONNAISSANCE"),
    ("V-verdict-hors-liste",
     "un verdict qui n'est pas l'un des CINQ",
     dict(verdict="REPORTEE", porteur="dn4-40"),
     "tout verdict est l'un des CINQ"),
    # ── Les controles voisins, pour retrecir « gardes par rien » ────────────
    ("G1-preuve-vide",
     "un champ preuve VIDE",
     dict(verdict="PORTEE", porteur="dn4-40", preuve=""),
     "tout champ preuve est non vide"),
    ("G2-preuve-adresse-nue",
     "une preuve qui se REDUIT a un `fichier:ligne`",
     dict(verdict="PORTEE", porteur="dn4-40", preuve="dn_ui.c:9948"),
     "aucune preuve ne se REDUIT a un `fichier:ligne`"),
    ("G3-date-invalide",
     "une date de disposition qui n'existe pas",
     dict(verdict="PORTEE", porteur="dn4-40", date="2026-13-45"),
     "toute date de disposition est une date reelle"),
    ("G4-marqueur-hors-liste",
     "un marqueur de tete hors de la liste fermee",
     dict(verdict="PORTEE", porteur="dn4-40", marqueur="🥕"),
     "aucun marqueur de tete n'est HORS LISTE"),
    ("G5-sans-disposition",
     "une entree ouverte SANS ligne de disposition",
     dict(verdict=None, porteur=None),
     "toute entree ouverte a une ligne de disposition"),
    ("G6-multi-disposition",
     "une entree qui porte DEUX lignes de disposition",
     dict(verdict="PORTEE", porteur="dn4-40", double=True),
     "une entree porte UNE seule ligne de disposition"),
]

# ── LE MUTANT DE TRACKER — le FAUX ROUGE ARME (AC40.1.d) ─────────────────────
# ⚠️ Il ne touche PAS le ledger : il fait passer a `done`, DANS LA COPIE, la
# story que la prose d'une entree parfaitement conforme cite comme FAIT
# BLOQUANT. Avant dn4-40, cette entree rougissait le jour ou cette story
# passait `done` — sans qu'un seul sens ait change.
MUTANT_TRACKER = "D-faux-rouge-arme"


def sites_par_libelle(chemin):
    """Les sites `ctrl()` du SOURCE, indexes par libelle LITTERAL.

    ⛔ Le libelle est lu AU SOURCE, jamais a la console : la console le
    tronque a 62 caracteres et 4 KO y collident deja.
    """
    src = io.open(chemin, encoding="utf-8").read()
    par_lib = {}
    for m in re.finditer(r"ctrl\(\s*(?:not\s+)?[^,]+?,\s*\n?\s*(\"[^\"]*\")",
                         src):
        lib = m.group(1)[1:-1]
        ligne = src.count("\n", 0, m.start()) + 1
        par_lib.setdefault(lib, []).append(ligne)
    return par_lib


def lit_trace(fic):
    """{site: verdict} — le site est la CLE STABLE."""
    # 🔴 REVUE 2026-09-03 — « DERNIERE GAGNE » RENDAIT DES REGRESSIONS
    #    INVISIBLES. Un site dans une boucle est trace une fois par element :
    #    mesure sur la gate du dossier, 30 lignes pour 23 sites, 4 collisions.
    #    Si le 1er element rougit et le dernier passe, l'ancienne lecture
    #    retenait « OK ». ⇒ UN SITE EST KO DES QU'UNE DE SES LIGNES EST KO.
    d = {}
    if not os.path.isfile(fic):
        return d
    for l in io.open(fic, encoding="utf-8"):
        p = l.rstrip("\n").split("\t")
        if len(p) == 3:
            if p[0] in d and d[p[0]][0] == "KO":
                continue
            d[p[0]] = (p[1], p[2])
    return d


def joue(cockpit_src, mutation, tmp):
    """Monte une COPIE du cockpit, applique UNE mutation, joue la gate."""
    faux = os.path.join(tmp, "cockpit")
    dst = os.path.join(faux, os.path.dirname(REL_LEDGER))
    os.makedirs(dst, exist_ok=True)
    led = io.open(os.path.join(cockpit_src, REL_LEDGER), encoding="utf-8").read()
    trk = io.open(os.path.join(cockpit_src, REL_TRACKER), encoding="utf-8").read()
    man_src = os.path.join(cockpit_src, REL_MANIFESTE)
    if os.path.isfile(man_src):
        shutil.copy(man_src, os.path.join(faux, REL_MANIFESTE))
    mute = None
    if mutation:
        led_a, trk_a = led, trk
        led, trk = mutation(led, trk)
        # 🔴 REVUE 2026-09-03 — UNE MUTATION QUI NE CHANGE RIEN REND UN VERT
        #    QUI NE PROUVE RIEN. Mesure : le mutant de tracker visait une cle
        #    COURTE la ou le tracker porte la cle LONGUE ⇒ le `re.sub` ne
        #    mordait pas, le fichier ressortait identique A L'OCTET, et la
        #    campagne imprimait « VERT (attendu) » quoi que fasse la gate.
        mute = (led != led_a) or (trk != trk_a)
    io.open(os.path.join(faux, REL_LEDGER), "w", encoding="utf-8").write(led)
    io.open(os.path.join(faux, REL_TRACKER), "w", encoding="utf-8").write(trk)
    # 🔴 SANS CETTE REGENERATION, LA CAMPAGNE NE MESURE RIEN — MESURE.
    #    Le manifeste est ancre par NUMERO DE LIGNE : inserer une entree
    #    temoin decale les 267 reperes, le controle « chaque ligne du
    #    manifeste REPRODUIT ce que le script produit » rougit, et il
    #    MASQUE le controle que le mutant visait. Premiere passe reelle :
    #    14 mutants sur 14 ne faisaient rougir QUE ce controle-la.
    #    ⇒ On regenere le manifeste DANS LA COPIE (la commande de dn4-39),
    #      pour que le seul rouge restant soit celui qu'on cherche.
    if os.path.isfile(os.path.join(faux, REL_MANIFESTE)):
        subprocess.run([sys.executable, GATE, "--cockpit", faux,
                        "--manifeste", "--en-place"],
                       capture_output=True, text=True)
    tr = os.path.join(tmp, "trace.txt")
    if os.path.isfile(tr):
        os.remove(tr)
    env = dict(os.environ, DN_TRACE_CTRL=tr)
    p = subprocess.run([sys.executable, GATE, "--cockpit", faux],
                       capture_output=True, text=True, env=env)
    return p.returncode, lit_trace(tr), mute


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cockpit", default=os.path.join(
        os.environ.get("HOME") or "/nonexistent", "projects", "compagnon_project"))
    ap.add_argument("--liste", action="store_true")
    ap.add_argument("--gate", default=None,
                    help="jouer contre une AUTRE version de la gate "
                         "(⇒ prouver l'etat AVANT correctif)")
    a = ap.parse_args()

    global GATE
    if a.gate:
        GATE = os.path.abspath(a.gate)

    if a.liste:
        for nom, quoi, _, cible in MUTANTS:
            print("%-24s %s" % (nom, quoi))
            print("%-24s   cible : %s" % ("", cible or "⇒ doit rester VERT"))
        print("%-24s %s" % (MUTANT_TRACKER,
                            "le faux rouge ARME : la story bloquante passe `done`"))
        return 0

    print("=" * 78)
    print("dn4-40 / AC40.7 — CAMPAGNE DE MUTANTS SUR verif_ledger_dn416.py")
    print("=" * 78)
    print("⛔ AUCUNE ecriture dans le cockpit vivant : chaque mutant joue")
    print("   dans une COPIE jetable. Indexation : site d'appel, ⛔ pas console.")

    par_lib = sites_par_libelle(GATE)
    tmp = tempfile.mkdtemp(prefix="dn440-")
    try:
        led0 = io.open(os.path.join(a.cockpit, REL_LEDGER), encoding="utf-8").read()
        ancre = ancre_desknode(led0)
        if ancre is None:
            print("⛔ ancre introuvable dans le ledger — campagne ININTERPRETABLE")
            return 1

        print("\n── T0 : L'ARBRE PROPRE ───────────────────────────────────────")
        rc0, tr0, _ = joue(a.cockpit, None, tmp)
        ko0 = {k for k, v in tr0.items() if v[0] == "KO"}
        print("   rc=%d · %d controle(s) traces · %d KO"
              % (rc0, len(tr0), len(ko0)))
        # 🔴 REVUE 2026-09-03 — LE `rc` ETAIT IMPRIME ET JAMAIS TESTE, ET UNE
        #    TRACE VIDE PASSAIT. Une gate qui meurt avant son premier controle
        #    laissait la campagne se derouler ENTIEREMENT et rendre
        #    « 0 echec(s), 0 controle(s) gardes par rien » — la sortie la plus
        #    rassurante possible AU-DESSUS D'UNE MESURE MORTE.
        if rc0 != 0 or not tr0 or ko0:
            motif = ("rc=%d ⛔ non nul" % rc0) if rc0 != 0 else (
                "⛔ AUCUN controle trace — la gate n'a pas tourne" if not tr0
                else "l'arbre propre n'est pas vert (%d KO)" % len(ko0))
            print("   ⛔ %s — campagne ININTERPRETABLE" % motif)
            return 1

        print("\n── LES MUTANTS ───────────────────────────────────────────────")
        vus = {}
        echecs = []
        for nom, quoi, ch, cible in MUTANTS:
            def mut(led, trk, ch=ch):
                return _mute_ledger(led, ch, ancre_desknode(led)), trk
            rc, tr, mute = joue(a.cockpit, mut, tmp)
            if mute is False:
                echecs.append(nom)
                print("   [!!] %-24s ⛔ MUTATION NULLE — le fichier ressort"
                      " IDENTIQUE, le mutant n'a rien prouve" % nom)
                print("        %s" % quoi)
                continue
            kos = {k for k, v in tr.items() if v[0] == "KO"}
            neufs = kos - ko0
            for k in neufs:
                vus.setdefault(k, []).append(nom)
            if cible is None:
                bon = not neufs
                verdict = "VERT (attendu)" if bon else \
                    "⛔ ROUGE INATTENDU : %s" % ", ".join(sorted(neufs))
            else:
                lignes = par_lib.get(cible, [])
                attendus = {"%s:%d" % (os.path.basename(GATE), l) for l in lignes}
                touche = attendus & neufs
                bon = bool(touche)
                verdict = ("VU ROUGE sur %s" % ", ".join(sorted(touche))) if bon \
                    else "⛔ NON VU (KO neufs : %s)" % (", ".join(sorted(neufs)) or "aucun")
            if not bon:
                echecs.append(nom)
            print("   [%s] %-24s %s" % ("OK" if bon else "!!", nom, verdict))
            print("        %s" % quoi)

        # ── LE MUTANT DE TRACKER : le faux rouge ARME (AC40.1.d) ────────────
        cible_arme = _story_bloquante(led0)
        if cible_arme:
            # 🔴 REVUE 2026-09-03 — CE MUTANT NE MUTAIT RIEN, ET C'ETAIT LA
            #    PREUVE MAITRESSE D'AC40.1.d. `_story_bloquante()` rend une cle
            #    COURTE (`dnN-M`) ; le tracker porte la cle LONGUE
            #    (`dnN-M-un-titre-en-slug`). Le motif `^(  <court>:)` ne pouvait
            #    donc JAMAIS mordre : le tracker ressortait identique a l'octet
            #    et la campagne imprimait « VERT (attendu) » quoi que fasse la
            #    gate. ⇒ on matche la cle COMPLETE par son prefixe, et la garde
            #    de mutation nulle de `joue()` attrape toute rechute.
            def mut_trk(led, trk, c=cible_arme):
                return led, re.sub(
                    r"^(  %s[a-z0-9\-]*:)\s*[a-z\-]+" % re.escape(c),
                    r"\1 done", trk, count=1, flags=re.M)
            rc, tr, mute = joue(a.cockpit, mut_trk, tmp)
            neufs = {k for k, v in tr.items() if v[0] == "KO"} - ko0
            bon = (mute is not False) and not neufs
            if not bon:
                echecs.append(MUTANT_TRACKER)
            print("   [%s] %-24s %s" % ("OK" if bon else "!!", MUTANT_TRACKER,
                                        "VERT (attendu)" if bon
                                        else ("⛔ MUTATION NULLE — le tracker"
                                              " ressort IDENTIQUE"
                                              if mute is False
                                              else "⛔ ROUGE : %s"
                                              % ", ".join(sorted(neufs)))))
            print("        `%s` passee `done` DANS LA COPIE ⇒ la gate doit"
                  " rester verte" % cible_arme)
        else:
            print("   [--] %-24s ⚠️ aucune prose ne cite de story comme fait"
                  " bloquant" % MUTANT_TRACKER)

        # ── LA SECONDE FACE : LES CONTROLES GARDES PAR RIEN ─────────────────
        print("\n── `controle ⇒ couvert` : LES CONTROLES GARDES PAR RIEN ───────")
        print("   ⛔ « N mutants, N vus rougir » prouve `mutant ⇒ rouge`.")
        print("      Ce compte-ci est l'AUTRE sens, et c'est celui qui manque.")
        tous = sorted(tr0)
        nus = [k for k in tous if k not in vus]
        print("   controles traces          : %d" % len(tous))
        print("   controles vus rougir      : %d" % len(vus))
        print("   ⚠️ GARDES PAR RIEN        : %d" % len(nus))
        for k in nus:
            print("        %-34s %s" % (k, tr0[k][1][:52]))

        print("\n" + "=" * 78)
        print("BILAN CAMPAGNE : %d mutant(s), %d echec(s), %d controle(s)"
              " gardes par rien" % (len(MUTANTS) + 1, len(echecs), len(nus)))
        print("=" * 78)
        return 1 if echecs else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _story_bloquante(led):
    """La story citee dans la PROSE d'un `bloquee par :` — le faux rouge ARME.

    ⛔ Ce n'est PAS un porteur : c'est un FAIT. Avant dn4-40, `findall` la
    ramassait quand meme ⇒ l'entree rougissait le jour ou elle passait `done`.

    ⚠️ REVUE 2026-09-03 — ELLE REND UNE CLE **COURTE** (`dnN-M`), et le tracker
    porte la cle **LONGUE**. Tout appelant qui la compare a une cle de tracker
    doit donc matcher PAR PREFIXE. C'est ecrit ici parce que l'ignorer a rendu
    le mutant d'AC40.1.d entierement INOPERANT sans qu'aucune sortie ne le dise.
    """
    for m in re.finditer(r"porteur\s*:\s*(bloqu\w*\s+par\s*:[^·]*)·", led):
        c = re.search(r"\b(dn\d+-\d+)\b", m.group(1), re.I)
        if c:
            return c.group(1).lower()
    return None


if __name__ == "__main__":
    sys.exit(main())
