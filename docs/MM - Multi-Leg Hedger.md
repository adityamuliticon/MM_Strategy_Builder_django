# Overview

**MM \- Multi-Leg Hedger**  
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date: 02-06-2026  
Prepared By: Aditya Vadodariya

# PLUGIN SUMMARY

# **✅ 1\. BRD VERSION (Formal, Precise, Functional Definition)**

## **Multi-Leg Hedger Plugin – Product Overview**

**Multi-Leg Hedger** is a multi-instrument, multi-leg automated strategy builder that allows traders to simultaneously construct and execute complex hedging and directional structures across multiple symbol legs under a single shared underlying. Each leg can independently target Futures, Options (CE/PE), or Stock instruments, and each leg carries its own Target, Stop-Loss, Trail SL, Re-entry, Re-execute, and Wait-and-Trade controls.

Unlike single-leg execution plugins, Multi-Leg Hedger is purpose-built for **structural trading**: Short/Long Straddles, Strangles, Iron Condors, Iron Butterflies, Ratio Spreads, Call/Put Spreads, Synthetic Calls, Covered Calls, Collars, Box Spreads, custom delta-hedged baskets, and any combination of options + futures legs that must execute and be managed as a unified strategy.

The plugin supports **three distinct trading modes** selectable at the top of the Main tab:

1. **Normal** — Standard time-based entry. Supports both Intraday and Positional Trading Types.  
2. **Range Breakout** — Entry triggered when the underlying breaks above or below a defined candle's High or Low. Replaces Entry Time with Candle Start Time + Candle End Time. Each leg specifies its own Breakout Direction.  
3. **BTST/STBT** — Buy/Sell Today, Square-off Tomorrow. Forces Positional Trading Type. Position is opened today and closed at a configured Next-Day Sqroff Time. Per-leg controls are reduced to Trail SL only.

The Advance tab provides **master-level portfolio controls** including Master Target / Master SL with Dynamic or Fix trailing, Trading Cycle (intraday / positional restart), VIX Filter, Dynamic Index Movement Cycle Trading (re-cycle on underlying movement), Sqroff by Fix Time (pre-expiry positional exit), Condition Checking Time delay, and a comprehensive safety toggle set (Sqroff All Legs, Trail SL to Cost, Sqroff on Rejection, Allow Late Trading, Consider Closed Trades PNL).

**Strategy Type ID (API):** `RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$`  
**API Endpoint:** `POST https://api.marketmaya.com/api/mainStrategy/CreateMultiLegCallPutStrategy`

---

## **Key Capabilities**

* Build **unlimited legs** per strategy, each independently mapped to FUT, OPT, or Stock instruments across NSE, NFO, BFO, BSE, MCX, CDS, and CRYPTO.  
* Switch seamlessly between **Normal**, **Range Breakout**, and **BTST/STBT** modes through a single radio control on the Main tab.  
* Configure **per-leg ATM Type**: Fix (ATM offset from underlying) or Dynamic (scan strikes for premium within Start–End range).  
* Define **per-leg Target / SL** with Money, Point, or Percentage(%) types.  
* Enable **per-leg Trail SL** with Market Move, SL Move, and No of Trail SL controls.  
* Configure **per-leg Re-entry** (wait for price reversion to original entry, then re-enter) or **Re-execute** (immediately open new position at current ATM with optional delay).  
* Use **Wait and Trade** to delay entry until premium has moved by a defined amount or percentage in a specific direction.  
* Apply **Master Target / Master SL** with Money, Point, or Total Premium(%) types across the combined cycle MTM.  
* Trail the master SL using **Dynamic** (Profit Move → SL Move ladder) or **Fix** (custom profit/SL table) trail engines, with optional Live Max MTM as profit move tracking.  
* Run multiple **Trading Cycles** per day with configurable Cycle Delay (Intraday and Positional).  
* Apply a **VIX Filter** at cycle start so the strategy enters only when VIX is within the configured range.  
* Use **Dynamic Index/Future Movement Cycle Trading** (Intraday only) to automatically close the current cycle and start a new one when the underlying moves by a defined Percentage or Points value.  
* Use **Sqroff by Fix Time** to exit positional cycles on a specific weekday and time before expiry.  
* Apply **Condition Checking Time** to delay TP/SL evaluation from Day 2 onwards by N minutes after market open, preventing false triggers on gap-up/gap-down opens.  
* Use the **Trail SL to Cost on other leg SL** option to reset other legs' trail SL to break-even when any leg's SL is hit.  
* Restrict trading to selected **Working Days** (Mon–Sun).  
* Use **Templates** and Description fields for reuse and Copilot training context.

The plugin supports a wide range of use cases including:

* Index option straddles and strangles (BANKNIFTY, NIFTY, FINNIFTY, MIDCPNIFTY)  
* Iron condors, iron butterflies, and broken-wing structures  
* Delta-hedged futures + options combinations  
* BTST overnight directional plays with managed Trail SL  
* Range breakout intraday plays on index futures  
* Premium-decay-based theta strategies with re-execute on SL  
* Synthetic positions (Synthetic Call, Synthetic Put, Collar)  
* Calendar and diagonal spreads via NEAR/NEXT/FAR contract selection

---

## **Primary Objective**

To provide a **complete multi-leg, multi-mode, multi-instrument execution framework** that turns complex options and futures structures into fully automated, individually managed, and centrally controlled live trading strategies — with leg-level and master-level exit, re-entry, and re-cycle controls built in.

---

# **✅ 2\. COPILOT VERSION (AI-Optimized, Natural Language, Training Input)**

**Multi-Leg Hedger is a multi-instrument, multi-leg, multi-mode strategy execution plugin** that handles options structures, futures hedges, BTST/STBT carry plays, and range breakout entries within a single unified configuration model.

Copilot should understand that:

* This plugin is the **default choice** when a user describes a strategy with two or more legs, an options structure (straddle/strangle/condor/spread), a hedged position, or any setup combining FUT and OPT instruments.  
* The plugin operates in **three modes** — Normal, Range Breakout, BTST/STBT — selected via a Trading Mode radio at the top of the Main tab. Mode selection reshapes the visible fields on Main, Legs, and Advance tabs.  
* Each leg is **independently configured** (Symbol, ATM Type, Lot/Qty, Trade Side, Target, SL, Trail SL, Re-entry, Re-execute, Wait and Trade). In Range Breakout mode, the per-leg checkbox group collapses to a single Breakout Direction field.  
* In **BTST/STBT mode**, Trading Type is forced to Positional, the Sqroff Time label changes to "Next Day Sqroff Time", and per-leg controls show only the Trail SL checkbox.  
* The **Advance tab is mode-aware**: Trading Cycle, VIX Filter, and Dynamic Index Movement appear only in Normal Intraday; Sqroff by Fix Time appears in Normal Positional and BTST/STBT; safety toggles appear in all modes.  
* `cosider_closed_pnl` is the API field name (typo with one 'n') for the "Consider Closed Trades PNL for Master TP SL" toggle.  
* Master Target / SL applies **per cycle**, not cumulatively across cycles.

When a user asks Copilot to "create a multi-leg hedger strategy," Copilot should:

1. Identify the Trading Mode (Normal / Range Breakout / BTST-STBT).  
2. Identify the Underlying Symbol (Exchange + Segment + Symbol).  
3. Identify each leg (instrument, ATM Type, side, qty, target/SL, trail/re-entry/re-execute/wait).  
4. Set Master Target and Master SL if mentioned.  
5. Set Trading Cycle, VIX Filter, Dynamic Index Movement, or Sqroff by Fix Time when relevant.  
6. Enable safety toggles (Sqroff All Legs, Sqroff on Rejection, Trail to Cost, etc.) as appropriate.  
7. Map all inputs into valid plugin fields and emit a full JSON payload.

Copilot should treat Multi-Leg Hedger as the plugin for **all multi-leg, multi-instrument, structured options/futures trading** with internal entry rules.

---

# **✅ 3\. SHORT PLUGIN CARD SUMMARY (To display on homepage)**

### **Multi-Leg Hedger**

Build multi-leg options, futures, and equity strategies with per-leg target, SL, trail, re-entry, and re-execute.  
Switch between Normal, Range Breakout, and BTST/STBT in one click. Add master TP/SL, trading cycles, VIX filter, and dynamic index movement re-cycling for complete portfolio-grade execution control.

---

# Parameter Description

# Main Parameters

### **1\. Trading Mode**

**Description:** A radio group at the top of the Main tab that selects which mode the strategy operates in: Normal (time-based entry), Range Breakout (candle breakout entry), or BTST/STBT (carry-overnight). Selection of mode dynamically reshapes the visible fields on Main, Legs, and Advance tabs.  
**Logic:**

* **Normal** → standard time-based entry. Both Intraday and Positional Trading Types allowed. Entry Time, Sqroff Time, all per-leg controls visible.  
* **Range Breakout** → entry triggered when candle's High or Low is broken. Entry Time field is replaced by Candle Start Time and Candle End Time. Per-leg checkbox group is replaced by a single Breakout Direction field (High or Low). `is_range_break_out = true`.  
* **BTST/STBT** → open today, close next day. Forces Positional. Sqroff Time label becomes "Next Day Sqroff Time*". Per-leg controls show only the Trail SL checkbox. `is_btst_stbt = true`.

**Type:** Radio Group  
**Default Value:** Normal  
**Validation:** Exactly one of the three modes must be selected. `is_range_break_out` and `is_btst_stbt` cannot both be true at the same time.  
**Example:** Range Breakout  
**DB Field Name:** is\_range\_break\_out (bool), is\_btst\_stbt (bool) — when both are false, the strategy is Normal.  
**Execution Context:** Trading Server uses this flag pair to select the appropriate state machine for the strategy (time-trigger, candle-trigger, or BTST workflow). Mode also gates which Advance-tab sections are evaluated at runtime.  
---

### **2\. Strategy Name**

**Description:** User-defined name of the strategy. Shown in UI and used for identification.  
**Logic:** Does not affect execution. Used purely for listing, search, copy/duplicate, and Copilot reference.  
**Type:** String  
**Default Value:** Blank ("")  
**Validation:**

- Required  
- Must be unique per user  
- Minimum length 3, maximum 100 characters  
- Cannot include unsupported special characters

**Example:** "BNF Short Straddle Weekly"  
**DB Field Name:** strategyName  
**Execution Context:** Used only by UI and Copilot to reference the strategy. Trading Server ignores this value.  
---

### **3\. Underlying Symbol**

**Description:** The reference instrument whose live price drives strike selection for all option legs in the strategy. Opens the "Select Symbol" dialog where Exchange, Segment, and Symbol are configured, with quick-select chips for common symbols.  
**Logic:** The resolved underlying is displayed as a concatenated string (e.g., "BANKNIFTY FUT NFO" or "Nifty 50 INDEX NSE"). Trading Server uses the underlying's last traded price to compute the ATM strike for all OPT legs whose `atmType = "Fix"`. For `atmType = "Dynamic"` legs, the underlying is used to identify the option chain to scan.  
**Type:** Composite field (opens dialog)  
**Default Value:** Blank (required)  
**Validation:** Required. A valid Exchange + Segment + Symbol combination must be selected.  
**Example:** BANKNIFTY FUT NFO  
**DB Field Name:** exchange, segment, symbol, underlying (display string)  
**Execution Context:** Trading Server polls the live price of this underlying continuously and uses it for strike resolution, range breakout high/low locking, and dynamic index movement cycle triggers.  
---

### **4\. Trading Type**

**Description:** Select whether the strategy is Intraday or Positional.  
**Logic:**

* **Intraday** → all legs are squared off at Sqroff Time on the same trading day.  
* **Positional** → legs carry forward until natural exit (per-leg TP/SL), Master TP/SL, Sqroff by Fix Time, or contract expiry.  
* In **BTST/STBT** mode, Trading Type is forcibly set to Positional and the field becomes read-only.

**Type:** String (Dropdown)  
**Default Value:** Intraday  
**Validation:** Must be "Intraday" or "Positional". BTST/STBT mode forces Positional.  
**Example:** Intraday  
**DB Field Name:** isIntraday (true \= Intraday, false \= Positional)  
**Execution Context:** Drives same-day vs multi-day position lifecycle. Also gates which Advance-tab sections are visible (Trading Cycle / VIX Filter / Dynamic Index Movement for Intraday; Sqroff by Fix Time for Positional).  
---

### **5\. Product**

**Description:** Order product type used by the broker for every leg in this strategy.  
**Logic:** Included in every order request to the broker during execution.  
**Type:** String (Dropdown)  
**Default Value:** MIS for Intraday; NRML for Positional and BTST/STBT  
**Validation:** Allowed Values:

- MIS  
- NRML  
- CNC

**Example:** NRML  
**DB Field Name:** productType  
**Execution Context:** Trading Server uses this product type when placing every order for every leg in the strategy.  
---

### **6\. Entry Time**

**Description:** Time at which the strategy enters positions on a trading day. Hidden in Range Breakout mode (replaced by Candle Start Time).  
**Logic:** At Entry Time, all legs are evaluated for entry conditions (ATM resolution, dynamic premium scan, wait-and-trade checks). If a leg passes its entry filter, the order is placed. In Range Breakout mode, this field is internally set to the Candle Start Time value.  
**Type:** Time (HH:mm)  
**Default Value:** 09:16  
**Validation:** Must be a valid HH:mm time within market hours.  
**Example:** 09:16  
**DB Field Name:** entryTime  
**Execution Context:** Trading Server schedules a one-shot trigger at this time each day to initiate the entry workflow.  
---

### **7\. Sqroff Time / Next Day Sqroff Time**

**Description:** Time at which the strategy force-exits all open legs. Label changes to "Next Day Sqroff Time*" when Trading Mode is BTST/STBT.  
**Logic:**

* In **Intraday Normal** mode: same-day exit at this time.  
* In **Positional Normal** mode: exit at this time on expiry day (or earlier if Sqroff by Fix Time is configured).  
* In **BTST/STBT** mode: exit at this time on the next trading day after entry.

**Type:** Time (HH:mm)  
**Default Value:** 15:29  
**Validation:** Must be a valid HH:mm time within market hours. Should be earlier than the broker's auto-square-off time for MIS product to avoid forced broker liquidation.  
**Example:** 15:29  
**DB Field Name:** exitTime  
**Execution Context:** Trading Server schedules a daily force-exit at this time. In BTST/STBT mode, the exit is scheduled on T+1 instead of T.  
---

### **8\. Candle Start Time (Range Breakout only)**

**Description:** Time at which the breakout reference candle begins. Replaces Entry Time when Trading Mode \= Range Breakout.  
**Logic:** At this time, the underlying's price is recorded as the candle's opening reference. The candle continues to track running High and Low until Candle End Time.  
**Type:** Time (HH:mm)  
**Default Value:** 09:16  
**Validation:** Must be a valid HH:mm time, earlier than Candle End Time.  
**Example:** 09:16  
**DB Field Name:** entryTime (the same payload field is used; in Range Breakout it holds the candle start time)  
**Execution Context:** Trading Server starts tracking High and Low of the underlying from this timestamp.  
---

### **9\. Candle End Time (Range Breakout only)**

**Description:** Time at which the breakout reference candle ends. The High and Low recorded between Candle Start Time and this time become the breakout reference levels.  
**Logic:** Once this time is reached, the candle's High and Low are locked. From then onwards, every leg watches for the underlying to break above the High or below the Low (per the leg's Breakout Direction setting) to trigger entry.  
**Type:** Time (HH:mm)  
**Default Value:** 09:17  
**Validation:** Must be a valid HH:mm time, later than Candle Start Time. Always sent in the payload as `range_time`, even when Range Breakout mode is not selected (in which case it carries a default value).  
**Example:** 09:17  
**DB Field Name:** range\_time  
**Execution Context:** Trading Server locks the High/Low of the underlying at this time and arms breakout monitoring for each leg.  

---

# Legs Parameters

Each leg entry represents one tradable instrument and one independent set of execution rules. Multiple legs are supported and all configured legs are evaluated and executed under the strategy's entry conditions. Each leg is stored as one object inside the `sub[]` array of the API payload.

### **1\. Symbol**

**Description:** The instrument assigned to this leg. Clicking the Symbol field opens the "Select Symbol" dialog where Exchange, Segment, Symbol, Contract, Expiry, ATM, and Option Type are configured. Quick-select chips display common combinations (OPT and FUT).  
**Logic:** The resolved leg symbol is shown as a concatenated string (e.g., "BANKNIFTY OPT NEAR WEEKLY 0 CE", "NIFTY FUT NEAR MONTHLY"). Strike resolution occurs at signal/entry time based on ATM Type, ATM offset, and live underlying price.  
**Type:** Composite field (opens dialog)  
**Default Value:** Blank (required)  
**Validation:** Required. A fully resolved instrument must be selected.  
**Example:** BANKNIFTY OPT NEAR WEEKLY 0 CE  
**DB Field Name:** exchange, segment, symbol, contract, expiry, atm, strikePrice, optionType (all stored as separate fields inside each sub object)  
**Execution Context:** Trading Server uses these fields to resolve the exact contract for order placement when entry conditions are met.  
---

#### **1.1 Exchange**

**Description:** The exchange for this leg's instrument.  
**Logic:** Determines which segments and symbols are available for this leg.  
**Type:** String (Dropdown)  
**Default Value:** NFO  
**Validation:** Allowed Values: NSE-EQ, NFO, BFO, BSE, MCX, CDS, CRYPTO  
**Example:** NFO  
**DB Field Name:** exchange (inside sub object)  
**Execution Context:** Selects the appropriate market feed and instrument master for this leg.  
---

#### **1.2 Segment**

**Description:** Segment of the leg instrument.  
**Logic:** Determines instrument type. ATM Type, ATM offset, Option Type, Premium Start/End Range fields are active only when Segment \= OPT.  
**Type:** String (Dropdown)  
**Default Value:** FUT  
**Validation:** Allowed Values: FUT, OPT, Stock, INDEX  
**Example:** OPT  
**DB Field Name:** segment (inside sub object)  
**Execution Context:** Drives the strike-resolution and contract-resolution path for this leg.  
---

#### **1.3 Symbol Name**

**Description:** The underlying symbol traded by this leg.  
**Logic:** All symbols are filtered by selected Exchange and Segment. Symbol on a leg can be different from the strategy-level Underlying Symbol.  
**Type:** String (Dropdown / Searchable)  
**Default Value:** BANKNIFTY  
**Validation:** Must be a valid symbol for the selected exchange and segment.  
**Example:** NIFTY, BANKNIFTY, RELIANCE  
**DB Field Name:** symbol (inside sub object)  
**Execution Context:** Used as the instrument master lookup key.  
---

#### **1.4 Contract**

**Description:** Contract series selection for this leg.  
**Logic:** Determines which expiry contract in the chain is used. NEAR = nearest/current; NEXT = next contract in sequence; FAR = far contract.  
**Type:** String (Dropdown)  
**Default Value:** NEAR  
**Validation:** Allowed Values: NEAR, NEXT, FAR  
**Example:** NEAR  
**DB Field Name:** contract (inside sub object)  
**Execution Context:** Combined with Expiry to resolve the exact contract date.  
---

#### **1.5 Expiry**

**Description:** Expiry type for the leg.  
**Logic:** Resolved at runtime using the symbol's expiry calendar combined with the Contract selection.  
**Type:** String (Dropdown)  
**Default Value:** MONTHLY  
**Validation:** Allowed Values: MONTHLY, WEEKLY (shown only for symbols that support weekly expiry).  
**Example:** WEEKLY  
**DB Field Name:** expiry (inside sub object)  
**Execution Context:** Trading Server resolves to the exact expiry date during contract resolution.  
---

### **2\. ATM Type**

**Description:** Defines how the strike is resolved for option legs. Either Fix (relative to underlying ATM) or Dynamic (scan strikes for premium within a range).  
**Logic:**

* **Fix** → strike is selected as `ATM ± offset`. ATM is computed from the underlying's live price.  
* **Dynamic** → reveals Premium Start Range and Premium End Range fields. At entry time, the system scans all available strikes on the option chain and selects the strike whose current premium falls within the configured Start–End range.

**Type:** String (Dropdown)  
**Default Value:** Fix  
**Validation:** Allowed Values: Fix, Dynamic. When Dynamic is selected, Premium Start Range and Premium End Range must both be non-zero and Start \<= End.  
**Example:** Dynamic  
**DB Field Name:** atmType  
**Execution Context:** Drives the strike-resolution engine at signal/entry time. Fix → arithmetic offset. Dynamic → chain scan.  
---

#### **2.1 ATM (offset)**

**Description:** Strike offset from At-The-Money, used when ATM Type \= Fix.  
**Logic:** 0 = exactly ATM. Positive integer = move strikes away from ATM in steps of 100 (e.g., \+100 → next strike up). Negative integer = move strikes away in the opposite direction. The exact strike interval depends on the underlying's standard strike spacing.  
**Type:** Integer  
**Default Value:** 0  
**Validation:** Applicable only for OPT segment with ATM Type \= Fix.  
**Example:** 0 (ATM), \+100, \-100  
**DB Field Name:** atm  
**Execution Context:** Strike resolution at entry time uses this offset relative to the live ATM strike.  
---

#### **2.2 Premium Start Range**

**Description:** Lower bound of the premium range used for Dynamic ATM Type strike selection.  
**Logic:** Active only when ATM Type \= Dynamic. The strike scanner selects the strike whose live premium is \>= Premium Start Range and \<= Premium End Range.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Required and \> 0 when ATM Type \= Dynamic. Must be \<= Premium End Range.  
**Example:** 100  
**DB Field Name:** premiumStartRange  
**Execution Context:** Trading Server scans the option chain at signal time and picks the first strike whose premium falls inside this range.  
---

#### **2.3 Premium End Range**

**Description:** Upper bound of the premium range used for Dynamic ATM Type strike selection.  
**Logic:** Active only when ATM Type \= Dynamic.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Required and \>= Premium Start Range when ATM Type \= Dynamic.  
**Example:** 1000  
**DB Field Name:** premiumEndRange  
**Execution Context:** Upper boundary for the chain scan.  
---

#### **2.4 Option Type**

**Description:** CE (Call) or PE (Put) for option legs. Empty string for FUT and Stock legs.  
**Logic:** Active only when Segment \= OPT.  
**Type:** String (Dropdown)  
**Default Value:** "" (blank for FUT/Stock); CE for OPT  
**Validation:** Allowed Values: CE, PE, "". Must be CE or PE when Segment \= OPT.  
**Example:** CE  
**DB Field Name:** optionType  
**Execution Context:** Drives the side of the option chain used for strike selection.  
---

### **3\. Lot/Qty**

**Description:** Base quantity for this leg. Field label toggles between "Lot" and "Qty" depending on Qty Type.  
**Logic:** Final order quantity = base value × qtyMultiply (deployment-time multiplier). For Lot type, the base is multiplied by the exchange lot size internally. For Qty type, the value is used directly.  
**Type:** Number with type toggle (Lot / Qty)  
**Default Value:** 1  
**Validation:** Must be a positive number.  
**Example:** 1 (Lot) or 30 (Qty)  
**DB Field Name:** qty, lot, qtyType ("Qty" or "Lot")  
**Execution Context:** Trading Server multiplies this by qtyMultiply when placing orders.  
---

### **4\. Trade Side**

**Description:** BUY or SELL direction for this leg.  
**Logic:** Determines whether this leg opens a long or short position.  
**Type:** String (Dropdown)  
**Default Value:** BUY  
**Validation:** Allowed Values: BUY, SELL  
**Example:** SELL (for short straddle CE/PE legs)  
**DB Field Name:** tradeSide  
**Execution Context:** Trading Server places a BUY or SELL order for this leg accordingly.  
---

### **5\. Target**

**Description:** Per-leg profit target value with type toggle (Money / Point / Percentage(%)).  
**Logic:** When this leg's individual P\&L reaches the target value (in the configured unit), the leg is squared off. 0 disables the per-leg target.  
**Type:** Number with type toggle (M / Pt / %)  
**Default Value:** 0 M  
**Validation:** Must be \>= 0. 0 disables.  
**Example:** 100 (Money), 5 (Point), 25 (Percentage)  
**DB Field Name:** target (numeric), targetBy ("Money" / "Point" / "Percentage(%)")  
**Execution Context:** Trading Server monitors this leg's P\&L continuously and triggers leg-level exit when target hits.  
---

### **6\. SL**

**Description:** Per-leg stop-loss value with type toggle (Money / Point / Percentage(%)).  
**Logic:** When this leg's individual loss reaches the SL value (in the configured unit), the leg is squared off. 0 disables the per-leg SL.  
**Type:** Number with type toggle (M / Pt / %)  
**Default Value:** 0 M  
**Validation:** Must be \>= 0. 0 disables.  
**Example:** 10 (Money), 2 (Point), 15 (Percentage)  
**DB Field Name:** sl (numeric), slBy ("Money" / "Point" / "Percentage(%)")  
**Execution Context:** Trading Server monitors this leg's loss continuously and triggers leg-level SL exit when reached.  
---

### **7\. Trail SL (Checkbox 1 of 4)**

**Description:** Enable stop-loss trailing for this leg. When checked, four sub-fields become active. This is the ONLY per-leg checkbox visible in BTST/STBT mode.  
**Logic:** As the leg's profit grows by the configured Market Move amount, the SL shifts by the configured SL Move amount in the favorable direction. The trail is repeated up to No of Trail SL times (0 = unlimited).  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False. When True, all four sub-fields should be configured.  
**Example:** True  
**DB Field Name:** is\_trail\_sl  
**Execution Context:** Activates dynamic SL adjustment for this leg.  
---

#### **7.1 Trail SL By**

**Description:** Unit type for Market Move and SL Move values.  
**Logic:** Determines whether trailing thresholds are interpreted in Points, Money, or Percentage(%).  
**Type:** String (Dropdown)  
**Default Value:** Point  
**Validation:** Allowed Values: Point, Money, Percentage(%)  
**Example:** Point  
**DB Field Name:** trail\_sl\_by  
**Execution Context:** Unit converter used by the trailing engine.  
---

#### **7.2 Market Move**

**Description:** Profit movement amount that must occur for one trail step to trigger.  
**Logic:** Each time the leg's profit increases by this amount (in the configured unit), the SL is shifted by SL Move. Profit measurement starts from the entry price.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0. 0 disables trailing even if checkbox is on.  
**Example:** 0.2 (Point)  
**DB Field Name:** trail\_sl\_market\_move  
**Execution Context:** Threshold for one trail step.  
---

#### **7.3 SL Move**

**Description:** Amount by which the SL shifts on each trail step.  
**Logic:** Each time Market Move is breached, the SL moves by this amount in the favorable direction (toward higher levels for BUY legs, lower levels for SELL legs).  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 0.2 (Point)  
**DB Field Name:** trail\_sl\_move  
**Execution Context:** Step size for each SL trailing adjustment.  
---

#### **7.4 No of Trail SL**

**Description:** Maximum number of trail steps allowed for this leg.  
**Logic:** After this many trailing steps, no further SL adjustments are made. 0 = unlimited.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 10  
**DB Field Name:** no\_of\_time\_trail\_sl  
**Execution Context:** Caps total number of trailing operations.  
---

### **8\. Reentry (Checkbox 2 of 4)**

**Description:** Enable Re-entry behavior for this leg. Hidden in BTST/STBT mode.  
**Logic:** After the leg closes by TP or SL (or both, depending on Reentry On selection), the leg waits for the underlying/premium to return to the original entry price level, then re-enters the position. This repeats up to No of Reentry times.  
**Type:** Boolean (Checkbox)  
**Default Value:** False (`reentry_on = "None"`)  
**Validation:** Allowed values: True / False. When True, Reentry On and No of Reentry must be configured.  
**Example:** True  
**DB Field Name:** reentry\_on (when not "None", reentry is active)  
**Execution Context:** Activates the re-entry watcher for this leg after a TP/SL exit.  
---

#### **8.1 Reentry On**

**Description:** Specifies under what exit condition re-entry should occur.  
**Logic:** Determines whether re-entry is armed after a TP exit, an SL exit, or both.  
**Type:** String (Dropdown)  
**Default Value:** None  
**Validation:** Allowed Values: TP Only, SL Only, TP SL Both, None  
**Example:** TP Only  
**DB Field Name:** reentry\_on  
**Execution Context:** Filters which exit events should trigger re-entry monitoring.  
---

#### **8.2 No of Reentry**

**Description:** Maximum number of times this leg can re-enter in a cycle.  
**Logic:** After this many re-entries, the leg stops attempting further re-entries until next cycle.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0. 0 effectively disables re-entry.  
**Example:** 1  
**DB Field Name:** no\_of\_reentry  
**Execution Context:** Counter limit for re-entry attempts.  
---

### **9\. Reexecute (Checkbox 3 of 4)**

**Description:** Enable Re-execute behavior for this leg. Hidden in BTST/STBT mode.  
**Logic:** After the leg closes by TP or SL (or both), the leg immediately opens a new position at the current ATM (or current Dynamic-resolved) strike, without waiting for price reversion. An optional delay can be applied before the new position is opened.  
**Type:** Boolean (Checkbox)  
**Default Value:** False (`reexecute_on = "None"`)  
**Validation:** Allowed values: True / False.  
**Example:** True  
**DB Field Name:** reexecute\_on (when not "None", reexecute is active)  
**Execution Context:** Activates the re-execute trigger for this leg after a TP/SL exit.  
---

#### **9.1 Reexecute On**

**Description:** Exit condition that triggers re-execute.  
**Logic:** TP Only / SL Only / TP SL Both.  
**Type:** String (Dropdown)  
**Default Value:** None  
**Validation:** Allowed Values: TP Only, SL Only, TP SL Both, None  
**Example:** SL Only  
**DB Field Name:** reexecute\_on  
**Execution Context:** Filters which exit events arm the re-execute path.  
---

#### **9.2 No of Reexecute**

**Description:** Maximum number of times this leg can re-execute in a cycle.  
**Logic:** Counter limit for re-execute attempts.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 1  
**DB Field Name:** no\_of\_reexecute  
**Execution Context:** Caps re-execute attempts per cycle.  
---

#### **9.3 Reexecute Delay (Minute)**

**Description:** Delay in minutes before opening the new position after a re-execute trigger.  
**Logic:** Useful to avoid immediate re-entry into the same volatility burst. 0 = immediate.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 2  
**DB Field Name:** reexecute\_delay  
**Execution Context:** Inserts a wait period between the close event and the new entry.  
---

### **10\. Wait and Trade (Checkbox 4 of 4)**

**Description:** Enable Wait and Trade behavior for this leg. Hidden in BTST/STBT mode.  
**Logic:** Once the Entry Time is reached, the leg does not enter immediately. Instead, it waits until the premium has moved by the configured Value in the configured Direction (UP %, Down %, Up Pts., Down Pts.) from the entry reference, then enters at that point.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False. When True, Value and Direction must be configured.  
**Example:** True  
**DB Field Name:** is\_wait\_and\_trade  
**Execution Context:** Activates the wait-watcher that delays entry until the premium movement condition is met.  
---

#### **10.1 Value**

**Description:** Numeric magnitude of the required premium movement.  
**Logic:** Interpreted in the unit defined by Direction (percentage or points).  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \> 0 when checkbox is on.  
**Example:** 10  
**DB Field Name:** wait\_value  
**Execution Context:** Movement threshold.  
---

#### **10.2 Direction**

**Description:** Direction and unit of the required premium movement.  
**Logic:** Defines whether the wait-watcher triggers on an upward or downward move and whether the unit is percentage or points.  
**Type:** String (Dropdown)  
**Default Value:** None  
**Validation:** Allowed Values: UP %, Down %, Up Pts., Down Pts., None  
**Example:** UP %  
**DB Field Name:** wait\_for  
**Execution Context:** Direction selector for the wait-watcher.  
---

### **11\. Breakout Direction (Range Breakout legs only)**

**Description:** Direction in which the underlying must break out of the reference candle to trigger this leg's entry. Visible only when Trading Mode \= Range Breakout. Replaces the 4-checkbox group with a single field (only Trail SL checkbox remains visible alongside).  
**Logic:**

* **High** → leg enters when underlying breaks above the candle High.  
* **Low** → leg enters when underlying breaks below the candle Low.

**Type:** String (Dropdown)  
**Default Value:** High  
**Validation:** Allowed Values: High, Low  
**Example:** High  
**DB Field Name:** range\_breakout\_direction  
**Execution Context:** Trading Server arms a breakout watcher for this leg using the locked candle High or Low.  
---

### **12\. Copy (Icon)**

**Description:** Duplicates this leg row with identical settings.  
**Logic:** Creates a new sub object pre-filled with all values from the current leg. User can then modify the duplicate.  
**Type:** UI Action (Icon)  
**DB Field Name:** (UI only — triggers creation of a new sub object)  
**Execution Context:** Not an execution parameter. Used for rapid multi-leg setup.  
---

### **13\. Add (+)**

**Description:** Adds a new blank leg row.  
**Logic:** Creates an empty sub object for configuration.  
**Type:** UI Action (Button)  
**DB Field Name:** (UI only)  
**Execution Context:** Not an execution parameter.  
---

### **14\. Delete (×)**

**Description:** Removes this leg from the strategy.  
**Logic:** Deletes the sub object permanently from the configuration.  
**Type:** UI Action (Icon)  
**DB Field Name:** (UI only)  
**Execution Context:** Not an execution parameter.  

---

# Advance Parameters

The Advance tab is **mode-aware** — different sections are shown depending on Trading Mode and Trading Type. The following sections describe every section and field; mode-specific availability is noted on each.

## **Section A. Master Target & Stop-Loss (all modes)**

### **1\. Master Target**

**Description:** Combined-cycle profit target across all legs.  
**Logic:** When the combined MTM profit of all open and closed legs in the current cycle reaches this value (in the configured unit), all open legs are squared off and the cycle ends. 0 disables.  
**Type:** Number with type toggle (M / Pt / Total Premium(%))  
**Default Value:** 0 M  
**Validation:** Must be \>= 0.  
**Example:** 5000 (Money)  
**DB Field Name:** target (numeric); targetBy ("Money" / "Point" / "Total Premium(%)")  
**Execution Context:** Trading Server monitors combined cycle MTM continuously and triggers full cycle exit at this threshold.  
---

### **2\. Master SL**

**Description:** Combined-cycle stop-loss across all legs.  
**Logic:** When the combined MTM loss of all open and closed legs in the current cycle reaches this value, all open legs are squared off and the cycle ends. 0 disables. UI displays the value as `-0` to emphasize the loss-direction nature of the field.  
**Type:** Number with type toggle (M / Pt / Total Premium(%))  
**Default Value:** 0 M (displayed as \-0 in UI)  
**Validation:** Must be \>= 0.  
**Example:** 3000 (Money)  
**DB Field Name:** sl (numeric); slBy ("Money" / "Point" / "Total Premium(%)")  
**Execution Context:** Trading Server monitors combined loss continuously and triggers full cycle exit at this threshold.  
---

### **3\. Trail SL? (Master Trail)**

**Description:** Enable Master SL trailing across the combined cycle MTM.  
**Logic:** When enabled, reveals Trail Type (Dynamic or Fix) and corresponding sub-fields.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** isTrailSl  
**Execution Context:** Activates the master trail engine for the combined cycle MTM.  
---

#### **3.1 Trail Type**

**Description:** Master trail engine type.  
**Logic:**

* **Dynamic** → uses Profit Move / SL Move / No of Trail SL ladder.  
* **Fix** → uses a custom table of (Profit Move, SL Value) pairs.

**Type:** String (Dropdown)  
**Default Value:** Dynamic  
**Validation:** Allowed Values: Dynamic, Fix  
**Example:** Dynamic  
**DB Field Name:** trailType  
**Execution Context:** Selects which trailing engine evaluates master SL.  
---

#### **3.2 Profit Move (Dynamic only)**

**Description:** Combined profit increment required to trigger one master SL trail step.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 2000  
**DB Field Name:** profitMove  
**Execution Context:** Threshold per trail step.  
---

#### **3.3 SL Move (Dynamic only)**

**Description:** Amount by which master SL shifts per trail step.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 500  
**DB Field Name:** slMove  
**Execution Context:** Step size for master SL adjustment.  
---

#### **3.4 No of Trail SL (Dynamic only)**

**Description:** Max number of master SL trail steps. 0 = unlimited.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 5  
**DB Field Name:** noOfTrailSL  
**Execution Context:** Caps master trail iterations.  
---

#### **3.5 Live max MTM as profit move (Dynamic only)**

**Description:** When enabled, the trail uses the running peak MTM (live max) as the reference, rather than a fixed Profit Move threshold. The master SL is computed as `peak MTM − SL Move`, refreshing whenever the peak rises.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** is\_live\_mtm\_profit\_move (0 = false, 1 = true)  
**Execution Context:** Switches the trail engine from threshold-step mode to peak-tracking mode.  
---

#### **3.6 Fix Trail Table (Fix only)**

**Description:** Custom mapping of (Profit Move → Master SL value) pairs. For each row, when combined MTM crosses the Profit Move value, the master SL is set to the row's SL value.  
**Type:** Table (JSON-encoded string in payload)  
**Default Value:** "" (empty)  
**Validation:** Each row must contain a positive Profit Move and a valid SL Value.  
**Example:** `[{"profit":2000,"sl":-500},{"profit":5000,"sl":1000},{"profit":10000,"sl":4000}]`  
**DB Field Name:** fixTrail (JSON string)  
**Execution Context:** Engine reads rows in order and applies the SL value matching the highest crossed Profit Move.  

**Additional payload fields:** `startTrailAfterProfit` (numeric, defaults 0) and `replaceMasterSlWithStartTrailing` (boolean, defaults false) are always sent in the payload to support advanced trail behaviors.

---

## **Section B. Working Days (all modes)**

### **4\. Working Days**

**Description:** Days of the week on which the strategy is allowed to run.  
**Logic:** When the current day is not enabled, the strategy does not enter new positions. Existing positions continue to be managed.  
**Type:** Multiple Boolean Flags (Checkboxes)  
**Default Value:** MON = True, TUE = True, WED = True, THU = True, FRI = True, SAT = False, SUN = False  
**Validation:** Allowed values per day: True / False  
**Example:** Mon–Fri enabled, Sat–Sun disabled  
**DB Field Name:** mon, tue, wed, thu, fri, sat, sun  
**Execution Context:** Checked at strategy entry time each day.  
---

### **5\. Required Margin**

**Description:** Estimated margin for analytics and capital planning. Does not block trades.  
**Logic:** Informational only — used in capital utilization analytics.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be \>= 0.  
**Example:** 100000  
**DB Field Name:** requiredMargin  
**Execution Context:** Used by analytics dashboards only.  

---

## **Section C. Safety Checkboxes (all modes)**

### **6\. Sqroff All Legs (on any single leg close by TP or SL)**

**Description:** When any single leg closes due to its own TP or SL, all other open legs are squared off immediately.  
**Logic:** Used when the multi-leg structure must enter and exit as a complete basket.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** squareoffLegs (also sent as sqroffAllLegs in some payloads)  
**Execution Context:** Single leg exit cascades to all remaining legs.  
---

### **7\. Trail SL to cost on other leg SL**

**Description:** When any leg's SL hits, the trail SL of all other open legs is reset to their break-even (cost) levels.  
**Logic:** Configured per-leg via the `trail_sl_cost` field inside each sub object. Lets the surviving legs lock in zero-loss after a hedge leg is stopped out.  
**Type:** Boolean (Checkbox, per leg)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** trail\_sl\_cost (per-leg field inside sub object)  
**Execution Context:** Updates other legs' SL to their entry price on any leg's SL exit.  
---

### **8\. Sqroff Position on Rejection**

**Description:** When any leg's order is rejected by the broker (margin shortfall, freeze, etc.), all currently confirmed open legs are squared off.  
**Logic:** Prevents incomplete strategy positions when partial leg execution occurs.  
**Type:** Boolean (Checkbox)  
**Default Value:** False (UI default; payload examples ship with true)  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** squareoffRejection  
**Execution Context:** Safety net for partial leg fills.  
---

### **9\. Allow Late Trading**

**Description:** Permit the strategy to start even if the current time is past the configured Entry Time.  
**Logic:** When disabled, missing the Entry Time means the strategy will not enter that day. When enabled, the strategy can be started after Entry Time and will enter immediately if other conditions allow.  
**Type:** Boolean (Checkbox)  
**Default Value:** False (UI default; payload examples ship with true)  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** allowLateTrading  
**Execution Context:** Skips the Entry Time check at startup.  
---

### **10\. Consider Closed Trades PNL for Master TP SL**

**Description:** Include the realized P\&L of legs that have already closed (by TP, SL, or trail) in the master TP/SL calculation.  
**Logic:** When enabled, the Master Target/SL evaluates against `realized P&L + unrealized P&L` of all legs in the cycle. When disabled, only unrealized P\&L of currently open legs counts.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** cosider\_closed\_pnl (note: API field has a typo — single 'n')  
**Execution Context:** Switches master MTM aggregation mode.  

---

## **Section D. Trading Cycle (Normal Intraday and Normal Positional only)**

### **11\. No of Cycle**

**Description:** Number of trading cycles per day (Intraday) or per holding period (Positional).  
**Logic:** When the current cycle ends (by Master TP/SL or all-legs exit), a new cycle begins after the configured Cycle Delay. Master TP/SL resets per cycle and is not cumulative.  
**Type:** Number  
**Default Value:** 1  
**Validation:** Must be \>= 1.  
**Example:** 2  
**DB Field Name:** noOfIntradayCycle  
**Execution Context:** Cycle scheduler restarts the strategy this many times.  
---

### **12\. Cycle Delay (in Minute)**

**Description:** Wait time in minutes between cycles.  
**Logic:** After one cycle closes, the strategy waits this long before starting the next cycle. 0 = immediate.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 10  
**DB Field Name:** intraday\_cycle\_delay  
**Execution Context:** Inserts wait between cycle boundaries.  

---

## **Section E. VIX Filter (Normal Intraday and Normal Positional only)**

### **13\. VIX Filter**

**Description:** Enable VIX-based entry gating.  
**Logic:** When enabled, at Entry Time the system checks if VIX is within the configured Start–End range. If yes, the cycle proceeds. If no, no trades are placed for that cycle. Re-checked on manual restart only.  
**Type:** Boolean (Enable / Disable Dropdown)  
**Default Value:** Disable  
**Validation:** Allowed values: Enable / Disable  
**Example:** Enable  
**DB Field Name:** enableVixFilter  
**Execution Context:** Trading Server reads live VIX at cycle entry time.  
---

#### **13.1 VIX Start Value**

**Description:** Lower bound of acceptable VIX value.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0. Must be \<= VIX End Value.  
**Example:** 15  
**DB Field Name:** vixStartValue  
**Execution Context:** Lower bound of the VIX gate.  
---

#### **13.2 VIX End Value**

**Description:** Upper bound of acceptable VIX value.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= VIX Start Value.  
**Example:** 16  
**DB Field Name:** vixEndValue  
**Execution Context:** Upper bound of the VIX gate.  

---

## **Section F. Dynamic Index/Future Movement Cycle Trading (Normal Intraday only)**

### **14\. Enable Dynamic Index Movement Cycle**

**Description:** Enable auto-cycling when the underlying moves by a configured amount.  
**Logic:** When the underlying moves by Index Movement (in Percentage or Points) from the current cycle's entry reference, the current positions are closed and a new cycle starts. Up to No of Cycle Per Day such auto-cycles are allowed.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** isResetCycle  
**Execution Context:** Activates the underlying-movement watcher for automatic re-cycling.  
---

#### **14.1 Index Move By**

**Description:** Unit type for Index Movement.  
**Logic:** Determines whether Index Movement is interpreted in Percentage or Points.  
**Type:** String (Dropdown)  
**Default Value:** Percentage(%)  
**Validation:** Allowed Values: Percentage(%), Point  
**Example:** Point  
**DB Field Name:** index\_move\_by  
**Execution Context:** Unit converter for the movement check.  
---

#### **14.2 Index Movement**

**Description:** Magnitude of underlying movement that triggers a re-cycle.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \> 0 when enabled.  
**Example:** 100 (Points) or 1 (%)  
**DB Field Name:** resetCycleIndexPercentage  
**Execution Context:** Triggers cycle reset when the underlying moves by this amount.  
---

#### **14.3 No of Cycle Per Day**

**Description:** Maximum number of auto re-cycles allowed in a single day.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 2  
**DB Field Name:** noOfCyclePerDay  
**Execution Context:** Caps auto-cycle count per trading day.  

---

## **Section G. Sqroff by Fix Time (Normal Positional and BTST/STBT only)**

### **15\. Sqroff by Fix Time**

**Description:** Enable a pre-expiry exit on a specific weekday and time.  
**Logic:** For positional strategies, configures a specific day (relative to expiry) and time at which positions are exited instead of waiting until expiry day. In BTST/STBT mode, this section is always shown and the user enables/disables it.  
**Type:** Boolean (Checkbox)  
**Default Value:** False  
**Validation:** Allowed values: True / False  
**Example:** True  
**DB Field Name:** sqroffByFixTime  
**Execution Context:** Schedules an early-exit job on the configured day and time.  
---

#### **15.1 Exit before Expiry Days**

**Description:** Number of days before expiry to exit. 0 = exit on expiry day.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 1 (exit one day before expiry)  
**DB Field Name:** sqroff\_before\_expiry\_days  
**Execution Context:** Trading Server schedules the exit relative to the contract's expiry date.  
---

#### **15.2 Sqroff Time**

**Description:** Time on the configured exit day at which the strategy exits.  
**Type:** Time (HH:mm)  
**Default Value:** ""  
**Validation:** Must be a valid HH:mm time when enabled.  
**Example:** 12:00  
**DB Field Name:** sqroffTime  
**Execution Context:** Scheduled exit clock time.  
---

#### **15.3 Sqroff Week Day**

**Description:** Day of the week on which the exit occurs.  
**Type:** String (Dropdown)  
**Default Value:** ""  
**Validation:** Allowed Values: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday  
**Example:** Thursday  
**DB Field Name:** sqroffWeekDay  
**Execution Context:** Scheduled exit weekday.  

---

## **Section H. Condition Checking Time (Normal Positional and BTST/STBT only)**

### **16\. Delay after market start (minutes)**

**Description:** Delay TP/SL evaluation from Day 2 onwards by N minutes after market open.  
**Logic:** Prevents false TP/SL triggers caused by overnight gap-up or gap-down opens. On the entry day, TP/SL evaluation is immediate. From the second day onwards (for positional/BTST positions), TP/SL evaluation is paused for N minutes after market open.  
**Type:** Number  
**Default Value:** 0  
**Validation:** Must be \>= 0.  
**Example:** 60  
**DB Field Name:** chk\_con\_delay\_after\_market\_start  
**Execution Context:** Inserts a daily morning delay window before TP/SL monitoring resumes.  

---

## **Mode-specific Visibility Summary**

| Section | Normal Intraday | Normal Positional | Range Breakout | BTST/STBT |
|---------|-----------------|--------------------|----------------|-----------|
| Master TP/SL + Master Trail | ✓ | ✓ | ✓ | ✓ |
| Working Days + Required Margin | ✓ | ✓ | ✓ | ✓ |
| Safety Checkboxes | ✓ | ✓ | ✓ | ✓ |
| Trading Cycle | ✓ | ✓ | ✗ | ✗ |
| VIX Filter | ✓ | ✓ | ✗ | ✗ |
| Dynamic Index Movement | ✓ | ✗ | ✗ | ✗ |
| Sqroff by Fix Time | ✗ | ✓ | ✗ | ✓ |
| Condition Checking Time | ✗ | ✓ | ✗ | ✓ |

---

# Description Parameters

### **1\. Short Description**

**Description:** Brief one-line summary of the strategy.  
**Logic:** Informational only. Used for quick identification in lists and Copilot context.  
**Type:** Single-line Text Input  
**Default Value:** ""  
**Validation:** Optional. Recommended max length 100–150 characters.  
**Example:** "BNF short straddle weekly, Master SL 5k, trail to cost on leg SL."  
**DB Field Name:** shortDescription  
**Execution Context:** Displayed only — not used in execution.  
---

### **2\. Long Description**

**Description:** Detailed strategy explanation for documentation and Copilot training.  
**Logic:** Informational only.  
**Type:** Multi-line Text Area  
**Default Value:** ""  
**Validation:** Optional.  
**Example:** "Weekly Banknifty short straddle. Sells ATM CE and ATM PE in equal quantity at 9:16. Master Target 5000, Master SL 3000 with dynamic trail (Profit Move 2000, SL Move 500). Trail SL to cost on any leg SL. Sqroff All Legs enabled. Exits 1 day before expiry at 12:00."  
**DB Field Name:** longDescription  
**Execution Context:** Displayed only — not used in execution.  

---

# Help

### **🔹 TAB 1: MAIN – HELP**

**Strategy Name**  
Define your strategy name. E.g., "Banknifty Short Straddle". Used only for identification.

**Underlying Symbol**  
Select the underlying for option trading. The system watches this price to derive leg strike prices. E.g., NFO → FUT → BANKNIFTY.

**Trading Mode**  
Choose Normal, Range Breakout, or BTST/STBT.  
Normal: standard time-based entry.  
Range Breakout: entry when selected interval candle's High or Low is broken. Set Candle Start Time and Candle End Time. If market never breaks the range, no position is taken.  
BTST/STBT: open today, close next day. Forces Positional.

**Trading Type**  
Intraday = closes all positions at Sqroff Time on the same day.  
Positional = holds until expiry or Sqroff by Fix Time.

**Product**  
MIS (auto-closed by broker if not closed), NRML (positional F&O), CNC (equity positional).

**Entry Time**  
Strategy entry time. Recommend 09:17 or later to avoid high slippage at market open.

**Sqroff Time**  
Exit time for Intraday, or expiry-day exit time for Positional. Use a time before broker auto-exit for MIS.

**Next Day Sqroff Time (BTST/STBT)**  
Close position on the next trading day at this time.

**Candle Start Time / Candle End Time (Range Breakout)**  
Define the breakout reference candle. The system tracks the underlying's High and Low between these times, and triggers entry when the underlying breaks the candle High or Low (per each leg's Breakout Direction).

---

### **🔹 TAB 2: LEGS – HELP**

**Symbol**  
Click to open the "Select Symbol" dialog. Configure Exchange, Segment, Symbol, Contract, Expiry, ATM, and Option Type for this leg. Quick-select chips show common combinations.

**ATM Type**  
Fix = strike by ATM offset (0 ATM, +100, -100, etc.).  
Dynamic = scan all premiums; find a strike whose premium is in the Start–End range.

**Lot/Qty**  
Base quantity per leg. Multiplied by QtyX at deployment.

**Trade Side**  
BUY or SELL.

**Leg Target**  
Define by Money, Point, or Percentage. The leg closes when target is hit. 0 disables.

**Leg SL**  
Define by Money, Point, or Percentage. The leg closes when SL is hit. 0 disables.

**Leg Trail SL**  
Trail the leg SL as the market moves in your favour.  
Market Move = how much the market must move to trigger one trail step.  
SL Move = how much SL shifts per step.  
No of Trail SL = 0 means infinite.

**Leg Re-entry**  
After TP/SL, wait for the price to return to the original entry level, then re-enter. Repeat per the configured count.

**Leg Re-execute**  
After TP/SL, immediately open a new position at the current underlying/ATM. Repeat per count, with optional delay in minutes.

**Wait and Trade**  
Wait for the premium to move by the configured amount (UP %, Down %, Up Pts., Down Pts.) before entering.

**Breakout Direction (Range Breakout only)**  
High = enter only if underlying breaks above the candle High.  
Low = enter only if underlying breaks below the candle Low.

---

### **🔹 TAB 3: ADVANCE – HELP**

**Master Target**  
Close all legs when combined cycle MTM profit reaches this level. Money, Point, or Total Premium(%).

**Master Stop-Loss**  
Close all legs when combined cycle MTM loss reaches this level. Money, Point, or Total Premium(%).

**Trail Master Stop-Loss**  
Fix type = a custom Profit/SL value table.  
Dynamic type = Profit Move / SL Move / No of Trail SL.  
Live max MTM as profit move = trail against running peak MTM.

**Working Days**  
Trade only on selected days.

**Trading Cycle**  
Restart the strategy N times after each cycle completes. Cycle Delay = wait time between cycles. Master TP/SL resets each cycle.

**VIX Filter**  
Start the cycle only when VIX is within the VIX Start and VIX End range.

**Dynamic Index/Future Movement Cycle Trading (Intraday only)**  
Start a new cycle when the underlying moves by Index Movement (Points or %). Limited by No of Cycle Per Day.

**Sqroff Position on Rejection**  
Close all confirmed legs if any one leg's order is rejected.

**Allow Late Trading**  
When disabled, the strategy cannot start after Entry Time has passed.

**Sqroff by Fix Time**  
For positional strategies, exit on a configured day (Exit before Expiry Days) at Sqroff Time instead of waiting for expiry.

**Sqroff All Legs**  
Close all legs immediately when any one leg hits its TP or SL.

**Trail SL to cost on other leg SL**  
When any leg's SL hits, reset the trail SL of all other open legs to their break-even (cost) levels.

**Consider Closed Trades PNL for Master TP SL**  
Include the P&L of already-closed legs in the Master TP/SL calculation.

**Condition checking time**  
From Day 2 onwards, delay TP/SL checking by N minutes after market open to prevent false triggers on gap openings.

---

### **🔹 TAB 4: DESCRIPTION – HELP**

**Short Description**  
One-line summary for strategy identification.

**Detailed Description**  
Full explanation for ML training and user clarity.

---

# FAQ

**Q1. Which strategies can I build with Multi-Leg Hedger?**  
Options strategies (Short/Long Straddle, Short/Long Strangle, Call Spread, Put Spread, Synthetic Call, Covered Call, Collar, Butterfly, Iron Condor, Iron Butterfly, Box Spread), futures hedges, multi-leg time-based directional plays, BTST/STBT overnight carries, and Range Breakout intraday entries.

**Q2. What market segments are supported?**  
NSE-EQ, NFO, BFO, BSE, MCX, CDS, and CRYPTO. Each leg can be on a different exchange/segment.

**Q3. What happens on contract expiry?**  
For Positional strategies, positions are squared off on expiry day at the configured Sqroff Time (or earlier if Sqroff by Fix Time is configured for an earlier weekday).

**Q4. Can I build a strategy with multiple symbols?**  
Yes. Add as many legs as required, each with different symbols across different exchanges and segments. All legs are managed under a single strategy.

**Q5. NRML vs CNC for Positional strategies — which should I use?**  
Use **NRML** for F&O positional positions. Use **CNC** for equity/stock positional (delivery) positions.

**Q6. What's the difference between Intraday and Positional?**  
Intraday closes all legs at the configured Sqroff Time on the same trading day. Positional holds positions until expiry, until Sqroff by Fix Time is reached, or until Master/Leg TP/SL triggers.

**Q7. What happens when all legs close — does a new cycle start?**  
Yes, if **No of Cycle** is greater than 1. After all legs close, the strategy waits for the configured **Cycle Delay** minutes and then begins a new cycle.

**Q8. What is Cycle Delay?**  
Wait time (in minutes) between cycles. 0 = the next cycle starts immediately after the previous one ends.

**Q9. How does the VIX Filter work?**  
At the cycle's entry time, the system checks the current VIX value. If VIX falls within the configured Start–End range, the cycle proceeds and trades are placed. If not, no trades are placed for that cycle. The filter is re-checked on manual restart.

**Q10. What's the difference between Leg Target/SL and Master Target/SL?**  
Leg Target/SL applies to one individual leg. Master Target/SL applies to the combined MTM of the cycle across all legs.

**Q11. What is "Sqroff All Legs"?**  
When any one leg closes by TP or SL, all other open legs are immediately squared off. Useful for basket strategies that must enter and exit as a complete unit.

**Q12. What is "Consider Closed Trades PNL for Master TP SL"?**  
When enabled, the realized P&L of legs that have already closed (by leg TP/SL, trail, or rejection) is included in the Master TP/SL calculation. When disabled, only the unrealized P&L of currently open legs counts.

**Q13. What is "Sqroff Position on Rejection"?**  
When any leg's order is rejected by the broker, all confirmed open legs are immediately closed. This prevents incomplete (unhedged) strategy positions.

**Q14. What is "Allow Late Trading"?**  
When disabled, the strategy cannot start after the configured Entry Time has passed. When enabled, the strategy can be started later and will attempt entry immediately if other conditions allow.

**Q15. What is BTST/STBT mode?**  
Buy/Sell Today, Square-off Tomorrow. The strategy opens today and closes at the configured Next Day Sqroff Time on the next trading day. Trading Type is forced to Positional. Per-leg, only the Trail SL checkbox is available.

**Q16. What Trading Type does BTST/STBT force?**  
Positional. The field becomes read-only when BTST/STBT mode is selected.

**Q17. What is Range Breakout mode?**  
The system observes the underlying's High and Low during the candle defined by Candle Start Time → Candle End Time. After the candle ends, the system enters the leg's position when the underlying breaks above the candle High (Breakout Direction = High) or below the candle Low (Breakout Direction = Low).

**Q18. What's the difference between Fix and Dynamic ATM Type?**  
**Fix**: strike is selected as ATM ± offset from the underlying's current ATM strike.  
**Dynamic**: the system scans the entire option chain at entry time and selects the strike whose current premium falls within the configured Premium Start Range and Premium End Range.

**Q19. What is Leg Re-entry?**  
After the leg closes by TP/SL, the system waits for the price to return to the original entry level, then re-enters the position. Repeats up to the configured number of times.

**Q20. What is Leg Re-execute?**  
After the leg closes by TP/SL, the system immediately opens a new position at the current ATM (or current Dynamic-resolved) strike, without waiting for price reversion. An optional delay (in minutes) can be applied.

**Q21. What's the difference between Re-entry and Re-execute?**  
**Re-entry** waits for the price to revert to the original entry level. **Re-execute** opens a new position immediately at the current price. Re-entry is useful for mean-reversion setups; Re-execute is useful for trend-following or theta-collection setups.

**Q22. What is Wait and Trade?**  
After the Entry Time is reached, the leg waits until the premium has moved by the configured amount (UP %, Down %, Up Pts., Down Pts.) before actually entering. Useful when the user wants the premium to confirm a move before committing.

**Q23. What is Trail SL at the leg level?**  
The leg's SL is moved in the favorable direction as the market moves. **Market Move** = how much the market must move (in the configured unit) to trigger one trail step. **SL Move** = how much the SL shifts per step.

**Q24. What is Trail SL at the master level?**  
Master Trail can be Dynamic or Fix. **Dynamic** trails the master SL using the Profit Move / SL Move / No of Trail SL ladder. **Fix** uses a custom table of (Profit Move → Master SL) pairs.

**Q25. What is "Live max MTM as profit move"?**  
When enabled, the master trail uses the running peak MTM as the reference point — the master SL is computed as `peak MTM − SL Move`, refreshing every time the peak rises. This is different from the threshold-step mode where each Profit Move increment triggers one fixed SL shift.

**Q26. What is Fix Trail?**  
A custom table mapping Profit Move levels to specific Master SL values. As the combined MTM crosses each Profit Move row, the master SL is set to that row's SL value. Provides granular, non-linear SL control.

**Q27. What is Sqroff by Fix Time?**  
For Positional strategies, this configures a specific weekday and time (relative to expiry) at which the strategy exits — instead of waiting until expiry day. E.g., exit at Thursday 12:00, 1 day before expiry.

**Q28. What is Condition Checking Time?**  
From Day 2 onwards (for positional and BTST positions), TP/SL evaluation starts N minutes after market open. This avoids false triggers caused by overnight gap-ups or gap-downs.

**Q29. What is Dynamic Index/Future Movement Cycle Trading?**  
(Intraday only.) When the underlying moves by the configured Index Movement (Percentage or Points) from the cycle's entry reference, the current positions are closed and a new cycle is started. Limited by No of Cycle Per Day.

**Q30. Can I set a QtyX multiplier?**  
Yes. The `qtyMultiply` value is set at deployment time and multiplies every leg's quantity at order placement.

**Q31. What is Trail SL to cost on other leg SL?**  
When any one leg's SL is hit, the trail SL of all other open legs is reset to their break-even (cost) levels. This lets the surviving legs lock in zero loss after a hedge leg is stopped out.

**Q32. What if the Range Breakout candle is never broken?**  
No position is taken that day. For Intraday strategies, the strategy stays idle until Sqroff Time and then resets for the next day. For Positional strategies, the system can retry on the next trading day.

**Q33. How does the simulator work?**  
**Follow Simulator** prices the Target and SL from the theoretical entry price (not the actual broker fill price), standardizing the strategy's behavior across users regardless of individual slippage.

**Q34. What's the difference between Underlying Symbol and Leg Symbol?**  
**Underlying Symbol** is the price reference used to compute option ATM strikes. **Leg Symbol** is the actual instrument that gets traded. The two are typically related (e.g., underlying = BANKNIFTY FUT, leg = BANKNIFTY OPT) but can also be entirely different instruments.

---

# Copilot Rulebook

Below is the **FULL "HOW COPILOT SHOULD RESPOND" RULEBOOK** for the Multi-Leg Hedger Plugin.

This is a master AI-instruction document that completely defines:

* How Copilot must interpret user prompts for multi-leg strategies  
* How Copilot must select the Trading Mode (Normal / Range Breakout / BTST/STBT)  
* How Copilot must configure each leg's ATM, side, qty, target, SL, trail, re-entry, re-execute, wait-and-trade  
* How Copilot must configure Advance-tab sections per mode  
* How Copilot must ask clarifying questions (only when needed)  
* How Copilot must generate strategy output  
* How Copilot must avoid mistakes

---

# **🧠📘 Multi-Leg Hedger – COPILOT RESPONSE RULEBOOK**

### ***AI Behavior & Interpretation Logic***

---

# **1️⃣ COPILOT's PURPOSE**

The Copilot's job is to **convert trader instructions** (natural language) into a **complete Multi-Leg Hedger strategy configuration** spanning:

* Trading Mode (Normal / Range Breakout / BTST/STBT)  
* Main Parameters  
* Legs Parameters (one or more legs)  
* Advance Parameters (mode-aware)  
* Description Tab

Copilot must generate **100% valid, executable configurations** following all plugin field rules, mode-specific visibility rules, and per-leg checkbox availability rules.

Copilot should behave like a **professional options strategist**, not a chatbot.

---

# **2️⃣ CORE RESPONSIBILITIES**

Copilot must:

### **✔ Map natural language to the correct Trading Mode**

* "open today, close tomorrow" / "carry overnight" → BTST/STBT  
* "break of opening 5-min candle" / "after market opens, if breaks high" → Range Breakout  
* Everything else → Normal

### **✔ Identify each leg and configure it fully**

For each leg: Exchange, Segment, Symbol, Contract, Expiry, ATM Type (Fix vs Dynamic), ATM offset OR Premium Range, Option Type, Trade Side, Lot/Qty, Target, SL, Trail SL, Reentry, Reexecute, Wait and Trade.

### **✔ Configure Advance-tab sections per mode**

* Normal Intraday → Master TP/SL, Trail, Trading Cycle, VIX Filter, Dynamic Index Movement, Safety  
* Normal Positional → Master TP/SL, Trail, Trading Cycle, VIX Filter, Sqroff by Fix Time, Condition Checking Time, Safety  
* Range Breakout → Master TP/SL, Trail, Safety (no cycle / VIX / dynamic index)  
* BTST/STBT → Master TP/SL, Trail, Sqroff by Fix Time, Condition Checking Time, Safety

### **✔ Ask only necessary clarifying questions**

Only when a critical piece of information is missing.

### **✔ Generate valid JSON output per the API payload spec**

All fields must be set to valid values; mode-specific fields must be set per mode rules.

---

# **3️⃣ HOW COPILOT MUST INTERPRET NATURAL LANGUAGE**

---

## **A. Identify Trading Mode**

| User Phrase | Trading Mode | DB Flags |
|-------------|--------------|----------|
| "intraday straddle" | Normal | is\_range\_break\_out=false, is\_btst\_stbt=false |
| "positional iron condor" | Normal | is\_range\_break\_out=false, is\_btst\_stbt=false |
| "5-min opening range breakout" | Range Breakout | is\_range\_break\_out=true |
| "candle high break entry" | Range Breakout | is\_range\_break\_out=true |
| "BTST", "carry overnight", "open today close tomorrow" | BTST/STBT | is\_btst\_stbt=true |
| "STBT short overnight" | BTST/STBT | is\_btst\_stbt=true |

---

## **B. Identify ATM Type per Leg**

| User Phrase | ATM Type | Sub-fields |
|-------------|----------|------------|
| "ATM CE" / "ATM PE" | Fix | atm=0 |
| "100 points OTM" | Fix | atm=+100 (for CE) / -100 (for PE) |
| "premium around 100" | Dynamic | premiumStartRange=90, premiumEndRange=110 |
| "premium between 100 and 200" | Dynamic | premiumStartRange=100, premiumEndRange=200 |

---

## **C. Identify Trade Side**

| User Phrase | tradeSide |
|-------------|-----------|
| "buy", "long", "buy CE", "buy PE" | BUY |
| "sell", "short", "write", "sell CE", "sell PE" | SELL |

---

## **D. Identify Re-entry vs Re-execute**

| User Phrase | Mapping |
|-------------|---------|
| "re-enter when price comes back" | reentry\_on |
| "re-execute immediately after SL" | reexecute\_on = "SL Only" |
| "after target hit, re-enter at same price" | reentry\_on = "TP Only" |
| "after SL, open new position right away" | reexecute\_on = "SL Only" |

---

## **E. Identify Wait and Trade**

| User Phrase | Mapping |
|-------------|---------|
| "enter only after 10% rise in premium" | is\_wait\_and\_trade=true, wait\_for="UP %", wait\_value=10 |
| "wait for 20 point drop before entry" | is\_wait\_and\_trade=true, wait\_for="Down Pts.", wait\_value=20 |

---

## **F. Identify Trail SL By Type**

| User Phrase | trail\_sl\_by |
|-------------|---------------|
| "trail 5 points" | Point |
| "trail 500 rupees" | Money |
| "trail 10%" | Percentage(%) |

---

## **G. Identify Master Target / SL By Type**

| User Phrase | targetBy / slBy |
|-------------|-----------------|
| "master target 5000" | Money |
| "master target 50 points" | Point |
| "master target 10% of premium" | Total Premium(%) |

---

## **H. Identify VIX Filter**

| User Phrase | Mapping |
|-------------|---------|
| "only trade when VIX is 15 to 20" | enableVixFilter=true, vixStartValue=15, vixEndValue=20 |
| "skip high VIX days" | enableVixFilter=true with sensible bounds |

---

## **I. Identify Dynamic Index Movement (Intraday only)**

| User Phrase | Mapping |
|-------------|---------|
| "restart cycle if Nifty moves 100 points" | isResetCycle=true, index\_move\_by="Point", resetCycleIndexPercentage=100 |
| "if index moves 1% start new cycle" | isResetCycle=true, index\_move\_by="Percentage(%)", resetCycleIndexPercentage=1 |

---

# **4️⃣ WHEN COPILOT MUST ASK CLARIFYING QUESTIONS**

Only when **critical information is missing**:

1. **Symbol / Exchange / Segment unclear** → "Which instrument should this leg trade — futures or options?"  
2. **ATM offset ambiguous** → "Should this be ATM, OTM, or ITM? How many strikes from ATM?"  
3. **Reentry vs Reexecute unclear** → "After SL, do you want to wait for the price to come back (Re-entry) or immediately re-enter at current price (Re-execute)?"  
4. **Fix vs Dynamic ATM unclear** → "Should the strike be selected by ATM offset (Fix) or by premium range (Dynamic)?"  
5. **No legs defined at all** → "Which legs should I add to this strategy?"

---

# **5️⃣ WHEN NOT TO ASK QUESTIONS**

If information can be **reasonably inferred or is always defaulted**:

* `followSimulator` is always true → never ask  
* `paperTrading` is always true → never ask  
* `pauseAndSqrOffOnMarginExceed` is always true → never ask  
* `workingDay` per leg is always "ALL" → never ask  
* `qty_distribution` per leg is always "Fix" → never ask  
* `allowUpdateParameters` is always true → never ask  
* `effect_all_sub_strategies` is always false → never ask  
* No working days mention → Mon–Fri enabled, Sat–Sun disabled  
* No Master Target/SL mention → 0 (disabled)  
* No VIX Filter mention → Disabled  
* No Dynamic Index Movement mention → Disabled

---

# **6️⃣ OUTPUT FORMAT COPILOT MUST FOLLOW**

Every Copilot output must generate:

### **✔ A full Multi-Leg Hedger JSON configuration**

* Trading Mode flags  
* Main fields (strategyName, underlying, productType, isIntraday, entryTime, exitTime, range\_time)  
* Each leg as one object in `sub[]`  
* Advance fields (Master TP/SL, trail, Cycle, VIX, Dynamic Index, Sqroff by Fix Time, Safety)  
* Description (shortDescription + longDescription)  
* All hidden / default fields (followSimulator=true, paperTrading=true, etc.)

### **✔ MUST RESPECT MODE-SPECIFIC RULES**

* Range Breakout legs → only Trail SL checkbox (other 3 hidden) + Breakout Direction visible  
* BTST/STBT legs → only Trail SL checkbox; force isIntraday=false  
* Range Breakout / BTST/STBT → no Trading Cycle, no VIX, no Dynamic Index in payload (still serialize defaults)

### **✔ MUST EMIT ALL HIDDEN FIELDS AT DEFAULT VALUES**

`followSimulator: true`, `paperTrading: true`, `allowUpdateParameters: true`, `effect_all_sub_strategies: false`, `requiredCapital: 1`, `isEditCode: false`, `pauseAndSqrOffOnMarginExceed: true`, `qtyMultiply: 1`, `rebacktest: false`, and per-leg `qty_distribution: "Fix"`, `workingDay: "ALL"`, `product: null`.

---

# **7️⃣ MAPPING TABLES**

---

## **A. Trading Mode Selection**

| Mode | is\_range\_break\_out | is\_btst\_stbt | isIntraday |
|------|----------------------|----------------|------------|
| Normal Intraday | false | false | true |
| Normal Positional | false | false | false |
| Range Breakout | true | false | true or false |
| BTST/STBT | false | true | false (forced) |

---

## **B. ATM Type Mapping**

| atmType | Active Sub-fields |
|---------|--------------------|
| Fix | atm offset (e.g., 0, +100, -100) |
| Dynamic | premiumStartRange, premiumEndRange |

---

## **C. Trade Side Mapping**

| tradeSide | Use Case |
|-----------|----------|
| BUY | Long call/put, buy futures, buy stock |
| SELL | Write call/put, short futures, short stock |

---

## **D. Reentry / Reexecute Options**

| Field | Allowed Values |
|-------|----------------|
| reentry\_on | None, TP Only, SL Only, TP SL Both |
| reexecute\_on | None, TP Only, SL Only, TP SL Both |

---

## **E. Wait and Trade Directions**

| wait\_for | Meaning |
|-----------|---------|
| UP % | Wait for upward % rise in premium |
| Down % | Wait for downward % drop |
| Up Pts. | Wait for upward point rise |
| Down Pts. | Wait for downward point drop |
| None | Wait and Trade disabled |

---

## **F. Trail SL By (Leg Level)**

| trail\_sl\_by | Unit |
|---------------|------|
| Point | Points |
| Money | Rupees |
| Percentage(%) | Percentage |

---

## **G. Master Target/SL By**

| targetBy / slBy | Unit |
|------------------|------|
| Money | Rupees |
| Point | Points |
| Total Premium(%) | Percentage of total combined premium |

---

## **H. VIX Filter**

| enableVixFilter | Behavior |
|------------------|----------|
| true | Cycle entry only when VIX is within [vixStartValue, vixEndValue] |
| false | No VIX gating |

---

## **I. Index Move By**

| index\_move\_by | Unit |
|------------------|------|
| Percentage(%) | % movement of underlying |
| Point | Absolute point movement |

---

# **8️⃣ VALIDATION RULES**

* Strategy Name is required and unique  
* At least 1 leg must be present in `sub[]`  
* Each leg must have valid Exchange, Segment, Symbol  
* If BTST/STBT → isIntraday must be false  
* If Range Breakout → range\_time (Candle End Time) must be set and > Candle Start Time  
* If Dynamic ATM → premiumStartRange and premiumEndRange must both be > 0 and Start <= End  
* If is\_trail\_sl is true at leg level → trail\_sl\_market\_move and trail\_sl\_move must be > 0 for trailing to activate  
* If isTrailSl is true at master level with Dynamic → profitMove and slMove must be > 0 (or is\_live\_mtm\_profit\_move must be true)  
* If isTrailSl is true at master level with Fix → fixTrail must contain at least one row  
* If isResetCycle is true → resetCycleIndexPercentage must be > 0 and noOfCyclePerDay must be > 0  
* is\_range\_break\_out and is\_btst\_stbt cannot both be true  
* For Range Breakout legs: only Trail SL checkbox is honored; reentry\_on / reexecute\_on / is\_wait\_and\_trade must remain at defaults  
* For BTST/STBT legs: only Trail SL checkbox is honored; reentry\_on / reexecute\_on / is\_wait\_and\_trade must remain at defaults

---

# **9️⃣ SAMPLE PROMPTS AND RESPONSES**

---

### **Example 1**

**User:** "Create a Banknifty intraday short straddle. Sell ATM CE and ATM PE, 1 lot each. Master SL 3000, Master Target 5000. Sqroff All Legs when any leg hits target."

**Copilot output:**

* Trading Mode: Normal, Trading Type: Intraday  
* Underlying: BANKNIFTY FUT NFO  
* Leg 1: NIFTY OPT NEAR WEEKLY, atm=0, optionType=CE, atmType=Fix, tradeSide=SELL, qty=1 Lot  
* Leg 2: NIFTY OPT NEAR WEEKLY, atm=0, optionType=PE, atmType=Fix, tradeSide=SELL, qty=1 Lot  
* Master TP: 5000 Money, Master SL: 3000 Money  
* Sqroff All Legs: true  
* Working Days: Mon–Fri  
* No clarifying questions

---

### **Example 2**

**User:** "Build a NIFTY weekly iron condor, 100 OTM wings, premium between 80 and 100 for short legs. Master SL 4000."

**Copilot output:**

* 4 legs: short CE (Dynamic, 80-100), long CE OTM 100 (Fix, +100), short PE (Dynamic, 80-100), long PE OTM 100 (Fix, -100)  
* Master SL: 4000 Money  
* Sqroff All Legs: true (basket exit)

---

### **Example 3**

**User:** "BTST short straddle on Banknifty. Trail SL 5 points per leg with market move of 3 points."

**Copilot output:**

* Trading Mode: BTST/STBT (is\_btst\_stbt=true)  
* isIntraday: false (forced)  
* Two legs: BANKNIFTY OPT WEEKLY CE ATM SELL, BANKNIFTY OPT WEEKLY PE ATM SELL  
* Each leg: is\_trail\_sl=true, trail\_sl\_by=Point, trail\_sl\_market\_move=3, trail\_sl\_move=5  
* Other 3 per-leg checkboxes left at defaults

---

### **Example 4**

**User:** "5-minute opening range breakout strategy on NIFTY futures. 1 lot. SL 30 points. Trail 10 points after 20-point move."

**Copilot output:**

* Trading Mode: Range Breakout (is\_range\_break\_out=true)  
* entryTime: 09:15, range\_time: 09:20  
* Leg: NIFTY FUT NEAR MONTHLY, BUY, qty=1 Lot, sl=30 Point, range\_breakout\_direction=High  
* is\_trail\_sl=true, trail\_sl\_by=Point, trail\_sl\_market\_move=20, trail\_sl\_move=10

---

### **Example 5**

**User:** "Positional Banknifty butterfly. Master SL 5000. Exit Thursday 12:00 before expiry."

**Copilot output:**

* Trading Mode: Normal, Trading Type: Positional  
* 3 legs: long ATM-100 CE, short 2× ATM CE, long ATM+100 CE  
* Master SL: 5000 Money  
* Sqroff by Fix Time: enabled, sqroffWeekDay="Thursday", sqroffTime="12:00", sqroff\_before\_expiry\_days=0

---

# **🔟 COPILOT MUST ALWAYS INCLUDE DESCRIPTION TAB**

Copilot must generate:

**Short Description**  
A one-line summary of the multi-leg structure, mode, and key controls.

**Long Description**  
Detailed explanation of the structure, leg roles, entry timing, target/SL, trail rules, and any special advance-tab features used.

---

# **1️⃣1️⃣ WHAT COPILOT MUST NEVER DO**

❌ Never set both `is_range_break_out` and `is_btst_stbt` to true  
❌ Never leave `sub[]` empty — at least one leg required  
❌ Never set `reentry_on = "None"` when the user implies Reentry should be active  
❌ Never set BTST/STBT with `isIntraday=true`  
❌ Never set Dynamic ATM with `premiumStartRange=0` or `premiumEndRange=0`  
❌ Never enable Trail SL at the leg without setting `trail_sl_market_move` and `trail_sl_move`  
❌ Never enable Master Trail Fix without populating `fixTrail` with at least one row  
❌ Never enable Master Trail Dynamic with all of `profitMove`, `slMove`, `noOfTrailSL` set to 0 and `is_live_mtm_profit_move=0`  
❌ Never assume Range Breakout legs support Reentry / Reexecute / Wait and Trade — only Trail SL is honored  
❌ Never assume BTST/STBT legs support Reentry / Reexecute / Wait and Trade — only Trail SL is honored  
❌ Never enable Dynamic Index Movement for Positional or BTST/STBT (Intraday only)  
❌ Never enable Sqroff by Fix Time for Intraday (Positional or BTST/STBT only)  
❌ Never set ATM offset or Option Type for FUT / Stock legs

---

# **1️⃣2️⃣ DEFAULTS COPILOT SHOULD USE**

**Main tab:**

* Trading Mode: Normal (is\_range\_break\_out=false, is\_btst\_stbt=false)  
* Trading Type: Intraday (isIntraday=true)  
* Product: MIS (Intraday) / NRML (Positional or BTST)  
* Entry Time: 09:16  
* Sqroff Time: 15:29  
* range\_time (Candle End Time): 09:17

**Per leg:**

* atmType: Fix  
* atm: 0  
* qtyType: Qty  
* qty: 1 (Lot=1)  
* tradeSide: BUY  
* target: 0, targetBy: Money  
* sl: 0, slBy: Money  
* is\_trail\_sl: false  
* trail\_sl\_by: Point  
* reentry\_on: None  
* reexecute\_on: None  
* is\_wait\_and\_trade: false  
* wait\_for: None  
* range\_breakout\_direction: High  
* qty\_distribution: Fix  
* workingDay: ALL  
* product: null

**Advance tab:**

* Master target: 0, targetBy: Money  
* Master sl: 0, slBy: Money  
* isTrailSl: false  
* trailType: Dynamic  
* profitMove / slMove / noOfTrailSL: 0  
* is\_live\_mtm\_profit\_move: 0  
* noOfIntradayCycle: 1  
* intraday\_cycle\_delay: 0  
* enableVixFilter: false  
* vixStartValue / vixEndValue: 0  
* isResetCycle: false  
* index\_move\_by: Percentage(%)  
* resetCycleIndexPercentage / noOfCyclePerDay: 0  
* sqroffByFixTime: false  
* sqroffWeekDay: ""  
* sqroffTime: ""  
* sqroff\_before\_expiry\_days: 0  
* chk\_con\_delay\_after\_market\_start: 0  
* Working Days: mon=tue=wed=thu=fri=true, sat=sun=false  
* requiredMargin: 1  
* squareoffLegs / squareoffRejection / allowLateTrading / cosider\_closed\_pnl: false  
* fixTrail: ""

**Hidden / fixed:**

* followSimulator: true  
* paperTrading: true  
* allowUpdateParameters: true  
* effect\_all\_sub\_strategies: false  
* requiredCapital: 1  
* isEditCode: false  
* pauseAndSqrOffOnMarginExceed: true  
* qtyMultiply: 1  
* rebacktest: false

---

# **1️⃣3️⃣ INTERNAL COPILOT DECISION PRIORITY TREE**

1. **Which mode?** → Normal / Range Breakout / BTST/STBT  
2. **Which Trading Type?** → Intraday / Positional (forced Positional for BTST/STBT)  
3. **Which legs?** → For each leg: Exchange, Segment, Symbol, Contract, Expiry, ATM Type, ATM/Premium, Option Type, Trade Side, Lot/Qty, Target, SL  
4. **Which per-leg checkboxes?** → Trail SL / Reentry / Reexecute / Wait and Trade (Reentry/Reexecute/Wait hidden in Range Breakout and BTST/STBT)  
5. **Master TP/SL?** → If user mentions combined target/SL → set; else 0  
6. **Master Trail?** → Dynamic ladder or Fix table  
7. **Which Advance sections apply?** → Based on mode:  
   * Normal Intraday → Trading Cycle, VIX, Dynamic Index  
   * Normal Positional → Trading Cycle, VIX, Sqroff by Fix Time, Condition Checking Time  
   * Range Breakout → none of the above  
   * BTST/STBT → Sqroff by Fix Time, Condition Checking Time  
8. **Safety toggles** → Sqroff All Legs, Trail to Cost, Sqroff on Rejection, Allow Late Trading, Consider Closed PNL  
9. **Working Days** → default Mon–Fri  
10. **Apply hidden defaults** → followSimulator, paperTrading, qtyMultiply, etc.  
11. **Validate all fields** per Section 8 rules  
12. **Generate full JSON payload**

---

# **1️⃣4️⃣ FINAL COPILOT OUTPUT STRUCTURE**

The final JSON payload follows this structure (field order matches the API spec):

1. Header: `id`, `strategyName`, `shortDescription`, `longDescription`, `strategyId` (always `RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$`)  
2. Underlying: `exchange`, `segment`, `symbol`, `underlying` (string)  
3. Timing: `entryTime`, `exitTime`, `range_time`  
4. Product: `productType`, `isIntraday`, `qtyMultiply`  
5. Master TP/SL: `targetBy`, `target`, `slBy`, `sl`  
6. Working Days: `mon`–`sun`  
7. Required Margin: `requiredMargin`, `requiredCapital`  
8. Safety: `squareoffLegs`, `squareoffRejection`, `allowLateTrading`, `cosider_closed_pnl`, `pauseAndSqrOffOnMarginExceed`, `sqroffAllLegs`  
9. Cycle: `noOfIntradayCycle`, `intraday_cycle_delay`  
10. VIX: `enableVixFilter`, `vixStartValue`, `vixEndValue`  
11. Master Trail: `isTrailSl`, `trailType`, `trail_sl_by`, `startTrailAfterProfit`, `profitMove`, `slMove`, `noOfTrailSL`, `is_live_mtm_profit_move`, `fixTrail`, `replaceMasterSlWithStartTrailing`  
12. Dynamic Index: `isResetCycle`, `index_move_by`, `resetCycleIndexPercentage`, `noOfCyclePerDay`  
13. Sqroff by Fix Time: `sqroffByFixTime`, `sqroffWeekDay`, `sqroffTime`, `sqroff_before_expiry_days`  
14. Condition Checking: `chk_con_delay_after_market_start`  
15. Mode flags: `is_btst_stbt`, `is_range_break_out`  
16. Engine flags: `followSimulator`, `paperTrading`, `allowUpdateParameters`, `effect_all_sub_strategies`, `isEditCode`, `rebacktest`  
17. **sub[]** array — each leg object contains:  
    * Symbol fields: `id`, `exchange`, `segment`, `symbol`, `contract`, `expiry`, `atm`, `strikePrice`, `optionType`  
    * Strategy fields: `atmType`, `qtyType`, `tradeSide`, `qty`, `lot`, `range_breakout_direction`, `qty_distribution`, `workingDay`, `product`  
    * Target/SL: `target`, `targetBy`, `sl`, `slBy`  
    * Trail SL: `is_trail_sl`, `trail_sl_by`, `trail_sl_market_move`, `trail_sl_move`, `no_of_time_trail_sl`, `trail_sl_cost`  
    * Dynamic ATM: `premiumStartRange`, `premiumEndRange`  
    * Reentry: `reentry_on`, `no_of_reentry`  
    * Reexecute: `reexecute_on`, `no_of_reexecute`, `reexecute_delay`  
    * Wait and Trade: `is_wait_and_trade`, `wait_for`, `wait_value`

---

# API Reference

## **Strategy Creation**

**Endpoint:** `POST https://api.marketmaya.com/api/mainStrategy/CreateMultiLegCallPutStrategy`  
**Authentication:** Bearer JWT token  
**Content-Type:** application/json  
**Strategy Type ID:** `RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$`

---

## **Sample Payload 1 — Minimal Positional (single FUT leg)**

```json
{
  "id": "",
  "strategyName": "12342123123",
  "shortDescription": "",
  "longDescription": "",
  "exchange": "NFO",
  "segment": "FUT",
  "symbol": "BANKNIFTY",
  "entryTime": "09:16",
  "exitTime": "15:29",
  "strategyId": "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$",
  "underlying": "BANKNIFTY FUT NFO",
  "productType": "NRML",
  "qtyMultiply": 1,
  "targetBy": "Money",
  "target": 0,
  "slBy": "Money",
  "sl": 0,
  "requiredMargin": 1,
  "mon": true, "tue": true, "wed": true, "thu": true, "fri": true, "sat": false, "sun": false,
  "followSimulator": true,
  "squareoffRejection": true,
  "squareoffLegs": false,
  "paperTrading": true,
  "allowLateTrading": true,
  "cosider_closed_pnl": false,
  "allowUpdateParameters": true,
  "isTrailSl": false,
  "isIntraday": false,
  "enableVixFilter": false,
  "vixStartValue": 0, "vixEndValue": 0,
  "trail_sl_by": "Money",
  "startTrailAfterProfit": 0, "profitMove": 0, "slMove": 0, "noOfTrailSL": 0,
  "noOfIntradayCycle": 1,
  "pauseAndSqrOffOnMarginExceed": true,
  "sqroffAllLegs": false,
  "sqroffByFixTime": false, "sqroffWeekDay": "", "sqroffTime": "",
  "replaceMasterSlWithStartTrailing": false,
  "isResetCycle": false, "resetCycleIndexPercentage": 0, "noOfCyclePerDay": 0,
  "trailType": "Dynamic",
  "is_btst_stbt": false,
  "is_live_mtm_profit_move": 0,
  "intraday_cycle_delay": 0,
  "is_range_break_out": false,
  "range_time": "09:17",
  "index_move_by": "Percentage(%)",
  "sqroff_before_expiry_days": 0,
  "chk_con_delay_after_market_start": 0,
  "fixTrail": "",
  "rebacktest": false,
  "sub": [
    {
      "exchange": "NFO", "segment": "FUT", "symbol": "BANKNIFTY",
      "contract": "NEAR", "expiry": "MONTHLY",
      "atm": 0, "strikePrice": 0, "optionType": "",
      "atmType": "Fix", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 30, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 0, "premiumEndRange": 0,
      "trail_sl_cost": false,
      "reentry_on": "None", "no_of_reentry": 0,
      "reexecute_delay": 0, "workingDay": "ALL",
      "wait_for": "None", "wait_value": 0,
      "reexecute_on": "None", "no_of_reexecute": 0
    }
  ],
  "requiredCapital": 1, "isEditCode": false, "effect_all_sub_strategies": false
}
```

---

## **Sample Payload 2 — Intraday with VIX Filter + Dynamic Index Movement**

```json
{
  "id": "xplRG7GPFZYR4j7aB0$FqArkAaC0$aC0$",
  "strategyName": "test intraday",
  "shortDescription": "", "longDescription": "",
  "exchange": "NSE", "segment": "INDEX", "symbol": "Nifty 50",
  "entryTime": "9:16", "exitTime": "15:29",
  "strategyId": "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$",
  "underlying": "Nifty 50 INDEX NSE",
  "productType": "MIS", "qtyMultiply": 1,
  "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
  "requiredMargin": 1,
  "mon": true, "tue": true, "wed": true, "thu": true, "fri": true, "sat": false, "sun": false,
  "followSimulator": true, "squareoffRejection": true, "squareoffLegs": false,
  "paperTrading": true, "allowLateTrading": true, "cosider_closed_pnl": false,
  "allowUpdateParameters": true,
  "isTrailSl": false, "isIntraday": true,
  "enableVixFilter": true, "vixStartValue": 15, "vixEndValue": 16,
  "trail_sl_by": "Money",
  "startTrailAfterProfit": 0, "profitMove": 0, "slMove": 0, "noOfTrailSL": 0,
  "noOfIntradayCycle": 1,
  "pauseAndSqrOffOnMarginExceed": true,
  "sqroffAllLegs": false,
  "sqroffByFixTime": false, "sqroffWeekDay": "", "sqroffTime": "",
  "replaceMasterSlWithStartTrailing": false,
  "isResetCycle": true, "resetCycleIndexPercentage": 100, "noOfCyclePerDay": 2,
  "trailType": "Dynamic",
  "is_btst_stbt": false,
  "is_live_mtm_profit_move": 0,
  "intraday_cycle_delay": 0,
  "is_range_break_out": false,
  "range_time": "9:17",
  "index_move_by": "Point",
  "sqroff_before_expiry_days": 0,
  "chk_con_delay_after_market_start": 0,
  "fixTrail": "",
  "rebacktest": true,
  "sub": [
    {
      "id": "f1jEDN1KIGHum2TmY1EaB0$KAaC0$aC0$",
      "exchange": "NFO", "segment": "OPT", "symbol": "NIFTY",
      "contract": "NEAR", "expiry": "WEEKLY",
      "atm": 0, "strikePrice": 0, "optionType": "CE",
      "atmType": "Dynamic", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 65, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 100, "premiumEndRange": 100,
      "trail_sl_cost": false,
      "reentry_on": "None", "no_of_reentry": 0,
      "reexecute_delay": 0, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": false, "wait_for": "None", "wait_value": 0,
      "reexecute_on": "None", "no_of_reexecute": 0
    }
  ],
  "requiredCapital": 1, "isEditCode": false, "effect_all_sub_strategies": false
}
```

---

## **Sample Payload 3 — Positional with Sqroff by Fix Time**

```json
{
  "id": "kzg5E5aA0$ZAC6ikxil6t0kFgaC0$aC0$",
  "strategyName": "test positional",
  "shortDescription": "", "longDescription": "",
  "exchange": "NSE", "segment": "INDEX", "symbol": "Nifty 50",
  "entryTime": "9:16", "exitTime": "15:29",
  "strategyId": "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$",
  "underlying": "Nifty 50 INDEX NSE",
  "productType": "NRML", "qtyMultiply": 1,
  "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
  "requiredMargin": 1,
  "mon": true, "tue": true, "wed": true, "thu": true, "fri": true, "sat": false, "sun": false,
  "followSimulator": true, "squareoffRejection": true, "squareoffLegs": false,
  "paperTrading": true, "allowLateTrading": true, "cosider_closed_pnl": false,
  "allowUpdateParameters": true,
  "isTrailSl": false, "isIntraday": false,
  "enableVixFilter": true, "vixStartValue": 15, "vixEndValue": 16,
  "trail_sl_by": "Money",
  "startTrailAfterProfit": 0, "profitMove": 0, "slMove": 0, "noOfTrailSL": 0,
  "noOfIntradayCycle": 2,
  "pauseAndSqrOffOnMarginExceed": true,
  "sqroffAllLegs": false,
  "sqroffByFixTime": true, "sqroffWeekDay": "Thursday", "sqroffTime": "12:00",
  "replaceMasterSlWithStartTrailing": false,
  "isResetCycle": true, "resetCycleIndexPercentage": 100, "noOfCyclePerDay": 2,
  "trailType": "Dynamic",
  "is_btst_stbt": false,
  "is_live_mtm_profit_move": 0,
  "intraday_cycle_delay": 10,
  "is_range_break_out": false,
  "range_time": "9:17",
  "index_move_by": "Point",
  "sqroff_before_expiry_days": 1,
  "chk_con_delay_after_market_start": 60,
  "fixTrail": "",
  "run_sat": false, "run_sun": false,
  "rebacktest": true,
  "sub": [
    {
      "id": "VnBvXcaA0$KBIaBgDL550C0eQaC0$aC0$",
      "exchange": "NFO", "segment": "OPT", "symbol": "NIFTY",
      "contract": "NEAR", "expiry": "WEEKLY",
      "atm": 0, "strikePrice": 0, "optionType": "CE",
      "atmType": "Dynamic", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 65, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 100, "premiumEndRange": 100,
      "trail_sl_cost": false,
      "reentry_on": "None", "no_of_reentry": 0,
      "reexecute_delay": 0, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": false, "wait_for": "None", "wait_value": 0,
      "reexecute_on": "None", "no_of_reexecute": 0
    }
  ],
  "requiredCapital": 1, "isEditCode": false, "effect_all_sub_strategies": false
}
```

---

## **Sample Payload 4 — BTST/STBT**

```json
{
  "id": "qFo8Qdcep2gnX5QVxwrvHQaC0$aC0$",
  "strategyName": "test btst",
  "shortDescription": "", "longDescription": "",
  "exchange": "NSE", "segment": "INDEX", "symbol": "Nifty 50",
  "entryTime": "9:16", "exitTime": "15:29",
  "strategyId": "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$",
  "underlying": "Nifty 50 INDEX NSE",
  "productType": "NRML", "qtyMultiply": 1,
  "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
  "requiredMargin": 1,
  "mon": true, "tue": true, "wed": true, "thu": true, "fri": true, "sat": false, "sun": false,
  "followSimulator": true, "squareoffRejection": true, "squareoffLegs": false,
  "paperTrading": true, "allowLateTrading": true, "cosider_closed_pnl": false,
  "allowUpdateParameters": true,
  "isTrailSl": false, "isIntraday": false,
  "enableVixFilter": false, "vixStartValue": 0, "vixEndValue": 0,
  "trail_sl_by": "Money",
  "startTrailAfterProfit": 0, "profitMove": 0, "slMove": 0, "noOfTrailSL": 0,
  "noOfIntradayCycle": 1,
  "pauseAndSqrOffOnMarginExceed": true,
  "sqroffAllLegs": false,
  "sqroffByFixTime": true, "sqroffWeekDay": "Thursday", "sqroffTime": "12:00",
  "replaceMasterSlWithStartTrailing": false,
  "isResetCycle": false, "resetCycleIndexPercentage": 0, "noOfCyclePerDay": 0,
  "trailType": "Dynamic",
  "is_btst_stbt": true,
  "is_live_mtm_profit_move": 0,
  "intraday_cycle_delay": 0,
  "is_range_break_out": false,
  "range_time": "9:17",
  "index_move_by": "Percentage(%)",
  "sqroff_before_expiry_days": 1,
  "chk_con_delay_after_market_start": 60,
  "fixTrail": "",
  "run_sat": false, "run_sun": false,
  "rebacktest": true,
  "sub": [
    {
      "id": "i8DfkIx2c7rrONyakpJJbgaC0$aC0$",
      "exchange": "NFO", "segment": "OPT", "symbol": "NIFTY",
      "contract": "NEAR", "expiry": "WEEKLY",
      "atm": 0, "strikePrice": 0, "optionType": "CE",
      "atmType": "Dynamic", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 65, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 100, "premiumEndRange": 100,
      "trail_sl_cost": false,
      "reentry_on": "None", "no_of_reentry": 0,
      "reexecute_delay": 0, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": false, "wait_for": "None", "wait_value": 0,
      "reexecute_on": "None", "no_of_reexecute": 0
    }
  ],
  "requiredCapital": 1, "isEditCode": false, "effect_all_sub_strategies": false
}
```

---

## **Sample Payload 5 — Full Multi-Leg (5 legs, all options used)**

```json
{
  "id": "Fkkgk1vl7kbCsRysW6cangaC0$aC0$",
  "strategyName": "test leg",
  "shortDescription": "", "longDescription": "",
  "exchange": "NFO", "segment": "FUT", "symbol": "BANKNIFTY",
  "entryTime": "9:16", "exitTime": "15:29",
  "strategyId": "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$",
  "underlying": "BANKNIFTY FUT NFO",
  "productType": "MIS", "qtyMultiply": 1,
  "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
  "requiredMargin": 1,
  "mon": true, "tue": true, "wed": true, "thu": true, "fri": true, "sat": false, "sun": false,
  "followSimulator": true, "squareoffRejection": true, "squareoffLegs": false,
  "paperTrading": true, "allowLateTrading": true, "cosider_closed_pnl": false,
  "allowUpdateParameters": true,
  "isTrailSl": false, "isIntraday": true,
  "enableVixFilter": false, "vixStartValue": 0, "vixEndValue": 0,
  "trail_sl_by": "Money",
  "startTrailAfterProfit": 0, "profitMove": 0, "slMove": 0, "noOfTrailSL": 0,
  "noOfIntradayCycle": 1,
  "pauseAndSqrOffOnMarginExceed": true,
  "sqroffAllLegs": false,
  "sqroffByFixTime": false, "sqroffWeekDay": "", "sqroffTime": "",
  "replaceMasterSlWithStartTrailing": false,
  "isResetCycle": false, "resetCycleIndexPercentage": 0, "noOfCyclePerDay": 0,
  "trailType": "Dynamic",
  "is_btst_stbt": false,
  "is_live_mtm_profit_move": 0,
  "intraday_cycle_delay": 0,
  "is_range_break_out": false,
  "range_time": "9:17",
  "index_move_by": "Percentage(%)",
  "sqroff_before_expiry_days": 0,
  "chk_con_delay_after_market_start": 0,
  "fixTrail": "",
  "rebacktest": true,
  "sub": [
    {
      "id": "sk337TaA0$Cjfw4DbjOdhNXRwaC0$aC0$",
      "exchange": "NFO", "segment": "FUT", "symbol": "BANKNIFTY",
      "contract": "NEAR", "expiry": "MONTHLY",
      "atm": 0, "strikePrice": 0, "optionType": "",
      "atmType": "Fix", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 30, "lot": 1,
      "targetBy": "Money", "target": 100, "slBy": "Money", "sl": 10,
      "trail_sl_market_move": 0.2, "trail_sl_move": 0.2, "no_of_time_trail_sl": 10,
      "is_trail_sl": true, "trail_sl_by": "Point",
      "premiumStartRange": 0, "premiumEndRange": 0,
      "trail_sl_cost": false,
      "reentry_on": "TP Only", "no_of_reentry": 1,
      "reexecute_delay": 2, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": true, "wait_for": "UP %", "wait_value": 10,
      "reexecute_on": "SL Only", "no_of_reexecute": 1
    },
    {
      "id": "tAoxnmU7zSGbvfKX99sD9waC0$aC0$",
      "exchange": "NFO", "segment": "OPT", "symbol": "BANKNIFTY",
      "contract": "NEAR", "expiry": "WEEKLY",
      "atm": 0, "strikePrice": 0, "optionType": "CE",
      "atmType": "Dynamic", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 30, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 100, "premiumEndRange": 1000,
      "trail_sl_cost": false,
      "reentry_on": "None", "no_of_reentry": 0,
      "reexecute_delay": 0, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": false, "wait_for": "None", "wait_value": 0,
      "reexecute_on": "None", "no_of_reexecute": 0
    },
    {
      "id": "nupqpAmoGoRAmkiPA8aB0$4KwaC0$aC0$",
      "exchange": "NFO", "segment": "OPT", "symbol": "BANKNIFTY",
      "contract": "NEAR", "expiry": "WEEKLY",
      "atm": 0, "strikePrice": 0, "optionType": "PE",
      "atmType": "Fix", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 30, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 0, "premiumEndRange": 0,
      "trail_sl_cost": false,
      "reentry_on": "TP Only", "no_of_reentry": 12,
      "reexecute_delay": 0, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": false, "wait_for": "None", "wait_value": 0,
      "reexecute_on": "None", "no_of_reexecute": 0
    },
    {
      "id": "DhYFXfhZGTh4XPeoytXQJAaC0$aC0$",
      "exchange": "NFO", "segment": "OPT", "symbol": "BANKNIFTY",
      "contract": "NEAR", "expiry": "WEEKLY",
      "atm": -100, "strikePrice": 0, "optionType": "PE",
      "atmType": "Fix", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 30, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 0, "premiumEndRange": 0,
      "trail_sl_cost": false,
      "reentry_on": "None", "no_of_reentry": 0,
      "reexecute_delay": 8, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": false, "wait_for": "None", "wait_value": 0,
      "reexecute_on": "SL Only", "no_of_reexecute": 1
    },
    {
      "id": "cd8tUhWX5yRZYUL8HjxG5waC0$aC0$",
      "exchange": "NFO", "segment": "FUT", "symbol": "BANKNIFTY",
      "contract": "FAR", "expiry": "MONTHLY",
      "atm": 0, "strikePrice": 0, "optionType": "",
      "atmType": "Fix", "qtyType": "Qty", "tradeSide": "BUY",
      "range_breakout_direction": "High",
      "qty_distribution": "Fix", "qty": 30, "lot": 1,
      "targetBy": "Money", "target": 0, "slBy": "Money", "sl": 0,
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0,
      "is_trail_sl": false, "trail_sl_by": "Point",
      "premiumStartRange": 0, "premiumEndRange": 0,
      "trail_sl_cost": false,
      "reentry_on": "None", "no_of_reentry": 0,
      "reexecute_delay": 0, "product": null, "workingDay": "ALL",
      "is_wait_and_trade": true, "wait_for": "UP %", "wait_value": 12,
      "reexecute_on": "None", "no_of_reexecute": 0
    }
  ],
  "requiredCapital": 1, "isEditCode": false, "effect_all_sub_strategies": false
}
```

---

## **API Field Reference Table**

| UI Field | DB / API Field | Type | Notes |
|----------|----------------|------|-------|
| Trading Mode | is\_range\_break\_out + is\_btst\_stbt | boolean pair | Both false = Normal |
| Strategy Name | strategyName | string | Required, unique |
| Underlying Symbol | exchange, segment, symbol, underlying | composite | Strategy-level reference |
| Trading Type | isIntraday | boolean | Forced false for BTST/STBT |
| Product | productType | string | MIS / NRML / CNC |
| Entry Time | entryTime | string (HH:mm) | In Range Breakout, holds Candle Start Time |
| Sqroff Time / Next Day Sqroff Time | exitTime | string (HH:mm) | Label changes for BTST/STBT |
| Candle End Time | range\_time | string (HH:mm) | Always sent; relevant in Range Breakout |
| Master Target | target + targetBy | number + string | targetBy ∈ Money/Point/Total Premium(%) |
| Master SL | sl + slBy | number + string | slBy ∈ Money/Point/Total Premium(%) |
| Trail SL? (Master) | isTrailSl | boolean | |
| Trail Type | trailType | string | Dynamic / Fix |
| Profit Move | profitMove | number | Dynamic master trail |
| SL Move | slMove | number | Dynamic master trail |
| No of Trail SL | noOfTrailSL | number | 0 = infinite |
| Live max MTM as profit move | is\_live\_mtm\_profit\_move | number (0/1) | |
| Fix Trail Table | fixTrail | string (JSON) | |
| Start Trail After Profit | startTrailAfterProfit | number | Always sent |
| Replace Master SL With Start Trailing | replaceMasterSlWithStartTrailing | boolean | Always sent |
| Working Days | mon, tue, wed, thu, fri, sat, sun | booleans | Mon-Fri true by default |
| — (Positional/BTST) | run\_sat | boolean | API-only; mirrors `sat`; sent in Positional and BTST payloads. Always false. |
| — (Positional/BTST) | run\_sun | boolean | API-only; mirrors `sun`; sent in Positional and BTST payloads. Always false. |
| Required Margin | requiredMargin | number | Analytics only |
| Sqroff All Legs | squareoffLegs / sqroffAllLegs | boolean | |
| Trail SL to Cost (per leg) | sub[].trail\_sl\_cost | boolean | Per-leg field |
| Sqroff Position on Rejection | squareoffRejection | boolean | |
| Allow Late Trading | allowLateTrading | boolean | |
| Consider Closed Trades PNL | cosider\_closed\_pnl | boolean | Typo: single 'n' |
| No of Cycle | noOfIntradayCycle | number | |
| Cycle Delay (Minute) | intraday\_cycle\_delay | number | |
| VIX Filter | enableVixFilter | boolean | |
| VIX Start Value | vixStartValue | number | |
| VIX End Value | vixEndValue | number | |
| Dynamic Index Movement (Enable) | isResetCycle | boolean | Intraday only |
| Index Move By | index\_move\_by | string | Percentage(%) / Point |
| Index Movement | resetCycleIndexPercentage | number | |
| No of Cycle Per Day | noOfCyclePerDay | number | |
| Sqroff by Fix Time | sqroffByFixTime | boolean | Positional / BTST only |
| Sqroff Week Day | sqroffWeekDay | string | Day name |
| Sqroff Time (Fix) | sqroffTime | string (HH:mm) | |
| Exit before Expiry Days | sqroff\_before\_expiry\_days | number | 0 = expiry day |
| Condition Checking Time | chk\_con\_delay\_after\_market\_start | number | Minutes |
| Short Description | shortDescription | string | |
| Long Description | longDescription | string | |
| Strategy Type (fixed) | strategyId | string | Always RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$ |
| — | followSimulator | boolean | Always true (deployment) |
| — | paperTrading | boolean | Always true (deployment) |
| — | allowUpdateParameters | boolean | Always true |
| — | effect\_all\_sub\_strategies | boolean | Always false |
| — | requiredCapital | number | Always 1 |
| — | isEditCode | boolean | False on create |
| — | pauseAndSqrOffOnMarginExceed | boolean | Always true |
| — | qtyMultiply | number | Set at deployment |
| — | rebacktest | boolean | true in backtest mode |
| Sub: ID | sub[].id | string | Auto-generated; "" on create |
| Sub: Exchange | sub[].exchange | string | NSE-EQ/NFO/BFO/BSE/MCX/CDS/CRYPTO |
| Sub: Segment | sub[].segment | string | FUT / OPT / Stock / INDEX |
| Sub: Symbol | sub[].symbol | string | |
| Sub: Contract | sub[].contract | string | NEAR / NEXT / FAR |
| Sub: Expiry | sub[].expiry | string | MONTHLY / WEEKLY |
| Sub: ATM | sub[].atm | integer | 0 = ATM |
| Sub: Strike Price | sub[].strikePrice | number | 0 = use ATM |
| Sub: Option Type | sub[].optionType | string | CE / PE / "" |
| Sub: ATM Type | sub[].atmType | string | Fix / Dynamic |
| Sub: Premium Start Range | sub[].premiumStartRange | number | Dynamic only |
| Sub: Premium End Range | sub[].premiumEndRange | number | Dynamic only |
| Sub: Qty Type | sub[].qtyType | string | Lot / Qty |
| Sub: Qty | sub[].qty | number | |
| Sub: Lot | sub[].lot | number | |
| Sub: Trade Side | sub[].tradeSide | string | BUY / SELL |
| Sub: Target | sub[].target | number | |
| Sub: Target By | sub[].targetBy | string | Money / Point / Percentage(%) |
| Sub: SL | sub[].sl | number | |
| Sub: SL By | sub[].slBy | string | Money / Point / Percentage(%) |
| Sub: Trail SL | sub[].is\_trail\_sl | boolean | |
| Sub: Trail SL By | sub[].trail\_sl\_by | string | Point / Money / Percentage(%) |
| Sub: Market Move | sub[].trail\_sl\_market\_move | number | |
| Sub: SL Move | sub[].trail\_sl\_move | number | |
| Sub: No of Trail SL | sub[].no\_of\_time\_trail\_sl | number | 0 = infinite |
| Sub: Trail to Cost | sub[].trail\_sl\_cost | boolean | |
| Sub: Reentry On | sub[].reentry\_on | string | None/TP Only/SL Only/TP SL Both |
| Sub: No of Reentry | sub[].no\_of\_reentry | number | |
| Sub: Reexecute On | sub[].reexecute\_on | string | None/TP Only/SL Only/TP SL Both |
| Sub: No of Reexecute | sub[].no\_of\_reexecute | number | |
| Sub: Reexecute Delay | sub[].reexecute\_delay | number | Minutes |
| Sub: Wait and Trade | sub[].is\_wait\_and\_trade | boolean | |
| Sub: Wait Value | sub[].wait\_value | number | |
| Sub: Wait Direction | sub[].wait\_for | string | UP %/Down %/Up Pts./Down Pts./None |
| Sub: Breakout Direction | sub[].range\_breakout\_direction | string | High / Low (Range Breakout only) |
| Sub: Qty Distribution | sub[].qty\_distribution | string | Always "Fix" |
| Sub: Working Day | sub[].workingDay | string | Always "ALL" |
| Sub: Product | sub[].product | null | Always null |
