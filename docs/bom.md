# What to buy to build a DeskNode

**Affiliate links.** The five `Source` links below are affiliate links — the board at Waveshare's own
store, the four modules on AliExpress — each marked `affiliate link` in its own cell. Buying through one
of them may pay the owner of this repository, and costs you nothing more; the terms, and what is still
unknown about them, are on [the affiliate links page](affiliation.md).
⚠️ Every price here is a **dated survey**, ⛔ not a promise: a price without its date is worth nothing.

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
| Touchscreen development board | **Waveshare ESP32-S3-Touch-LCD-2.8B** (Type B, **480 × 640**) | 1 | Waveshare official store | **29.99 USD** (version *With Touch Function*; the page shows 22.99 – 29.99 USD across its two versions) | 2026-09-15 | [Waveshare store: ESP32-S3-Touch-LCD-2.8B](https://www.waveshare.com/esp32-s3-touch-lcd-2.8b.htm?&aff_id=180651) — affiliate link |
| USB-C data cable | any, **data AND charging** | 1 | — | ⛔ **not surveyed** — generic consumable, no single reference to order: ⛔ so no source was tried | — | — |

### 🔴 The most likely buying mistake — and it costs less than the right one

Waveshare sells **several boards with almost the same name**. Surveyed on 2026-09-06, on the same results page:

<!-- ⛔ NOT A BOM TABLE : a COMPARISON table. It carries two prices to
     show that the wrong board is the cheaper one — ⛔ it offers nothing
     for purchase, and both prices are dated in the sentence before it. -->

| What you want | What you risk taking |
|---|---|
| `ESP32-S3-Touch-LCD-2.8**B**` — **480 × 640**, Type B — **26.77 €** | `ESP32-S3-Touch-LCD-2.8` — **240 × 320** — **23.08 €** |

⇒ **the wrong board is the cheaper one.** What settles it is the resolution: **480 × 640**. If the listing
does not state it, ⛔ do not buy it. A round `2.8C` in 480 × 480 exists too — ⛔ surveyed nowhere here.

⚠️ **This tier ships reasoned and instrumented, ⛔ never booted on bare silicon**: the step that establishes
it, **`dn4-41`**, is **still open** — status `in-progress`, re-read on **2026-09-06**. ⛔ So we do not write
"validated" to you. You may be the first to assemble it.

---

## Tier "DeskNode + Ambiance" — the board + two sensors

**Exactly** the board above, **plus these two sensors** — the jumper wire row is a consumable, ⛔ not a
third module.

🔴 **Name trap**: searching "BME680" also brings up **BME688** and **BME280**. These ⛔ are not the same
chip — the BME280 has **no** gas sensor. Check that the listing says **680**, ⛔ not "6xx".

| Item | Exact reference | Qty | Supplier | Price | Survey date | Source |
|---|---|---|---|---|---|---|
| Temperature / humidity / pressure / gas sensor | **BME680**, breakout type **CJMCU-680** (6 pins `VCC GND SCL SDA SDO CS`) | 1 | AliExpress marketplace | median **11.74 €** (10 listings, 7.77 – 16.96 €) | 2026-09-06 | [AliExpress search: BME680 module](https://s.click.aliexpress.com/e/_c4Dp3sBL) — affiliate link |
| Light sensor | **BH1750**, module **GY-302** (5 pins `VCC GND SCL SDA ADDR`, 3 – 5 V) | 1 | AliExpress marketplace | median **1.93 €** (10 listings, 1.45 – 14.62 €) | 2026-09-06 | [AliExpress search: BH1750 GY-302](https://s.click.aliexpress.com/e/_c4OQ98X7) — affiliate link |
| Jumper wire | Dupont female-female, ~10 cm | 4 min. | — | ⛔ **not surveyed** — generic consumable sold in packs, no single reference: ⛔ so no source was tried | — | — |

⚠️ **"4 min." is a floor**: each module needs its own four wires, plus the BH1750's `ADDR` to ground —
**nine in total**, ⛔ neither 8 nor 5. **Get a pack.** Both pin headers are **supplied unsoldered**, and the
two breakouts ⛔ do not line up pin for pin. Where every wire goes, with the two traps that send the UART to
a sensor without saying so: [wiring a DeskNode](cablage.md).

---

## What is on the prototype and **outside both tiers**

These two modules are visible on the photos and present in the measurement folder. They are **in no tier**,
and here is **why** — ⛔ a component of the prototype absent from this page without a written reason would
be a defect. ⛔ Neither is needed to build a V1 DeskNode.

| Module | Exact reference | Price surveyed | Survey date | Source | Why it is **not** in the catalogue |
|---|---|---|---|---|---|
| Distance sensor | **TOF050C-VL6180X** (⛔ **NOT** a VL53L0X) | **3.21 €** (1 listing naming it explicitly) | 2026-09-06 | [AliExpress search: TOF050C-VL6180X](https://s.click.aliexpress.com/e/_c3w7WL8h) — affiliate link | 🔴 **The tested unit is doubly defective**: its **analog stage is dead** — no reaction to a light variation of **~2 280×**, while its digital stage answers perfectly — **and** its presence **prevents the board from booting** (black screen, processor halted, no more USB). ⇒ ⛔ outside V1. |
| Current sensor | **INA219**, module **CJMCU** (shunt `R100`, 0.1 Ω) | median **1.87 €** (3 listings, 1.80 – 2.41 €) | 2026-09-06 | [AliExpress search: INA219 CJMCU](https://s.click.aliexpress.com/e/_c3vm4Fkp) — affiliate link | Project decision: **not now**. It was **physically removed from the bus on 2026-08-21** and the corresponding reading removed from the code. ⇒ power consumption **will not be measured in V1**. |

---

## Affiliate links

**This page carries no affiliate link.** The URLs above are bare search addresses.

⚠️ *Outdated since 2026-09-15* — the sentence above was true until that day and is kept as it was. What is
in force is the paragraph below.

**This page carries affiliate links**, from two programmes: the board's `Source` link goes to Waveshare's
own store, the four others to AliExpress searches, each with the words `affiliate link` in its cell. What
each programme pays, what it forbids, and the conditions still unread are on
[the affiliate links page](affiliation.md), which also says what the owner had to sign himself.

**The switch-over point** — what had to become true for the sentence above to change, and is, as of
2026-09-15:

1. **both programmes are open to this repository** — AliExpress and Waveshare each approved the owner's
   application that day;
2. **the owner opened both accounts themselves** and accepted their terms — ⛔ not a gesture an agent can
   make in their place;
3. **both status sentences are annotated** — this one and the one on
   [the affiliate links page](affiliation.md): the outdated sentence **stays**, the new one is written
   below it, and a check keeps that true in both directions.

---

## Where the rest of this page went

This page was **398 lines** until 2026-09-15 and is now under a hundred, by an owner decision of that day.
What left it moved **word for word** into [the log](journal-de-bord.md) — ⛔ nothing was erased: the tier's
total cost, why a median and not a mean, the I²C addresses measured on the two sensors and the photos of
them, the nine-wire count in full, the **ten shop addresses that could not be reached** on 2026-09-06, and
every dated annotation this page had collected since 2026-09-07.

---

## Licence

This page is documentation: **CC-BY-SA-4.0**, like the rest of this directory. See
[LICENSING.md](../LICENSING.md).
