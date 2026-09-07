PROVENANCE DES FIXTURES
=======================

dn63-citations-temoins.md
-------------------------
  Origine   : ECRITE pour `dn6-3` (2026-09-07). ⛔ Ce n'est PAS une capture :
              c'est un PORTEUR DE JETON, dont le seul role est d'etre RENCONTRE
              par `tools/verif_photos_dn63.py` (c5) a chaque passe.
  Contenu   : le nom `install_01.jpg` cite entre accents graves — un nom
              d'image qui ⛔ ne suit PAS la convention de `docs/cablage/` et
              dont le fichier n'est PAS au depot.
  Motif     : le temoin etait ancre sur `hardware/…-capteurs-i2c.md` SEUL
              (2 occurrences mesurees). Or ce dossier est le territoire d'une
              marche VIVANTE, et le perimetre de `dn6` interdit de l'ecrire :
              le jour ou elle passe, (c5) serait sorti « JAMAIS VU » et cette
              marche n'aurait ⛔ PAS eu le droit de la reparer.
  ⚠️ Un temoin negatif qui depend d'un fichier que sa propre marche ne peut
     pas ecrire n'est pas un temoin : c'est une dette.

lhm_metrics_2026-08-21.txt
--------------------------
  Origine   : `GET http://127.0.0.1:8085/metrics` sur DESKTOP-08RT3CL
              (MSI X99A MPOWER MS-7885, Intel i7-6900K, Win10 Pro 19045)
  Producteur: LibreHardwareMonitor 0.9.6, build .NET Framework, lance ELEVE,
              driver noyau PawnIO 2.2.0 (KERNEL_DRIVER / RUNNING)
  Date      : 2026-08-21, seance TOUR de la story dn4-8 (AC1)
  Contenu   : 260 capteurs, dont le Super I/O `nct6792d` (31 capteurs) et
              7 ventilateurs. ⚠️ DEUX ventilateurs a 0 RPM : la sonde EXISTE,
              elle n'est PAS absente (`/fan/3` et `/fan/5` -- le 200 mm de
              facade n'a pas de fil tachymetrique, 0 RPM DANS LE BIOS AUSSI).

🔴 CE QUE CETTE FIXTURE EST, ET CE QU'ELLE N'EST PAS
  ✅ Elle est une capture REELLE, non retouchee, d'une machine reelle : elle
     sert a exercer le PARSEUR et les chemins d'echec de `SourceLhm` sans la tour.
  ⛔ Elle N'EST PAS une mesure de regime : c'est UN instantane, n = 1. Aucun de
     ses nombres ne qualifie quoi que ce soit (le mouvement, c'est AC4), et aucun
     ne doit etre republie comme un resultat.
  ⚠️ Elle est DATEE dans son nom pour qu'une capture ulterieure ne l'ecrase pas
     en silence : deux versions de LHM ne rendent pas forcement la meme forme --
     ce dossier a deja vu QUATRE affirmations tirees de `master` refutees par le
     binaire installe.
