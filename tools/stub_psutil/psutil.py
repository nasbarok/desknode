#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STUB de `psutil` — ⛔ CE N'EST PAS `psutil`, ET IL LE CRIE.

Motif : `psutil` N'EXISTE PAS EN WSL. Sans lui, la boucle de `dn_agent.py` ne
peut pas etre exercee du tout hors de la tour — donc chaque verification de
cadence, de trame, de checksum ou de champ vide couterait une seance Windows.

🔴 IL VALIDE LA BOUCLE, LA CADENCE, LA TRAME ET LE CHECKSUM.
⛔ IL NE VALIDE **AUCUNE** SOURCE WINDOWS : les nombres qu'il rend sont
   FABRIQUES, et aucun d'eux n'a le droit d'atterrir dans un artefact de mesure.

🔴 DEUX GARDES, PARCE QU'UN STUB SILENCIEUX EST UN GENERATEUR DE FAUX CHIFFRES :
  1. Il REFUSE de s'importer sans `DN_STUB_PSUTIL=1` dans l'environnement.
     ⚠️ Sans ca, un `PYTHONPATH` qui trainerait sur la tour ferait tourner
     l'agent REEL sur des donnees INVENTEES, et rien ne le dirait. Ce depot a
     deja paye « un jeu etiquete reel dont les nombres venaient d'une maquette ».
  2. Il ecrit une banniere sur stderr A CHAQUE IMPORT.

Usage :
    DN_STUB_PSUTIL=1 PYTHONPATH=tools/stub_psutil python3 agent/dn_agent.py \
        --stdout --duree 4
"""
import os
import sys

if os.environ.get("DN_STUB_PSUTIL") != "1":
    raise ImportError(
        "STUB psutil charge SANS DN_STUB_PSUTIL=1. \u26d4 REFUS DELIBERE : si ce "
        "stub s'importait par accident (un PYTHONPATH oublie), l'agent publierait "
        "des nombres FABRIQUES sans que rien ne le dise. Poser DN_STUB_PSUTIL=1 "
        "pour l'exercice en WSL, ou retirer tools/stub_psutil du PYTHONPATH.")

print("[stub] \u26a0\ufe0f  psutil est un STUB (tools/stub_psutil) : les valeurs cpu/ram/"
      "net/disk sont FABRIQUEES. \u26d4 Aucun chiffre de cette session n'est une "
      "mesure.", file=sys.stderr)

__version__ = "0.0-stub"

_t = [0.0]


def _tic():
    _t[0] += 1.0
    return _t[0]


def cpu_percent(interval=None, percpu=False):
    _tic()
    if percpu:
        return [10.0 + (i * 3.5) % 60.0 for i in range(16)]
    return 23.4


class _Freq(object):
    current = 3201.0


def cpu_freq():
    return _Freq()


class _VM(object):
    percent = 41.2
    total = 34359738368  # 32 Gio EXACTEMENT -- \u26a0\ufe0f fabrique


def virtual_memory():
    return _VM()


class _Cnt(object):
    def __init__(self, n):
        self.bytes_recv = 1000000 * n
        self.bytes_sent = 500000 * n
        self.read_bytes = 2000000 * n
        self.write_bytes = 1000000 * n


_n = [0]


def net_io_counters():
    _n[0] += 1
    return _Cnt(_n[0])


_d = [0]


def disk_io_counters():
    _d[0] += 1
    return _Cnt(_d[0])


class Process(object):
    def __init__(self, pid=None):
        pass

    def cpu_times(self):
        class _T(object):
            user = 0.01
            system = 0.005
        return _T()
