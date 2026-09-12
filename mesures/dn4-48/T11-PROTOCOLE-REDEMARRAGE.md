# `dn4-48` / T11 — LE REDEMARRAGE QUI FERME `AC48.3`   (⛔ À JOUER, PAS ENCORE MESURÉ)

> 🔴 **C'EST UN PROTOCOLE, ⛔ PAS UNE MESURE.** Aucun chiffre ici n'est un
> résultat. L'instrument est **l'ŒIL DE L'OWNER** plus trois requêtes.

## L'ÉTAT FIGÉ **AVANT** LE REDÉMARRAGE — c'est lui qui rend le après lisible

    code déployé sur la tour : 9e8107b  (PROVENANCE.txt, déposé ce jour)
    tâche au logon           : POSÉE, RunLevel=Limited
      action : ... dn_agent_tour.ps1 tache -Serie COM3 -Duree 0  -AttenteLhm 300
      RestartCount=3 · RestartInterval=PT1M   (⛔ INCHANGÉS)
    LastRunTime=09/12/2026 18:13:13 LastTaskResult=12
    dn-agent.log             : 995526 o
    agent                    : ARRÊTÉ, COM3 rendu

⚠️ **`LastTaskResult = 12` CI-DESSUS EST LA PANNE DU 2026-09-12**, laissée telle
quelle exprès : c'est l'ancien refus dur. S'il vaut encore `12` après le
redémarrage, la marche **N'A RIEN CHANGÉ**. S'il passe à `0`, le refus est mort.

## LE GESTE

**Redémarrer la tour.** ⛔ **NE RIEN LANCER À LA MAIN** ensuite — ⛔ ni
`dn-agent.bat start`, ⛔ ni le bouton de la page. Tout l'intérêt est que
**seule la tâche au logon** ait tiré.

⚠️ **CE REDÉMARRAGE TUE LA SESSION WSL** (et donc l'agent Claude). Les preuves
ci-dessous sont **sur disque** : elles survivent, et se relisent après.

## CE QU'IL FAUT RELEVER, ET CE QUE CHAQUE RELEVÉ TRANCHE

**(1) À L'ŒIL, LE SEUL QUI FERME `AC48.3`** — la dalle se remplit-elle **sans que
personne n'ait rien lancé** ? Et si LHM manque : **une boîte de message
est-elle apparue**, disant POURQUOI ?

**(2) LA TÂCHE, RE-DEMANDÉE AU SYSTÈME** (⛔ pas déduite d'un message) :

    powershell -NoProfile -Command "Get-ScheduledTask -TaskName 'DeskNode agent' | Get-ScheduledTaskInfo | Format-List LastRunTime,LastTaskResult,NextRunTime"

  · `LastTaskResult = 0`  ⇒ le pré-vol est passé (LHM là, ou arrivé pendant l'attente).
  · `LastTaskResult = 12` ⇒ ⛔ **LA MARCHE A ÉCHOUÉ** : le refus dur est encore là.
  · `LastRunTime` **doit** avoir bougé. S'il vaut encore `18:13:13`, la tâche
    ⛔ **n'a pas tiré du tout** — c'est un AUTRE défaut, ⛔ pas celui-ci.

**(3) AVEC QUOI L'AGENT A DÉMARRÉ** — la ligne que le pré-vol écrit :

    type H:\dev\projets\desknode\dn-agent.started

  Chercher la ligne `lhm :`.
  · `lhm : repond 200 sur http://...`           ⇒ LHM était là, ou est arrivé.
  · `lhm : DEMARRAGE DEGRADE - ABSENT (attendu N s ...)` ⇒ le dégradé a joué,
    et **la dalle doit être VIVANTE quand même**, 4 champs à ` -- `.

**(4) L'ATTENTE A-T-ELLE SERVI ?** C'est la preuve DIRECTE que le correctif a
mordu — chercher les lignes de tour dans le journal :

    findstr /C:"on ATTEND (" H:\dev\projets\desknode\dn-agent.log

  · **Au moins une ligne** ⇒ 🎯 **LHM était en retard, et l'agent l'a ATTENDU
    au lieu de mourir.** C'est exactement la panne du 2026-09-12, rejouée et
    survécue.
  · **Aucune ligne** ⇒ LHM était debout dès le premier tir de sonde. Le cas du
    retard ⛔ n'a PAS été exercé ce coup-ci — ⛔ ce n'est **pas** un échec, c'est
    un tirage qui n'a pas sorti le cas. Le dire, ⛔ ne pas le maquiller.

**(5) L'INSTRUMENT QUI DIT TOUT SANS RIEN CHANGER** :

    H:\dev\projets\desknode\dn-agent.bat etat

  Il redit la dégradation à la demande, et nomme la tâche.

## ⛔ CE QUE CE REDÉMARRAGE NE PROUVERA PAS

⛔ Il ⛔ ne prouve **rien** du cas « LHM ne vient **JAMAIS** » si LHM démarre
normalement. Ce cas-là est joué mécaniquement par `tools/verif_lhm_ps_dn83.py`
(sens DÉGRADÉ), ⛔ pas ici.
⛔ Et il ⛔ ne dit rien de la **lisibilité** de la boîte de message : ça, c'est
l'œil, et l'œil seul.

---

## ✅ RELEVÉ DU REDÉMARRAGE — 2026-09-12, ~23:10   (⛔ plus un protocole : une MESURE)

**CONSTAT OWNER, VERBATIM** : *« ok ! good la dalle se rempli bien au redemarrage »*.
Rien n'a été lancé à la main.

    tâche tirée        23:09:09   LastTaskResult = 267009 (0x41301 = TÂCHE EN COURS)
    LHM démarré        23:09:44   (35 s APRÈS le tir de la tâche)
    pré-vol terminé    23:10:12   (dn-agent.started, 28 s après LHM)
      lhm : repond 200 sur http://127.0.0.1:8085/metrics
    agents vivants     1

🎯 **LE CAS DU 12/09 A ÉTÉ REJOUÉ, ET SURVÉCU.** La tâche a tiré **35 s avant** LHM —
le 12/09, avec **21 s** d'écart, l'ancien refus sortait en `12` et la dalle restait
morte. Aujourd'hui : `LastTaskResult` ⛔ n'est plus `12` (il vaut « en cours », parce
que la tâche porte l'agent au premier plan), l'agent tourne, **complet**.

🔴 **LE DISCRIMINANT (4) DE CE PROTOCOLE ÉTAIT FAUX, ET LA MESURE L'A DIT.** Il
cherchait les lignes `on ATTEND (` dans `dn-agent.log` : **0 ligne**. ⛔ Ça ne prouve
PAS que le pré-vol n'a pas attendu — en régime tâche, `:RUN` lance `prevol` **SANS
redirection** (`tools/dn-agent.bat`), sa sortie part dans une console CACHÉE et
**n'est écrite nulle part**. « 0 ligne » est une propriété de la MÉTHODE.
⇒ l'attente est **inférée du minutage** (tâche 35 s avant LHM, pré-vol fini 63 s
après le tir), ⛔ pas lue.
⚠️ Et c'est un **écart à la marche** : elle promettait que « le journal de la tâche »
dirait ce qui se passe pendant l'attente. En régime tâche, **ce journal n'existe pas**.

⛔ **CE QUI RESTE NON FERMÉ** : `AC48.3` (le POURQUOI qui atteint un humain) ⛔ n'a PAS
été exercé — LHM est venu, donc aucun démarrage dégradé, donc aucun `msg.exe`.
