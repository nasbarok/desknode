# What to buy to build a DeskNode

This page says **what to order**, **at which tier**, and **how much it cost on the day we
looked**. It is written for someone who has never seen this project.

⚠️ **What it does not promise**: no price here is guaranteed. These are **dated** surveys, made
on marketplaces where prices move without notice. **A price without its date is worth nothing** —
which is why every one of them carries its own.

⚠️ **Affiliate links on this page**: the `Source` links of the five AliExpress rows are affiliate links,
each marked `affiliate link` where it appears — the details are in the last section of this page.

---

## The two tiers

These are the same two tiers as the [README](../README.md) — same names, ⛔ not synonyms.

| Tier | What you build |
|---|---|
| **DeskNode** | the board, alone. ⛔ This is **not** a degraded mode: it is a valid and guarded configuration. |
| **DeskNode + Ambiance** | the same board, **plus two sensors** soldered onto the I²C header. |

---

## Tier "DeskNode" — the board alone

| Item | Exact reference | Qty | Supplier | Price | Survey date | Source |
|---|---|---|---|---|---|---|
| Touchscreen development board | **Waveshare ESP32-S3-Touch-LCD-2.8B** (Type B, **480 × 640**) | 1 | AliExpress marketplace | **26.77 – 27.88 €** (median **27.32 €**, 2 listings) | 2026-09-06 | [AliExpress search: Waveshare ESP32-S3-Touch-LCD-2.8B](https://s.click.aliexpress.com/e/_c3yKWEah) — affiliate link |
| USB-C data cable | any, **data AND charging** | 1 | — | ⛔ **not surveyed** — generic consumable, no single reference to order: ⛔ so no source was tried | — | — |

⛔ **Manufacturer price not surveyable.** `https://www.waveshare.com/esp32-s3-touch-lcd-2.8b.htm` returns
**HTTP 403** to any automated retrieval (tried on 2026-09-06). The hardware folder already writes
the same thing about the official wiki. ⇒ the price above comes from a **marketplace**, ⛔ not from
the manufacturer, and that is written rather than left unsaid.

⚠️ *Annotated on 2026-09-15 (`dn6-6`)* — **the paragraph above is refuted, ⛔ not erased.** Re-read on
2026-09-07 with a browser header, the same product page returns **HTTP 200**: the 403 was a property
of the retrieval tool, ⛔ not of the address — the lesson is written in section 3 of
[the affiliate links page](affiliation.md). ⇒ the manufacturer price **is** surveyable. ⛔ It is
still not filled in here: a price table is re-surveyed, ⛔ not patched, and that re-survey is carried
by the project's planning ledger.

### 🔴 The most likely buying mistake — and it costs less than the right one

Waveshare sells **several boards with almost the same name**. Surveyed on 2026-09-06, **on the
same results page**:

<!-- ⛔ NOT A BOM TABLE : a COMPARISON table. It carries two prices to
     show that the wrong board is the cheaper one — ⛔ it offers nothing
     for purchase, and both prices are dated in the sentence before it. -->

| What you want | What you risk taking |
|---|---|
| `ESP32-S3-Touch-LCD-2.8**B**` — **480 × 640**, Type B — **26.77 €** | `ESP32-S3-Touch-LCD-2.8` — **240 × 320** — **23.08 €** |

⇒ **the wrong board is the cheaper one**, by 3.69 €. Someone who sorts by increasing price takes
the wrong one. There is also a round `2.8C` at 480 × 480 — ⛔ **surveyed nowhere here**: no listing naming it was opened on 2026-09-06, so ⛔ neither price nor source. It is written so that you rule it out, ⛔ not so that you compare it.

**What settles it is the resolution: 480 × 640.** If the listing does not state it, ⛔ do not buy it.

⚠️ **And the manufacturer's documentation is not reliable on this point.** The hardware folder
cross-checked three sources on four verifiable points: they got it wrong or contradicted each other
**four times** — including a reseller mirror that announces a `CH343P` chip **measured absent** from the
real board, because it mixes up the `2.8` and `2.8B` variants. Details in **§14.2** of
`hardware/ESP32-S3-Touch-LCD-2.8B-affichage.md`. **The silkscreen and the measurement are what count.**

### ⚠️ What this tier really has been, and what it has not

The step that establishes it is **`dn4-41`**, and it is **still open** — status `in-progress`,
re-read on **2026-09-06**, last annotation on **2026-09-01**. ⛔ So we do not write "validated" to you.

What **has** been measured: the ToF module was **really unplugged** — established by three concordant
sources, including **the physical fact asked of the owner** — while the other sensor answered
5 times out of 5. Six real cold boots, **zero false positives**.

What has **not** been done, and remains open, **by their keys** — `AC2.9`, closed **with a declared
gap**, and `AC5`, **not measured**: the cold boot **with no sensor at all**, and the electrical
conditions of a bare bus. The reason is written: there is **only one
board**, the development one. ⇒ this tier ships **reasoned and instrumented**, ⛔ **never booted
on bare silicon**. You may be the first to assemble it.

---

## Tier "DeskNode + Ambiance" — the board + two sensors

**Exactly** the board above, **plus these two sensors** — the connection row that
follows is a consumable, ⛔ not a third module.

🔴 **Name trap, measured during the survey**: searching "BME680" also brings up **BME688** and
**BME280**. These ⛔ **are not** the same chip — the BME280 has **no** gas sensor. On the
listings retained on 2026-09-06, they had to be **ruled out by reading the titles**. Check that
the listing says **680**, ⛔ not "6xx".

| Item | Exact reference | Qty | Supplier | Price | Survey date | Source |
|---|---|---|---|---|---|---|
| Temperature / humidity / pressure / gas sensor | **BME680**, breakout type **CJMCU-680** (6 pins `VCC GND SCL SDA SDO CS`) | 1 | AliExpress marketplace | median **11.74 €** (10 listings, 7.77 – 16.96 €) | 2026-09-06 | [AliExpress search: BME680 module](https://s.click.aliexpress.com/e/_c4Dp3sBL) — affiliate link |
| Light sensor | **BH1750**, module **GY-302** (5 pins `VCC GND SCL SDA ADDR`, 3 – 5 V) | 1 | AliExpress marketplace | median **1.93 €** (10 listings, 1.45 – 14.62 €) | 2026-09-06 | [AliExpress search: BH1750 GY-302](https://s.click.aliexpress.com/e/_c4OQ98X7) — affiliate link |
| Jumper wire | Dupont female-female, ~10 cm | 4 min. | — | ⛔ **not surveyed** — generic consumable sold in packs, no single reference: ⛔ so no source was tried | — | — |

**Cost of the tier, as of 2026-09-06:** about **27.32 + 11.74 + 1.93 ≈ 41 €**, excluding shipping, excluding cables.

<!-- ⛔ ANNOTATION, NOT A REWRITE (NFR3): the "Jumper wire" row
     above stays AS IT IS. What follows makes it precise; the
     deferral inherited from dn6-1 designated wiring as the territory of the next step. -->

### ⚠️ Annotation of 2026-09-07 — the "Jumper wire" row, made precise

The row **"Jumper wire — Dupont female-female, ~10 cm | 4 min."** above stays as
it is; this paragraph **makes it precise**, it does not replace it.

**The connector targeted by THIS row is the 2×12 header at 2.54 mm pitch**, row `B`: female-female
Dupont plugs straight into it. ⚠️ **This is a CONNECTOR TYPE constraint, ⛔ not an access
choice**: the board offers **two** access points to the bus, both valid, and the other — a
**4-pin JST** socket — needs a **JST cable**, ⛔ which Dupont does not replace. If you go
through the JST socket, that is the cable you need, ⛔ not this row. And in both cases, picking the
wrong neighbour (twin socket, or neighbouring row) sends the UART to the sensor **without anything
signalling it**. The details, with the silkscreen of both access points and their two traps:
[wiring a DeskNode](cablage.md).

⚠️ **And "4 min." is a floor, ⛔ not the count.** On an I²C bus, `SDA` and `SCL` are
**shared by both modules** — one bus, ⛔ not two — but **sharing a signal ⛔ saves
no wire**: each module wants its own physical connection. The count is laid out here rather
than asserted out of thin air:

| What you need | How many | Why |
|---|---|---|
| connections to the **1st** module | **4** | `3V3`, `GND`, `SDA`, `SCL` |
| connections to the **2nd** module | **4 as well** | it needs the **same four** signals: ⛔ a module does not connect with fewer because the bus is shared |
| `ADDR` wire of the BH1750 to ground | **+1** | it is an **address selection input**, ⛔ not a free pin — leaving it floating makes the address undefined |

⚠️ **What VARIES is WHERE the four wires of the 2nd module start from, ⛔ not their number**:
either from the board (row `B` carries `3V3` and `G`, and row `A` carries **two more**), or
branched off the 1st module. In both cases these are **four more wires**.

⇒ **Nine wires in total**, and ⛔ it is neither 8 nor 5: `SDA`/`SCL` are **shared** in the
**electrical** sense — one bus, ⛔ not two — but that ⛔ saves **no wire**. **Get a pack**, ⛔ do not
count to the exact wire: it is a consumable, and that is why the row above has no price,
no source, and no firm quantity.

### ⚠️ Why a median and not a mean

Because the mean lies, and it is **measured here**. Out of the 10 BH1750 listings, **a single one at
14.62 €** (a pack, or a pricing error) moves the mean from **2.14 to 3.39 €** — **+58 %** —
while the median only moves from 1.86 to 1.93 €.

⇒ on a marketplace, **the median is what settles it**. Every row above publishes it, and the
range is given next to it so that you can see the spread.

### What the project measured on these two modules

These values come from the folder `hardware/ESP32-S3-Touch-LCD-2.8B-capteurs-i2c.md`, where **each one
cites the measurement it comes from** — ⛔ never a copy of a datasheet.

| | BME680 | BH1750 |
|---|---|---|
| I²C address **measured** | `0x77` (§13.3) | `0x23` (§13.3) |
| How it was established | reading an identity register, then the factory coefficients (§13.6 bis) | by **light stimulus** — it has no register to read (§13.16.8) |
| Address pin | `SDO` measured at 3.3 V ⇒ `0x77` | `ADDR` **left free** ⇒ `0x23`, deterministic, **5 answers out of 5** |
| Voltage | +3.3 V measured with the multimeter, board powered | 3 – 5 V (printed on the bag) |
| Pin header | **supplied unsoldered** | **supplied unsoldered** |

🔴 **Both need soldering, and ⛔ they are not wired the same way.** Neither breakout lines up
"first pin with first pin": on these two modules, **`SDA` and `SCL` are crossed** relative
to each other. The wiring diagram is the subject of the next step — until then, the
photos are here:
[BME680 before soldering](cablage/2026-08-16_2140-bme680-recto-barrette-non-soudee.jpg) ·
[BH1750 pin side](cablage/2026-08-19_1720-bh1750-gy302-face-broches-vcc-gnd-scl-sda-addr.jpg) ·
[BH1750 silkscreen V322](cablage/2026-08-19_1720-bh1750-gy302-face-composants-serigraphie-v322.jpg) ·
[BH1750 silkscreen and bag](cablage/2026-08-19_1720-bh1750-gy302-face-composants-et-sachet.jpg)

⚠️ *Annotated on 2026-09-15 (`dn6-6`)*: "the next step" above has shipped (`dn6-2`, 2026-09-07) — the
wiring page is [wiring a DeskNode](cablage.md). The sentence and the photos stay as they were.

⚠️ **The board's I²C pinout is `SDA = GPIO15`, `SCL = GPIO7`** — and a third-party source gave
them **swapped**. Measurement and silkscreen in **§13.1** of the sensors folder.

---

## What is on the prototype and **outside both tiers**

These two modules are visible on the photos and present in the measurement folder. They are
**in no tier**, and here is **why** — ⛔ a component of the prototype absent from this page
without a written reason would be a defect.

| Module | Exact reference | Price surveyed | Survey date | Source | Why it is **not** in the catalogue |
|---|---|---|---|---|---|
| Distance sensor | **TOF050C-VL6180X** (⛔ **NOT** a VL53L0X) | **3.21 €** (1 listing naming it explicitly) | 2026-09-06 | [AliExpress search: TOF050C-VL6180X](https://s.click.aliexpress.com/e/_c3w7WL8h) — affiliate link | 🔴 **The tested unit is doubly defective**: its **analog stage is dead** — no reaction to a light variation of **~2 280×**, while its digital stage answers perfectly — **and** its presence **prevents the board from booting** (black screen, processor halted, no more USB). ⇒ ⛔ outside V1. |
| Current sensor | **INA219**, module **CJMCU** (shunt `R100`, 0.1 Ω) | median **1.87 €** (3 listings, 1.80 – 2.41 €) | 2026-09-06 | [AliExpress search: INA219 CJMCU](https://s.click.aliexpress.com/e/_c3vm4Fkp) — affiliate link | Project decision: **not now**. It was **physically removed from the bus on 2026-08-21** and the corresponding reading removed from the code. ⇒ power consumption **will not be measured in V1**. |

These two modules are on the photos of the prototype, and **the captions say so**: ⛔ what you
see there is not what you buy.
[BH1750 **and INA219** soldered side by side](cablage/2026-08-20_0116-bh1750-et-ina219-barrettes-SOUDEES.jpg) ·
[the prototype in hand — **four** modules, two of them outside the tiers](cablage/2026-08-20_0951-montage-final-en-main-les-quatre-modules.jpg)

🔴 **Trap if you look for an INA219 yourself**: out of 12 results surveyed, **9 were bare
chips** to solder (SOP8, SOIC-8, SC70-6 packages) — up to 41.68 € for a bag of 50. What you
want is a **module** with a terminal block and pins. The name alone is not enough to sort them.

---

## The sources we could not reach

Written because it is information, ⛔ not a gap: **10 sources tried on 2026-09-06, 10 without a
usable price.**

⚠️ Each row carries **the exact address** that was tried and **the date of the attempt**: ⛔ a
shop name cannot be retried, a URL can.

| Address tried | Date of the attempt | Result |
|---|---|---|
| `https://www.waveshare.com/esp32-s3-touch-lcd-2.8b.htm` | 2026-09-06 | HTTP 403 |
| `https://www.mouser.fr/c/?q=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | timed out at 60 s |
| `https://www.tinytronics.nl/en/search?query=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | HTTP 403 |
| `https://eckstein-shop.de/en/search?sSearch=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | HTTP 403 |
| `https://octopart.com/search?q=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | HTTP 403 |
| `https://www.adafruit.com/?q=BME680` | 2026-09-06 | HTTP 403 |
| `https://www.gotronic.fr/search.php?q=BME680` | 2026-09-06 | HTTP 404 |
| `https://www.welectron.com/catalogsearch/result/?q=BH1750` | 2026-09-06 | HTTP 404 |
| `https://www.berrybase.de/search?q=ESP32-S3-Touch-LCD-2.8B` | 2026-09-06 | page rendered, **no product page** |
| `https://thepihut.com/search?q=BME680` | 2026-09-06 | page rendered, "no results found" |

⚠️ *Annotated on 2026-09-15 (`dn6-6`)*: the **first row** of this table — the manufacturer's product page,
HTTP 403 — is refuted the same way as the paragraph under the first tier table: re-read on 2026-09-07
with a browser header, that page returns HTTP 200. The row stays as it was tried on 2026-09-06, with an
automated retrieval tool; ⛔ it is not rewritten.

Only one European alternative answered, and it is **a different product**: Pimoroni sells its
own "BME680 Breakout" at **11.05 GBP** excluding VAT (surveyed on 2026-09-06) — ⛔ it is not the
6-pin module of the prototype.

⚠️ **What these prices do not contain**: neither shipping, nor import taxes, nor lead time. And
no product page was opened one by one — these are the prices of the results pages, where a
product page may carry cheaper or more expensive variants.

---

## Affiliate links

**This page carries no affiliate link.** The URLs above are bare search addresses.

⚠️ *Outdated since 2026-09-15 (`dn6-6`)* — the sentence above was true until that day and is kept as it
was; what is in force is the annotation of 2026-09-15 at the end of this section.

⚠️ If that changes one day, it will be said **here**, in this place. Setting up an affiliation is not
a box to tick — it means signing up somewhere, declaring it, and keeping the promise
over time. It is therefore carried as a subject in its own right, ⛔ not as a footnote line.

<!-- ⛔ ANNOTATION, NOT A REWRITE (NFR3): the two paragraphs
     above stay WORD FOR WORD. What follows completes them — the subject
     announced "in its own right" now has its page, and the switch-over
     point is written here, where the status sentence already lives. -->
<!-- ⚠️ ANNOTATED ON 2026-09-15 (dn6-6): those two paragraphs were TRANSLATED
     from French that day, with the whole page. "Word for word" now holds for
     their translation; the French original lives in the git history. -->

### Annotation of 2026-09-07 — the subject has its page, and the switch-over point is written

The subject announced "in its own right" above **now has its page**:
[the affiliate links](affiliation.md). It says which programmes really exist for the
suppliers that **this** page cites, on which terms, what French and European law
requires to be declared — each fact with its address and its date, each unverifiable fact **declared**
as such — and what the owner must sign themselves.

**The switch-over point**, that is, what must be true for the status sentence above to
change:

1. **the programme must be open to this repository** — today **unknown, ⛔ not acquired**: the
   admission terms of AliExpress are behind an authentication, and those of Waveshare,
   **public and read on 2026-09-07**, say they invite *"primarily"* people with a
   presence on **GitHub** — and this repository is **private** there;
   ⚠️ *annotated on 2026-09-15 (`dn8-8`): this repository is **public** there since that day;*
2. **the owner must open the account themselves** and accept the terms and conditions — ⛔ this is not
   a gesture that an agent can make in their place;
3. **both status sentences must be rewritten** — this one and the one on the page above. They
   will stop saying "none" to say what is true; ⛔ they will not be erased.

⚠️ **And it will be said here, in this place.** This is not an intention: it is **guarded mechanically,
in both directions**. As long as no published address carries an affiliate marker, both
pages must **assert it**; the day one of them carries one, the assertion becomes false and the
check **turns red** — even if nobody thought of coming back to write here.

⚠️ *Annotated on 2026-09-15 (`dn6-6`)*: the check described in the paragraph above is the one that guarded
the old promise. It was rewritten that day for the new one — every tracked address is declared in its own
cell, next to the mention, and the mention never sits on an address that is not tracked (see the
annotation of 2026-09-15 below).

<!-- ⛔ ANNOTATION, NOT A REWRITE (NFR3): the status sentence at the top of
     this section stays, translated from its original, and so do the three
     conditions above. The declaration in force is written BELOW them, as
     point 3 of the switch-over point says it would be. -->

### Annotation of 2026-09-15 (`dn6-6`) — the switch-over has happened

**This page carries affiliate links.** The five AliExpress rows above — the board, the two sensors
of the "DeskNode + Ambiance" tier, and the two modules outside the tiers — each carry, in their
`Source` cell, a tracked link of the **AliExpress affiliate programme** (the AliExpress Portals
programme), with the words **`affiliate link`** written right next to the link. If you buy through
one of them, the owner of this repository may be paid a commission by the programme — or nothing,
depending on the seller: the terms read on the programme's portal are on
[the affiliate links page](affiliation.md), section 3.

⚠️ The status sentence at the top of this section **stays**, translated from its original: it was
true until 2026-09-15, and the rule is to annotate, ⛔ not to erase. **What is in force is this
annotation.**

**Where each link comes from.** The owner generated the five links on 2026-09-15 with the
programme's batch link tool, from the **same five search pages** where the prices above were read on
2026-09-06 — so each `Source` cell is still the source of its price, **as the owner states it**: that
statement is pending the owner's one-time click check on each link. The correspondence between each
link code and the bare search address it was generated from is published in
[the survey of 2026-09-15](../mesures/dn6-6/T1-releves-du-2026-09-15.txt), so that a price can be
checked again **without clicking a tracked link**. ⚠️ The destination of the links was ⛔ **not**
opened by the agent that wrote this annotation — a click is counted by the programme — and checking
it is a gesture of the owner. ⛔ No price, no date and none of the 10 addresses tried was changed
on 2026-09-15.

⚠️ The two modules outside the tiers carry a tracked link too: that does ⛔ **not** put them back in a
tier, their reasons for exclusion above are unchanged, and they are ⛔ **not** to be bought to build a V1
DeskNode.

**The switch-over point, condition by condition, as of 2026-09-15:**

1. **the programme is open to this repository** — for **AliExpress, yes**: the owner's affiliate
   account is active (read by the owner on the programme's portal on 2026-09-15). For **Waveshare,
   not yet**: the application is **waiting for approval**, and ⛔ no Waveshare link is published here;
2. **the owner opened the account themselves** and accepted the programme's rules — a gesture of the
   owner, ⛔ not of an agent;
3. **both status sentences are annotated** — this one, and the one on
   [the affiliate links page](affiliation.md): the old sentence stays, the new one is written below
   it. The check that guarded the old promise was rewritten the same day to guard the new one:
   **every tracked address is declared, in its place** — on this page, in its own cell, next to the
   words `affiliate link` — and those words never decorate an address that is not tracked.

---

## Licence

This page is documentation: **CC-BY-SA-4.0**, like the rest of this directory. See
[LICENSING.md](../LICENSING.md).
