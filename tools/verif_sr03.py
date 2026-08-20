#!/usr/bin/env python3
"""
Garde dn4-7 / AC1 : la table SR03 du FIRMWARE est-elle celle de [AN] AN4545 ?

    python3 tools/verif_sr03.py <AN4545.pdf> firmware/desknode/main/dn_console.c

⛔ Ce harnais N'A PAS le droit de contenir la sequence. Il l'EXTRAIT des deux
   cotes et les compare :
     · cote document : le texte de l'AN4545, via pdftotext
     · cote firmware : la table C de main/dn_console.c
   Un harnais qui porterait la sequence en dur ne prouverait que sa propre
   coherence avec lui-meme.

⚠️ IL SE PROUVE PAR MUTATION, et ça a ete FAIT le 2026-08-21 : valeur changee,
   deux entrees permutees, entree supprimee, registre public non declare
   modifie ⇒ les QUATRE mutants sortent en exit 1. Une garde qu'on n'a jamais
   vue rouge ne prouve rien (§13.19.x).

🔴 LE PDF N'EST PAS AU DEPOT — c'est un document STMicroelectronics, on ne le
   redistribue pas. Son EMPREINTE, elle, est ici : le harnais REFUSE tout autre
   fichier. Ce n'est pas de la coquetterie — deux URL de miroir rendaient en
   HTTP 200 un PDF ST authentique... du VL53L0X. Le code de retour et le nom de
   fichier mentaient tous les deux.

   AN4545 « VL6180X basic ranging application note », DocID026571 Rev 1,
   juin 2014. Verifie identique depuis DEUX hebergeurs independants :
     https://cdn.sparkfun.com/datasheets/Sensors/Proximity/VL6180_ApplicationNote.pdf
     https://www.pololu.com/file/0J962/AN4545.pdf
   ⚠️ st.com est INJOIGNABLE depuis ce poste (et depuis Windows hors WSL) : le
      TLS aboutit puis le flux HTTP/2 casse (INTERNAL_ERROR).
"""
import re, sys, subprocess, pathlib, hashlib

AN4545_SHA256 = "091291adc9812852e4206f4bf33a6a1646a51c1c9d92bf5c4b00d1ee5efabbab"

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(2)

PDF = sys.argv[1]
SRC = sys.argv[2]

vu = hashlib.sha256(pathlib.Path(PDF).read_bytes()).hexdigest()
if vu != AN4545_SHA256:
    print(f"🔴 CE N'EST PAS L'AN4545 Rev 1 ATTENDU.")
    print(f"   attendu {AN4545_SHA256}")
    print(f"   lu      {vu}")
    print("   ⛔ La garde REFUSE de comparer a un document qu'elle n'a pas")
    print("      identifie : elle rendrait un vert qui ne veut rien dire.")
    sys.exit(2)

# ── cote DOCUMENT ────────────────────────────────────────────────────────────
txt = subprocess.run(["pdftotext", "-layout", PDF, "-"],
                     capture_output=True, text=True, check=True).stdout
# On ne prend QUE la section 9, delimitee par son titre et la revision history.
m = re.search(r"^\s*9\s+SR03 settings\s*$(.*?)Revision history", txt,
              re.S | re.M)
if not m:
    print("🔴 section 9 introuvable dans le PDF"); sys.exit(2)
sec = m.group(1)

# Le bloc « Mandatory : private registers » s'arrete au commentaire suivant.
mm = re.search(r"//\s*Mandatory\s*:\s*private registers(.*?)//\s*Recommended",
               sec, re.S)
if not mm:
    print("🔴 bloc « Mandatory : private registers » introuvable"); sys.exit(2)

def writes(block):
    return [(int(r, 16), int(v, 16)) for r, v in
            re.findall(r"WriteByte\(\s*0x([0-9a-fA-F]{3,4})\s*,\s*0x([0-9a-fA-F]{1,2})\s*\)",
                       block)]

doc_prive = writes(mm.group(1))
# « Recommended » va jusqu'a « Optional »
mr = re.search(r"//\s*Recommended\s*:\s*Public registers(.*?)Optional\s*:", sec, re.S)
doc_public = writes(mr.group(1)) if mr else []

# ⚠️ Et le bloc « Optional », qui est EXTRAIT LUI AUSSI depuis le 2026-08-21.
# Motif : 0x0014 y vit, et il n'est PAS optionnel en pratique — sans lui
# ([DS] §6.2.12, [2:0] range_int_mode = 0 = « Disabled ») le telemetre ne
# signale JAMAIS sa mesure. Le firmware en joue UN SEUL des trois, et la garde
# doit pouvoir le VERIFIER contre le document plutot que de l'excepter.
mo = re.search(r"Optional\s*:\s*Public registers(.*?)(?:\Z|Revision history)", sec, re.S)
doc_optional = writes(mo.group(1)) if mo else []

# ── cote FIRMWARE ────────────────────────────────────────────────────────────
src = pathlib.Path(SRC).read_text(encoding="utf-8")

def table(nom):
    m = re.search(r"k_" + nom + r"\[\]\s*=\s*\{(.*?)\n\};", src, re.S)
    if not m:
        print(f"🔴 table k_{nom}[] introuvable dans {SRC}"); sys.exit(2)
    return [(int(r, 16), int(v, 16)) for r, v in
            re.findall(r"\{\s*0x([0-9A-Fa-f]{3,4})\s*,\s*0x([0-9A-Fa-f]{1,2})\s*\}",
                       m.group(1))]

fw_prive  = table("sr03_prive")
fw_public = table("sr03_public")

ok = True
print(f"[AN] prives  : {len(doc_prive):2d}   firmware : {len(fw_prive):2d}")
print(f"[AN] publics : {len(doc_public):2d}   firmware : {len(fw_public):2d}")
if not doc_prive:
    print("🔴 ZERO ecriture extraite du PDF — le harnais mesurerait du vide."); sys.exit(2)

if doc_prive != fw_prive:
    ok = False
    print("\n🔴 BLOC PRIVE : ECART (ordre compris)")
    for i, (d, f) in enumerate(zip(doc_prive, fw_prive)):
        if d != f:
            print(f"   [{i:02d}] doc 0x{d[0]:04X}=0x{d[1]:02X}  fw 0x{f[0]:04X}=0x{f[1]:02X}")
    if len(doc_prive) != len(fw_prive):
        print(f"   longueurs differentes : {len(doc_prive)} vs {len(fw_prive)}")
else:
    print("✅ BLOC PRIVE : les 30 ecritures sont IDENTIQUES, valeurs ET ordre")

# Le bloc public porte UN ECART VOULU et DECLARE (0x0040 16 bits).
ecart_attendu = {0x0040}
# Le firmware joue AUSSI 0x0014, pris dans le bloc « Optional » du MEME document.
# Il n'est donc pas « non declare » — mais sa valeur doit correspondre AU DOCUMENT.
d_opt = dict(doc_optional)
d_map = dict(doc_public)
f_map = dict(fw_public)

print(f"[AN] optionnels : {len(doc_optional):2d}   dont joues par le firmware : "
      + (", ".join(f"0x{r:04X}" for r in sorted(set(d_opt) & set(f_map))) or "aucun"))
joues_opt = set(d_opt) & set(f_map)
for r in sorted(joues_opt):
    if d_opt[r] != f_map[r]:
        ok = False
        print(f"🔴 OPTIONNEL 0x{r:04X} : doc 0x{d_opt[r]:02X} / fw 0x{f_map[r]:02X}")
    else:
        print(f"✅ OPTIONNEL 0x{r:04X} = 0x{d_opt[r]:02X} — conforme au document")
# Ce qui vient du bloc « Optional » n'est pas un ecart au bloc « Recommended ».
ecart_attendu |= joues_opt
diffs = {r for r in set(d_map) | set(f_map) if d_map.get(r) != f_map.get(r)}
imprevus = diffs - ecart_attendu - {0x0041}
if imprevus:
    ok = False
    print(f"\n🔴 BLOC PUBLIC : ecart(s) NON DECLARE(S) : "
          + ", ".join(f"0x{r:04X}" for r in sorted(imprevus)))
    for r in sorted(imprevus):
        print(f"   0x{r:04X} : doc {d_map.get(r)} / fw {f_map.get(r)}")
else:
    print("✅ BLOC PUBLIC : conforme, hors l'ecart 0x0040/0x0041 DECLARE en commentaire")
    print(f"   doc 0x0040=0x{d_map.get(0x0040,0):02X}  ⇒  fw 0x0040=0x{f_map.get(0x0040,0):02X} "
          f"+ 0x0041=0x{f_map.get(0x0041,0):02X}   ([DS] §6.2.36, registre 16 b champ [8:0])")

sys.exit(0 if ok else 1)
