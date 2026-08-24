#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dn4-13 / AC7 — LES HARNAIS NE CONCLUENT PLUS SUR DES LECTURES QUI N'ONT PAS EU
LIEU. Jouable depuis WSL, ⛔ sans carte.

======================= CE QUE CET OUTIL FAIT ==============================

Il fait DEUX choses, et rien d'autre :

  1. IL JOUE LES TROIS TÉMOINS NÉGATIFS des harnais corrigés
     (`temoins_ac2_dn44.py`, `diag_p1_dn44.py`, `anim_courbe_dn44.py`), en
     appelant leurs VERDICTS EXTRAITS avec des entrées fabriquées.
     🔴 AC7.5 : *« une gate qu'aucun test n'a vue échouer est décorative »*.
     Les trois harnais ont donc chacun un `--temoin-negatif` qui leur donne des
     entrées qui DOIVENT les faire rougir — et on vérifie qu'elles les font
     rougir.

  2. IL CHASSE LES RÉFÉRENCES FANTÔMES (AC7.4). `dn_console.py` renvoyait à
     *« la fonction `drainer()` des harnais de dn4-4 »* — une fonction QUI
     N'EXISTAIT NULLE PART. Un lecteur qui suit le renvoi cherche du vide, et
     un dépôt qui nomme ce qui n'est pas ne peut pas être relu. Le contrôle est
     donc GÉNÉRALISÉ à tout `tools/*.py` : toute mention entre accents graves
     d'une fonction du dépôt doit correspondre à du code QUI EXISTE.

⛔ CE QU'IL NE FAIT PAS : il ne parle pas à la carte. Aucun de ces témoins ne
   dit que la propagation marche ; ils disent que L'INSTRUMENT ne peut plus
   rendre vert sans avoir lu. Les quatre témoins d'AC2 se tirent EN SÉANCE.

Sortie : exit 0 si tout passe, 1 sinon. Publie le sha256 des sources LUES.
"""

import hashlib
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(RACINE, "tools")

HARNAIS = ["temoins_ac2_dn44.py", "diag_p1_dn44.py", "anim_courbe_dn44.py"]

ok_total = [0]
ko_total = [0]


def lire(chemin):
    with open(chemin, "rb") as f:
        brut = f.read()
    return brut.decode("utf-8"), hashlib.sha256(brut).hexdigest()[:16]


def ctrl(ok, libelle, detail=""):
    if ok:
        ok_total[0] += 1
        print("  [OK ] %-54s %s" % (libelle, detail))
    else:
        ko_total[0] += 1
        print("  [KO ] %-54s %s" % (libelle, detail))
    return ok


def sans_code(txt):
    """Ne garde QUE les commentaires et les docstrings — c'est là que vivent les
    renvois. ⛔ Chercher dans le code entier confondrait un APPEL (qui prouve
    l'existence) avec un RENVOI (qui la suppose)."""
    morceaux = []
    for m in re.finditer(r'"""(.*?)"""', txt, re.S):
        morceaux.append(m.group(1))
    for ligne in txt.split("\n"):
        i = ligne.find("#")
        if i >= 0:
            morceaux.append(ligne[i:])
    return "\n".join(morceaux)


def _py_du_depot():
    """Tous les `.py` du dépôt qui portent du code à nous : `tools/` **et**
    `agent/`. ⛔ Oublier `agent/` faisait passer `_lire_corps()` pour un fantôme
    alors qu'il est défini dans `dn_agent.py` — un instrument qui cherche au
    mauvais endroit fabrique un rouge PLAUSIBLE."""
    for d in (TOOLS, os.path.join(RACINE, "agent")):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".py"):
                yield d, f


def fonctions_du_depot():
    """{nom: [fichiers]} pour toute fonction (ou méthode) définie chez nous."""
    out = {}
    for d, f in _py_du_depot():
        txt, _ = lire(os.path.join(d, f))
        for m in re.finditer(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", txt, re.M):
            out.setdefault(m.group(1), []).append(f)
    return out


def code_des_outils():
    """Le CODE (⛔ pas les commentaires) de tous nos `.py`, concaténé."""
    morceaux = []
    for d, f in _py_du_depot():
        txt, _ = lire(os.path.join(d, f))
        txt = re.sub(r'"""(.*?)"""', " ", txt, flags=re.S)
        txt = re.sub(r"#[^\n]*", " ", txt)
        morceaux.append(txt)
    return "\n".join(morceaux)


def code_du_firmware():
    """Le source C du firmware — pour reconnaître un nom de fonction EMBARQUÉE."""
    d = os.path.join(RACINE, "firmware", "desknode", "main")
    morceaux = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".c") or f.endswith(".h"):
            txt, _ = lire(os.path.join(d, f))
            morceaux.append(txt)
    return "\n".join(morceaux)


# Les noms cités dans les commentaires qui ne sont PAS des fonctions de `tools/`
# et n'ont pas à l'être : API tierce, commandes du firmware, méthodes d'objets.
HORS_PERIMETRE = {
    # pyserial / stdlib
    "reset_input_buffer", "read", "write", "flush", "close", "sleep", "open",
    "in_waiting", "encode", "decode", "print", "int", "len", "set", "range",
    # firmware / console de la carte
    "esp_restart", "lv_chart_set_x_start_point", "lv_chart_refresh",
    "lv_obj_invalidate", "lv_label_set_text", "case_poser",
    "detail_reparametrer", "courbe_reparametrer", "build_scene",
    "dn_hist_poser", "dn_hist_minmax", "dn_hist_series_de_case",
    "dn_hist_octets", "dn_hist_couverture_s", "dn_hist_init", "dn_hist_reels",
    "dn_ui_pc_maj", "dn_ui_regime", "dn_val_regime_nom",
    "dn_val_regime_couleur", "dn_link_ingest_ligne", "pousser_metrique",
    "cmd_widget", "selections_auditer", "dn_widget_unite", "composer",
    "ui_case_origine", "dn_ui_case_rect", "dn_widget_largeur",
    "lv_chart_set_series_ext_y_array", "dn_hist_rattraper", "dn_hist_ecrits",
    "dn_ui_set_detail_panh", "dn_ui_garde_hauteur", "dn_ui_detail_courbe_axes",
    "lv_chart_hide_series", "lv_chart_set_range", "lv_chart_set_series_color",
    "esp_timer_get_time", "lvgl_port_pause", "lvgl_port_lock",
    "dn_measure_wait_vsync", "wait_frame_done", "dn_touch_read",
    "esp_lcd_touch_read_data", "lv_indev_reset", "lv_timer_enable",
    "dn_ui_nav_open", "lv_chart_get_series_color", "lv_screen_active",
    "built_in_font_gen",
    # 🔴 API TIERCES NOMMÉES EN PROSE, jamais appelées par nous : elles EXISTENT,
    #    elles ne sont simplement pas de ce dépôt. Les lister est le prix à payer
    #    pour que la gate reste capable de voir un VRAI fantôme.
    "create_time",
}


def bloc_fantomes():
    """AC7.4 — un renvoi vers du code qui n'existe pas.

    🔴 LA RÈGLE, ET POURQUOI ELLE EST À TROIS TERMES. Une mention `` `nom()` ``
       dans un commentaire est LÉGITIME si `nom` est :
         (a) DÉFINI dans `tools/` — c'est le cas nominal ;
         (b) APPELÉ dans notre code (`tools/` + `agent/`) — méthode d'une tierce
             (`cpu_percent()`, `getresponse()`, `monotonic()`) : elle existe, elle
             n'est simplement pas de nous ;
         (c) présent dans le SOURCE C du firmware — la console de la carte et ses
             fonctions embarquées se citent constamment ici.
       ⇒ Est FANTÔME ce qui n'est NI défini, NI appelé, NI embarqué. C'était
         exactement le cas de `drainer()` : promis par `dn_console.py` depuis
         `dn4-4`, appelé nulle part, défini nulle part.
    ⚠️ ⛔ CETTE GATE COUVRE **TOUT** `tools/`, ⛔ pas seulement les 3 harnais de
       cette story : « une gate scopée à UNE fonction peut épingler VERT le même
       défaut ailleurs ».
    """
    print("\n── AC7.4 — AUCUN RENVOI VERS UNE FONCTION QUI N'EXISTE PAS ────────")
    connues = fonctions_du_depot()
    code_py = code_des_outils()
    code_c = code_du_firmware()
    fantomes = []
    cites = 0
    for f in sorted(os.listdir(TOOLS)):
        if not f.endswith(".py"):
            continue
        txt, _ = lire(os.path.join(TOOLS, f))
        for m in re.finditer(r"`([a-z_][a-z0-9_]*)\(\)`", sans_code(txt)):
            nom = m.group(1)
            cites += 1
            if nom in HORS_PERIMETRE or nom in connues:
                continue
            if re.search(r"\b" + re.escape(nom) + r"\s*\(", code_py):
                continue  # (b) appelé quelque part dans nos outils
            if nom in code_c:
                continue  # (c) fonction du firmware, citée à raison
            fantomes.append((f, nom))
    for f, nom in fantomes:
        ctrl(False, "renvoi FANTÔME : `%s()`" % nom,
             "cité par tools/%s, défini NULLE PART" % f)
    ctrl(not fantomes,
         "les %d renvois en accents graves des commentaires existent tous"
         % cites, "%d fantôme(s)" % len(fantomes))

    # 🔴 LE CHASSEUR EST-IL CAPABLE DE VOIR ? ⛔ Un contrôle qui rend vert sur un
    #    dépôt sain sans avoir jamais vu un rouge est décoratif (AC7.5). On lui
    #    fabrique DEUX cas : un fantôme évident, et un renvoi LÉGITIME qu'il ne
    #    doit PAS confondre avec lui.
    # ⚠️ LE NOM EST **ASSEMBLÉ**, ⛔ pas écrit d'un bloc. Écrit d'un bloc, il
    #    apparaissait dans CE fichier sous la forme `nom(` — donc `code_py`, qui
    #    inclut la gate elle-même, le voyait « appelé quelque part », et le
    #    chasseur ne le détectait pas. Le témoin échouait pour une raison qui
    #    n'avait rien à voir avec ce qu'il teste : l'instrument se prenait
    #    lui-même dans son propre filet.
    nom_faux = "une_fonction_" + "qui_n_existe_" + "pas"
    faux = "# renvoi vers `%s()`, cf. dn4-4" % nom_faux
    vus = [m.group(1) for m in re.finditer(r"`([a-z_][a-z0-9_]*)\(\)`",
                                           sans_code(faux))]
    detecte = (nom_faux in vus and nom_faux not in connues
               and not re.search(r"\b" + re.escape(nom_faux) + r"\s*\(", code_py)
               and nom_faux not in code_c)
    ctrl(detecte, "le chasseur VOIT un fantôme fabriqué", "`%s()`" % nom_faux)
    vrai = "# la parade est `drainer()`, cote appelant"
    vus2 = [m.group(1) for m in re.finditer(r"`([a-z_][a-z0-9_]*)\(\)`",
                                            sans_code(vrai))]
    ctrl("drainer" in vus2 and "drainer" in connues,
         "…et il ne confond PAS un renvoi légitime avec un fantôme",
         "`drainer()` est reconnu comme défini")
    ctrl("drainer" in connues and "dn_console.py" in connues.get("drainer", []),
         "`drainer()` existe, et il vit dans `dn_console.py`",
         "⛔ il était PROMIS depuis dn4-4 sans exister")
    anim, _ = lire(os.path.join(TOOLS, "anim_courbe_dn44.py"))
    ctrl("dn_console.drainer(" in anim,
         "`anim_courbe_dn44.py` APPELLE `drainer()`",
         "⛔ la boucle inline est remplacée, pas doublée")
    ctrl("while time.time() < fin:" not in anim,
         "…et la boucle de drainage inline a bien DISPARU",
         "sinon deux drainages coexisteraient")


def bloc_temoins():
    print("\n── AC7.5 — LES TROIS TÉMOINS NÉGATIFS SONT JOUÉS ──────────────────")
    for h in HARNAIS:
        chemin = os.path.join(TOOLS, h)
        r = subprocess.run([sys.executable, chemin, "--temoin-negatif"],
                           capture_output=True, text=True)
        lignes = [l for l in r.stdout.split("\n") if l.strip()]
        rouges = [l for l in lignes if "🔴" in l]
        resume = lignes[-1][:60] if lignes else "(aucune sortie)"
        ctrl(r.returncode == 0 and not rouges, "témoin négatif : %s" % h,
             "exit %d · %s" % (r.returncode, resume))
        if r.returncode != 0 or rouges:
            for l in rouges[:6]:
                print("        " + l.strip())
            if r.stderr.strip():
                print("        stderr : " + r.stderr.strip()[:200])


def bloc_sentinelles():
    """Le contrôle STRUCTUREL : une sentinelle se teste AVANT d'être comparée."""
    print("\n── AC7.1 + AC7.2 — LA SENTINELLE EST TESTÉE **AVANT** L'USAGE ─────")
    t, _ = lire(os.path.join(TOOLS, "temoins_ac2_dn44.py"))
    ctrl("def lu(" in t and t.count("if not lu(") >= 4,
         "les 4 verdicts d'AC2 appellent `lu()` en PREMIER",
         "%d appels" % t.count("if not lu("))
    # ⛔ ON COMPTE DANS LE **CODE**, pas dans la prose : la docstring CITE la
    #    sentinelle trois fois pour expliquer le défaut, et c'est exactement ce
    #    qu'on veut qu'elle fasse. Un compteur qui lit les commentaires aurait
    #    fait rougir la documentation du correctif.
    t_code = re.sub(r'"""(.*?)"""', " ", t, flags=re.S)
    t_code = re.sub(r"#[^\n]*", " ", t_code)
    n_lit = t_code.count('"<NON RELU>"')
    ctrl(n_lit == 1,
         "la sentinelle d'AC2 est NOMMÉE une seule fois dans le code",
         "%d littéral(aux) — la constante `NON_RELU`" % n_lit)
    d, _ = lire(os.path.join(TOOLS, "diag_p1_dn44.py"))
    ctrl("def delta_compteur(" in d and "NON_RELU_INT" in d,
         "`diag_p1` teste `-1` AVANT toute soustraction publiée",
         "`delta_compteur()` rend `None`, ⛔ pas `0`")
    ctrl(re.search(r"if a\.tours < 2:", d) is not None
         and "if len(lignes) < 2:" in d,
         "`--tours >= 2` est gardé DANS l'argparse **et** dans le verdict",
         "⛔ une garde d'interface seule est contournable")
    a, _ = lire(os.path.join(TOOLS, "anim_courbe_dn44.py"))
    ctrl("_trames_acceptees" in a and "n_ecrites" in a,
         "`anim_courbe` distingue ÉCRITES et ACCEPTÉES",
         "⛔ « N trames emises » n'était pas une mesure")
    ctrl("mock_coupe" in a and "REFUS" in a,
         "…et il REFUSE de démarrer si le mock n'est pas RELU coupé",
         "G3 armée ⇒ aucune trame réelle n'atteint l'écran")
    ctrl('dn_console.envoyer(ser, f"nav open' in a,
         "…et `nav open` est RELU, ⛔ plus seulement écrit",
         "`ESP_ERR_INVALID_STATE` si la vue était déjà l'active")


def main():
    print("=" * 78)
    print("dn4-13 / AC7 — LES HARNAIS, ÉPROUVÉS HORS CARTE")
    print("=" * 78)
    for f in HARNAIS + ["dn_console.py"]:
        _, sha = lire(os.path.join(TOOLS, f))
        print("  %-24s sha256[:16] = %s" % (f, sha))

    bloc_temoins()
    bloc_sentinelles()
    bloc_fantomes()

    print("\n" + "=" * 78)
    print("⚠️ CE QUE CETTE GATE NE SOLDE PAS : les quatre témoins d'AC2 eux-mêmes,")
    print("   qui se tirent SUR LA CARTE (AC11.4), et le constat owner à l'œil sur")
    print("   les formes d'`anim_courbe`. Elle prouve que les INSTRUMENTS ne")
    print("   peuvent plus conclure sur du vide, ⛔ pas que la carte a raison.")
    if ko_total[0] == 0:
        print("✅ %d contrôles passent, 0 échec." % ok_total[0])
        return 0
    print("⛔ %d ÉCHEC(S) sur %d contrôles."
          % (ko_total[0], ok_total[0] + ko_total[0]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
