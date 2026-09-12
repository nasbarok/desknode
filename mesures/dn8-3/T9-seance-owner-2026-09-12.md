# `dn8-3` / T9 — LA SEANCE OWNER DU 2026-09-12, SUR LA PAGE **SERVIE**

> 🔴 **CE FICHIER EST UNE MESURE, ⛔ PAS UN PROTOCOLE.** L'instrument est **l'ŒIL DE
> L'OWNER**, et c'est declare. Les observations sont rapportees **telles qu'elles ont ete
> faites**, ⛔ pas resumees.
> **Date** : 2026-09-12 · **Produit mesure** : la tour REDEPLOYEE a `d33166d` le meme jour
> a 14:40:44 — ⛔ pas la copie perimee du 2026-08-28.

## Ce qui rendait cette seance possible, et qui ne l'etait pas ce matin

`mesures/dn8-3/T4-refus-cote-tour.txt` avait mesure que la tour portait `e3064f0`
(2026-08-28) avec **ZERO** occurrence de `exit 12`. ⇒ une seance jouee avant redeploiement
aurait mesure un produit d'il y a deux semaines. **Le redeploiement a eu lieu d'abord** :
les 5 fichiers identiques, `PROVENANCE.txt` a jour, `exit 12` x3 et `-Lhm` x2 presents.
Pre-vol depuis le partage WSL : **`ERRORLEVEL=0`**, charge **intacte (CRC32 verifie)**,
`psutil` / `pyserial` / **LibreHardwareMonitor presents**. `dn_lhm_tour.ps1` : **rc=0**.

---

## Geste C — 🔴 **POSITION ACTIVE : RELEVEE**   (ferme `AC7.4.3`)

**Question posee** : les **deux** selecteurs de langue — celui de la page en tete, celui de
la dalle a l'etape 3 — montrent-ils leur position active **REMPLIE**, lisible **sans
survoler et sans comparer** ?

**REPONSE DE L'OWNER, VERBATIM** : *« position active oik »* ⇒ **OUI**.

⇒ **C'EST L'INSTRUMENT QUI FERMAIT `AC7.4.3`, ET IL A RENDU SON VERDICT.** Le defaut que
`dn7-4` avait mesure — les deux regles d'etat portant **rigoureusement** les declarations de
`button:hover:enabled`, donc « selectionne » et « survole » **indiscernables** — est
**resolu a l'œil sur la page servie**, et ⛔ pas seulement garde par `verif_placement_dn74.py`.

## Geste A — le verdict d'un verbe s'ecrit **SOUS LE BOUTON**   (ferme la moitie a l'ŒIL d'`AC7.4.1`)

**REPONSE DE L'OWNER** : *« arreter l'agent ok ! »* puis *« retirer l'agent ok ! »*, avec le
bloc de verdict de la page colle. ⚠️ La page **affiche la commande qu'elle lance**
(`installeur/index.html:2068`, `"$ " + d.commande`) : le collage est donc bien **la sortie de
la page**, ⛔ pas un tir en terminal.

Verdict rendu sous « Arreter l'agent et rendre le port » :

    === STOP ===
      aucun agent reconnu.
    === PREUVE : ON RE-OUVRE LE PORT ===
      python.exe vivants : 2  (portant dn_agent.py : 0 | CommandLine ILLISIBLE : 0)
      port COM3 : libre
      usbipd : 3-5 303a:1001 Peripherique serie USB (COM3) ... Shared
      marqueur : absent
      OK - COM3 se REOUVRE : le port est rendu.
    code de retour : 0  - rendu par l'outil
    le port a ete REOUVERT apres l'arret : il est rendu. C'est l'ouverture qui fait foi,
    PAS le code de retour.

⚠️ **CE QUE CE TIR N'EXERCE PAS, ET C'EST DIT** : « aucun agent reconnu » parce que l'agent
avait deja ete arrete ~20 min plus tot, au redeploiement. ⇒ ce geste exerce **LA PLACE DU
VERDICT**, ⛔ pas un arret reel. La preuve du port, elle, est jouee : COM3 se rouvre.

Verdict rendu sous « Retirer l'agent », en section 4 :

    $ powershell -NoProfile -ExecutionPolicy Bypass -File H:\dev\projets\desknode\dn_agent_tour.ps1 retirer -Serie COM3
    === RETRAIT DE LA TACHE ===
      tache 'DeskNode agent' ABSENTE - retrait verifie.
      /!\ L'AGENT N'EST PLUS LA APRES LE RETRAIT.
      /!\   Le Planificateur a termine l'arbre d'action de la tache : le bilan
      /!\   de fin est PERDU (TerminateProcess, aucun --stop-si lu).
      /!\   => la prochaine fois, jouer 'dn-agent.bat stop' AVANT 'retirer'.
    code de retour : 0  - rendu par l'outil
    la tache << DeskNode agent >> est ABSENTE - re-interrogee apres coup.

🔴 **LA COMMANDE CITEE NOMME `H:\dev\projets\desknode\dn_agent_tour.ps1`** — la copie
**REDEPLOYEE**. La seance a donc tourne contre le produit neuf, ⛔ pas le perime.
✅ Et la tache est **RE-INTERROGEE APRES COUP**, ⛔ pas deduite du message : c'est la
propriete que `dn7-5` avait posee.

## Geste B — le selecteur **ANNULE** dit le fait exact   (ferme le residu d'`AC7.4.2`)

**REPONSE DE L'OWNER** : *« 3 oui »*, avec le texte rendu par la page :

    Aucun port n'a ete choisi.
    Le selecteur a ete ferme sans selectionner la ligne. Rien n'est ouvert, et rien n'a ete
    lu. Recliquez le bouton, puis cliquez la ligne avant de valider.
    (NotFoundError: Failed to execute 'requestPort' on 'Serial': No port selected by the user.)
    Cette page ne tient PAS le port serie - rien de notre fait ne le retient.

⇒ **C'EST LE MESSAGE NEUF, MOT POUR MOT**, et ⛔ **PAS** l'ancienne supposition *« le plus
souvent, un selecteur est deja ouvert »*. Le domaine de `langue.port-indisponible` a bien
**RETRECI** au seul cas ou sa phrase est vraie, comme `AC7.4.2` le demandait.

---

## ⛔ CE QUE CETTE SEANCE NE FERME PAS

- **`AC8.3.3`** reste **BLOQUEE** : le bouton reellement grise, « Activer l'agent » constate
  **vivant par requete**, le geste `pip` **et son temps** (plafond **900 s**, toujours
  ⛔ jamais confronte a une mesure), le verdict de `pip` indisponible, et **la course au
  logon**. Protocole : `mesures/dn7-6/T2-A-JOUER-COTE-WINDOWS.md`.
- **`AC7.5.3`** — le refus cote tour dans les deux sens (`mesures/dn7-5/T2-b-3`) ⛔ n'a pas
  ete joue. Il est desormais **jouable** : le refus est deploye.

## ⚠️ DEUX FAITS D'ETAT LAISSES SUR LA MACHINE

1. 🔴 **LA TACHE AU LOGON EST RETIREE.** Le geste « Retirer l'agent » l'a supprimee, et le
   retrait est **verifie**. ⇒ **l'agent ⛔ ne redemarrera PAS au prochain logon** tant que la
   permanence n'est pas reposee : `dn-agent.bat permanence`, ou le bouton de la page.
2. L'agent **ne tourne pas**. Pour le relancer : `H:\dev\projets\desknode\dn-agent.bat start`.
